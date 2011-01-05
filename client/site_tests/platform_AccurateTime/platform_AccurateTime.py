# Copyright (c) 2010 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import logging, math, re
from autotest_lib.client.bin import test, utils
from autotest_lib.client.common_lib import error
from autotest_lib.client.cros import cros_logging


class platform_AccurateTime(test.test):
    version = 1


    def __get_offset(self, string):
	if (string.find('No time correction needed') > -1) :
            return float(0.0)
        else :
            offset = re.search(r'Setting (-?[\d+\.]+) seconds', string)
            if offset is None:
                # If string is empty, check the sys logs dumped later.
                raise error.TestError('Unable to find offset in %s' % string)
            return float(offset.group(1))

    def run_once(self):
        reader = cros_logging.LogReader()
        reader.set_start_by_current()
        # Check if htpdate is currently running
        if utils.system('pgrep htpdate', ignore_status=True) != 0:
            raise error.TestError('htpdate server was not already running')
        # Stop it since we cannot start another instance of htpdate
        utils.system('initctl stop htpdate')
        try:
            # Now grab the current time and get its offset
            cmd = '/usr/sbin/htpdate -u ntp:ntp -s -t -w www.google.com'
            output = utils.system_output(cmd,retain_output=True)
            server_offset = self.__get_offset(output)
            logging.info("server time offset: %f" % server_offset)

            self.write_perf_keyval({'seconds_offset': abs(server_offset)})
        finally:
            utils.system('initctl start htpdate')
            logging.debug('sys logs emitted: %s' % reader.get_logs())
