# -*- coding: utf-8 -*-
# Copyright (c) 2010 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.


# DESCRIPTION :
#
# This is a factory test to test the audio.  Operator will test both record and
# playback for headset and built-in audio.  Recordings are played back for
# confirmation.  An additional pre-recorded sample is played to confirm speakers
# operate independently


import gtk
import logging
import os
import re
import sys

from autotest_lib.client.bin import test
from autotest_lib.client.common_lib import error
from autotest_lib.client.common_lib import utils
from autotest_lib.client.cros import factory_setup_modules
from cros.factory.test import factory
from cros.factory.test import ui as ful


_LABEL_BIG_SIZE = (280, 60)
_LABEL_STATUS_SIZE = (140, 30)
_LABEL_START_STR = 'hit SPACE to start each audio test\n' +\
    '按空白键开始各项声音测试\n\n'
_LABEL_RESPONSE_STR = ful.USER_PASS_FAIL_SELECT_STR + '\n'
_SAMPLE_LIST = ['Headset Audio Test']
_VERBOSE = False

# Add -D hw:0,0 since default argument does not work properly.
# See crosbug.com/p/12330
_CMD_PLAY_AUDIO = 'aplay -D hw:0,0 %s'
_CMD_RECORD_AUDIO = 'arecord -D hw:0,0 -f dat -t wav %s'


