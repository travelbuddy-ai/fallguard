/**
 * @file app_fall_handler.c
 * @brief Fall detection response handler
 */

#include <string.h>
#include <ctype.h>

#include "tal_api.h"
#include "tuya_iot.h"
#include "tuya_iot_dp.h"
#include "app_fall_handler.h"
#include "tuya_config.h"

#if defined(ENABLE_COMP_AI_DISPLAY) && (ENABLE_COMP_AI_DISPLAY == 1)
#include "ai_ui_manage.h"
#endif

#if defined(ENABLE_COMP_AI_AUDIO) && (ENABLE_COMP_AI_AUDIO == 1)
#include "ai_audio_player.h"
#endif

#include "ai_manage_mode.h"

#define FALL_RESPONSE_TIMEOUT_MS  (30 * 1000)
#define FALL_REPEAT_INTERVAL_MS   (60 * 1000)

/***********************************************************
 * DP IDs — must match the Tuya IoT Platform definition
 ***********************************************************/
#define DPID_USER_OK    104
#define DPID_NEEDS_HELP 105

/***********************************************************
 * Internal state
 ***********************************************************/
typedef enum {
    FALL_STATE_IDLE = 0,
    FALL_STATE_WAITING,    /* prompted user, waiting for yes/no */
    FALL_STATE_NEEDS_HELP, /* repeating alert every 60s */
} fall_state_t;

static volatile fall_state_t s_state       = FALL_STATE_IDLE;
static TIMER_ID              s_timeout_tmr = NULL;
static TIMER_ID              s_repeat_tmr  = NULL;
static AI_CHAT_MODE_E        s_saved_mode  = AI_CHAT_MODE_WAKEUP;

/***********************************************************
 * Helpers
 ***********************************************************/
static void _report_bool_dp(uint8_t dpid, bool value)
{
    tuya_iot_client_t *client = tuya_iot_client_get();
    if (!client || !client->is_activated) {
        return;
    }
    dp_obj_t dp = {
        .id            = dpid,
        .type          = PROP_BOOL,
        .value.dp_bool = value,
    };
    tuya_iot_dp_obj_report(client, client->activate.devid, &dp, 1, 0);
}

static void _show_screen(const char *status, const char *msg)
{
#if defined(ENABLE_COMP_AI_DISPLAY) && (ENABLE_COMP_AI_DISPLAY == 1)
    if (status) {
        ai_ui_disp_msg(AI_UI_DISP_STATUS, (uint8_t *)status, strlen(status));
    }
    if (msg) {
        ai_ui_disp_msg(AI_UI_DISP_SYSTEM_MSG, (uint8_t *)msg, strlen(msg));
    }
#endif
}

static void _start_listening(void)
{
    ai_mode_get_curr_mode(&s_saved_mode);
#if defined(ENABLE_COMP_AI_MODE_FREE) && (ENABLE_COMP_AI_MODE_FREE == 1)
    ai_mode_switch(AI_CHAT_MODE_FREE);
#endif
}

static void _restore_mode(void)
{
    ai_mode_switch(s_saved_mode);
}

/***********************************************************
 * Timer callbacks
 ***********************************************************/
static void _repeat_alert_cb(TIMER_ID timer_id, void *arg)
{
    if (s_state != FALL_STATE_NEEDS_HELP) {
        tal_sw_timer_stop(s_repeat_tmr);
        return;
    }
    PR_WARN("[FALL] Repeating needs_help alert");
    _report_bool_dp(DPID_NEEDS_HELP, true);
}

static void _timeout_cb(TIMER_ID timer_id, void *arg)
{
    if (s_state != FALL_STATE_WAITING) {
        return;
    }
    PR_WARN("[FALL] No response in 30s — treating as needs help");
    s_state = FALL_STATE_NEEDS_HELP;

    _show_screen("NO RESPONSE", "No response — alerting caregiver");
    _report_bool_dp(DPID_NEEDS_HELP, true);
    tal_sw_timer_start(s_repeat_tmr, FALL_REPEAT_INTERVAL_MS, TAL_TIMER_CYCLE);
    _restore_mode();
}

/***********************************************************
 * Public API
 ***********************************************************/
OPERATE_RET app_fall_handler_init(void)
{
    OPERATE_RET rt = OPRT_OK;
    TUYA_CALL_ERR_RETURN(tal_sw_timer_create(_timeout_cb,      NULL, &s_timeout_tmr));
    TUYA_CALL_ERR_RETURN(tal_sw_timer_create(_repeat_alert_cb, NULL, &s_repeat_tmr));
    return OPRT_OK;
}

void app_fall_detected(void)
{
    if (s_state != FALL_STATE_IDLE) {
        PR_WARN("[FALL] Already handling a fall — ignoring duplicate");
        return;
    }

    PR_NOTICE("[FALL] Fall detected — prompting user");
    s_state = FALL_STATE_WAITING;

#if defined(ENABLE_COMP_AI_AUDIO) && (ENABLE_COMP_AI_AUDIO == 1)
    ai_audio_player_alert(AI_AUDIO_ALERT_WAKEUP);
#endif

    _show_screen("FALL DETECTED", "Are you okay? Say YES or NO");
    _start_listening();
    tal_sw_timer_start(s_timeout_tmr, FALL_RESPONSE_TIMEOUT_MS, TAL_TIMER_ONCE);
}

bool app_fall_response_is_pending(void)
{
    return s_state == FALL_STATE_WAITING;
}

void app_fall_handle_asr_text(const char *text)
{
    if (s_state != FALL_STATE_WAITING || !text) {
        return;
    }

    tal_sw_timer_stop(s_timeout_tmr);

    /* Lowercase copy for keyword matching */
    char lower[128] = {0};
    size_t len = strlen(text);
    if (len >= sizeof(lower)) len = sizeof(lower) - 1;
    for (size_t i = 0; i < len; i++) {
        lower[i] = (char)tolower((unsigned char)text[i]);
    }

    bool is_yes = strstr(lower, "yes")  || strstr(lower, "yeah") ||
                  strstr(lower, "ok")   || strstr(lower, "fine") ||
                  strstr(lower, "good") || strstr(lower, "sure");
    bool is_no  = strstr(lower, "no")   || strstr(lower, "nope") ||
                  strstr(lower, "help") || strstr(lower, "hurt");

    if (is_yes && !is_no) {
        PR_NOTICE("[FALL] User said YES — reporting user_ok DP");
        s_state = FALL_STATE_IDLE;
        _show_screen("FALSE ALARM", "False alarm — person is okay");
        _report_bool_dp(DPID_USER_OK, true);
        _restore_mode();
    } else {
        PR_NOTICE("[FALL] User said NO — reporting needs_help DP");
        s_state = FALL_STATE_NEEDS_HELP;
        _show_screen("NEEDS HELP", "Person responded — alerting caregiver");
        _report_bool_dp(DPID_NEEDS_HELP, true);
        tal_sw_timer_start(s_repeat_tmr, FALL_REPEAT_INTERVAL_MS, TAL_TIMER_CYCLE);
        _restore_mode();
    }
}

void app_fall_acknowledge(void)
{
    if (s_state == FALL_STATE_NEEDS_HELP) {
        PR_NOTICE("[FALL] Caregiver acknowledged — stopping repeat alerts");
        tal_sw_timer_stop(s_repeat_tmr);
        s_state = FALL_STATE_IDLE;
        _show_screen("STANDBY", "Caregiver acknowledged");
    }
}
