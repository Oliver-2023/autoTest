#!/usr/bin/python3
# Copyright (c) 2013 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import os
import sys

import common

from autotest_lib.client.common_lib import control_data
from autotest_lib.client.common_lib import global_config

AUTOTEST_INSTALL_DIR = global_config.global_config.get_config_value('SCHEDULER',
                                                 'drone_installation_directory')
autoserv_directory = os.path.join(AUTOTEST_INSTALL_DIR, 'server')
autoserv_path = os.path.join(autoserv_directory, 'autoserv')


def autoserv_run_job_command(autoserv_directory,
                             machines,
                             results_directory=None,
                             extra_args=[],
                             job=None,
                             queue_entry=None,
                             verbose=True,
                             write_pidfile=True,
                             fast_mode=False,
                             ssh_verbosity=0,
                             no_console_prefix=False,
                             ssh_options=None,
                             use_packaging=True,
                             in_lab=False,
                             host_attributes=None,
                             use_virtualenv=False,
                             host_info_subdir='',
                             companion_hosts=None,
                             dut_servers=None,
                             libs_server=None,
                             is_cft=False):
    """
    Construct an autoserv command from a job or host queue entry.

    @param autoserv_directory: Absolute path to directory containing the
                               autoserv executable.
    @param machines: A machine or comma separated list of machines to run
                     job on. Leave as None or empty string for hostless job
                     (String).
    @param results_directory: Absolute path to directory in which to deposit
                             results.
    @param extra_args: Additional arguments to pass to autoserv
                       (List of Strings).
    @param job: Job object. If supplied, -u owner, -l name, and --test-retry,
                and -c or -s (client or server) parameters will be added.
    @param queue_entry: HostQueueEntry object. If supplied and no job
                        was supplied, this will be used to lookup the job.
    @param verbose: Boolean (default: True) for autoserv verbosity.
    @param write_pidfile: Boolean (default: True) for whether autoserv should
                          write a pidfile.
    @param fast_mode: bool to use fast mode (disables slow autotest features).
    @param ssh_verbosity: integer between 0 and 3 (inclusive) which sents the
                          verbosity level of ssh. Default: 0.
    @param no_console_prefix: If true, supress timestamps and other prefix info
                              in autoserv console logs.
    @param ssh_options: A string giving extra arguments to be tacked on to
                        ssh commands.
    @param use_packaging Enable install modes that use the packaging system.
    @param in_lab: If true, informs autoserv it is running within a lab
                   environment. This information is useful as autoserv knows
                   the database is available and can make database calls such
                   as looking up host attributes at runtime.
    @param host_attributes: Dict of host attributes to pass into autoserv.
    @param use_virtualenv: Whether to run autoserv inside of virtualenv. In
                           general this should be set to True in our production
                           lab, and probably False in most other use cases
                           (moblab, local testing) until we rollout virtualenv
                           support everywhere. Default: False.
    @param host_info_subdir: When set, a sub-directory of the results directory
                             where host info file(s) are stored.
    @param companion_hosts: a str or list of hosts to be used as companions
                            for the and provided to test. NOTE: these are
                            different than  machines, where each host is a host
                            that the test would be run on.
    @param dut_servers: a str or list of hosts to be used as DUT server
                        provided to test.
    @param libs_server: str for the host to be used for the libs server,
                        provided to the test.

    @returns The autoserv command line as a list of executable + parameters.

    """
    script_name = 'virtualenv_autoserv' if use_virtualenv else 'autoserv'

    full_script_path = os.path.join(autoserv_directory, script_name)

    # virtualenv_autoserv is a `POSIX shell script, ASCII text executable`.
    # Calling with `sys.executable` would fail because python doesn't
    # interpret shebangs itself.
    if use_virtualenv:
        command = [full_script_path]
    else:
        command = [sys.executable, full_script_path]

    if write_pidfile:
        command.append('-p')

    if results_directory:
        command += ['-r', results_directory]
    if host_info_subdir:
        command += ['--local-only-host-info', 'True']
        command += ['--host-info-subdir', host_info_subdir]

    if machines:
        command += ['-m', machines]

    if companion_hosts:
        if not isinstance(companion_hosts, list):
            companion_hosts = [companion_hosts]
        command += ['-ch', ",".join(companion_hosts)]

    if dut_servers:
        if not isinstance(dut_servers, list):
            dut_servers = [dut_servers]
        command += ['--dut_servers', ",".join(dut_servers)]

    if libs_server:
        command += ['--libs_server', libs_server]

    if ssh_verbosity:
        command += ['--ssh_verbosity', str(ssh_verbosity)]

    if ssh_options:
        command += ['--ssh_options', ssh_options]

    if no_console_prefix:
        command += ['--no_console_prefix']

    if job or queue_entry:
        if not job:
            job = queue_entry.job

        owner = getattr(job, 'owner', None)
        name = getattr(job, 'name', None)
        control_type = getattr(job, 'control_type', None)


        if owner:
            command += ['-u', owner]
        if name:
            command += ['-l', name]
        if control_type is not None: # still want to enter if control_type==0
            control_type_value = control_data.CONTROL_TYPE.get_value(
                    control_type)
            if control_type_value == control_data.CONTROL_TYPE.CLIENT:
                command.append('-c')
            elif control_type_value == control_data.CONTROL_TYPE.SERVER:
                command.append('-s')

    if host_attributes:
        command += ['--host_attributes', repr(host_attributes)]

    if verbose:
        command.append('--verbose')

    if fast_mode:
        command.append('--disable_sysinfo')
        command.append('--no_collect_crashinfo')

    if not use_packaging:
        command.append('--no_use_packaging')

    if in_lab:
        command.extend(['--lab', 'True'])

    if is_cft:
        command.append('--CFT')

    py_version = os.getenv('PY_VERSION')
    if py_version:
        command.extend(['--py_version', py_version])

    return command + extra_args
