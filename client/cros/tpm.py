# Copyright 2021 The ChromiumOS Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Utilities to interact with the TPM on a CrOS device."""

import re

import common

from autotest_lib.client.bin import utils
from autotest_lib.client.common_lib import error

UNAVAILABLE_ACTION = 'Unknown action or no action given.'
TPM_MANAGER_CMD = '/usr/bin/tpm_manager_client'


class ChromiumOSError(error.TestError):
    """Generic error for ChromiumOS-specific exceptions."""

    pass


def get_tpm_status():
    """Get the TPM status.

    Returns:
        A TPM status dictionary, for example:
        { 'Enabled': True,
          'Owned': True,
          'Ready': True
        }
    """
    out = run_cmd(TPM_MANAGER_CMD + ' status')
    status = {}
    for field in ['enabled', 'owned']:
        match = re.search('%s: (true|false)' % field, out)
        if not match:
            raise ChromiumOSError('Invalid TPM status: "%s".' % out)
        status[field] = match.group(1) == 'true'
    status['Enabled'] = status['enabled']
    status['Owned'] = status['owned']
    status['Ready'] = status['enabled'] and status['owned']
    return status


def get_tpm_da_info():
    """Get the TPM dictionary attack information.
    Returns:
        A TPM dictionary attack status dictionary, for example:
        {
          'dictionary_attack_counter': 0,
          'dictionary_attack_threshold': 200,
          'dictionary_attack_lockout_in_effect': False,
          'dictionary_attack_lockout_seconds_remaining': 0
        }
    """
    status = {}
    out = run_cmd(TPM_MANAGER_CMD + ' get_da_info')
    for line in out.splitlines()[1:-1]:
        items = line.strip().split(':')
        if len(items) != 2:
            continue
        if items[1].strip() == 'false':
            value = False
        elif items[1].strip() == 'true':
            value = True
        elif items[1].split('(')[0].strip().isdigit():
            value = int(items[1].split('(')[0].strip())
        else:
            value = items[1].strip(' "')
        status[items[0].strip()] = value
    return status


def get_tpm_spec_revision():
    """Get Spec Revision from tpm_version."""
    out = run_cmd('tpm_version')
    m = re.search('Spec Revision: +(\d+)', out)
    if m is None:
        raise error.TestError('Unexpected tpm_version output: %s' % out)
    return int(m.group(1))


def take_ownership():
    """Take TPM ownership.

    Args:
        wait_for_ownership: block until TPM is owned if true
    """
    run_cmd(TPM_MANAGER_CMD + ' take_ownership')


def get_tpm_password():
    """Get the TPM password.

    Returns:
        A TPM password
    """
    out = run_cmd(TPM_MANAGER_CMD + ' status')
    match = re.search('owner_password: (\w*)', out)
    password = ''
    if match:
        hex_pass = match.group(1)
        password = ''.join(
                chr(int(hex_pass[i:i + 2], 16))
                for i in range(0, len(hex_pass), 2))
    return password


def is_tpm_lockout_in_effect():
    """Returns true if the TPM lockout is in effect; false otherwise."""
    status = get_tpm_da_info()
    return status.get('dictionary_attack_lockout_in_effect', None)


def run_cmd(cmd):
    """Run a command on utils.system_output, and append '2>&1'."""
    return utils.system_output(cmd + ' 2>&1', retain_output=True,
                               ignore_status=True).strip()
