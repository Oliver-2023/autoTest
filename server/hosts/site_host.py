# Copyright (c) 2012 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import logging
import re
import subprocess
import time
import xmlrpclib

from autotest_lib.client.bin import utils
from autotest_lib.client.common_lib import global_config, error
from autotest_lib.client.common_lib.cros import autoupdater
from autotest_lib.server import autoserv_parser
from autotest_lib.server import site_host_attributes
from autotest_lib.server.cros import servo
from autotest_lib.server.hosts import remote


RPM_FRONTEND_URI = global_config.global_config.get_config_value('CROS',
        'rpm_frontend_uri', type=str, default='')


class RemotePowerException(Exception):
    """This is raised when we fail to set the state of the device's outlet."""
    pass


def make_ssh_command(user='root', port=22, opts='', hosts_file=None,
                     connect_timeout=None, alive_interval=None):
    """Override default make_ssh_command to use options tuned for Chrome OS.

    Tuning changes:
      - ConnectTimeout=30; maximum of 30 seconds allowed for an SSH connection
      failure.  Consistency with remote_access.sh.

      - ServerAliveInterval=180; which causes SSH to ping connection every
      180 seconds. In conjunction with ServerAliveCountMax ensures that if the
      connection dies, Autotest will bail out quickly. Originally tried 60 secs,
      but saw frequent job ABORTS where the test completed successfully.

      - ServerAliveCountMax=3; consistency with remote_access.sh.

      - ConnectAttempts=4; reduce flakiness in connection errors; consistency
      with remote_access.sh.

      - UserKnownHostsFile=/dev/null; we don't care about the keys. Host keys
      change with every new installation, don't waste memory/space saving them.

      - SSH protocol forced to 2; needed for ServerAliveInterval.
    """
    base_command = ('/usr/bin/ssh -a -x %s -o StrictHostKeyChecking=no'
                    ' -o UserKnownHostsFile=/dev/null -o BatchMode=yes'
                    ' -o ConnectTimeout=30 -o ServerAliveInterval=180'
                    ' -o ServerAliveCountMax=3 -o ConnectionAttempts=4'
                    ' -o Protocol=2 -l %s -p %d')
    return base_command % (opts, user, port)


