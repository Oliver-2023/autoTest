# Copyright 2022 The Chromium Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.


class RemotePlatformOptions(object):
  """Options to be used for creating a remote platform instance."""


class AndroidPlatformOptions(RemotePlatformOptions):
  """Android-specific remote platform options."""

  def __init__(self, device=None, android_denylist_file=None):
    super(AndroidPlatformOptions, self).__init__()

    self.device = device
    self.android_denylist_file = android_denylist_file
