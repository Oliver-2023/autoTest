# Lint as: python2, python3
#!/usr/bin/env python3
# Copyright 2022 The ChromiumOS Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
"""
This file generates all chromium_Telemetry control files from a main list.
"""

from datetime import datetime
import logging
import os
import re

PERF_PER_BUILD_TESTS = (
        'loading.desktop',
        'rendering.desktop',
        'speedometer2',
)

DEFAULT_YEAR = str(datetime.now().year)

DEFAULT_AUTHOR = 'Chrome Browser Infra Team'

CONTROLFILE_TEMPLATE = (
        """# Copyright {year} The ChromiumOS Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

# Do not edit this file! It was created by generate_controlfiles.py.

AUTHOR = '{author}'
NAME = 'chromium_Telemetry.{test}'
TIME = 'LONG'
TEST_CATEGORY = 'Benchmark'
TEST_CLASS = 'performance'
TEST_TYPE = 'server'
PY_VERSION = 3

DOC = '''
This server side test suite executes the Telemetry Benchmark:
{test}
This benchmark will run on lacros built by browser infra.

This control file is still in experimental stage.
'''

def run_benchmark(machine):
    host = hosts.create_host(machine)
    job.run_test('chromium_Telemetry',
                host=host,
                args=args,
                tag='{test}',
                benchmark='{test}')

parallel_simple(run_benchmark, machines)
""")


def get_existing_fields(filename):
    """Returns the existing copyright year and author of the control file."""
    if not os.path.isfile(filename):
        return (DEFAULT_YEAR, DEFAULT_AUTHOR)

    copyright_year = DEFAULT_YEAR
    author = DEFAULT_AUTHOR
    copyright_pattern = re.compile(
            '# Copyright (\d+) The ChromiumOS Authors')
    author_pattern = re.compile("AUTHOR = '(.+)'")
    with open(filename) as f:
        for line in f:
            match_year = copyright_pattern.match(line)
            if match_year:
                copyright_year = match_year.group(1)
            match_author = author_pattern.match(line)
            if match_author:
                author = match_author.group(1)
    return (copyright_year, author)


def generate_control(test):
    """Generates control file from the template."""
    filename = 'control.%s' % test
    copyright_year, author = get_existing_fields(filename)

    with open(filename, 'w+') as f:
        content = CONTROLFILE_TEMPLATE.format(author=author,
                                              test=test,
                                              year=copyright_year)
        f.write(content)


def check_unmanaged_control_files():
    """Prints warning if there is unmanaged control file."""
    for filename in os.listdir('.'):
        if not filename.startswith('control.'):
            continue
        test = filename[len('control.'):]
        if test not in PERF_PER_BUILD_TESTS:
            logging.warning('warning, unmanaged control file:', test)


def main():
    """The main function."""
    for test in PERF_PER_BUILD_TESTS:
        generate_control(test)
    check_unmanaged_control_files()


if __name__ == "__main__":
    main()
