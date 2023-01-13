# Lint as: python2, python3
# Copyright 2016 The ChromiumOS Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import logging
import os
import random
import re
import subprocess
import time

from autotest_lib.client.bin import test
from autotest_lib.client.common_lib import error
from autotest_lib.client.cros import upstart
from autotest_lib.client.cros.audio import audio_helper

_STREAM_TYPE_INPUT = 0
_STREAM_TYPE_OUTPUT = 1

class audio_CrasStress(test.test):
    """Checks if output buffer will drift to super high level."""
    version = 2
    _MAX_STREAMS = 3
    _LOOP_COUNT = 300
    _INPUT_BUFFER_LEVEL = '.*?READ_AUDIO.*?hw_level.*?(\d+).*?'
    _OUTPUT_BUFFER_LEVEL = '.*?FILL_AUDIO.*?hw_level.*?(\d+).*?'
    _ODEV_NO_STREAMS = '.*?ODEV_NO_STREAMS.*?dev.*?(\d+).*?'
    _ODEV_LEAVE_NO_STREAMS = '.*?ODEV_LEAVE_NO_STREAMS.*?dev.*?(\d+).*?'
    _AUDIO_LOG_TIME_FMT = '%Y-%m-%dT%H:%M:%S.%f'
    _CHECK_PERIOD_TIME_SECS = 1 # Check buffer level every second.

    """
    We only run 1024 and 512 block size streams in this test. So buffer level
    of input device should stay between 0 and 1024. Buffer level of output
    device should between 1024 to 2048. Sometimes it will be a little more.
    Therefore, we set input buffer criteria to 3 * 1024 and output buffer
    criteria to 5 * 1024.
    """
    _RATES = ['48000', '44100']
    _BLOCK_SIZES = ['512', '1024']
    _INPUT_BUFFER_DRIFT_CRITERIA = 3 * 1024
    _OUTPUT_BUFFER_DRIFT_CRITERIA = 5 * 1024

    def initialize(self):
        """Initialize the test"""
        try:
            upstart.stop_job('ui')
        except:
            pass

    def _new_stream(self, stream_type):
        """Runs new stream by cras_test_client."""
        if stream_type == _STREAM_TYPE_INPUT:
            cmd = ['cras_test_client', '--capture_file', '/dev/null']
        else:
            cmd = ['cras_test_client', '--playback_file', '/dev/zero']

        cmd += ['--rate', self._RATES[random.randint(0, 1)],
                '--block_size', self._BLOCK_SIZES[random.randint(0, 1)]]

        return subprocess.Popen(cmd)

    def _check_buffer_level(self, stream_type, audio_thread_log):

        buffer_level = self._get_buffer_level(stream_type, audio_thread_log)

        if stream_type == _STREAM_TYPE_INPUT:
            logging.debug("Max input buffer level: %d", buffer_level)
            if buffer_level > self._INPUT_BUFFER_DRIFT_CRITERIA:
                audio_helper.dump_audio_diagnostics(
                        os.path.join(self.resultsdir, "audio_diagnostics.txt"))
                raise error.TestFail('Input buffer level %d drift too high' %
                                     buffer_level)

        if stream_type == _STREAM_TYPE_OUTPUT:
            logging.debug("Max output buffer level: %d", buffer_level)
            if buffer_level > self._OUTPUT_BUFFER_DRIFT_CRITERIA:
                audio_helper.dump_audio_diagnostics(
                        os.path.join(self.resultsdir, "audio_diagnostics.txt"))
                raise error.TestFail('Output buffer level %d drift too high' %
                                     buffer_level)

    def cleanup(self):
        """Clean up all streams."""
        while len(self._streams) > 0:
            self._streams[0].kill()
            self._streams.remove(self._streams[0])
        upstart.restart_job('ui')

    def run_once(self, input_stream=True, output_stream=True):
        """
        Repeatedly add output streams of random configurations and
        remove them to verify if output buffer level would drift.

        @params input_stream: If true, run input stream in the test.
        @params output_stream: If true, run output stream in the test.
        """

        if not input_stream and not output_stream:
            raise error.TestError('Not supported mode.')

        upstart.restart_job('cras')
        time.sleep(3)

        self._streams = []

        loop_count = 0
        proc = subprocess.Popen(['cras_test_client', '--follow_atlog'],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT,
                                universal_newlines=True,
                                encoding='utf-8',
                                bufsize=1)

        while loop_count < self._LOOP_COUNT:
            # 1 for adding stream, 0 for removing stream.
            add = random.randint(0, 1)
            if not self._streams:
                add = 1
            elif len(self._streams) == self._MAX_STREAMS:
                add = 0

            if add == 1:
                # 0 for input stream, 1 for output stream.
                stream_type = random.randint(0, 1)
                if not input_stream:
                    stream_type = _STREAM_TYPE_OUTPUT
                elif not output_stream:
                    stream_type = _STREAM_TYPE_INPUT

                self._streams.append(self._new_stream(stream_type))
            else:
                self._streams[0].kill()
                self._streams.remove(self._streams[0])
                time.sleep(0.1)
            loop_count += 1

        proc.terminate()
        stdout, _ = proc.communicate()

        with open(os.path.join(self.resultsdir, "follow_atlog.txt"), 'w') as f:
            f.write(stdout)

        # Check buffer level.
        if input_stream:
            self._check_buffer_level(_STREAM_TYPE_INPUT, stdout)
        if output_stream:
            self._check_buffer_level(_STREAM_TYPE_OUTPUT, stdout)

    def _get_buffer_level(self, stream_type, audio_thread_log):
        """Gets a rough number about current buffer level.

        @returns: The current buffer level.

        """
        if stream_type == _STREAM_TYPE_INPUT:
            match_str = self._INPUT_BUFFER_LEVEL
        else:
            match_str = self._OUTPUT_BUFFER_LEVEL

        buffer_level = 0
        skip = False
        for line in audio_thread_log.splitlines():
            no_stream = re.match(self._ODEV_NO_STREAMS, line)
            leave_no_stream = re.match(self._ODEV_LEAVE_NO_STREAMS, line)

            if no_stream:
                skip = True

            if leave_no_stream:
                skip = False

            if skip:
                continue

            search = re.match(match_str, line)
            if search:
                tmp = int(search.group(1))
                if tmp > buffer_level:
                    buffer_level = tmp

        return buffer_level
