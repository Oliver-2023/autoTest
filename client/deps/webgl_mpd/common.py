# Copyright 2013 The ChromiumOS Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import os
import sys

dirname = os.path.dirname(sys.modules[__name__].__file__)
# Load setup_modules from client_dir (two level up from current dir).
client_dir = os.path.abspath(os.path.join(dirname, "..", ".."))
sys.path.insert(0, client_dir)
import setup_modules
sys.path.pop(0)
setup_modules.setup(base_path=client_dir,
                    root_module_name="autotest_lib.client")
