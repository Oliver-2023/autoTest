# Lint as: python2, python3
# Copyright 2020 The ChromiumOS Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import logging
import time

from autotest_lib.client.common_lib.cros import chrome
from autotest_lib.client.cros.power import power_test
from autotest_lib.client.cros.power import power_utils


URL = 'http://crospower.page.link/power_Speedometer2'
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
        # --disable-sync disables test account info sync, eg. Wi-Fi credentials,
        # so that each test run does not remember info from last test run.
        extra_browser_args = ['--disable-sync']
        # b/228256145 to avoid powerd restart
        extra_browser_args.append('--disable-features=FirmwareUpdaterApp')
        with chrome.Chrome(autotest_ext=True,
                           extra_browser_args=extra_browser_args,
                           init_network_controller=True) as self.cr:
            # Run in full-screen.
            tab = self.cr.browser.tabs[0]
            tab.Activate()
            power_utils.set_fullscreen(self.cr)

            # Stop services and disable multicast again as Chrome might have
            # restarted them.
            self._services.stop_services()
            self._multicast_disabler.disable_network_multicast()

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

            # Re-enable multicast here instead of in the cleanup because Chrome
            # might re-enable it and we can't verify that multicast is off.
            self._multicast_disabler.enable_network_multicast()
