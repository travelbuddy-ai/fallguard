#include <stdio.h>
#include "ui_fallguard.h"
#include "lvgl.h"
#include "tal_log.h"

static lv_obj_t *sg_camera_canvas = NULL;
static lv_obj_t *sg_status_bar    = NULL;
static lv_obj_t *sg_status_label  = NULL;
static lv_obj_t *sg_score_label   = NULL;
static lv_obj_t *sg_alert_box     = NULL;

void ui_fallguard_init(void)
{
    lv_obj_set_style_bg_color(lv_scr_act(), lv_color_black(), 0);
    lv_obj_set_style_bg_opa(lv_scr_act(), LV_OPA_COVER, 0);

    sg_camera_canvas = lv_canvas_create(lv_scr_act());
    lv_obj_set_size(sg_camera_canvas, 320, 240);
    lv_obj_align(sg_camera_canvas, LV_ALIGN_TOP_MID, 0, 0);

    sg_status_bar = lv_obj_create(lv_scr_act());
    lv_obj_set_size(sg_status_bar, 320, 40);
    lv_obj_align(sg_status_bar, LV_ALIGN_BOTTOM_MID, 0, 0);
    lv_obj_set_style_bg_color(sg_status_bar, lv_color_make(0, 200, 0), 0);
    lv_obj_set_style_border_width(sg_status_bar, 0, 0);
    lv_obj_set_style_radius(sg_status_bar, 0, 0);

    sg_status_label = lv_label_create(sg_status_bar);
    lv_label_set_text(sg_status_label, "FallGuard: Monitoring");
    lv_obj_set_style_text_color(sg_status_label, lv_color_white(), 0);
    lv_obj_align(sg_status_label, LV_ALIGN_LEFT_MID, 8, 0);

    sg_score_label = lv_label_create(sg_status_bar);
    lv_label_set_text(sg_score_label, "Score: 0");
    lv_obj_set_style_text_color(sg_score_label, lv_color_white(), 0);
    lv_obj_align(sg_score_label, LV_ALIGN_RIGHT_MID, -8, 0);

    TAL_PR_INFO("FallGuard UI initialized");
}

void ui_fallguard_camera_update(uint8_t *data, int width, int height)
{
    if (!sg_camera_canvas || !data) return;
    lv_canvas_set_buffer(sg_camera_canvas, data,
                         width, height, LV_IMG_CF_TRUE_COLOR);
    lv_obj_invalidate(sg_camera_canvas);
}

void ui_fallguard_set_state(FALLGUARD_STATE_E state)
{
    if (!sg_status_bar) return;
    switch (state) {
    case FALLGUARD_STATE_MONITORING:
        lv_obj_set_style_bg_color(sg_status_bar, lv_color_make(0, 200, 0), 0);
        lv_label_set_text(sg_status_label, "FallGuard: Monitoring");
        if (sg_alert_box) { lv_obj_del(sg_alert_box); sg_alert_box = NULL; }
        break;
    case FALLGUARD_STATE_MOTION:
        lv_obj_set_style_bg_color(sg_status_bar, lv_color_make(255, 165, 0), 0);
        lv_label_set_text(sg_status_label, "Motion Detected!");
        break;
    case FALLGUARD_STATE_FALL:
        lv_obj_set_style_bg_color(sg_status_bar, lv_color_make(220, 0, 0), 0);
        lv_label_set_text(sg_status_label, "FALL DETECTED!");
        if (!sg_alert_box) {
            sg_alert_box = lv_obj_create(lv_scr_act());
            lv_obj_set_size(sg_alert_box, 280, 100);
            lv_obj_align(sg_alert_box, LV_ALIGN_CENTER, 0, -20);
            lv_obj_set_style_bg_color(sg_alert_box, lv_color_make(220, 0, 0), 0);
            lv_obj_set_style_border_color(sg_alert_box, lv_color_white(), 0);
            lv_obj_set_style_border_width(sg_alert_box, 2, 0);
            lv_obj_t *lbl = lv_label_create(sg_alert_box);
            lv_label_set_text(lbl, "FALL DETECTED\nAlert sent!");
            lv_obj_set_style_text_color(lbl, lv_color_white(), 0);
            lv_obj_set_style_text_align(lbl, LV_TEXT_ALIGN_CENTER, 0);
            lv_obj_align(lbl, LV_ALIGN_CENTER, 0, 0);
        }
        break;
    }
}

void ui_fallguard_set_motion_score(int score)
{
    if (!sg_score_label) return;
    char buf[32];
    snprintf(buf, sizeof(buf), "Score: %d", score / 1000);
    lv_label_set_text(sg_score_label, buf);
}
