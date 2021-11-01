# Copyright 2020 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import logging
import time

from autotest_lib.client.common_lib.cros import chrome
from autotest_lib.client.cros.input_playback import keyboard
from autotest_lib.client.cros.power import power_test

URL = 'https://browserbench.org/Speedometer2.0/'
RESULT = 'result'

class power_Speedometer2(power_test.power_Test):
    """class for running Speedometer2 test in Chrome.

    Run Speedometer2 and collect logger data.
    """
    version = 1

    def initialize(self, pdash_note='', force_discharge=False):
        """Measure power with a short interval while running Speedometer2."""
        super(power_Speedometer2, self).initialize(
                seconds_period=1., pdash_note=pdash_note,
                force_discharge=force_discharge)

    def run_once(self, url=URL):
        """Measure power with multiple loggers while running Speedometer2.

        @param url: url of Speedometer2 test page.
        """
        with chrome.Chrome(init_network_controller=True) as self.cr:
            tab = self.cr.browser.tabs[0]
            tab.Activate()

            # Run in full-screen.
            fullscreen = tab.EvaluateJavaScript('document.webkitIsFullScreen')
            if not fullscreen:
                with keyboard.Keyboard() as keys:
                    keys.press_key('f4')

            logging.info('Navigating to url: %s', url)
            tab.Navigate(url)
            tab.WaitForDocumentReadyStateToBeComplete()

            # Allow CPU to idle.
            time.sleep(5)

            self.start_measurements()
            tab.EvaluateJavaScript('startTest()')
            time.sleep(60)
            result = ''
            while not result:
                time.sleep(10)
                result = tab.EvaluateJavaScript(
                        'document.getElementById("%s-number").innerHTML' % \
                        RESULT)
            end_time = time.time()
            result = float(result)

            keyvals = {RESULT: result}
            for key, val in keyvals.items():
                logging.info('Speedometer2 %s: %s', key, val)
            self.keyvals.update(keyvals)
            self.output_perf_value(description=RESULT, value=result,
                                   higher_is_better=True)

            self._keyvallogger.add_item(RESULT, result, 'point', 'perf')
            self._keyvallogger.set_end(end_time)
