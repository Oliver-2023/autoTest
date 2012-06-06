# -*- coding: utf-8 -*-
# Copyright (c) 2012 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.


# DESCRIPTION :
#
# This is a factory test for audio quality. External equipment will send
# command through ethernet to configure the audio loop path. Note that it's
# External equipment's responsibility to capture and analyze the audio signal.

import gobject
import gtk
import os
import re
import socket
import subprocess
import tempfile

from autotest_lib.client.bin import test, utils
from autotest_lib.client.common_lib import error
from autotest_lib.client.cros import factory
from autotest_lib.client.cros.audio import audio_helper
from autotest_lib.client.cros.factory import ui as ful

# Host test machine crossover connected to DUT, fix local ip and port for
# communication in between.
_HOST = ''
_PORT = 8888
_LOCAL_IP = '192.168.1.2'

# Label strings.
_LABEL_CONNECTED = 'Connected\n已連線\n'
_LABEL_WAITING = 'Waiting for command\n等待指令中\n'
_LABEL_AUDIOLOOP = 'Audio looping\n音源回放中\n'
_LABEL_SPEAKER_MUTE_OFF = 'Speaker on\n喇叭開啟\n'
_LABEL_DMIC_ON = 'Dmic on\nLCD mic開啟\n'
_LABEL_PLAYTONE_LEFT = ('Playing tone to left channel\n'
                        '播音至左聲道\n')
_LABEL_PLAYTONE_RIGHT = ('Playing tone to right channel\n'
                         '播音至右聲道\n')

# Regular expression to match external commands.
_LOOP_0_RE = re.compile("(?i)loop_0")
_LOOP_1_RE = re.compile("(?i)loop_1")
_LOOP_2_RE = re.compile("(?i)loop_2")
_LOOP_3_RE = re.compile("(?i)loop_3")
_XTALK_L_RE = re.compile("(?i)xtalk_l")
_XTALK_R_RE = re.compile("(?i)xtalk_r")
_SEND_FILE_RE = re.compile("(?i)send_file\,\s*[^\,]+\,\s*(\d)+$")
_TEST_COMPLETE_RE = re.compile("(?i)test_complete")
_RESULT_PASS_RE = re.compile("(?i)result_pass")
_RESULT_FAIL_RE = re.compile("(?i)result_fail")

# Common mixer settings for special audio configurations, board specific
# settings should goes to each test list.
_DMIC_SWITCH_MIXER_SETTINGS = []
_INIT_MIXER_SETTINGS = [{'name': '"HP/Speaker Playback Switch"',
                         'value': 'on'},
                        {'name': '"Headphone Playback Switch"',
                         'value': 'on,on'},
                        {'name': '"Headphone Playback Volume"',
                         'value': '100,100'},
                        {'name': '"Speaker Playback Volume"',
                         'value': '100,100'}]
_UNMUTE_SPEAKER_MIXER_SETTINGS = [{'name': '"HP/Speaker Playback Switch"',
                                   'value': 'off'}]


