# Lint as: python2, python3
# Copyright 2020 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Server side Bluetooth audio tests."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging
import os
import re
import subprocess
import time

import common
from autotest_lib.client.bin import utils
from autotest_lib.client.common_lib import error
from autotest_lib.client.cros.bluetooth.bluetooth_audio_test_data import (
        A2DP, HFP_NBS, HFP_WBS, AUDIO_DATA_TARBALL_PATH, VISQOL_BUFFER_LENGTH,
        DATA_DIR, VISQOL_PATH, VISQOL_SIMILARITY_MODEL, VISQOL_TEST_DIR,
        AUDIO_RECORD_DIR, audio_test_data, get_audio_test_data,
        get_visqol_binary)
from autotest_lib.server.cros.bluetooth.bluetooth_adapter_tests import (
    BluetoothAdapterTests, test_retry_and_log)
from six.moves import range


class BluetoothAdapterAudioTests(BluetoothAdapterTests):
    """Server side Bluetooth adapter audio test class."""

    DEVICE_TYPE = 'BLUETOOTH_AUDIO'
    FREQUENCY_TOLERANCE_RATIO = 0.01
    WAIT_DAEMONS_READY_SECS = 1
    DEFAULT_CHUNK_IN_SECS = 1
    IGNORE_LAST_FEW_CHUNKS = 2

    # Useful constant for upsampling NBS files for compatibility with ViSQOL
    MIN_VISQOL_SAMPLE_RATE = 16000

    # The node types of the bluetooth output nodes in cras are the same for both
    # A2DP and HFP.
    CRAS_BLUETOOTH_OUTPUT_NODE_TYPE = 'BLUETOOTH'
    CRAS_INTERNAL_SPEAKER_OUTPUT_NODE_TYPE = 'INTERNAL_SPEAKER'
    # The node types of the bluetooth input nodes in cras are different for WBS
    # and NBS.
    CRAS_HFP_BLUETOOTH_INPUT_NODE_TYPE = {HFP_WBS: 'BLUETOOTH',
                                          HFP_NBS: 'BLUETOOTH_NB_MIC'}

    def _get_pulseaudio_bluez_source(self, get_source_method, device,
                                     test_profile):
        """Get the specified bluez device number in the pulseaudio source list.

        @param get_source_method: the method to get distinct bluez source
        @param device: the bluetooth peer device
        @param test_profile: the test profile used, A2DP, HFP_WBS or HFP_NBS

        @returns: True if the specified bluez source is derived
        """
        sources = device.ListSources(test_profile)
        logging.debug('ListSources()\n%s', sources)
        self.bluez_source = get_source_method(test_profile)
        result = bool(self.bluez_source)
        if result:
            logging.debug('bluez_source device number: %s', self.bluez_source)
        else:
            logging.debug('waiting for bluez_source ready in pulseaudio...')
        return result


    def _get_pulseaudio_bluez_sink(self, get_sink_method, device, test_profile):
        """Get the specified bluez device number in the pulseaudio sink list.

        @param get_sink_method: the method to get distinct bluez sink
        @param device: the bluetooth peer device
        @param test_profile: the test profile used, A2DP, HFP_WBS or HFP_NBS

        @returns: True if the specified bluez sink is derived
        """
        sinks = device.ListSinks(test_profile)
        logging.debug('ListSinks()\n%s', sinks)
        self.bluez_sink = get_sink_method(test_profile)
        result = bool(self.bluez_sink)
        if result:
            logging.debug('bluez_sink device number: %s', self.bluez_sink)
        else:
            logging.debug('waiting for bluez_sink ready in pulseaudio...')
        return result


    def _get_pulseaudio_bluez_source_a2dp(self, device, test_profile):
        """Get the a2dp bluez source device number.

        @param device: the bluetooth peer device
        @param test_profile: the test profile used, A2DP, HFP_WBS or HFP_NBS

        @returns: True if the specified a2dp bluez source is derived
        """
        return self._get_pulseaudio_bluez_source(
                device.GetBluezSourceA2DPDevice, device, test_profile)


    def _get_pulseaudio_bluez_source_hfp(self, device, test_profile):
        """Get the hfp bluez source device number.

        @param device: the bluetooth peer device
        @param test_profile: the test profile used, A2DP, HFP_WBS or HFP_NBS

        @returns: True if the specified hfp bluez source is derived
        """
        return self._get_pulseaudio_bluez_source(
                device.GetBluezSourceHFPDevice, device, test_profile)


    def _get_pulseaudio_bluez_sink_hfp(self, device, test_profile):
        """Get the hfp bluez sink device number.

        @param device: the bluetooth peer device
        @param test_profile: the test profile used, A2DP, HFP_WBS or HFP_NBS

        @returns: True if the specified hfp bluez sink is derived
        """
        return self._get_pulseaudio_bluez_sink(
                device.GetBluezSinkHFPDevice, device, test_profile)


    def _check_audio_frames_legitimacy(self, audio_test_data, recording_device,
                                       recorded_file=None):
        """Check if audio frames in the recorded file are legitimate.

        For a wav file, a simple check is to make sure the recorded audio file
        is not empty.

        For a raw file, a simple check is to make sure the recorded audio file
        are not all zeros.

        @param audio_test_data: a dictionary about the audio test data
                defined in client/cros/bluetooth/bluetooth_audio_test_data.py
        @param recording_device: which device recorded the audio,
                possible values are 'recorded_by_dut' or 'recorded_by_peer'
        @param recorded_file: the recorded file name

        @returns: True if audio frames are legitimate.
        """
        result = self.bluetooth_facade.check_audio_frames_legitimacy(
                audio_test_data, recording_device, recorded_file)
        if not result:
            self.results = {'audio_frames_legitimacy': 'empty or all zeros'}
            logging.error('The recorded audio file is empty or all zeros.')
        return result


    def _check_frequency(self, test_profile, recorded_freq, expected_freq):
        """Check if the recorded frequency is within tolerance.

        @param test_profile: the test profile used, A2DP, HFP_WBS or HFP_NBS
        @param recorded_freq: the frequency of recorded audio
        @param expected_freq: the expected frequency

        @returns: True if the recoreded frequency falls within the tolerance of
                  the expected frequency
        """
        tolerance = expected_freq * self.FREQUENCY_TOLERANCE_RATIO
        return abs(expected_freq - recorded_freq) <= tolerance


    def _check_primary_frequencies(self, test_profile, audio_test_data,
                                   recording_device, recorded_file=None):
        """Check if the recorded frequencies meet expectation.

        @param test_profile: the test profile used, A2DP, HFP_WBS or HFP_NBS
        @param audio_test_data: a dictionary about the audio test data
                defined in client/cros/bluetooth/bluetooth_audio_test_data.py
        @param recording_device: which device recorded the audio,
                possible values are 'recorded_by_dut' or 'recorded_by_peer'
        @param recorded_file: the recorded file name

        @returns: True if the recorded frequencies of all channels fall within
                the tolerance of expected frequencies
        """
        recorded_frequencies = self.bluetooth_facade.get_primary_frequencies(
                audio_test_data, recording_device, recorded_file)
        expected_frequencies = audio_test_data['frequencies']
        final_result = True
        self.results = dict()

        if len(recorded_frequencies) < len(expected_frequencies):
            logging.error('recorded_frequencies: %s, expected_frequencies: %s',
                          str(recorded_frequencies), str(expected_frequencies))
            final_result = False
        else:
            for channel, expected_freq in enumerate(expected_frequencies):
                recorded_freq = recorded_frequencies[channel]
                ret_val = self._check_frequency(
                        test_profile, recorded_freq, expected_freq)
                pass_fail_str = 'pass' if ret_val else 'fail'
                result = ('primary frequency %d (expected %d): %s' %
                          (recorded_freq, expected_freq, pass_fail_str))
                self.results['Channel %d' % channel] = result
                logging.info('Channel %d: %s', channel, result)

                if not ret_val:
                    final_result = False

        logging.debug(str(self.results))
        if not final_result:
            logging.error('Failure at checking primary frequencies')
        return final_result


    def _poll_for_condition(self, condition, timeout=20, sleep_interval=1,
                            desc='waiting for condition'):
        try:
            utils.poll_for_condition(condition=condition,
                                     timeout=timeout,
                                     sleep_interval=sleep_interval,
                                     desc=desc)
        except Exception as e:
            raise error.TestError('Exception occurred when %s (%s)' % (desc, e))


    def initialize_bluetooth_audio(self, device, test_profile):
        """Initialize the Bluetooth audio task.

        Note: pulseaudio is not stable. Need to restart it in the beginning.

        @param device: the bluetooth peer device
        @param test_profile: the test profile used, A2DP, HFP_WBS or HFP_NBS

        """
        if not self.bluetooth_facade.create_audio_record_directory(
                AUDIO_RECORD_DIR):
            raise error.TestError('Failed to create %s on the DUT' %
                                  AUDIO_RECORD_DIR)

        if not device.StartPulseaudio(test_profile):
            raise error.TestError('Failed to start pulseaudio.')
        logging.debug('pulseaudio is started.')

        if test_profile in (HFP_WBS, HFP_NBS):
            if device.StartOfono():
                logging.debug('ofono is started.')
            else:
                raise error.TestError('Failed to start ofono.')
        elif device.StopOfono():
            logging.debug('ofono is stopped.')
        else:
            logging.warning('Failed to stop ofono. Ignored.')

        # Need time to complete starting services.
        time.sleep(self.WAIT_DAEMONS_READY_SECS)


    def cleanup_bluetooth_audio(self, device, test_profile):
        """Cleanup for Bluetooth audio.

        @param device: the bluetooth peer device
        @param test_profile: the test profile used, A2DP, HFP_WBS or HFP_NBS

        """
        if device.StopPulseaudio():
            logging.debug('pulseaudio is stopped.')
        else:
            logging.warning('Failed to stop pulseaudio. Ignored.')

        if device.StopOfono():
            logging.debug('ofono is stopped.')
        else:
            logging.warning('Failed to stop ofono. Ignored.')


    def initialize_bluetooth_player(self, device):
        """Initialize the Bluetooth media player.

        @param device: the Bluetooth peer device.

        """
        if not device.ExportMediaPlayer():
            raise error.TestError('Failed to export media player.')
        logging.debug('mpris-proxy is started.')

        # Wait for player to show up and observed by playerctl.
        desc='waiting for media player'
        self._poll_for_condition(
                lambda: bool(device.GetExportedMediaPlayer()), desc=desc)


    def cleanup_bluetooth_player(self, device):
        """Cleanup for Bluetooth media player.

        @param device: the bluetooth peer device.

        """
        device.UnexportMediaPlayer()


    def select_audio_output_node(self):
        """Select the audio output node through cras.

        @raises: error.TestError if failed.
        """
        def bluetooth_type_selected(node_type):
            """Check if the bluetooth node type is selected."""
            selected = self.bluetooth_facade.get_selected_output_device_type()
            logging.debug('active output node type: %s, expected %s',
                          selected, node_type)
            return selected == node_type

        node_type = self.CRAS_BLUETOOTH_OUTPUT_NODE_TYPE
        if not self.bluetooth_facade.select_output_node(node_type):
            raise error.TestError('select_output_node failed')

        desc='waiting for %s as active cras audio output node type' % node_type
        logging.debug(desc)
        self._poll_for_condition(lambda: bluetooth_type_selected(node_type),
                                 desc=desc)


    def initialize_hfp(self, device, test_profile, test_data,
                       recording_device, bluez_function):
        """Initial set up for hfp tests.

        Setup that is required for all hfp tests where
        dut is either source or sink. Selects input device, starts recording,
        and lastly it waits for pulseaudio bluez source/sink.

        @param device: the bluetooth peer device
        @param test_profile: the test profile used, HFP_WBS or HFP_NBS
        @param test_data: a dictionary about the audio test data defined in
                client/cros/bluetooth/bluetooth_audio_test_data.py
        @param recording_device: which device recorded the audio, possible
                values are 'recorded_by_dut' or 'recorded_by_peer'
        @param bluez_function: the appropriate bluez hfp function either
                _get_pulseaudio_bluez_source_hfp or
                _get_pulseaudio_bluez_sink_hfp depending on the role of the dut
        """
        device_type = 'DUT' if recording_device == 'recorded_by_dut' else 'Peer'
        dut_role = 'sink' if recording_device == 'recorded_by_dut' else 'source'

        # Select audio input device.
        desc = 'waiting for cras to select audio input device'
        logging.debug(desc)
        self._poll_for_condition(
                lambda: self.bluetooth_facade.select_input_device(device.name),
                desc=desc)

        # Select audio output node so that we do not rely on chrome to do it.
        self.select_audio_output_node()

        # Enable HFP profile.
        logging.debug('Start recording audio on {}'.format(device_type))
        if not self.bluetooth_facade.start_capturing_audio_subprocess(
                test_data, recording_device):
            desc = '{} failed to start capturing audio.'.format(device_type)
            raise error.TestError(desc)

        # Wait for pulseaudio bluez hfp source/sink
        desc = 'waiting for pulseaudio bluez hfp {}'.format(dut_role)
        logging.debug(desc)
        self._poll_for_condition(lambda: bluez_function(device, test_profile),
                                 desc=desc)


    def hfp_record_on_dut(self, device, test_profile, test_data):
        """Play audio from test_data dictionary from peer device to dut.

        Play file described in test_data dictionary from peer device to dut
        using test_profile, either HFP_WBS or HFP_NBS and record on dut.

        @param device: the bluetooth peer device
        @param test_profile: the test profile used, HFP_WBS or HFP_NBS
        @param test_data: a dictionary about the audio test data defined in
                client/cros/bluetooth/bluetooth_audio_test_data.py

        @returns: True if the recorded audio frames are legitimate, False
                if they are not, ie. it did not record.
        """
        # Select audio input device.
        logging.debug('Select input device')
        if not self.bluetooth_facade.select_input_device(device.name):
            raise error.TestError('DUT failed to select audio input device.')

        # Start playing audio on chameleon.
        logging.debug('Start playing audio on Pi')
        if not device.StartPlayingAudioSubprocess(test_profile, test_data):
            err = 'Failed to start playing audio file on the peer device'
            raise error.TestError(err)

        time.sleep(test_data['duration'])

        # Stop playing audio on chameleon.
        logging.debug('Stop playing audio on Pi')
        if not device.StopPlayingAudioSubprocess():
            err = 'Failed to stop playing audio on the peer device'
            raise error.TestError(err)

        # Disable HFP profile.
        logging.debug('Stop recording audio on DUT')
        if not self.bluetooth_facade.stop_capturing_audio_subprocess():
            raise error.TestError('DUT failed to stop capturing audio.')

        # Check if the audio frames in the recorded file are legitimate.
        return self._check_audio_frames_legitimacy(test_data, 'recorded_by_dut')


    def hfp_record_on_peer(self, device, test_profile, test_data):
        """Play audio from test_data dictionary from dut to peer device.

        Play file described in test_data dictionary from dut to peer device
        using test_profile, either HFP_WBS or HFP_NBS and record on peer.

        @param device: The bluetooth peer device.
        @param test_profile: The test profile used, HFP_WBS or HFP_NBS.
        @param test_data: A dictionary about the audio test data defined in
                client/cros/bluetooth/bluetooth_audio_test_data.py.

        @returns: True if the recorded audio frames are legitimate, False
                if they are not, ie. it did not record.
        """
        logging.debug('Start recording audio on Pi')
        # Start recording audio on the peer Bluetooth audio device.
        if not device.StartRecordingAudioSubprocess(test_profile, test_data):
            raise error.TestError(
                    'Failed to record on the peer Bluetooth audio device.')

        # Play audio on the DUT in a non-blocked way.
        # If there are issues, cras_test_client playing back might be blocked
        # forever. We would like to avoid the testing procedure from that.
        logging.debug('Start playing audio')
        if not self.bluetooth_facade.start_playing_audio_subprocess(test_data):
            raise error.TestError('DUT failed to play audio.')

        time.sleep(test_data['duration'])

        logging.debug('Stop recording audio on Pi')
        # Stop recording audio on the peer Bluetooth audio device.
        if not device.StopRecordingingAudioSubprocess():
            msg = 'Failed to stop recording on the peer Bluetooth audio device'
            logging.error(msg)

        # Disable HFP profile.
        logging.debug('Stop recording audio on DUT')
        if not self.bluetooth_facade.stop_capturing_audio_subprocess():
            raise error.TestError('DUT failed to stop capturing audio.')

        # Stop playing audio on DUT.
        logging.debug('Stop playing audio on DUT')
        if not self.bluetooth_facade.stop_playing_audio_subprocess():
            raise error.TestError('DUT failed to stop playing audio.')

        # Copy the recorded audio file to the DUT for spectrum analysis.
        logging.debug('Scp to DUT')
        recorded_file = test_data['recorded_by_peer']
        device.ScpToDut(recorded_file, recorded_file, self.host.ip)

        # Check if the audio frames in the recorded file are legitimate.
        return self._check_audio_frames_legitimacy(test_data,
                                                   'recorded_by_peer')


    def parse_visqol_output(self, stdout, stderr):
        """
        Parse stdout and stderr string from VISQOL output and parse into
        a float score.

        On error, stderr will contain the error message, otherwise will be None.
        On success, stdout will be a string, first line will be
        VISQOL version, followed by indication of speech mode. Followed by
        paths to reference and degraded file, and a float MOS-LQO score, which
        is what we're interested in. Followed by more detailed charts about
        specific scoring by segments of the files. Stdout is None on error.

        @param stdout: The stdout bytes from commandline output of VISQOL.
        @param stderr: The stderr bytes from commandline output of VISQOL.

        @returns: A tuple of a float score and string representation of the
                srderr or None if there was no error.
        """
        string_out = stdout.decode('utf-8') or ''
        stderr = stderr.decode('utf-8')

        # Log verbose VISQOL output:
        log_file = os.path.join(VISQOL_TEST_DIR, 'VISQOL_LOG.txt')
        with open(log_file, 'w+') as f:
            f.write('String Error:\n{}\n'.format(stderr))
            f.write('String Out:\n{}\n'.format(string_out))

        # pattern matches first float or int after 'MOS-LQO:' in stdout,
        # e.g. it would match the line 'MOS-LQO       2.3' in the stdout
        score_pattern = re.compile(r'.*MOS-LQO:\s*(\d+.?\d*)')
        score_search = re.search(score_pattern, string_out)

        # re.search returns None if no pattern match found, otherwise the score
        # would be in the match object's group 1 matches just the float score
        score = float(score_search.group(1)) if score_search else -1.0
        return stderr, score


    def get_visqol_score(self, ref_file, deg_file, speech_mode=True,
                         verbose=True):
        """
        Runs VISQOL using the subprocess library on the provided reference file
        and degraded file and returns the VISQOL score.

        @param ref_file: File path to the reference wav file.
        @param deg_file: File path to the degraded wav file.
        @param speech_mode: [Optional] Defaults to True, accepts 16k sample
                rate files and ignores frequencies > 8kHz for scoring.
        @param verbose: [Optional] Defaults to True, outputs more details.

        @returns: A float score for the tested file.
        """
        visqol_cmd = [VISQOL_PATH]
        visqol_cmd += ['--reference_file', ref_file]
        visqol_cmd += ['--degraded_file', deg_file]
        visqol_cmd += ['--similarity_to_quality_model', VISQOL_SIMILARITY_MODEL]

        if speech_mode:
            visqol_cmd.append('--use_speech_mode')
        if verbose:
            visqol_cmd.append('--verbose')

        visqol_process = subprocess.Popen(visqol_cmd, stdout=subprocess.PIPE,
                                          stderr=subprocess.PIPE)
        stdout, stderr = visqol_process.communicate()

        err, score = self.parse_visqol_output(stdout, stderr)

        if err:
            raise error.TestError(err)
        elif score < 0.0:
            raise error.TestError('Failed to parse score, got {}'.format(score))

        return score


    def get_ref_and_deg_files(self, trimmed_file, test_profile, test_data):
        """Return path for reference and degraded files to run visqol on.

        @param trimmed_file: Path to the trimmed audio file on DUT.
        @param test_profile: The test profile used HFP_WBS or HFP_NBS.
        @param test_data: A dictionary about the audio test data defined in
                client/cros/bluetooth/bluetooth_audio_test_data.py.

        @returns: A tuple of path to the reference file and degraded file if
                they exist, otherwise False for the files that aren't available.
        """
        # Path in autotest server in ViSQOL folder to store degraded file from
        # retrieved from the DUT
        deg_file = os.path.join(VISQOL_TEST_DIR, os.path.split(trimmed_file)[1])
        played_file = test_data['file']
        # If profile is WBS, no resampling required
        if test_profile == HFP_WBS:
            self.host.get_file(trimmed_file, deg_file)
            return played_file, deg_file

        # On NBS, degraded and reference files need to be resampled to 16 kHz
        # Build path for the upsampled (us) reference (ref) file on DUT
        ref_file = '{}_us_ref{}'.format(*os.path.splitext(played_file))
        # If resampled ref file already exists, don't need to do it again
        if not os.path.isfile(ref_file):
            if not self.bluetooth_facade.convert_audio_sample_rate(
                    played_file, ref_file, test_data,
                    self.MIN_VISQOL_SAMPLE_RATE):
                return False, False
            # Move upsampled reference file to autotest server
            self.host.get_file(ref_file, ref_file)

        # Build path for resampled degraded file on DUT
        deg_on_dut = '{}_us{}'.format(*os.path.splitext(trimmed_file))
        # Resample degraded file to 16 kHz and move to autotest server
        if not self.bluetooth_facade.convert_audio_sample_rate(
                trimmed_file, deg_on_dut, test_data,
                self.MIN_VISQOL_SAMPLE_RATE):
            return ref_file, False

        self.host.get_file(deg_on_dut, deg_file)

        return ref_file, deg_file


    def format_recorded_file(self, test_data, test_profile, recording_device):
        """Format recorded files to be compatible with ViSQOL.

        Convert raw files to wav if recorded file is a raw file, trim file to
        duration, if required, resample the file, then lastly return the paths
        for the reference file and degraded file on the autotest server.

        @param test_data: A dictionary about the audio test data defined in
                client/cros/bluetooth/bluetooth_audio_test_data.py.
        @param test_profile: The test profile used, HFP_WBS or HFP_NBS.
        @param recording_device: Which device recorded the audio, either
                'recorded_by_dut' or 'recorded_by_peer'.

        @returns: A tuple of path to the reference file and degraded file if
                they exist, otherwise False for the files that aren't available.
        """
        # Path to recorded file either on DUT or BT peer
        recorded_file = test_data[recording_device]
        untrimmed_file = recorded_file
        if recorded_file.endswith('.raw'):
            # build path for file converted from raw to wav, i.e. change the ext
            untrimmed_file = os.path.splitext(recorded_file)[0] + '.wav'
            if not self.bluetooth_facade.convert_raw_to_wav(
                    recorded_file, untrimmed_file, test_data):
                raise error.TestError('Could not convert raw file to wav')

        # Compute the duration of played file without added buffer
        new_duration = test_data['duration'] - VISQOL_BUFFER_LENGTH
        # build path for file resulting from trimming to desired duration
        trimmed_file = '{}_t{}'.format(*os.path.splitext(untrimmed_file))
        if not self.bluetooth_facade.trim_wav_file(
                untrimmed_file, trimmed_file, new_duration, test_data):
            raise error.TestError('Failed to trim recorded file')

        return self.get_ref_and_deg_files(trimmed_file, test_profile, test_data)


    # ---------------------------------------------------------------
    # Definitions of all bluetooth audio test cases
    # ---------------------------------------------------------------


    @test_retry_and_log(False)
    def test_select_audio_output_node_bluetooth(self):
        """Select the Bluetooth device as output node.

        @returns: True on success. False otherwise.
        """
        return self._test_select_audio_output_node(
                self.CRAS_BLUETOOTH_OUTPUT_NODE_TYPE)


    @test_retry_and_log(False)
    def test_select_audio_output_node_internal_speaker(self):
        """Select the internal speaker as output node.

        @returns: True on success. False otherwise.
        """
        return self._test_select_audio_output_node(
                self.CRAS_INTERNAL_SPEAKER_OUTPUT_NODE_TYPE)


    def _test_select_audio_output_node(self, node_type=None):
        """Select the audio output node through cras.

        @param node_type: a str representing node type defined in
                          CRAS_NODE_TYPES.
        @raises: error.TestError if failed.

        @return True if select given node success.
        """
        def node_type_selected(node_type):
            """Check if the given node type is selected."""
            selected = self.bluetooth_facade.get_selected_output_device_type()
            logging.debug('active output node type: %s, expected %s', selected,
                          node_type)
            return selected == node_type

        if not self.bluetooth_facade.select_output_node(node_type):
            raise error.TestError('select_output_node failed')

        desc = 'waiting for %s as active cras audio output node type' % node_type
        logging.debug(desc)
        self._poll_for_condition(lambda: node_type_selected(node_type),
                                 desc=desc)

        return True


    @test_retry_and_log(False)
    def test_audio_is_alive_on_dut(self):
        """Test that if the audio stream is alive on the DUT.

        @returns: True if the audio summary is found on the DUT.
        """
        summary = self.bluetooth_facade.get_audio_thread_summary()
        result = bool(summary)

        # If we can find something starts with summary like: "Summary: Output
        # device [Silent playback device.] 4096 48000 2  Summary: Output stream
        # CRAS_CLIENT_TYPE_TEST CRAS_STREAM_TYPE_DEFAULT 480 240 0x0000 48000
        # 2 0" this means that there's an audio stream alive on the DUT.
        desc = " ".join(str(line) for line in summary)
        logging.debug('find summary: %s', desc)

        self.results = {'test_audio_is_alive_on_dut': result}
        return all(self.results.values())


    @test_retry_and_log(False)
    def test_check_chunks(self,
                          device,
                          test_profile,
                          test_data,
                          duration,
                          check_legitimacy=True,
                          check_frequencies=True):
        """Check chunks of recorded streams and verify the primary frequencies.

        @param device: the bluetooth peer device
        @param test_profile: the a2dp test profile;
                             choices are A2DP and A2DP_LONG
        @param test_data: the test data of the test profile
        @param duration: the duration of the audio file to test
        @param check_legitimacy: specify this to True to run
                                _check_audio_frames_legitimacy test
        @param check_frequencies: specify this to True to run
                                 _check_primary_frequencies test

        @returns: True if all chunks pass the frequencies check.
        """
        chunk_in_secs = test_data['chunk_in_secs']
        if not bool(chunk_in_secs):
            chunk_in_secs = self.DEFAULT_CHUNK_IN_SECS
        nchunks = duration // chunk_in_secs
        logging.info('Number of chunks: %d', nchunks)

        check_audio_frames_legitimacy = True
        check_primary_frequencies = True
        for i in range(nchunks):
            logging.info('Check chunk %d', i)

            recorded_file = device.HandleOneChunk(chunk_in_secs, i,
                                                  self.host.ip)
            if recorded_file is None:
                raise error.TestError('Failed to handle chunk %d' % i)

            if check_legitimacy:
                # Check if the audio frames in the recorded file are legitimate.
                if not self._check_audio_frames_legitimacy(
                        test_data, 'recorded_by_peer', recorded_file=recorded_file):
                    if (i > self.IGNORE_LAST_FEW_CHUNKS and
                            i >= nchunks - self.IGNORE_LAST_FEW_CHUNKS):
                        logging.info('empty chunk %d ignored for last %d chunks',
                                     i, self.IGNORE_LAST_FEW_CHUNKS)
                    else:
                        check_audio_frames_legitimacy = False
                    break

            if check_frequencies:
                # Check if the primary frequencies of the recorded file
                # meet expectation.
                if not self._check_primary_frequencies(
                        test_profile,
                        test_data,
                        'recorded_by_peer',
                        recorded_file=recorded_file):
                    if (i > self.IGNORE_LAST_FEW_CHUNKS and
                            i >= nchunks - self.IGNORE_LAST_FEW_CHUNKS):
                        msg = 'partially filled chunk %d ignored for last %d chunks'
                        logging.info(msg, i, self.IGNORE_LAST_FEW_CHUNKS)
                    else:
                        check_primary_frequencies = False
                    break

        self.results = dict()
        if check_legitimacy:
            self.results['check_audio_frames_legitimacy'] = (
                    check_audio_frames_legitimacy)

        if check_frequencies:
            self.results['check_primary_frequencies'] = (
                    check_primary_frequencies)

        return all(self.results.values())


    @test_retry_and_log(False)
    def test_check_empty_chunks(self, device, test_data, duration):
        """Check if all the chunks are empty.

        @param device: The Bluetooth peer device.
        @param test_data: The test data of the test profile.
        @param duration: The duration of the audio file to test.

        @returns: True if all the chunks are empty.
        """
        chunk_in_secs = test_data['chunk_in_secs']
        if not bool(chunk_in_secs):
            chunk_in_secs = self.DEFAULT_CHUNK_IN_SECS
        nchunks = duration // chunk_in_secs
        logging.info('Number of chunks: %d', nchunks)

        all_chunks_empty = True
        for i in range(nchunks):
            logging.info('Check chunk %d', i)

            recorded_file = device.HandleOneChunk(chunk_in_secs, i,
                                                  self.host.ip)
            if recorded_file is None:
                raise error.TestError('Failed to handle chunk %d' % i)


            # Check if the audio frames in the recorded file are legitimate.
            if self._check_audio_frames_legitimacy(
                    test_data, 'recorded_by_peer', recorded_file):
                if (i > self.IGNORE_LAST_FEW_CHUNKS and
                        i >= nchunks - self.IGNORE_LAST_FEW_CHUNKS):
                    logging.info('empty chunk %d ignored for last %d chunks',
                                 i, self.IGNORE_LAST_FEW_CHUNKS)
                else:
                    all_chunks_empty = False
                break

        self.results = {'all chunks are empty': all_chunks_empty}

        return all(self.results.values())


    @test_retry_and_log(False)
    def test_dut_to_start_playing_audio_subprocess(self, test_data):
        """Start playing audio in a subprocess.

        @param test_data: the audio test data

        @returns: True on success. False otherwise.
        """
        start_playing_audio = self.bluetooth_facade.start_playing_audio_subprocess(
                test_data)
        self.results = {
                'dut_to_start_playing_audio_subprocess': start_playing_audio
        }
        return all(self.results.values())

    @test_retry_and_log(False)
    def test_dut_to_stop_playing_audio_subprocess(self):
        """Stop playing audio in the subprocess.

        @returns: True on success. False otherwise.
        """
        stop_playing_audio = (
                self.bluetooth_facade.stop_playing_audio_subprocess())

        self.results = {
                'dut_to_stop_playing_audio_subprocess': stop_playing_audio
        }
        return all(self.results.values())

    @test_retry_and_log(False)
    def test_dut_to_start_capturing_audio_subprocess(self, audio_data,
                                                     recording_device):
        """Start capturing audio in a subprocess.

        @param audio_data: the audio test data
        @param recording_device: which device recorded the audio,
                possible values are 'recorded_by_dut' or 'recorded_by_peer'

        @returns: True on success. False otherwise.
        """
        start_capturing_audio = self.bluetooth_facade.start_capturing_audio_subprocess(
                audio_data, recording_device)
        self.results = {
                'dut_to_start_capturing_audio_subprocess':
                start_capturing_audio
        }
        return all(self.results.values())

    @test_retry_and_log(False)
    def test_dut_to_stop_capturing_audio_subprocess(self):
        """Stop capturing audio.

        @returns: True on success. False otherwise.
        """
        stop_capturing_audio = (
                self.bluetooth_facade.stop_capturing_audio_subprocess())

        self.results = {
                'dut_to_stop_capturing_audio_subprocess': stop_capturing_audio
        }
        return all(self.results.values())

    @test_retry_and_log(False)
    def test_device_to_start_playing_audio_subprocess(self, device,
                                                      test_profile, test_data):
        """Start playing the audio file in a subprocess.

        @param device: the bluetooth peer device
        @param test_data: the audio file to play and data about the file
        @param audio_profile: the audio profile, either a2dp, hfp_wbs, or hfp_nbs

        @returns: True on success. False otherwise.
        """
        start_playing_audio = device.StartPlayingAudioSubprocess(
                test_profile, test_data)
        self.results = {
                'device_to_start_playing_audio_subprocess': start_playing_audio
        }
        return all(self.results.values())

    @test_retry_and_log(False)
    def test_device_to_stop_playing_audio_subprocess(self, device):
        """Stop playing the audio file in a subprocess.

        @param device: the bluetooth peer device

        @returns: True on success. False otherwise.
        """
        stop_playing_audio = device.StopPlayingAudioSubprocess()
        self.results = {
                'device_to_stop_playing_audio_subprocess': stop_playing_audio
        }
        return all(self.results.values())

    @test_retry_and_log(False)
    def test_device_to_start_recording_audio_subprocess(
            self, device, test_profile, test_data):
        """Start recording audio in a subprocess.

        @param device: the bluetooth peer device
        @param test_profile: the audio profile used to get the recording settings
        @param test_data: the details of the file being recorded

        @returns: True on success. False otherwise.
        """
        start_recording_audio = device.StartRecordingAudioSubprocess(
                test_profile, test_data)
        self.results = {
                'device_to_start_recording_audio_subprocess':
                start_recording_audio
        }
        return all(self.results.values())

    @test_retry_and_log(False)
    def test_device_to_stop_recording_audio_subprocess(self, device):
        """Stop the recording subprocess.

        @returns: True on success. False otherwise.
        """
        stop_recording_audio = device.StopRecordingingAudioSubprocess()
        self.results = {
                'device_to_stop_recording_audio_subprocess':
                stop_recording_audio
        }
        return all(self.results.values())


    @test_retry_and_log(False)
    def test_hfp_dut_as_source_visqol_score(self, device, test_profile):
        """Test Case: hfp test files streaming from peer device to dut

        @param device: the bluetooth peer device
        @param test_profile: which test profile is used, HFP_WBS or HFP_NBS

        @returns: True if the all the test files score at or above their
                  source_passing_score value as defined in
                  bluetooth_audio_test_data.py
        """
        # list of test wav files
        hfp_test_data = audio_test_data[test_profile]
        test_files = hfp_test_data['visqol_test_files']

        get_visqol_binary()
        get_audio_test_data()

        # Download test data to DUT
        self.host.send_file(AUDIO_DATA_TARBALL_PATH, AUDIO_DATA_TARBALL_PATH)
        if not self.bluetooth_facade.unzip_audio_test_data(
                AUDIO_DATA_TARBALL_PATH, DATA_DIR):
            logging.error('Audio data directory not found in DUT')
            raise error.TestError('Failed to unzip audio test data to DUT')

        # Result of visqol test on all files
        visqol_results = dict()

        for test_file in test_files:
            filename = os.path.split(test_file['file'])[1]
            logging.debug('Testing file: {}'.format(filename))

            # Set up hfp test to record on peer
            self.initialize_hfp(device, test_profile, test_file,
                                'recorded_by_peer',
                                self._get_pulseaudio_bluez_source_hfp)
            logging.debug('Initialized HFP')

            if not self.hfp_record_on_peer(device, test_profile, test_file):
                return False
            logging.debug('Recorded {} successfully'.format(filename))

            ref_file, deg_file = self.format_recorded_file(test_file,
                                                           test_profile,
                                                           'recorded_by_peer')
            if not ref_file or not deg_file:
                desc = 'Failed to get ref and deg file: ref {}, deg {}'.format(
                        ref_file, deg_file)
                raise error.TestError(desc)

            score = self.get_visqol_score(ref_file, deg_file,
                                          speech_mode=test_file['speech_mode'])

            logging.info('{} scored {}, min passing score: {}'.format(
                    filename, score, test_file['source_passing_score']))
            passed = score >= test_file['source_passing_score']
            visqol_results[filename] = passed

            # Track visqol performance
            test_desc = '{}_{}_{}'.format(test_profile, 'source',
                                          test_file['reporting_type'])
            self.write_perf_keyval({test_desc: score})

            if not passed:
                logging.warning('Failed: {}'.format(filename))

        return all(visqol_results.values())


    @test_retry_and_log(False)
    def test_hfp_dut_as_sink_visqol_score(self, device, test_profile):
        """Test Case: hfp test files streaming from peer device to dut

        @param device: the bluetooth peer device
        @param test_profile: which test profile is used, HFP_WBS or HFP_NBS

        @returns: True if the all the test files score at or above their
                  sink_passing_score value as defined in
                  bluetooth_audio_test_data.py
        """
        # list of test wav files
        hfp_test_data = audio_test_data[test_profile]
        test_files = hfp_test_data['visqol_test_files']

        get_visqol_binary()
        get_audio_test_data()
        self.host.send_file(AUDIO_DATA_TARBALL_PATH, AUDIO_DATA_TARBALL_PATH)
        if not self.bluetooth_facade.unzip_audio_test_data(
                AUDIO_DATA_TARBALL_PATH, DATA_DIR):
            logging.error('Audio data directory not found in DUT')
            raise error.TestError('Failed to unzip audio test data to DUT')

        # Result of visqol test on all files
        visqol_results = dict()

        for test_file in test_files:
            filename = os.path.split(test_file['file'])[1]
            logging.debug('Testing file: {}'.format(filename))

            # Set up hfp test to record on dut
            self.initialize_hfp(device, test_profile, test_file,
                                'recorded_by_dut',
                                self._get_pulseaudio_bluez_sink_hfp)
            logging.debug('Initialized HFP')
            # Record audio on dut played from pi, returns true if anything
            # was successfully recorded, false otherwise
            if not self.hfp_record_on_dut(device, test_profile, test_file):
                return False
            logging.debug('Recorded {} successfully'.format(filename))

            ref_file, deg_file = self.format_recorded_file(test_file,
                                                           test_profile,
                                                           'recorded_by_dut')
            if not ref_file or not deg_file:
                desc = 'Failed to get ref and deg file: ref {}, deg {}'.format(
                        ref_file, deg_file)
                raise error.TestError(desc)

            score = self.get_visqol_score(ref_file, deg_file,
                                          speech_mode=test_file['speech_mode'])

            logging.info('{} scored {}, min passing score: {}'.format(
                    filename, score, test_file['sink_passing_score']))
            passed = score >= test_file['sink_passing_score']
            visqol_results[filename] = passed

            # Track visqol performance
            test_desc = '{}_{}_{}'.format(test_profile, 'sink',
                                          test_file['reporting_type'])
            self.write_perf_keyval({test_desc: score})

            if not passed:
                logging.warning('Failed: {}'.format(filename))

        return all(visqol_results.values())

    @test_retry_and_log(False)
    def test_device_a2dp_connected(self, device, timeout=15):
        """ Tests a2dp profile is connected on device. """
        self.results = {}
        check_connection = lambda: self._get_pulseaudio_bluez_source_a2dp(
                device, A2DP)
        is_connected = self._wait_for_condition(check_connection,
                                                'test_device_a2dp_connected',
                                                timeout=timeout)
        self.results['peer a2dp connected'] = is_connected

        return all(self.results.values())


    @test_retry_and_log(False)
    def test_hfp_dut_as_source(self, device, test_profile):
        """Test Case: hfp sinewave streaming from dut to peer device

        @param device: the bluetooth peer device
        @param test_profile: which test profile is used, HFP_WBS or HFP_NBS

        @returns: True if the recorded primary frequency is within the
                  tolerance of the playback sine wave frequency.
        """
        hfp_test_data = audio_test_data[test_profile]

        self.initialize_hfp(device, test_profile, hfp_test_data,
                            'recorded_by_peer',
                            self._get_pulseaudio_bluez_source_hfp)

        if not self.hfp_record_on_peer(device, test_profile, hfp_test_data):
            return False

        # Check if the primary frequencies of recorded file meet expectation.
        check_freq_result = self._check_primary_frequencies(
                test_profile, hfp_test_data, 'recorded_by_peer')
        return check_freq_result


    @test_retry_and_log(False)
    def test_hfp_dut_as_sink(self, device, test_profile):
        """Test Case: hfp sinewave streaming from peer device to dut

        @param device: the bluetooth peer device
        @param test_profile: which test profile is used, HFP_WBS or HFP_NBS

        @returns: True if the recorded primary frequency is within the
                  tolerance of the playback sine wave frequency.

        """
        hfp_test_data = audio_test_data[test_profile]

        # Set up hfp test to record on dut
        self.initialize_hfp(device, test_profile, hfp_test_data,
                            'recorded_by_dut',
                            self._get_pulseaudio_bluez_sink_hfp)

        # Record audio on dut play from pi, returns true if anything recorded
        if not self.hfp_record_on_dut(device, test_profile, hfp_test_data):
            return False

        # Check if the primary frequencies of recorded file meet expectation.
        check_freq_result = self._check_primary_frequencies(
                test_profile, hfp_test_data, 'recorded_by_dut')
        return check_freq_result


    @test_retry_and_log(False)
    def test_avrcp_commands(self, device):
        """Test Case: Test AVRCP commands issued by peer can be received at DUT

        The very first AVRCP command (Linux evdev event) the DUT receives
        contains extra information than just the AVRCP event, e.g. EV_REP
        report used to specify delay settings. Send the first command before
        the actual test starts to avoid dealing with them during test.

        The peer device name is required to monitor the event reception on the
        DUT. However, as the peer device itself already registered with the
        kernel as an udev input device. The AVRCP profile will register as an
        separate input device with the name pattern: name + (AVRCP), e.g.
        RASPI_AUDIO (AVRCP). Using 'AVRCP' as device name to help search for
        the device.

        @param device: the Bluetooth peer device

        @returns: True if the all AVRCP commands received by DUT, false
                  otherwise

        """
        device.SendMediaPlayerCommand('play')

        name = device.name
        device.name = 'AVRCP'

        result_pause = self.test_avrcp_event(device,
            device.SendMediaPlayerCommand, 'pause')
        result_play = self.test_avrcp_event(device,
            device.SendMediaPlayerCommand, 'play')
        result_stop = self.test_avrcp_event(device,
            device.SendMediaPlayerCommand, 'stop')
        result_next = self.test_avrcp_event(device,
            device.SendMediaPlayerCommand, 'next')
        result_previous = self.test_avrcp_event(device,
            device.SendMediaPlayerCommand, 'previous')

        device.name = name
        self.results = {'pause': result_pause, 'play': result_play,
                        'stop': result_stop, 'next': result_next,
                        'previous': result_previous}
        return all(self.results.values())


    @test_retry_and_log(False)
    def test_avrcp_media_info(self, device):
        """Test Case: Test AVRCP media info sent by DUT can be received by peer

        The test update all media information twice to prevent previous
        leftover data affect the current iteration of test. Then compare the
        expected results against the information received on the peer device.

        This test verifies media information including: playback status,
        length, title, artist, and album. Position of the media is not
        currently support as playerctl on the peer side cannot correctly
        retrieve such information.

        Length and position information are transmitted in the unit of
        microsecond. However, BlueZ process those time data in the resolution
        of millisecond. Discard microsecond detail when comparing those media
        information.

        @param device: the Bluetooth peer device

        @returns: True if the all AVRCP media info received by DUT, false
                  otherwise

        """
        # First round of updating media information to overwrite all leftovers.
        init_status = 'stopped'
        init_length = 20200414
        init_position = 8686868
        init_metadata = {'album': 'metadata_album_init',
                         'artist': 'metadata_artist_init',
                         'title': 'metadata_title_init'}
        self.bluetooth_facade.set_player_playback_status(init_status)
        self.bluetooth_facade.set_player_length(init_length)
        self.bluetooth_facade.set_player_position(init_position)
        self.bluetooth_facade.set_player_metadata(init_metadata)

        # Second round of updating for actual testing.
        expected_status = 'playing'
        expected_length = 68686868
        expected_position = 20200414
        expected_metadata = {'album': 'metadata_album_expected',
                             'artist': 'metadata_artist_expected',
                             'title': 'metadata_title_expected'}
        self.bluetooth_facade.set_player_playback_status(expected_status)
        self.bluetooth_facade.set_player_length(expected_length)
        self.bluetooth_facade.set_player_position(expected_position)
        self.bluetooth_facade.set_player_metadata(expected_metadata)

        received_media_info = device.GetMediaPlayerMediaInfo()
        logging.debug(received_media_info)

        try:
            actual_length = int(received_media_info.get('length'))
        except:
            actual_length = 0

        result_status = bool(expected_status ==
            received_media_info.get('status').lower())
        result_album = bool(expected_metadata['album'] ==
            received_media_info.get('album'))
        result_artist = bool(expected_metadata['artist'] ==
            received_media_info.get('artist'))
        result_title = bool(expected_metadata['title'] ==
            received_media_info.get('title'))
        # The AVRCP time information is in the unit of microseconds but with
        # milliseconds resolution. Convert both send and received length into
        # milliseconds for comparison.
        result_length = bool(expected_length // 1000 == actual_length // 1000)

        self.results = {'status': result_status, 'album': result_album,
                        'artist': result_artist, 'title': result_title,
                        'length': result_length}
        return all(self.results.values())


    # ---------------------------------------------------------------
    # Definitions of all bluetooth audio test sequences
    # ---------------------------------------------------------------

    def test_a2dp_sinewaves(self, device, test_profile, duration):
        """Test Case: a2dp sinewaves

        @param device: the bluetooth peer device
        @param test_profile: the a2dp test profile;
                             choices are A2DP and A2DP_LONG
        @param duration: the duration of the audio file to test
                         0 means to use the default value in the test profile

        """
        # Make a copy since the test_data may be formatted with distinct
        # arguments in the follow-up tests.
        test_data = audio_test_data[test_profile].copy()
        if bool(duration):
            test_data['duration'] = duration
        else:
            duration = test_data['duration']

        test_data['file'] %= duration
        logging.info('%s test for %d seconds.', test_profile, duration)

        # Wait for pulseaudio a2dp bluez source
        self.test_device_a2dp_connected(device)

        # Select audio output node so that we do not rely on chrome to do it.
        self.test_select_audio_output_node_bluetooth()

        # Start recording audio on the peer Bluetooth audio device.
        self.test_device_to_start_recording_audio_subprocess(
                device, test_profile, test_data)

        # Play audio on the DUT in a non-blocked way and check the recorded
        # audio stream in a real-time manner.
        self.test_dut_to_start_playing_audio_subprocess(test_data)

        # Check chunks of recorded streams and verify the primary frequencies.
        # This is a blocking call until all chunks are completed.
        self.test_check_chunks(device, test_profile, test_data, duration)

        # Stop recording audio on the peer Bluetooth audio device.
        self.test_device_to_stop_recording_audio_subprocess(device)

        # Stop playing audio on DUT.
        self.test_dut_to_stop_playing_audio_subprocess()


    def playback_and_connect(self, device, test_profile):
        """Connect then disconnect an A2DP device while playing stream.

        This test first plays the audio stream and then selects the BT device
        as output node, checking if the stream has routed to the BT device.
        After that, disconnect the BT device and also check whether the stream
        closes on it gracefully.

        @param device: the Bluetooth peer device.
        @param test_profile: to select which A2DP test profile is used.
        """
        test_data = audio_test_data[test_profile]

        # Start playing audio on the Dut.
        self.test_dut_to_start_playing_audio_subprocess(test_data)

        # Connect the Bluetooth device.
        self.test_device_set_discoverable(device, True)
        self.test_discover_device(device.address)
        self.test_pairing(device.address, device.pin, trusted=True)
        self.test_connection_by_adapter(device.address)
        self.test_device_a2dp_connected(device)

        # Select Bluetooth as output node.
        self.test_select_audio_output_node_bluetooth()

        self.test_device_to_start_recording_audio_subprocess(
                device, test_profile, test_data)

        # Handle chunks of recorded streams and verify the primary frequencies.
        # This is a blocking call until all chunks are completed.
        self.test_check_chunks(device, test_profile, test_data,
                               test_data['chunk_checking_duration'])

        self.test_device_to_stop_recording_audio_subprocess(device)

        self.test_select_audio_output_node_internal_speaker()

        # Check if the device disconnects successfully.
        self.expect_test(False, self.test_device_a2dp_connected, device)

        self.test_dut_to_stop_playing_audio_subprocess()


    def playback_and_disconnect(self, device, test_profile):
        """Disconnect the Bluetooth device while the stream is playing.

        This test will keep the stream playing and then disconnect the
        Bluetooth device. The goal is to check the stream is still alive
        after the Bluetooth device disconnected.

        @param device: the Bluetooth peer device.
        @param test_profile: to select which A2DP test profile is used.
        """
        test_data = audio_test_data[test_profile]

        # Connect the Bluetooth device.
        self.test_device_set_discoverable(device, True)
        self.test_discover_device(device.address)
        self.test_pairing(device.address, device.pin, trusted=True)
        self.test_connection_by_adapter(device.address)
        self.test_device_a2dp_connected(device)

        # Select Bluetooth as output node.
        self.test_select_audio_output_node_bluetooth()

        self.test_device_to_start_recording_audio_subprocess(
                device, test_profile, test_data)

        # Start playing audio on the DUT.
        self.test_dut_to_start_playing_audio_subprocess(test_data)

        # Handle chunks of recorded streams and verify the primary frequencies.
        # This is a blocking call until all chunks are completed.
        self.test_check_chunks(device, test_profile, test_data,
                               test_data['chunk_checking_duration'])

        self.test_device_to_stop_recording_audio_subprocess(device)

        # Disconnect the Bluetooth device.
        self.test_disconnection_by_adapter(device.address)

        # Obtain audio thread summary to check if the audio stream is still
        # alive.
        self.test_audio_is_alive_on_dut()

        # Stop playing audio on the DUT.
        self.test_dut_to_stop_playing_audio_subprocess()


    def playback_back2back(self, device, test_profile):
        """Repeat to start and stop the playback stream several times.

        This test repeats to start and stop the playback stream and verify
        that the Bluetooth device receives the stream correctly.

        @param device: the Bluetooth peer device.
        @param test_profile: to select which A2DP test profile is used.
        """
        test_data = audio_test_data[test_profile]

        self.test_device_set_discoverable(device, True)
        self.test_discover_device(device.address)
        self.test_pairing(device.address, device.pin, trusted=True)
        self.test_connection_by_adapter(device.address)

        self.test_device_a2dp_connected(device)
        self.test_select_audio_output_node_bluetooth()

        for _ in range(3):
            # TODO(b/208165757): In here if we record the audio stream before
            # playing that will cause an audio blank about 1~2 sec in the
            # beginning of the recorded file and make the chunks checking fail.
            # Need to fix this problem in the future.
            self.test_dut_to_start_playing_audio_subprocess(test_data)
            self.test_device_to_start_recording_audio_subprocess(
                    device, test_profile, test_data)
            self.test_check_chunks(device, test_profile, test_data,
                                   test_data['chunk_checking_duration'])
            self.test_dut_to_stop_playing_audio_subprocess()
            self.test_device_to_stop_recording_audio_subprocess(device)

            self.test_device_to_start_recording_audio_subprocess(
                    device, test_profile, test_data)
            self.test_check_empty_chunks(device, test_data,
                                         test_data['chunk_checking_duration'])
            self.test_device_to_stop_recording_audio_subprocess(device)

        self.test_disconnection_by_adapter(device.address)
