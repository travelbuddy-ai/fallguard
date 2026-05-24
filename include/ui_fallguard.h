#ifndef UI_FALLGUARD_H
#define UI_FALLGUARD_H

#include "lvgl.h"

typedef enum {
    FALLGUARD_STATE_MONITORING,
    FALLGUARD_STATE_MOTION,
    FALLGUARD_STATE_FALL,
} FALLGUARD_STATE_E;

void ui_fallguard_init(void);
void ui_fallguard_camera_update(uint8_t *data, int width, int height);
void ui_fallguard_set_state(FALLGUARD_STATE_E state);
void ui_fallguard_set_motion_score(int score);

#endif
