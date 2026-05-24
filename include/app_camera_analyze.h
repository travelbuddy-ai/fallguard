/**
 * @file app_camera_analyze.h
 * @brief Continuous camera → /analyze fall detection loop
 */

#ifndef APP_CAMERA_ANALYZE_H
#define APP_CAMERA_ANALYZE_H

#include "tuya_cloud_types.h"

/**
 * @brief Spawn the background task that captures JPEG frames and POSTs them
 *        to the backend /analyze endpoint.  Call once after MQTT connects.
 */
OPERATE_RET app_camera_analyze_init(void);

#endif /* APP_CAMERA_ANALYZE_H */
