# Copyright 2016 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

AUTHOR = "Chrome OS Project, chromeos-video@google.com"
NAME = "video_ChromeCameraMJpegHWDecodeUsed.arc"
PURPOSE = "Verify MJPEG camera video are HW accelerated."
ATTRIBUTES = "suite:arc-bvt-cq, suite:bvt-cq"
TIME = "SHORT"
TEST_CATEGORY = "General"
TEST_CLASS = "video"
TEST_TYPE = "client"
DEPENDENCIES = "hw_jpeg_acc_dec, arc"
JOB_RETRIES = 2
BUG_TEMPLATE = {
    'labels': ['OS-Chrome', 'VideoTestFailure'],
    'cc': ['chromeos-video-test-failures@google.com'],
}
ARC_MODE = "enabled"

DOC = """
Verify MJPEG camera video streams are HW accelerated.
"""

job.run_test('video_ChromeRTCHWDecodeUsed',
             video_name='crowd720_25frames.mjpeg',
             histogram_name='Media.VideoCaptureGpuJpegDecoder.InitDecodeSuccess',
             histogram_bucket_val=1,
             arc_mode=ARC_MODE)
