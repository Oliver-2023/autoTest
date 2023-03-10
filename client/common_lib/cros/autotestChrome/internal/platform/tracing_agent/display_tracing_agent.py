# Copyright 2022 The Chromium Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from __future__ import absolute_import

import common

from autotest_lib.client.common_lib.cros.autotestChrome.internal.platform import tracing_agent
from autotest_lib.client.common_lib.cros.autotestChrome.tracing.trace_data import trace_data


class DisplayTracingAgent(tracing_agent.TracingAgent):
  def __init__(self, platform_backend, config):
    super(DisplayTracingAgent, self).__init__(platform_backend, config)

  @classmethod
  def IsSupported(cls, platform_backend):
    return platform_backend.IsDisplayTracingSupported()

  def StartAgentTracing(self, config, timeout):
    del timeout  # unused
    if config.enable_platform_display_trace:
      self._platform_backend.StartDisplayTracing()
      return True

  def StopAgentTracing(self):
    # TODO: Split collection and stopping.
    pass

  def CollectAgentTraceData(self, trace_data_builder, timeout=None):
    # TODO: Move stopping to StopAgentTracing.
    del timeout
    surface_flinger_trace_data = self._platform_backend.StopDisplayTracing()
    trace_data_builder.AddTraceFor(
        trace_data.CHROME_TRACE_PART, surface_flinger_trace_data)