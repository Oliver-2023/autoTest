#!/bin/bash

# Copyright 2019 The ChromiumOS Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

FW_FILE="$1"

if [[ ! -f "${FW_FILE}" ]]; then
  echo "You must specify a firmware file to flash"
  exit 1
fi

# TODO: b/138782393 - Replace subprocessing with libec ASAP!
/opt/sbin/crosec-legacy-drv --noverify-all -V -p ec:type=fp -i EC_RW -w "${FW_FILE}"
