# Copyright 2020 The ChromiumOS Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.


"""The autotest performing FW update, both EC and AP in CCD mode."""
import logging

from autotest_lib.client.common_lib import error
from autotest_lib.server.cros.faft.cr50_test import Cr50Test
from autotest_lib.server.cros.servo import servo

MAX_EC_CLEANUP_TRIES=2
MAX_EC_RESPONSE_TRIES=3


class firmware_Cr50CCDFirmwareUpdate(Cr50Test):
    """A test that can provision a machine to the correct firmware version."""

    version = 1
    should_restore_fw = False

    def initialize(self, host, cmdline_args, full_args, fw_path=None):
        """Initialize the test and check if cr50 exists.

        Raises:
            TestNAError: If the dut is not proper for this test for its RDD
                         recognition problem.
        """
        servo_type = host.servo.get_servo_version()
        if 'ccd' not in servo_type:
            raise error.TestNAError('unsupported servo type: %s' % servo_type)
        super(firmware_Cr50CCDFirmwareUpdate,
              self).initialize(host, cmdline_args, full_args)

        # Don't bother if there is no Chrome EC.
        if not self.check_ec_capability():
            raise error.TestNAError('Nothing needs to be tested on this device')

        self.fw_path = fw_path
        self.b_ver = ''

        if eval(full_args.get('backup_fw', 'False')):
            self.backup_firmware()

    def cleanup(self):
        try:
            if not self.should_restore_fw:
                return

            self.servo.enable_main_servo_device()
            self.gsc.reboot()

            # Verify the EC is responsive before raising an error and going to
            # cleanup. Repair and cleanup don't recover corrupted EC firmware
            # very well.
            try:
                self.verify_ec_response()
            except Exception as e:
                logging.error('Caught exception: %s', str(e))

            if self.is_firmware_saved():
                logging.info('Restoring firmware')
                self.restore_firmware()
            else:
                logging.info('chromeos-firmwareupdate --mode=recovery')
                result = self._client.run('chromeos-firmwareupdate'
                                          ' --mode=recovery',
                                          ignore_status=True,
                                          timeout=600)
                if result.exit_status != 0:
                    logging.error('chromeos-firmwareupdate failed: %s',
                                  result.stdout.strip())
                self._client.reboot()
        except Exception as e:
            logging.error('Caught exception: %s', str(e))
        finally:
            super(firmware_Cr50CCDFirmwareUpdate, self).cleanup()

    def verify_ec_response(self):
        """ Verify the EC is responsive."""
        # Try to reflash EC a couple of times to see if it's possible to recover
        # the device now.
        for _ in range(MAX_EC_CLEANUP_TRIES):
            # Try a few times to get response before resorting to reflash.
            for _ in range(MAX_EC_RESPONSE_TRIES):
                try:
                    if self.servo.get_ec_board():
                        return
                except servo.ConsoleError as e:
                    logging.error('EC console is unresponsive: %s', str(e))

            try:
                self.cros_host.firmware_install(build=self.b_ver,
                                                local_tarball=self.fw_path,
                                                install_bios=False)
            except Exception as e:
                logging.error('firmware_install failed: %s', str(e))

        logging.error('DUT likely needs a manual recovery.')

    def run_once(self, host, rw_only=False):
        """The method called by the control file to start the test.

        Args:
          host: a CrosHost object of the machine to update.
          rw_only: True to only update the RW firmware.

        Raises:
          TestFail: if the firmware version remains unchanged.
          TestError: if the latest firmware release cannot be located.
          TestNAError: if the test environment is not properly set.
                       e.g. the servo type doesn't support this test.
        """
        self.cros_host = host
        # Get the parent (a.k.a. reference board or baseboard), and hand it
        # to get_latest_release_version so that it
        # can use it in search as secondary candidate. For example, bob doesn't
        # have its own release directory, but its parent, gru does.
        parent = getattr(self.faft_config, 'parent', None)

        # Allow faft_config.fw_update_build to override
        # get_latest_release_version().
        config_fw_build = getattr(self.faft_config, 'fw_update_build', None)

        if not self.fw_path:
            if config_fw_build:
                logging.info('Using faft_config.fw_update_build %s',
                        config_fw_build)
                self.b_ver = config_fw_build
            else:
                self.b_ver = host.get_latest_release_version(
                        self.faft_config.platform, parent)
            if not self.b_ver:
                raise error.TestError(
                        'Cannot locate the latest release for %s' %
                        self.faft_config.platform)

        # Fast open cr50 and check if testlab is enabled.
        self.fast_ccd_open(enable_testlab=True)
        if not self.servo.enable_ccd_servo_device():
            raise error.TestNAError('Cannot make ccd active')
        # If it is ITE EC, then allow CCD I2C access for flashing EC.
        if self.servo.get('ec_chip').startswith('it8'):
            self.gsc.set_cap('I2C', 'Always')

        # Make sure to use the GSC ec_reset command for cold reset snce that's
        # what normal ccd devices will use.
        if self.servo.has_control('cold_reset_select'):
            self.servo.set('cold_reset_select', 'gsc_ec_reset')
        # TODO(b/196824029): remove when servod supports using the power state
        # controller with the ccd device.
        try:
            self.host.servo.get_power_state_controller().reset()
        except Exception as e:
            logging.info(e)
            raise error.TestNAError('Unable to do power state reset with '
                                    'active ccd device')

        # Flashing the dut involves running power_state:reset. If this locks
        # ccd, flashing won't work. Raise an error to fix cold_reset.
        if self.gsc.get_ccd_level() != self.gsc.OPEN:
            raise error.TestError(
                    'Resetting the dut locked ccd. Flashing with '
                    'CCD will not work. Switch cold_reset to '
                    'gsc_ec_reset')

        self.should_restore_fw = True
        try:
            self.cros_host.firmware_install(build=self.b_ver,
                                            rw_only=rw_only,
                                            local_tarball=self.fw_path,
                                            dest=self.resultsdir,
                                            verify_version=True)
        except Exception as e:
            # The test failed to flash the firmware.
            raise error.TestFail('firmware_install failed with CCD: %s' %
                                 str(e))