class factory_AudioQuality(test.test):
    version = 2

    def handle_connection(self, conn, *args):
        '''
        Asynchronous handler for socket connection.
        '''
        line = conn.recv(1024)
        if line:
            factory.log("Received command %s" % line)
        else:
            return False

        for key in self._handlers.iterkeys():
            if key.match(line):
                self._handlers[key](conn, line)
                break

        # Respond by the received command with '_OK' postfix.
        conn.send(line + '_OK')
        return False

    def start_loop(self):
        '''
        Starts the internal audio loopback.
        '''
        cmdargs = [self._ah.sox_path, '-t', 'alsa', self._input_dev, '-t',
                'alsa', self._output_dev]
        self._loop_process = subprocess.Popen(cmdargs, stderr=subprocess.PIPE)

    def play_tone(self):
        '''
        Plays a single tone.
        '''
        cmdargs = [self._ah.sox_path, '-n', '-d', 'synth', '20.0', 'sine',
                '1000.0']
        self._play_tone_process = subprocess.Popen(cmdargs,
                stderr=subprocess.PIPE)

    def restore_configuration(self):
        '''
        Stops all the running process and restore the mute settings.
        '''
        if hasattr(self, '_play_tone_process') and self._play_tone_process:
            self._play_tone_process.kill()
            self._play_tone_process = None
        if hasattr(self, '_loop_process') and self._loop_process:
            self._loop_process.kill()
            self._loop_process = None
            factory.log("Stopped audio loop process")
        self._ah.set_mixer_controls(self._init_mixer_settings)

    def handle_send_file(self, *args):
        conn = args[0]
        conn.send('OK')

        params = args[1].split(',')
        file_name = params[1]
        size = int(params[2])

        with tempfile.NamedTemporaryFile(mode='w+t') as tmp_file:
            factory.log("created tmp_file: %s\n" % tmp_file.name)
            tmp_file.write('File name: %s\n' % file_name)

            # A message DONE will be concatenated to the end of detailed log.
            left = size + 4
            while left > 0:
                data = conn.recv(1024)
                left -= len(data)
                tmp_file.write(data)
            tmp_file.seek(0)
            for line in tmp_file:
                self._detail_log += line

        factory.log("Received file %s with size %d" % (file_name, size))

    def handle_result_pass(self, *args):
        self._test_passed = True

    def handle_result_fail(self, *args):
        self._test_passed = False

    def handle_test_complete(self, *args):
        gtk.main_quit()

    def handle_loop_none(self, *args):
        self.restore_configuration()
        self._loop_status_label.set_text(_LABEL_WAITING)

    def handle_loop(self, *args):
        self.restore_configuration()
        self._loop_status_label.set_text(_LABEL_AUDIOLOOP)
        self.start_loop()

    def handle_loop_from_dmic(self, *args):
        self.handle_loop()
        self._loop_status_label.set_text(_LABEL_AUDIOLOOP +
                _LABEL_DMIC_ON)
        self._ah.set_mixer_controls(self._dmic_switch_mixer_settings)

    def handle_loop_speaker_unmute(self, *args):
        self.handle_loop()
        self._loop_status_label.set_text(_LABEL_AUDIOLOOP +
                _LABEL_SPEAKER_MUTE_OFF)
        self.unmute_speaker()

    def handle_xtalk_left(self, *args):
        self.restore_configuration()
        self._loop_status_label.set_text(_LABEL_PLAYTONE_LEFT)
        self.headphone_playback_switch(False, True)
        self.play_tone()

    def handle_xtalk_right(self, *args):
        self.restore_configuration()
        self._loop_status_label.set_text(_LABEL_PLAYTONE_RIGHT)
        self.headphone_playback_switch(True, False)
        self.play_tone()

    def listen(self, sock, *args):
        '''
        Listens for connection and start handler for it.
        '''
        conn, addr = sock.accept()
        self._loop_status_label.set_text("Connected")
        gobject.io_add_watch(conn, gobject.IO_IN, self.handle_connection)
        return True

    def start_server(self):
        '''
        Initialize server and start listening for external commands.
        '''
        sock = socket.socket()
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((_HOST, _PORT))
        sock.listen(1)
        factory.log("Listening at port %d" % _PORT)
        gobject.io_add_watch(sock, gobject.IO_IN, self.listen)

    def headphone_playback_switch(self, left=False, right=False):
        '''
        Sets headphone playback switch values.

        Args:
            left: true to set left channel on.
            right: true to set right channel on.
        '''
        left_switch = 'on' if left else 'off'
        right_switch = 'on' if right else 'off'
        mixer_settings = [{'name': "'Headphone Playback Switch'",
                           'value': ('%s,%s' % (left_switch, right_switch))}]
        self._ah.set_mixer_controls(mixer_settings)

    def unmute_speaker(self):
        self._ah.set_mixer_controls(self._unmute_speaker_mixer_settings)

    def on_test_complete(self):
        '''
        Restores the original state before exiting the test.
        '''
        os.system('iptables -D INPUT -p tcp --dport %s -j ACCEPT' % _PORT)
        os.system('ifconfig %s down' % self._eth)
        os.system('ifconfig %s up' % self._eth)
        self.restore_configuration()
        self._ah.cleanup_deps(['sox'])

    def key_release_callback(self, widget, event):
        # Hit Q to force quit this test.
        if event.keyval == ord('Q'):
            self._test_passed = False
            gtk.main_quit()

    def register_callbacks(self, window):
        window.connect('key-release-event', self.key_release_callback)

    def check_eth_state(self):
        path = '/sys/class/net/%s/carrier' % self._eth
        output = None
        try:
            if os.path.exists(path):
                output = open(path).read()
        finally:
            if output:
                return output == '1\n'
            else:
                return False

    def run_once(self, input_dev='hw:0,0', output_dev='hw:0,0', eth='eth0',
            dmic_switch_mixer_settings=_DMIC_SWITCH_MIXER_SETTINGS,
            init_mixer_settings=_INIT_MIXER_SETTINGS,
            unmute_speaker_mixer_settings=_UNMUTE_SPEAKER_MIXER_SETTINGS):
        factory.log('%s run_once' % self.__class__)

        self._ah = audio_helper.AudioHelper(self, input_device=input_dev)
        self._ah.setup_deps(['sox'])
        self._detail_log = ''
        self._input_dev = input_dev
        self._output_dev = output_dev
        self._eth = eth

        # Mixer settings for different configurations.
        self._init_mixer_settings = init_mixer_settings
        self._unmute_speaker_mixer_settings = unmute_speaker_mixer_settings
        self._dmic_switch_mixer_settings = dmic_switch_mixer_settings
        self._ah.set_mixer_controls(self._init_mixer_settings)

        factory.log('Checking %s state....' % self._eth)
        utils.poll_for_condition(self.check_eth_state,
                                 timeout=30, desc='Checking %s' % self._eth)
        factory.log('Checking %s done!' % eth)

        # Configure local network environment to accept command from test host.
        os.system('ifconfig %s %s netmask 255.255.255.0 up' %
                (self._eth, _LOCAL_IP))
        os.system('iptables -A INPUT -p tcp --dport %s -j ACCEPT' % _PORT)

        # Register commands to corresponding handlers.
        self._handlers = {}
        self._handlers[_SEND_FILE_RE] = self.handle_send_file
        self._handlers[_RESULT_PASS_RE] = self.handle_result_pass
        self._handlers[_RESULT_FAIL_RE] = self.handle_result_fail
        self._handlers[_TEST_COMPLETE_RE] = self.handle_test_complete
        self._handlers[_LOOP_0_RE] = self.handle_loop_none
        self._handlers[_LOOP_1_RE] = self.handle_loop_from_dmic
        self._handlers[_LOOP_2_RE] = self.handle_loop_speaker_unmute
        self._handlers[_LOOP_3_RE] = self.handle_loop
        self._handlers[_XTALK_L_RE] = self.handle_xtalk_left
        self._handlers[_XTALK_R_RE] = self.handle_xtalk_right

        self.start_server()

        self._main_widget = gtk.EventBox()
        self._main_widget.modify_bg(gtk.STATE_NORMAL, ful.BLACK)
        self._loop_status_label = ful.make_label('No audio loop', fg=ful.WHITE)
        self._main_widget.add(self._loop_status_label)

        ful.run_test_widget(self.job, self._main_widget,
                window_registration_callback=self.register_callbacks,
                cleanup_callback=self.on_test_complete)
        if not self._test_passed:
            factory.log(self._detail_log)
            raise error.TestError('Test failed.')

        factory.log('%s run_once finished' % self.__class__)
