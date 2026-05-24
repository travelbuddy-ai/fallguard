/**
 * @file app_fall_handler.h
 * @brief Fall detection response handler
 *
 * Flow:
 *   Fall confirmed → screen lights up + alert tone
 *   → "Are you okay? Say YES or NO" displayed
 *   → FREE listening mode, 30s timeout
 *   YES     → POST /fall-response "ok"  → user_ok DP → Smart Life push
 *   NO      → POST /fall-response "help" → needs_help DP → Smart Life push
 *             + repeat every 60s until acknowledged
 *   Timeout → same as NO, "no response" message shown
 */

#ifndef __APP_FALL_HANDLER_H__
#define __APP_FALL_HANDLER_H__

#include "tuya_cloud_types.h"

#ifdef __cplusplus
extern "C" {
#endif

OPERATE_RET app_fall_handler_init(void);
void        app_fall_detected(void);
bool        app_fall_response_is_pending(void);
void        app_fall_handle_asr_text(const char *text);
void        app_fall_acknowledge(void);

#ifdef __cplusplus
}
#endif

#endif /* __APP_FALL_HANDLER_H__ */
