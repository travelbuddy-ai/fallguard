/**
 * @file app_fall_handler.c
 * @brief Fall detection response handler
 */

#include <string.h>

#include "tal_api.h"
#include "app_fall_handler.h"

#if defined(ENABLE_COMP_AI_DISPLAY) && (ENABLE_COMP_AI_DISPLAY == 1)
#include "ai_ui_manage.h"
#endif

#include "ai_agent.h"

#define FALL_COOLDOWN_MS  (15 * 1000)

typedef enum {
    FALL_STATE_IDLE = 0,
    FALL_STATE_ACTIVE,
} fall_state_t;

static volatile fall_state_t s_state       = FALL_STATE_IDLE;
static TIMER_ID              s_timeout_tmr = NULL;

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

/***********************************************************
 * Timer callbacks
 ***********************************************************/
static void _cooldown_cb(TIMER_ID timer_id, void *arg)
{
    s_state = FALL_STATE_IDLE;
    PR_NOTICE("[FALL] Cooldown complete — ready for next detection");
}

/***********************************************************
 * Public API
 ***********************************************************/
OPERATE_RET app_fall_handler_init(void)
{
    OPERATE_RET rt = OPRT_OK;
    TUYA_CALL_ERR_RETURN(tal_sw_timer_create(_cooldown_cb, NULL, &s_timeout_tmr));
    return OPRT_OK;
}

void app_fall_detected(void)
{
    if (s_state != FALL_STATE_IDLE) {
        PR_WARN("[FALL] Already handling a fall — ignoring duplicate");
        return;
    }

    PR_NOTICE("[FALL] Fall detected — prompting user");
    s_state = FALL_STATE_ACTIVE;

    _show_screen("FALL DETECTED", "Fall detected — contacts alerted");
    ai_agent_send_text("You are here to assist people who have fallen. Please ONLY speak, 'A fall has been detected. Your emergency contacts have been alerted' and say nothing else.");
    tal_sw_timer_start(s_timeout_tmr, FALL_COOLDOWN_MS, TAL_TIMER_ONCE);
}

bool app_fall_response_is_pending(void)
{
    return s_state == FALL_STATE_ACTIVE;
}

void app_fall_handle_asr_text(const char *text)
{
    /* no-op: response flow not used */
}

void app_fall_acknowledge(void)
{
    /* no-op: caregiver ack flow not used */
}
