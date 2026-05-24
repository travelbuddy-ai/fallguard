/**
 * @file app_camera_analyze.c
 * @brief Continuously captures JPEG frames and POSTs to the backend /analyze
 *        endpoint.  Triggers app_fall_detected() on a positive result.
 */

#include <stdint.h>
#include <stdbool.h>

#include "tal_api.h"
#include "cJSON.h"
#include "ai_video_input.h"
#include "http_client_interface.h"

#include "app_fall_handler.h"
#include "app_camera_analyze.h"
#include "tuya_config.h"

#define ANALYZE_INTERVAL_MS 1000
#define ANALYZE_TIMEOUT_MS  5000

static THREAD_HANDLE s_thread = NULL;

static void _analyze_task(void *arg)
{
    for (;;) {
        uint32_t t_start = tal_system_get_millisecond();

        /* Skip while already handling a fall response */
        if (app_fall_response_is_pending()) {
            tal_system_sleep(ANALYZE_INTERVAL_MS);
            continue;
        }

        uint8_t *jpeg = NULL;
        uint32_t jpeg_len = 0;
        if (ai_video_get_jpeg_frame(&jpeg, &jpeg_len) != OPRT_OK || !jpeg || jpeg_len == 0) {
            PR_WARN("[ANALYZE] failed to get JPEG frame");
            continue;
        }
        PR_DEBUG("[ANALYZE] got frame %u bytes, posting to backend", jpeg_len);

        http_client_header_t headers[2] = {
            { .key = "Content-Type",  .value = "image/jpeg"          },
            { .key = "X-Device-ID",   .value = TUYA_OPENSDK_UUID     },
        };

        http_client_response_t response = {0};
        http_client_status_t http_rt = http_client_request(
            &(const http_client_request_t){
                .host          = FALL_BACKEND_HOST,
                .port          = FALL_BACKEND_PORT,
                .path          = "/analyze",
                .method        = "POST",
                .headers       = headers,
                .headers_count = 2,
                .body          = jpeg,
                .body_length   = jpeg_len,
                .timeout_ms    = ANALYZE_TIMEOUT_MS,
                .cacert        = NULL,
                .cacert_len    = 0,
                .tls_no_verify = false,
            },
            &response
        );

        ai_video_jpeg_image_free(&jpeg);

        if (http_rt != HTTP_CLIENT_SUCCESS || response.status_code != 200) {
            PR_WARN("[ANALYZE] request failed: rt=%d status=%d", http_rt, response.status_code);
            http_client_free(&response);
            continue;
        }

        if (response.body && response.body_length > 0) {
            cJSON *json = cJSON_ParseWithLength((const char *)response.body, response.body_length);
            if (json) {
                cJSON *item = cJSON_GetObjectItem(json, "fall_detected");
                if (cJSON_IsTrue(item)) {
                    PR_NOTICE("[ANALYZE] Fall detected by backend — triggering response flow");
                    app_fall_detected();
                }
                cJSON_Delete(json);
            }
        }

        http_client_free(&response);

        uint32_t elapsed = tal_system_get_millisecond() - t_start;
        if (elapsed < ANALYZE_INTERVAL_MS) {
            tal_system_sleep(ANALYZE_INTERVAL_MS - elapsed);
        }
    }
}

OPERATE_RET app_camera_analyze_init(void)
{
    THREAD_CFG_T cfg = {
        .thrdname   = "cam_analyze",
        .stackDepth = 8192,
        .priority   = THREAD_PRIO_3,
    };
    return tal_thread_create_and_start(&s_thread, NULL, NULL, _analyze_task, NULL, &cfg);
}
