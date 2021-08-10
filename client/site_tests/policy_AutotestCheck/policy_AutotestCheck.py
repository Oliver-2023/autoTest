# Copyright 2019 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

# TODO(crbug.com/1237594): remove import of gobject.
from autotest_lib.client.common_lib import error
try:
    import gobject  # pylint: disable=unused-import
except ImportError:
    raise error.TestWarn('Unable to import gobject. crbug.com/1237594')

from autotest_lib.client.cros.enterprise import enterprise_policy_base


class policy_AutotestCheck(enterprise_policy_base.EnterprisePolicyTest):
    """
    Super small autotest to be put on CQ.

    The purpose of this autotest is to verify that all the basics of the
    Enteprise autotest work. Policy is set and applied.

    Test will verify these areas work:
    getAllPolicies API
    test_policyserver & protos
    Chrome login
    """
    version = 1

    POLICY_NAME = 'AllowDinosaurEasterEgg'

    def run_once(self):
        """
        Setup and run the test configured for the specified test case.

        """
        self.setup_case(user_policies={self.POLICY_NAME: True})
