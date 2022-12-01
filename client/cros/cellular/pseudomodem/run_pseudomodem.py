# Lint as: python2, python3
# Copyright 2014 The ChromiumOS Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import logging
import sys
import time

from autotest_lib.client.cros.cellular.pseudomodem import client
from autotest_lib.client.cros.cellular.pseudomodem import pseudomodem
from autotest_lib.client.cros.cellular.pseudomodem import pseudomodem_context

def main():
    """ Entry function to run pseudomodem standalone. """
    pmc = None
    flags = sys.argv[1:]
    cli_flag = (pseudomodem.CLI_FLAG in flags)

    # When run from the command line, override autotest logging defaults.
    root = logging.getLogger()
    for handler in root.handlers:
        root.removeHandler(handler)
    logging.basicConfig(
        format='%(asctime)s %(levelname)-5.5s|%(module)10.10s:%(lineno)4.4d| '
               '%(message)s',
        datefmt='%H:%M:%S')

    try:
        pmc = pseudomodem_context.PseudoModemManagerContext(
                True,
                block_output=cli_flag)
        pmc.cmd_line_flags = flags
        pmc.Start()
        if cli_flag:
            cli = client.PseudoModemClient()
            cli.Begin()  # Blocking
        else:
            # Block quietly till user interrupt.
            while True:
                time.sleep(30)
    except KeyboardInterrupt:
        print('Terminating on user request.')
    finally:
        # This is always hit, even when SIGINT is received.
        if pmc:
            pmc.Stop()


if __name__ == '__main__':
    main()
