# Lint as: python2, python3
# Copyright 2014 The ChromiumOS Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from collections import namedtuple


# light weight data structure to represent the result of an image comparison
ComparisonResult = namedtuple('ComparisonResult',
                              'diff_pixel_count comparison_url '
                              'pdiff_image_path')

ComparisonResult.__new__.__defaults__ = (0, '', None)
