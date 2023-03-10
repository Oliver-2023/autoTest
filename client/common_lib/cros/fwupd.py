# Copyright 2023 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import json
import logging
import re
import common

from autotest_lib.client.bin import test, utils
from autotest_lib.client.common_lib import error


def get_devices():
    """Gets info about all the devices currently detected by fwupd.

    Returns:
      A list of dicts containing the info of all the devices detected

    Raises:
      error.TestError if there was an error running fwupdmgr, if the
      output couldn't be parsed or if there were no devices found.
    """
    try:
        cmd = "fwupdmgr get-devices --json"
        output = utils.system_output(cmd)
    except error.CmdError as e:
        raise error.TestError(e)
    try:
        devices = json.loads(output)
    except json.decoder.JSONDecodeError as e:
        raise error.TestError("Error parsing <fwupdmgr get-devices> "
                              f"output: {e}")
    if 'Devices' not in devices:
        raise error.TestError("No devices found")
    return devices['Devices']


def _device_match_id(dev, dev_id):
    """Checks whether a device matches a device id.

    Args:
      dev: dictionary that defines the device to check. It should be
          one of the devices returned by get_devices()
      dev_id: the device id to match (string). It can be an fwupd
          instance id or a GUID

    Returns:
      True if dev has dev_id as an identifier. False otherwise
    """
    if dev.get('DeviceId') == dev_id:
        return True
    for guid in dev.get('Guid', []):
        if guid == dev_id:
            return True
    return False


def check_device(dev_id, devices):
    """Device sanity check.

    Checks if the device identified by dev_id is in the devices list
    and is updatable.

    Args:
      dev_id: the id of the device to check (string). It can be an
          fwupd instance id or a GUID
      devices: the list of devices returned by get_devices()

    Returns:
      The device identified by dev_id, if it exists in the devices list.

    Raises:
      error.TestError if the device is not found or is not updatable
    """
    for d in devices:
        if _device_match_id(d, dev_id):
            dev_name = d.get('Name', 'Unknown Device')
            if 'DeviceId' not in d:
                raise error.TestError(f"Device {dev_id} ({dev_name}) has "
                                      "no DeviceId")
            if 'Version' not in d:
                raise error.TestError(f"Device {dev_id} ({dev_name}) has "
                                      "no FW version info")
            if 'Flags' not in d:
                raise error.TestError(f"Device {dev_id} ({dev_name}) "
                                      "has no 'Flags' attribute")
            if 'updatable' in d['Flags']:
                return d
            else:
                raise error.TestError(f"Device {dev_id} ({dev_name}) "
                                      "is not updatable")
    raise error.TestError(f"Device {dev_id} not found")


def get_fwupdmgr_version():
    """Returns the fwupdmgr version as a string

    It can also be used to check whether fwupd (the daemon) is
    running, as fwupdmgr tries to connect to it to get the version
    info.

    Returns:
      A string containing the fwupdmgr version. <None> if fwupdmgr
      failed to run, if it couldn't connect to the daemon or if
      there was a problem fetching and parsing the data. Details are
      logged to the ERROR test log.

    Note:
      For the purposes of this test we don't need to differentiate
      between the daemon and client versions.
    """
    try:
        cmd = "fwupdmgr --version --json"
        output = utils.system_output(cmd)
    except error.CmdError as e:
        logging.error("fwupd not running, not found or broken")
        logging.error(e)
        return None
    try:
        versions = json.loads(output)
        for v in versions.get('Versions', []):
            if (v.get('AppstreamId') == 'org.freedesktop.fwupd'
                        and v.get('Type') == 'runtime'):
                return v.get('Version')
    except json.decoder.JSONDecodeError:
        # fallback: json output not supported, parse stdout
        m = re.search("client version:\s+([\d.]+)", output)
        if m:
            return m.group(1)
    logging.error("Error parsing fwupd version info")
    logging.error(output)
    return None