# Copyright (c) 2012 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import logging, os
from autotest_lib.server import utils
from autotest_lib.server.cros.faftsequence import FAFTSequence
from autotest_lib.client.common_lib import error


class firmware_UpdateFirmwareDataKeyVersion(FAFTSequence):
    """
    This test requires a USB disk plugged-in, which contains a Chrome OS
    install shim (built by "build_image factory_install"). The firmware id
    should matches fwid of shellball chromeos-firmwareupdate, or user can
    provide a shellball to do this test. In this way, the client will be update
    with the given shellball first. On runtime, this test modifies shellball
    and runs autoupdate. Check firmware datakey version after boot with
    firmware B, and then recover firmware A and B to original shellball.
    """
    version = 1

    def resign_datakey_version(self, host):
        host.send_file(os.path.join(
                            '~/trunk/src/platform/vboot_reference/scripts',
                            'keygeneration/common.sh'),
                       os.path.join(self.faft_client.updater.get_temp_path(),
                                     'common.sh'))
        host.send_file(os.path.join('~/trunk/src/third_party/autotest/files/',
                                    'server/site_tests',
                                    'firmware_UpdateFirmwareDataKeyVersion',
                                    'files/make_keys.sh'),
                       os.path.join(self.faft_client.updater.get_temp_path(),
                                    'make_keys.sh'))

        self.faft_client.system.run_shell_command('/bin/bash %s %s' % (
             os.path.join(self.faft_client.updater.get_temp_path(),
                          'make_keys.sh'),
             self._update_version))


    def check_firmware_datakey_version(self, expected_ver):
        actual_ver = self.faft_client.bios.get_datakey_version('a')
        actual_tpm_fwver = self.faft_client.tpm.get_firmware_datakey_version()
        if actual_ver != expected_ver or actual_tpm_fwver != expected_ver:
            raise error.TestFail(
                'Firmware data key version should be %s,'
                'but got (fwver, tpm_fwver) = (%s, %s).'
                % (expected_ver, actual_ver, actual_tpm_fwver))
        else:
            logging.info(
                'Update success, now datakey version is %s', actual_ver)


    def check_version_and_run_recovery(self):
        self.check_firmware_datakey_version(self._update_version)
        self.faft_client.updater.run_recovery()


    def initialize(self, host, cmdline_args, use_pyauto=False, use_faft=True):
        dict_args = utils.args_to_dict(cmdline_args)
        self.use_shellball = dict_args.get('shellball', None)
        super(firmware_UpdateFirmwareDataKeyVersion, self).initialize(
            host, cmdline_args, use_pyauto, use_faft)


    def setup(self, host=None):
        self.backup_firmware()
        updater_path = self.setup_firmwareupdate_shellball(self.use_shellball)
        self.faft_client.updater.setup(updater_path)

        # Update firmware if needed
        if updater_path:
            self.set_hardware_write_protect(enable=False)
            self.faft_client.updater.run_factory_install()
            self.sync_and_warm_reboot()
            self.wait_for_client_offline()
            self.wait_for_client()

        super(firmware_UpdateFirmwareDataKeyVersion, self).setup()
        self.setup_usbkey(usbkey=True, host=True, install_shim=True)
        self.setup_dev_mode(dev_mode=False)
        self._fwid = self.faft_client.updater.get_fwid()

        actual_ver = self.faft_client.bios.get_datakey_version('a')
        logging.info('Origin version is %s', actual_ver)
        self._update_version = actual_ver + 1
        logging.info('Firmware version will update to version %s',
            self._update_version)

        self.resign_datakey_version(host)
        self.faft_client.updater.resign_firmware(1)
        self.faft_client.updater.repack_shellball('test')


    def cleanup(self):
        self.faft_client.updater.cleanup()
        self.restore_firmware()
        self.invalidate_firmware_setup()
        super(firmware_UpdateFirmwareDataKeyVersion, self).cleanup()


    def run_once(self):
        self.register_faft_sequence((
            {   # Step1. Update firmware with new datakey version.
                'state_checker': (self.checkers.crossystem_checker, {
                    'mainfw_act': 'A',
                    'tried_fwb': '0',
                    'mainfw_type': 'normal',
                    'fwid': self._fwid
                }),
                'userspace_action': (
                     self.faft_client.updater.run_autoupdate,
                     'test'
                )
            },
            {   # Step2. Check firmware data key version and Rollback.
                'state_checker': (self.checkers.crossystem_checker, {
                    'mainfw_act': 'B',
                    'tried_fwb': '1'
                }),
                'userspace_action': (self.faft_client.updater.run_bootok,
                                     'test')
            },
            {   # Step3, Check firmware and TPM version, then recovery.
                'state_checker': (self.checkers.crossystem_checker, {
                    'mainfw_act': 'A',
                    'tried_fwb': '0'
                }),
                'userspace_action': (self.check_version_and_run_recovery),
                'reboot_action': (self.reboot_with_factory_install_shim),
            },
            {   # Step4, Check Rollback version.
                'state_checker': (self.checkers.crossystem_checker, {
                    'mainfw_act': 'A',
                    'tried_fwb': '0',
                    'fwid': self._fwid
                }),
                'userspace_action':(self.check_firmware_datakey_version,
                                    self._update_version - 1)
            }
        ))
        self.run_faft_sequence()
