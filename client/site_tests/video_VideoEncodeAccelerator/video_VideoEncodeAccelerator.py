# Copyright (c) 2014 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import errno
import hashlib
import logging
import os
import urllib2

from autotest_lib.client.bin import utils
from autotest_lib.client.common_lib import error
from autotest_lib.client.cros import chrome_binary_test

from contextlib import closing

DOWNLOAD_BASE = 'http://commondatastorage.googleapis.com/chromiumos-test-assets-public/'
BINARY = 'video_encode_accelerator_unittest'

def _remove_if_exists(filepath):
    try:
        os.remove(filepath)
    except OSError, e:
        if e.errno != errno.ENOENT: # no such file
            raise


def _download_video(download_path, local_file):
    url = '%s%s' % (DOWNLOAD_BASE, download_path)
    logging.info('download "%s" to "%s"', url, local_file)

    md5 = hashlib.md5()
    with closing(urllib2.urlopen(url)) as r, open(local_file, 'w') as w:
        while True:
            content = r.read(4096)
            if not content: break
            md5.update(content)
            w.write(content)

    md5sum = md5.hexdigest()
    if md5sum not in download_path:
        raise error.TestError('unmatched md5 sum: %s' % md5sum)


class video_VideoEncodeAccelerator(chrome_binary_test.ChromeBinaryTest):
    """
    This test is a wrapper of the chrome unittest binary:
    video_encode_accelerator_unittest.
    """

    version = 1


    def run_once(self, in_cloud, streams, profile):
        """Runs video_encode_accelerator_unittest on the streams.

        @param streams: The test streams for video_encode_accelerator_unittest.
        @param profile: The profile to encode into.

        @raises error.TestFail for video_encode_accelerator_unittest failures.
        """

        last_test_failure = None
        for path, width, height, bit_rate in streams:
            if in_cloud:
                input_path = os.path.join(self.tmpdir, path.split('/')[-1])
                _download_video(path, input_path)
            else:
                input_path = os.path.join(self.cr_source_dir, path)

            output_path = os.path.join(self.tmpdir,
                    '%s.out' % input_path.split('/')[-1])

            cmd_line = '--test_stream_data="%s:%s:%s:%s:%s:%s"' % (
                    input_path, width, height, profile, output_path, bit_rate)
            if utils.is_freon():
                cmd_line += ' --ozone-platform=gbm'
            try:
                self.run_chrome_test_binary(BINARY, cmd_line, as_chronos=False)
            except error.TestFail as test_failure:
                # Continue to run the remaining test streams and raise
                # the last failure after finishing all streams.
                logging.exception('error while encoding %s', input_path)
                last_test_failure = test_failure
            finally:
                # Remove the downloaded video
                if in_cloud:
                    _remove_if_exists(input_path)

        if last_test_failure:
            raise last_test_failure
