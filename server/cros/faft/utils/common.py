# Lint as: python2, python3
# Copyright 2014 The ChromiumOS Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import os, sys
dirname = os.path.dirname(sys.modules[__name__].__file__)
autotest_dir = os.path.abspath(
        os.path.join(dirname, os.pardir, os.pardir, os.pardir, os.pardir))
client_dir = os.path.join(autotest_dir, 'client')
sys.path.insert(0, client_dir)
import setup_modules
sys.path.pop(0)
setup_modules.setup(base_path=autotest_dir, root_module_name='autotest_lib')