class factory_Audio(test.test):
    version = 1

    def audio_subtest_widget(self, name):
        vb = gtk.VBox()
        ebh = gtk.EventBox()
        ebh.modify_bg(gtk.STATE_NORMAL, ful.LABEL_COLORS[ful.ACTIVE])
        ebh.add(ful.make_label(name, size=_LABEL_BIG_SIZE,
                               fg=ful.BLACK))
        vb.pack_start(ebh)
        vb.pack_start(ful.make_vsep(3), False, False)
        if re.search('Headset', name):
            lab_str = 'Connect headset to device\n将耳机接上音源孔'
        else:
            lab_str = 'Remove headset from device\n将耳机移开音源孔'
        vb.pack_start(ful.make_label(lab_str, fg=ful.WHITE))
        vb.pack_start(ful.make_vsep(3), False, False)
        instruction = ['Press & hold \'r\' to record',
                       '压住 \'r\' 键开始录音',
                       '[Playback will follow]',
                       '[之后会重播录到的声音]',
                       '']
        if self._test_left_right:
            instruction.extend([
                    'Press & hold left-Shift to play from left channel',
                    '压住 左Shift 键，从左声道播放范例',
                    'Press & hold right-Shift to play from right channel',
                    '压住 右Shift 键，从右声道播放范例'])
        else:
            instruction.extend(['Press & hold \'p\' to play sample',
                                '压住 \'p\' 键播放范例'])
        vb.pack_start(ful.make_label('\n'.join(instruction)))
        vb.pack_start(ful.make_vsep(3), False, False)
        vb.pack_start(ful.make_label(ful.USER_PASS_FAIL_SELECT_STR,
                                     fg=ful.WHITE))

        # Need event box to effect bg color.
        eb = gtk.EventBox()
        eb.modify_bg(gtk.STATE_NORMAL, ful.BLACK)
        eb.add(vb)

        self._subtest_widget = eb

        self._test_widget.remove(self._top_level_test_list)
        self._test_widget.add(self._subtest_widget)
        self._test_widget.show_all()

    def close_bgjob(self, sample_name):
        job = self._bg_job
        if job:
            utils.nuke_subprocess(job.sp)
            utils.join_bg_jobs([job], timeout=1)
            result = job.result
            if _VERBOSE and (result.stdout or result.stderr):
                raise error.CmdError(
                    sample_name, result,
                    'stdout: %s\nstderr: %s' % (result.stdout, result.stderr))
        self._bg_job = None

    def goto_next_sample(self):
        if not self._sample_queue:
            gtk.main_quit()
            return
        self._current_sample = self._sample_queue.pop()
        name = self._current_sample
        self._status_map[name] = ful.ACTIVE

    def cleanup_sample(self):
        factory.log('Inside cleanup_sample')
        self._test_widget.remove(self._subtest_widget)
        self._subtest_widget = None
        self._test_widget.add(self._top_level_test_list)
        self._test_widget.show_all()
        self.goto_next_sample()

    def key_press_callback(self, widget, event):
        name = self._current_sample
        if (event.keyval == gtk.keysyms.space and self._subtest_widget is None):
            # Start subtest.
            self.audio_subtest_widget(name)
        # Make sure we are not already recording. We can get repeated events.
        elif self._active == False:
            self.close_bgjob(name)
            cmd = None
            if event.keyval == ord('r'):
                # Record via mic.
                if os.path.isfile('rec.wav'):
                    os.unlink('rec.wav')
                cmd = _CMD_RECORD_AUDIO % 'rec.wav'
            else:
                if self._test_left_right:
                    if event.keyval == gtk.keysyms.Shift_L:
                        cmd = _CMD_PLAY_AUDIO % self._left_audio_sample_path
                    elif event.keyval== gtk.keysyms.Shift_R:
                        cmd= _CMD_PLAY_AUDIO % self._right_audio_sample_path
                else:
                    if event.keyval == ord('p'):
                        # Playback canned audio.
                        cmd = _CMD_PLAY_AUDIO % self._audio_sample_path
            if cmd:
                self._active = True
                self._bg_job = utils.BgJob(cmd, stderr_level=logging.DEBUG)
                factory.log("cmd: " + cmd)
        self._test_widget.queue_draw()
        return True

    def key_release_callback(self, widget, event):
        # Make sure we capture more advanced key events only when
        # entered a subtest.
        if self._subtest_widget is None:
            return True
        name = self._current_sample
        if event.keyval == gtk.keysyms.Tab:
            self._status_map[name] = ful.FAILED
            self.cleanup_sample()
        elif event.keyval == gtk.keysyms.Return:
            self._status_map[name] = ful.PASSED
            self.cleanup_sample()
        elif event.keyval == ord('Q'):
            gtk.main_quit()
        elif event.keyval == ord('r'):
            self.close_bgjob(name)
            cmd = _CMD_PLAY_AUDIO % 'rec.wav'
            self._bg_job = utils.BgJob(cmd, stderr_level=logging.DEBUG)
            factory.log("cmd: " + cmd)
            # Clear active recording state.
            self._active = False
        else:
            if self._test_left_right:
                stop_playing = (event.keyval == gtk.keysyms.Shift_L or
                                event.keyval == gtk.keysyms.Shift_R)
            else:
                stop_playing = event.keyval == ord('p')
            if stop_playing:
                self.close_bgjob(name)
                # Clear active playing state.
                self._active = False
        self._test_widget.queue_draw()
        return True

    def label_status_expose(self, widget, event, label=None, name=None):
        status = self._status_map[name]
        if label:
            label.set_text(status)
            label.modify_fg(gtk.STATE_NORMAL, ful.LABEL_COLORS[status])

    def make_sample_label_box(self, name):
        eb = gtk.EventBox()
        eb.modify_bg(gtk.STATE_NORMAL, ful.BLACK)
        label_status = ful.make_label(ful.UNTESTED, size=_LABEL_STATUS_SIZE,
                                      alignment=(0, 0.5),
                                      fg=ful.LABEL_COLORS['UNTESTED'])
        # Note that expose callback must not tie to the object we are going t
        # modify. Or it'll cause infinite event loop.
        expose_cb = lambda *x: self.label_status_expose(
                *x, **{'name':name, 'label':label_status})
        eb.connect('expose_event', expose_cb)
        label_en = ful.make_label(name, alignment=(1,0.5))
        label_sep = ful.make_label(' : ', alignment=(0.5, 0.5))
        hbox = gtk.HBox()
        hbox.pack_end(label_status, False, False)
        hbox.pack_end(label_sep, False, False)
        hbox.pack_end(label_en, False, False)
        eb.add(hbox)
        return eb

    def register_callbacks(self, window):
        window.connect('key-press-event', self.key_press_callback)
        window.add_events(gtk.gdk.KEY_PRESS_MASK)
        window.connect('key-release-event', self.key_release_callback)
        window.add_events(gtk.gdk.KEY_RELEASE_MASK)

    def run_once(self, audio_sample_path=None, audio_init_volume=None,
                 amixer_init_cmd=None, left_right_audio_sample_pair=None):

        factory.log('%s run_once' % self.__class__)

        # Change initial volume.
        if audio_init_volume:
            os.system("amixer -c 0 sset Master %d%%" % audio_init_volume)
        # Allow extra amixer command for init.
        if amixer_init_cmd:
            os.system("amixer -c 0 %s" % amixer_init_cmd)

        # Write recordings in tmpdir.
        os.chdir(self.tmpdir)

        self._bg_job = None

        self._test_left_right = left_right_audio_sample_pair is not None
        if self._test_left_right:
            left, right = left_right_audio_sample_pair
            self._left_audio_sample_path = utils.locate_file(
                left, base_dir=self.job.autodir)
            self._right_audio_sample_path = utils.locate_file(
                right, base_dir=self.job.autodir)
            if (self._left_audio_sample_path is None or
                self._right_audio_sample_path is None):
                raise error.TestFail(
                    'ERROR: left_right_audio_sample_pair should be a pair of '
                    'audio sample for left and right channel test.')
        else:
            self._audio_sample_path = utils.locate_file(
                audio_sample_path, base_dir=self.job.autodir)
            if self._audio_sample_path is None:
                raise error.TestFail('ERROR: must provide an audio sample '
                                     'via audio_sample_path.')

        self._sample_queue = [x for x in reversed(_SAMPLE_LIST)]
        self._status_map = dict((n, ful.UNTESTED) for n in _SAMPLE_LIST)
        # Ensure that we don't try to handle multiple overlapping
        # keypress actions. Make a note of when we are currently busy
        # and refuse events during that time.
        self._active = False

        prompt_label = ful.make_label(_LABEL_START_STR, alignment=(0.5, 0.5))

        self._top_level_test_list = gtk.VBox()
        self._top_level_test_list.pack_start(prompt_label, False, False)

        for name in _SAMPLE_LIST:
            label_box = self.make_sample_label_box(name)
            self._top_level_test_list.pack_start(label_box, False, False)

        self._test_widget = gtk.EventBox()
        self._test_widget.modify_bg(gtk.STATE_NORMAL, ful.BLACK)
        self._test_widget.add(self._top_level_test_list)

        self._subtest_widget = None

        self.goto_next_sample()

        ful.run_test_widget(self.job, self._test_widget,
            window_registration_callback=self.register_callbacks)

        failed_set = set(name for name, status in self._status_map.items()
                         if status is not ful.PASSED)
        if failed_set:
            raise error.TestFail('some samples failed (%s)' %
                                 ', '.join(failed_set))

        factory.log('%s run_once finished' % self.__class__)
