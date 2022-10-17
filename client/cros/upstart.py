# Copyright (c) 2011 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Provides utility methods for interacting with upstart"""

import logging
import os
import re

from autotest_lib.client.common_lib import utils


def emit_event(event_name):
    """Fails if the emit command fails.

    @param service_name: name of the service.
    """
    utils.system('initctl emit %s' % event_name)


def ensure_running(service_name):
    """Fails if |service_name| is not running.

    @param service_name: name of the service.
    """
    cmd = 'initctl status %s | grep start/running' % service_name
    utils.system(cmd)


def has_service(service_name):
    """Returns true if |service_name| is installed on the system.

    @param service_name: name of the service.
    """
    return os.path.exists('/etc/init/' + service_name + '.conf')


def is_running(service_name):
    """
    Returns true if |service_name| is running.

    @param service_name: name of service
    """
    cmd = 'status %s' % service_name
    utils.poll_for_condition(
        lambda: re.search(re.compile(r'start\/(pre-start|post-start)'),
        utils.system_output(cmd)) == None,
        timeout=10,
        sleep_interval=1)
    return utils.system_output(cmd).find('start/running') != -1


def get_pid(service_name):
    """
    Returns integer of PID of |service_name| or None if not running.

    @param service_name: name of service
    """
    res_str = utils.system_output('status %s' % service_name)
    match = re.search('process ([0-9]+)', res_str)
    if not match:
        return None
    return int(match.group(1))


def restart_job(service_name, timeout=None):
    """
    Restarts an upstart job if it's running.
    If it's not running, start it.

    @param service_name: name of service
    """

    if is_running(service_name):
        logging.debug('%s is already running: restart instead.', service_name)
        utils.system_output('restart %s' % service_name, timeout=timeout)
    else:
        utils.system_output('start %s' % service_name, timeout=timeout)


def stop_job(service_name, timeout=None):
    """
    Stops an upstart job.
    Fails if the stop command fails.

    @param service_name: name of service
    """

    utils.system('stop %s' % service_name, timeout=timeout)
