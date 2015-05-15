# Copyright 2015 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import logging
import os
import subprocess
import tempfile
import time

from autotest_lib.client.bin import utils
from autotest_lib.client.common_lib import error

class InputPlayback(object):
    """
    Provides an interface for playback and emulating peripherals via evemu-*.

    Example use: player = InputPlayback()
                 player.emulate(property_file=path_to_file)
                 player.find_connected_inputs()
                 player.playback(path_to_file)
                 player.blocking_playback(path_to_file)
                 player.close()

    """

    _DEFAULT_PROPERTY_FILES = {'mouse' : 'mouse.prop',
                               'keyboard' : 'keyboard.prop'}
    _PLAYBACK_COMMAND = 'evemu-play --insert-slot0 %s < %s'


    def __init__(self):
        self.nodes = {}
        self.names = {}
        self._device_emulation_process = None


    def has(self, input_type):
        """Return True/False if device has a input of given type.

        @param input_type: string of type, e.g. 'touchpad'

        """
        return input_type in self.nodes


    def _get_input_events(self):
        """Return a list of all input event nodes."""
        return utils.run('ls /dev/input/event*').stdout.strip().split()


    def emulate(self, input_type='mouse', property_file=None):
        """
        Emulate the given input (or default for type) with evemu-device.

        Emulating more than one of the same device type will only allow playback
        on the last one emulated.  The name of the last-emulated device is
        noted to be sure this is the case.

        Property files are made with the evemu-describe command,
        e.g. 'evemu-describe /dev/input/event12 > property_file'.

        @param input_type: 'mouse' or 'keyboard' to use default property files.
                           Need not be specified if supplying own file.
        @param property_file: Property file of device to be emulated.  Generate
                              with 'evemu-describe' command on test image.

        """
        if not property_file:
            if input_type not in self._DEFAULT_PROPERTY_FILES:
                raise error.TestError('Please supply a property file for input '
                                      'type %s' % input_type)
            current_dir = os.path.dirname(os.path.realpath(__file__))
            property_file = os.path.join(
                    current_dir, self._DEFAULT_PROPERTY_FILES[input_type])
        if not os.path.isfile(property_file):
            raise error.TestError('Property file %s not found!' % property_file)

        logging.info('Emulating %s %s', input_type, property_file)
        num_events_before = len(self._get_input_events())
        self._device_emulation_process = subprocess.Popen(
                ['evemu-device', property_file], stdout=subprocess.PIPE)
        utils.poll_for_condition(
                lambda: len(self._get_input_events()) > num_events_before,
                exception=error.TestError('Error emulating %s!' % input_type))

        with open(property_file) as fh:
            name_line = fh.readline() #Format "N: NAMEOFDEVICE"
            name = name_line[3:-1]
            self.names[input_type] = name


    def _find_device_properties(self, device):
        """Return string of properties for given node.

        @return: string of properties.

        """
        with tempfile.NamedTemporaryFile() as temp_file:
            filename = temp_file.name
            evtest_process = subprocess.Popen(['evtest', device],
                                              stdout=temp_file)

            def find_exit():
                """Polling function for end of output."""
                interrupt_cmd = 'grep "interrupt to exit" %s | wc -l' % filename
                line_count = utils.run(interrupt_cmd).stdout.strip()
                return line_count != '0'

            utils.poll_for_condition(find_exit)
            evtest_process.kill()
            temp_file.seek(0)
            props = temp_file.read()
        return props


    def _determine_input_type(self, node):
        """Find node's list of properties and return input type (if any).

        @return: string of type, or None

        """
        props = self._find_device_properties(node)
        if props.find('REL_X') >= 0 and props.find('REL_Y') >= 0:
            if (props.find('ABS_MT_POSITION_X') >= 0 and
                props.find('ABS_MT_POSITION_Y') >= 0):
                return 'multitouch_mouse'
            else:
                return 'mouse'
        if props.find('ABS_X') >= 0 and props.find('ABS_Y') >= 0:
            if (props.find('BTN_STYLUS') >= 0 or
                props.find('BTN_STYLUS2') >= 0 or
                props.find('BTN_TOOL_PEN') >= 0):
                return 'tablet'
            if (props.find('ABS_PRESSURE') >= 0 or
                props.find('BTN_TOUCH') >= 0):
                if (props.find('BTN_LEFT') >= 0 or
                    props.find('BTN_MIDDLE') >= 0 or
                    props.find('BTN_RIGHT') >= 0 or
                    props.find('BTN_TOOL_FINGER') >= 0):
                    return 'touchpad'
                else:
                    return 'touchscreen'
            if props.find('BTN_LEFT') >= 0:
                return 'touchscreen'
        if props.find('KEY_ESC') >= 0:
            return 'keyboard'
        return


    def find_connected_inputs(self):
        """Determine the nodes of all present input devices, if any.

        Cycle through all possible /dev/input/event* and find which ones
        are touchpads, touchscreens, mice, keyboards, etc.
        These nodes can be used for playback later.
        If a name already exists in self.names, prefer that device.
        Record the found nodes in self.nodes and their names in self.names.

        """
        self.nodes = {} #Discard any previously seen nodes.

        input_events = self._get_input_events()
        for event in input_events:
            input_type = self._determine_input_type(event)
            if input_type:
                class_folder = event.replace('dev', 'sys/class')
                name_file = os.path.join(class_folder, 'device', 'name')
                name = 'unknown'
                if os.path.isfile(name_file):
                    name = utils.run('cat %s' % name_file).stdout.strip()
                logging.info('Found %s: %s at %s.', input_type, name, event)

                # If a particular device is expected, make sure name matches.
                if input_type in self.names:
                    if self.names[input_type] != name:
                        continue

                # Save this device information for later use.
                self.nodes[input_type] = event
                self.names[input_type] = name


    def playback(self, filepath, input_type='touchpad'):
        """Playback a given input file.

        Create input file using evemu-record.
        E.g. 'evemu-record $NODE -1 > $FILENAME'

        @param filepath: path to the input file on the DUT.
        @param input_type: name of device type; 'touchpad' by default.
                           Types are returned by the _determine_input_type()
                           function.
                           input_type must be in self.nodes. Check using has().

        """
        assert(input_type in self.nodes)
        node = self.nodes[input_type]
        logging.info('Playing back finger-movement on %s, file=%s.', node,
                     filepath)
        utils.run(self._PLAYBACK_COMMAND % (node, filepath))


    def blocking_playback(self, filepath, input_type='touchpad'):
        """Playback a given set of inputs and sleep for duration.

        The input file is of the format <name>\nE: <time> <input>\nE: ...
        Find the total time by the difference between the first and last input.

        @param filepath: path to the input file on the DUT.
        @param input_type: name of device type; 'touchpad' by default.
                           Types are returned by the _determine_input_type()
                           function.
                           input_type must be in self.nodes. Check using has().

        """
        with open(filepath) as fh:
            lines = fh.readlines()
            start = float(lines[0].split(' ')[1])
            end = float(lines[-1].split(' ')[1])
            sleep_time = end - start
        self.playback(filepath, input_type)
        logging.info('Sleeping for %s seconds during playback.', sleep_time)
        time.sleep(sleep_time)


    def close(self):
        """Kill emulation if necessary."""
        if self._device_emulation_process:
            self._device_emulation_process.kill()


    def __exit__(self):
        self.close()
