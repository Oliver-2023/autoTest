# Lint as: python2, python3
# Copyright 2018 The ChromiumOS Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
import logging
import os
import shutil
import time

from autotest_lib.client.common_lib import error
from autotest_lib.client.common_lib.cros import chrome
from autotest_lib.client.cros.power import power_test
from autotest_lib.client.cros.power import power_utils


class power_Display(power_test.power_Test):
    """class for power_Display test.
    """
    version = 1
    tmp_path = '/tmp'

    # TODO(tbroch) find more patterns that typical display vendors use to show
    # average and worstcase display power.
    PAGES = ['checker1', 'black', 'white', 'red', 'green', 'blue']
    def run_once(self, pages=None, secs_per_page=60, brightness=''):
        """run_once method.

        @param pages: list of pages names that must be in
            <testdir>/html/<name>.html
        @param secs_per_page: time in seconds to display page and measure power.
        @param brightness: flag for brightness setting to use for testing.
                           possible value are 'max' (100%) and 'all' (all manual
                           brightness steps in ChromeOS)
        """
        if pages is None:
            pages = self.PAGES

        # https://crbug.com/1288417
        # Copy file to tmpdir to avoid the need of setting up local http server.
        file_path = os.path.join(self.bindir, 'html')
        dest_path = os.path.join(self.tmp_path, 'html')
        shutil.copytree(file_path, dest_path)
        http_path = 'file://' + dest_path

        # --disable-sync disables test account info sync, eg. Wi-Fi credentials,
        # so that each test run does not remember info from last test run.
        extra_browser_args = ['--disable-sync']
        # b/228256145 to avoid powerd restart
        extra_browser_args.append('--disable-features=FirmwareUpdaterApp')
        with chrome.Chrome(autotest_ext=True,
                           extra_browser_args=extra_browser_args,
                           init_network_controller=True) as self.cr:
            # Just measure power in full-screen.
            tab = self.cr.browser.tabs[0]
            tab.Activate()
            power_utils.set_fullscreen(self.cr)

            # Stop services and disable multicast again as Chrome might have
            # restarted them.
            self._services.stop_services()
            self.notify_ash_discharge_status()
            self._multicast_disabler.disable_network_multicast()

            if brightness not in ['', 'all', 'max']:
                raise error.TestFail(
                        'Invalid brightness flag: %s' % (brightness))

            if brightness == 'max':
                self.backlight.set_percent(100)

            brightnesses = []
            if brightness == 'all':
                self.backlight.set_percent(100)
                for step in range(16, 0, -1):
                    nonlinear = step * 6.25
                    linear = self.backlight.nonlinear_to_linear(nonlinear)
                    brightnesses.append((nonlinear, linear))
            else:
                linear = self.backlight.get_percent()
                nonlinear = self.backlight.linear_to_nonlinear(linear)
                brightnesses.append((nonlinear, linear))

            self.start_measurements()

            loop = 0
            for name in pages:
                url = os.path.join(http_path, name + '.html')
                logging.info('Navigating to url: %s', url)
                tab.Navigate(url)
                tab.WaitForDocumentReadyStateToBeComplete()

                for nonlinear, linear in brightnesses:
                    self.backlight.set_percent(linear)
                    tagname = '%s_%s' % (self.tagged_testname, name)
                    if len(brightnesses) > 1:
                        tagname += '_%.2f' % (nonlinear)
                    loop_start = time.time()
                    self.loop_sleep(loop, secs_per_page)
                    self.checkpoint_measurements(tagname, loop_start)
                    loop += 1

            # Re-enable multicast here instead of in the cleanup because Chrome
            # might re-enable it and we can't verify that multicast is off.
            self._multicast_disabler.enable_network_multicast()

        shutil.rmtree(dest_path)
