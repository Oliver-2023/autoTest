# Copyright (c) 2010 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import os, stat, time, utils
from autotest_lib.client.common_lib import error
from autotest_lib.client.cros import constants
from autotest_lib.client.cros import cros_ui_test, login, httpd

def respond_with_cookies(handler, url_args):
    """Responds with a Set-Cookie header to any GET request, and redirects
    to a chosen URL.
    """
    handler.send_response(303)
    handler.send_header('Set-Cookie', 'name=value')
    handler.send_header('Location', url_args['continue'][0])
    handler.end_headers()
    handler.wfile.write('Got form data:\n')
    handler.wfile.write('%s:\n' % url_args)


class login_ChromeProfileSanitary(cros_ui_test.UITest):
    version = 1

    def __wait_for_login_profile(self, timeout=10):
        start_time = time.time()
        while time.time() - start_time < timeout:
            if os.path.exists(constants.LOGIN_PROFILE + '/Cookies'):
                break;
            time.sleep(1)
        else:
            raise error.TestError('Login Profile took too long to populate')


    def initialize(self):
        spec = 'http://localhost:8000'
        path = '/set_cookie'
        self._wait_path = '/test_over'
        self._test_url = spec + path + '?continue=' + spec + self._wait_path
        self._testServer = httpd.HTTPListener(8000, docroot=self.srcdir)
        self._testServer.add_url_handler('/set_cookie', respond_with_cookies)
        self._testServer.run()
        super(login_ChromeProfileSanitary, self).initialize()


    def cleanup(self):
        self._testServer.stop()
        cros_ui_test.UITest.cleanup(self)


    def run_once(self, timeout=10):
        # Get Default/Cookies mtime.
        cookies_info = os.stat(constants.LOGIN_PROFILE + '/Cookies')
        cookies_mtime = cookies_info[stat.ST_MTIME]

        # Wait for chrome to show, then "crash" it.
        login.wait_for_initial_chrome_window()
        utils.nuke_process_by_name(constants.BROWSER, with_prejudice=True)

        login.refresh_window_manager()
        login.wait_for_browser()
        login.wait_for_initial_chrome_window()

        # Navigate to site that leaves cookies.
        latch = self._testServer.add_wait_url(self._wait_path)
        self.pyauto.NavigateToURL(self._test_url)
        latch.wait(timeout)
        if not latch.is_set():
            raise error.TestError('Never received callback from browser.')

        # Ensure chrome writes state to disk.
        self.login()  # will logout automatically

        # Check mtime of Default/Cookies.  If changed, KABLOOEY.
        self.__wait_for_login_profile()
        cookies_info = os.stat(constants.LOGIN_PROFILE + '/Cookies')

        if cookies_mtime != cookies_info[stat.ST_MTIME]:
            raise error.TestFail('Cookies in Default profile changed!')
