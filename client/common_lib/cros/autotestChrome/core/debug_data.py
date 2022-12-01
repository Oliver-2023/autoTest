# Copyright 2022 The Chromium Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

class DebugData(object):
  """A class for storing debug data in string format for later use.

  This is largely so that telemetry.core.exceptions' AppCrashException can
  share code with telemetry.internal.backends.browser_backends'
  CollectDebugData.
  """

  def __init__(self):
    super(DebugData, self).__init__()

    # List of strings, each element being a human-readable symbolized minidump.
    self.symbolized_minidumps = []
    self.stdout = ''
    self.system_log = ''