class SiteHost(remote.RemoteHost):
    """Chromium OS specific subclass of Host."""

    _parser = autoserv_parser.autoserv_parser

    # Time to wait for new kernel to be marked successful.
    _KERNEL_UPDATE_TIMEOUT = 120

    # Ephemeral file to indicate that an update has just occurred.
    _JUST_UPDATED_FLAG = '/tmp/just_updated'

    # Timeout values associated with various Chrome OS state
    # changes.  In general, the timeouts are the maximum time to
    # allow between some event X, and the time that the unit is
    # on (or off) the network.  Note that "time to get on the
    # network" is typically longer than the time to complete the
    # operation.
    #
    # TODO(jrbarnette):  None of these times have been thoroughly
    # tested empirically; if timeouts are a problem, increasing the
    # time limit really might be the right answer.
    #
    # SLEEP_TIMEOUT:  Time to allow for suspend to memory.
    # RESUME_TIMEOUT: Time to allow for resume after suspend.
    # BOOT_TIMEOUT: Time to allow for boot from power off.  Among
    #   other things, this includes time for the 30 second dev-mode
    #   screen delay,
    # USB_BOOT_TIMEOUT: Time to allow for boot from a USB device,
    #   including the 30 second dev-mode delay.
    # SHUTDOWN_TIMEOUT: Time to allow to shut down.
    # REBOOT_TIMEOUT: Combination of shutdown and reboot times.

    SLEEP_TIMEOUT = 2
    RESUME_TIMEOUT = 5
    BOOT_TIMEOUT = 45
    USB_BOOT_TIMEOUT = 150
    SHUTDOWN_TIMEOUT = 5
    REBOOT_TIMEOUT = SHUTDOWN_TIMEOUT + BOOT_TIMEOUT

    LAB_MACHINE_FILE = '/mnt/stateful_partition/.labmachine'
    RPM_HOSTNAME_REGEX = ('chromeos[0-9]+(-row[0-9]+)?-rack[0-9]+[a-z]*-'
                          'host[0-9]+')



    def _initialize(self, hostname, servo_host=None, servo_port=None,
                    *args, **dargs):
        """Initialize superclasses, and |self.servo|.

        For creating the host servo object, there are three
        possibilities:  First, if the host is a lab system known to
        have a servo board, we connect to that servo unconditionally.
        Second, if we're called from a control file that requires
        servo features for testing, it will pass settings for
        `servo_host`, `servo_port`, or both.  If neither of these
        cases apply, `self.servo` will be `None`.

        """
        super(SiteHost, self)._initialize(hostname=hostname,
                                          *args, **dargs)
        # self.env is a dictionary of environment variable settings
        # to be exported for commands run on the host.
        # LIBC_FATAL_STDERR_ can be useful for diagnosing certain
        # errors that might happen.
        self.env['LIBC_FATAL_STDERR_'] = '1'
        self._xmlrpc_proxy_map = {}
        self.servo = servo.Servo.get_lab_servo(hostname)
        if not self.servo:
            # The Servo constructor generally doesn't accept 'None'
            # for its parameters.
            if servo_host is not None:
                if servo_port is not None:
                    self.servo = servo.Servo(servo_host=servo_host,
                                             servo_port=servo_port)
                else:
                    self.servo = servo.Servo(servo_host=servo_host)
            elif servo_port is not None:
                self.servo = servo.Servo(servo_port=servo_port)


    def machine_install(self, update_url=None, force_update=False,
                        local_devserver=False):
        if not update_url and self._parser.options.image:
            update_url = self._parser.options.image
        elif not update_url:
            raise autoupdater.ChromiumOSError(
                'Update failed. No update URL provided.')

        # Attempt to update the system.
        updater = autoupdater.ChromiumOSUpdater(update_url, host=self,
                                                local_devserver=local_devserver)
        if updater.run_update(force_update):
            # Figure out active and inactive kernel.
            active_kernel, inactive_kernel = updater.get_kernel_state()

            # Ensure inactive kernel has higher priority than active.
            if (updater.get_kernel_priority(inactive_kernel)
                    < updater.get_kernel_priority(active_kernel)):
                raise autoupdater.ChromiumOSError(
                    'Update failed. The priority of the inactive kernel'
                    ' partition is less than that of the active kernel'
                    ' partition.')

            # Updater has returned, successfully, reboot the host.
            self.reboot(timeout=60, wait=True)

            # Following the reboot, verify the correct version.
            updater.check_version()

            # Figure out newly active kernel.
            new_active_kernel, _ = updater.get_kernel_state()

            # Ensure that previously inactive kernel is now the active kernel.
            if new_active_kernel != inactive_kernel:
                raise autoupdater.ChromiumOSError(
                    'Update failed. New kernel partition is not active after'
                    ' boot.')

            host_attributes = site_host_attributes.HostAttributes(self.hostname)
            if host_attributes.has_chromeos_firmware:
                # Wait until tries == 0 and success, or until timeout.
                utils.poll_for_condition(
                    lambda: (updater.get_kernel_tries(new_active_kernel) == 0
                             and updater.get_kernel_success(new_active_kernel)),
                    exception=autoupdater.ChromiumOSError(
                        'Update failed. Timed out waiting for system to mark'
                        ' new kernel as successful.'),
                    timeout=self._KERNEL_UPDATE_TIMEOUT, sleep_interval=5)

            # TODO(dalecurtis): Hack for R12 builds to make sure BVT runs of
            # platform_Shutdown pass correctly.
            if updater.update_version.startswith('0.12'):
                self.reboot(timeout=60, wait=True)

            # Mark host as recently updated. Hosts are rebooted at the end of
            # every test cycle which will remove the file.
            self.run('touch %s' % self._JUST_UPDATED_FLAG)

        # Clean up any old autotest directories which may be lying around.
        for path in global_config.global_config.get_config_value(
                'AUTOSERV', 'client_autodir_paths', type=list):
            self.run('rm -rf ' + path)


    def has_just_updated(self):
        """Indicates whether the host was updated within this boot."""
        # Check for the existence of the just updated flag file.
        return self.run(
            '[ -f %s ] && echo T || echo F'
            % self._JUST_UPDATED_FLAG).stdout.strip() == 'T'


    def close(self):
        super(SiteHost, self).close()
        self.xmlrpc_disconnect_all()


    def cleanup(self):
        """Special cleanup method to make sure hosts always get power back."""
        super(SiteHost, self).cleanup()
        if self.has_power():
            self.power_on()


    def reboot(self, **dargs):
        """
        This function reboots the site host. The more generic
        RemoteHost.reboot() performs sync and sleeps for 5
        seconds. This is not necessary for Chrome OS devices as the
        sync should be finished in a short time during the reboot
        command.
        """
        if 'reboot_cmd' not in dargs:
            dargs['reboot_cmd'] = ('((reboot & sleep 10; reboot -f &)'
                                   ' </dev/null >/dev/null 2>&1 &)')
        # Enable fastsync to avoid running extra sync commands before reboot.
        if 'fastsync' not in dargs:
            dargs['fastsync'] = True
        super(SiteHost, self).reboot(**dargs)


    def verify_software(self):
        """Ensure the stateful partition has space for Autotest and updates.

        Similar to what is done by AbstractSSH, except instead of checking the
        Autotest installation path, just check the stateful partition.

        Checking the stateful partition is preferable in case it has been wiped,
        resulting in an Autotest installation path which doesn't exist and isn't
        writable. We still want to pass verify in this state since the partition
        will be recovered with the next install.
        """
        super(SiteHost, self).verify_software()
        self.check_diskspace(
            '/mnt/stateful_partition',
            global_config.global_config.get_config_value(
                'SERVER', 'gb_diskspace_required', type=int,
                default=20))


    def xmlrpc_connect(self, command, port, cleanup=None):
        """Connect to an XMLRPC server on the host.

        The `command` argument should be a simple shell command that
        starts an XMLRPC server on the given `port`.  The command
        must not daemonize, and must terminate cleanly on SIGTERM.
        The command is started in the background on the host, and a
        local XMLRPC client for the server is created and returned
        to the caller.

        Note that the process of creating an XMLRPC client makes no
        attempt to connect to the remote server; the caller is
        responsible for determining whether the server is running
        correctly, and is ready to serve requests.

        @param command Shell command to start the server.
        @param port Port number on which the server is expected to
                    be serving.
        """
        self.xmlrpc_disconnect(port)

        # Chrome OS on the target closes down most external ports
        # for security.  We could open the port, but doing that
        # would conflict with security tests that check that only
        # expected ports are open.  So, to get to the port on the
        # target we use an ssh tunnel.
        local_port = utils.get_unused_port()
        tunnel_options = '-n -N -q -L %d:localhost:%d' % (local_port, port)
        ssh_cmd = make_ssh_command(opts=tunnel_options)
        tunnel_cmd = '%s %s' % (ssh_cmd, self.hostname)
        logging.debug('Full tunnel command: %s', tunnel_cmd)
        tunnel_proc = subprocess.Popen(tunnel_cmd, shell=True, close_fds=True)
        logging.debug('Started XMLRPC tunnel, local = %d'
                      ' remote = %d, pid = %d',
                      local_port, port, tunnel_proc.pid)

        # Start the server on the host.  Redirection in the command
        # below is necessary, because 'ssh' won't terminate until
        # background child processes close stdin, stdout, and
        # stderr.
        remote_cmd = '( %s ) </dev/null >/dev/null 2>&1 & echo $!' % command
        remote_pid = self.run(remote_cmd).stdout.rstrip('\n')
        logging.debug('Started XMLRPC server on host %s, pid = %s',
                      self.hostname, remote_pid)

        self._xmlrpc_proxy_map[port] = (cleanup, tunnel_proc)
        rpc_url = 'http://localhost:%d' % local_port
        return xmlrpclib.ServerProxy(rpc_url, allow_none=True)


    def xmlrpc_disconnect(self, port):
        """Disconnect from an XMLRPC server on the host.

        Terminates the remote XMLRPC server previously started for
        the given `port`.  Also closes the local ssh tunnel created
        for the connection to the host.  This function does not
        directly alter the state of a previously returned XMLRPC
        client object; however disconnection will cause all
        subsequent calls to methods on the object to fail.

        This function does nothing if requested to disconnect a port
        that was not previously connected via `self.xmlrpc_connect()`

        @param port Port number passed to a previous call to
                    `xmlrpc_connect()`
        """
        if port not in self._xmlrpc_proxy_map:
            return
        entry = self._xmlrpc_proxy_map[port]
        remote_name = entry[0]
        tunnel_proc = entry[1]
        if remote_name:
            # We use 'pkill' to find our target process rather than
            # a PID, because the host may have rebooted since
            # connecting, and we don't want to kill an innocent
            # process with the same PID.
            #
            # 'pkill' helpfully exits with status 1 if no target
            # process  is found, for which run() will throw an
            # exception.  We don't want that, so we the ignore
            # status.
            self.run("pkill -f '%s'" % remote_name, ignore_status=True)

        if tunnel_proc.poll() is None:
            tunnel_proc.terminate()
            logging.debug('Terminated tunnel, pid %d', tunnel_proc.pid)
        else:
            logging.debug('Tunnel pid %d terminated early, status %d',
                          tunnel_proc.pid, tunnel_proc.returncode)
        del self._xmlrpc_proxy_map[port]


    def xmlrpc_disconnect_all(self):
        """Disconnect all known XMLRPC proxy ports."""
        for port in self._xmlrpc_proxy_map.keys():
            self.xmlrpc_disconnect(port)


    def _ping_is_up(self):
        """Ping the host once, and return whether it responded."""
        return utils.ping(self.hostname, tries=1, deadline=1) == 0


    def _ping_wait_down(self, timeout):
        """Wait until the host no longer responds to `ping`.

        @param timeout Minimum time to allow before declaring the
                       host to be non-responsive.
        """

        # This function is a slightly faster version of wait_down().
        #
        # In AbstractSSHHost.wait_down(), `ssh` is used to determine
        # whether the host is down.  In some situations (mine, at
        # least), `ssh` can take over a minute to determine that the
        # host is down.  The `ping` command answers the question
        # faster, so we use that here instead.
        #
        # There is no equivalent for wait_up(), because a target that
        # answers to `ping` won't necessarily respond to `ssh`.
        end_time = time.time() + timeout
        while time.time() <= end_time:
            if not self._ping_is_up():
                return True

        # If the timeout is short relative to the run time of
        # _ping_is_up(), we might be prone to false failures for
        # lack of checking frequently enough.  To be safe, we make
        # one last check _after_ the deadline.
        return not self._ping_is_up()


    def test_wait_for_sleep(self):
        """Wait for the client to enter low-power sleep mode.

        The test for "is asleep" can't distinguish a system that is
        powered off; to confirm that the unit was asleep, it is
        necessary to force resume, and then call
        `test_wait_for_resume()`.

        This function is expected to be called from a test as part
        of a sequence like the following:

        ~~~~~~~~
            boot_id = host.get_boot_id()
            # trigger sleep on the host
            host.test_wait_for_sleep()
            # trigger resume on the host
            host.test_wait_for_resume(boot_id)
        ~~~~~~~~

        @exception TestFail The host did not go to sleep within
                            the allowed time.
        """
        if not self._ping_wait_down(timeout=self.SLEEP_TIMEOUT):
            raise error.TestFail(
                'client failed to sleep after %d seconds' %
                    self.SLEEP_TIMEOUT)


    def test_wait_for_resume(self, old_boot_id):
        """Wait for the client to resume from low-power sleep mode.

        The `old_boot_id` parameter should be the value from
        `get_boot_id()` obtained prior to entering sleep mode.  A
        `TestFail` exception is raised if the boot id changes.

        See @ref test_wait_for_sleep for more on this function's
        usage.

        @param[in] old_boot_id A boot id value obtained before the
                               target host went to sleep.

        @exception TestFail The host did not respond within the
                            allowed time.
        @exception TestFail The host responded, but the boot id test
                            indicated a reboot rather than a sleep
                            cycle.
        """
        if not self.wait_up(timeout=self.RESUME_TIMEOUT):
            raise error.TestFail(
                'client failed to resume from sleep after %d seconds' %
                    self.RESUME_TIMEOUT)
        else:
            new_boot_id = self.get_boot_id()
            if new_boot_id != old_boot_id:
                raise error.TestFail(
                    'client rebooted, but sleep was expected'
                    ' (old boot %s, new boot %s)'
                        % (old_boot_id, new_boot_id))


    def test_wait_for_shutdown(self):
        """Wait for the client to shut down.

        The test for "has shut down" can't distinguish a system that
        is merely asleep; to confirm that the unit was down, it is
        necessary to force boot, and then call test_wait_for_boot().

        This function is expected to be called from a test as part
        of a sequence like the following:

        ~~~~~~~~
            boot_id = host.get_boot_id()
            # trigger shutdown on the host
            host.test_wait_for_shutdown()
            # trigger boot on the host
            host.test_wait_for_boot(boot_id)
        ~~~~~~~~

        @exception TestFail The host did not shut down within the
                            allowed time.
        """
        if not self._ping_wait_down(timeout=self.SHUTDOWN_TIMEOUT):
            raise error.TestFail(
                'client failed to shut down after %d seconds' %
                    self.SHUTDOWN_TIMEOUT)


    def test_wait_for_boot(self, old_boot_id=None):
        """Wait for the client to boot from cold power.

        The `old_boot_id` parameter should be the value from
        `get_boot_id()` obtained prior to shutting down.  A
        `TestFail` exception is raised if the boot id does not
        change.  The boot id test is omitted if `old_boot_id` is not
        specified.

        See @ref test_wait_for_shutdown for more on this function's
        usage.

        @param[in] old_boot_id A boot id value obtained before the
                               shut down.

        @exception TestFail The host did not respond within the
                            allowed time.
        @exception TestFail The host responded, but the boot id test
                            indicated that there was no reboot.
        """
        if not self.wait_up(timeout=self.REBOOT_TIMEOUT):
            raise error.TestFail(
                'client failed to reboot after %d seconds' %
                    self.REBOOT_TIMEOUT)
        elif old_boot_id:
            if self.get_boot_id() == old_boot_id:
                raise error.TestFail(
                    'client is back up, but did not reboot'
                    ' (boot %s)' % old_boot_id)


    @staticmethod
    def check_for_rpm_support(hostname):
        """For a given hostname, return whether or not it is powered by an RPM.

        @return None if this host does not follows the defined naming format
                for RPM powered DUT's in the lab. If it does follow the format,
                it returns a regular expression MatchObject instead.
        """
        return re.match(SiteHost.RPM_HOSTNAME_REGEX, hostname)


    def has_power(self):
        """For this host, return whether or not it is powered by an RPM.

        @return True if this host is in the CROS lab and follows the defined
                naming format.
        """
        return SiteHost.check_for_rpm_support(self.hostname)


    def _set_power(self, new_state):
        client = xmlrpclib.ServerProxy(RPM_FRONTEND_URI, verbose=False)
        if not client.queue_request(self.hostname, new_state):
            raise RemotePowerException('Failed to change outlet status for'
                                       'host: %s to state: %s', self.hostname,
                                       new_state)


    def power_off(self):
        self._set_power('OFF')


    def power_on(self):
        self._set_power('ON')


    def power_cycle(self):
        self._set_power('CYCLE')
