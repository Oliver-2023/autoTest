# Copyright (c) 2011 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import logging
import os
import pwd
import stat

from autotest_lib.client.bin import utils
from autotest_lib.client.common_lib import error
from autotest_lib.client.cros import constants, cros_ui_test, cryptohome, login


class security_ProfilePermissions(cros_ui_test.UITest):
    version = 2
    _HOMEDIR_MODE = 0700

    def check_owner_mode(self, path, expected_owner, expected_mode):
        """
        Checks if the file/directory at 'path' is owned by 'expected_owner'
        with permissions matching 'expected_mode'.
        Returns True if they match, else False.
        Logs any mismatches to logging.error.
        """
        s = os.stat(path)
        actual_owner = pwd.getpwuid(s.st_uid).pw_name
        actual_mode = stat.S_IMODE(s.st_mode)
        if (expected_owner != actual_owner or
            expected_mode != actual_mode):
            logging.error("%s - Expected %s:%s, saw %s:%s" %
                          (path, expected_owner, oct(expected_mode),
                           actual_owner, oct(actual_mode)))
            return False
        else:
            return True


    def run_once(self):
        """Check permissions within cryptohome for anything too permissive."""
        passes = []
        login.wait_for_initial_chrome_window()

        homepath = constants.CRYPTOHOME_MOUNT_PT
        homemode = stat.S_IMODE(os.stat(homepath)[stat.ST_MODE])

        # TODO(jimhebert) homedir mode check excluded from BWSI right now.
        # Once crosbug.com/16425 is fixed, remove the is_mounted() check.
        if cryptohome.is_mounted() and homemode != self._HOMEDIR_MODE:
            passes.append(False)
            logging.error('%s permissions were %s' % (homepath, oct(homemode)))

        # An array of shell commands, each representing a test that
        # passes if it emits no output. The first test is the main one.
        # In general, writable by anyone else is bad, as is owned by
        # anyone else. Any exceptions to that are pruned out of the
        # first test and checked individually by subsequent tests.
        cmds = [
            ('find -L "%s" -path "%s/flimflam" -prune -o '
             ' -path "%s/.tpm" -prune -o '
             ' \\( -perm /022 -o \\! -user chronos \\) -ls') %
            (homepath, homepath, homepath),
            'find -L "%s/flimflam" \\( -perm /077 -o \\! -user root \\) -ls' %
            homepath,
            # TODO(jimhebert) Uncomment after crosbug.com/16425 is fixed.
            #('find -L "%s/.tpm" \\( -perm /007 -o \\! -user chronos '
            # ' -o \\! -group pkcs11 \\) -ls') % homepath,
        ]

        for cmd in cmds:
            cmd_output = utils.system_output(cmd, ignore_status=True)
            if cmd_output:
                passes.append(False)
                logging.error(cmd_output)

        # This next section only applies if we have a real vault mounted
        # (ie, not a BWSI tmpfs).
        if cryptohome.is_mounted():
            # Also check the permissions of the underlying vault and
            # supporting directory structure.
            vaultpath = cryptohome.current_mounted_vault()

            passes.append(self.check_owner_mode(vaultpath, "chronos",
                                                self._HOMEDIR_MODE))
            passes.append(self.check_owner_mode(vaultpath + "/../master.0",
                                                "root", 0600))
            passes.append(self.check_owner_mode(vaultpath + "/../",
                                                "root", 0700))
            passes.append(self.check_owner_mode(vaultpath + "/../../",
                                                "root", 0700))

        if False in passes:
            raise error.TestFail('Bad permissions found on cryptohome files')
