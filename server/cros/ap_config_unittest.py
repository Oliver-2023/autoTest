# Lint as: python2, python3
# Copyright 2019 The ChromiumOS Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import io
import six
import unittest

from . import common

from autotest_lib.client.common_lib import seven
from autotest_lib.server.cros import ap_config


class APTestCase(unittest.TestCase):
    def test_not_rpm_managed(self):
        conf = _parse_config_from_string("""
[test_bss]
rpm_managed = False
rpm_hostname = chromeos3-row2-rack3-rpm1
rpm_outlet = .A15""")
        ap = ap_config.AP('test_bss', conf)
        self.assertIsNone(ap.get_rpm_unit())


    def test_rpm_managed(self):
        conf = _parse_config_from_string("""
[test_bss]
rpm_managed = True
rpm_hostname = chromeos3-row2-rack3-rpm1
rpm_outlet = .A15""")
        ap = ap_config.AP('test_bss', conf)
        rpm_unit = ap.get_rpm_unit()
        self.assertIsNotNone(rpm_unit)
        self.assertEqual('chromeos3-row2-rack3-rpm1', rpm_unit.hostname)
        self.assertEqual('.A15', rpm_unit.outlet)

    def test_get_ap_list_returns_non_empty(self):
        self.assertGreater(len(ap_config.get_ap_list()), 0)


def _parse_config_from_string(conf):
    parser = seven.config_parser()
    if six.PY2:
        parser.readfp(io.BytesIO(conf))
    else:
        parser.read_string(conf)

    return parser


if __name__ == '__main__':
    unittest.main()