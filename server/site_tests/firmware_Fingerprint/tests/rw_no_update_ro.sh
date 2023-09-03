#!/bin/bash

# Copyright 2019 The ChromiumOS Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

set -e

# shellcheck source=./common.sh
. "$(dirname "$(readlink -f "${0}")")/common.sh"

echo "Running test to verify that RW cannot update RO"

readonly fw_file="${1}"

check_file_exists "${fw_file}"

echo "Making sure all write protect is enabled"
check_hw_and_sw_write_protect_enabled

echo "Validating initial state"
check_has_mp_rw_firmware
check_has_mp_ro_firmware
check_running_rw_firmware
check_is_rollback_set_to_initial_val

echo "Flashing RO firmware (expected to fail)"
# TODO: b/138782393 - Replace subprocessing with libec ASAP!
flash_ro_cmd="/opt/sbin/crosec-legacy-drv --noverify-all -V -p ec:type=fp -i EC_RO -w ${fw_file}"
if ${flash_ro_cmd}; then
  echo "Expected flashing of read-only firmware to fail"
  exit 1
fi
