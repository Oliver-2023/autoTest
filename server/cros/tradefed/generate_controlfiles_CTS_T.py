#!/usr/bin/env python3
# Lint as: python2, python3
# Copyright 2022 The ChromiumOS Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import collections
import os

CONFIG = {}

CONFIG['TEST_NAME'] = 'cheets_CTS_T'
CONFIG['BUNDLE_CONFIG_PATH'] = os.path.abspath(os.path.join(os.path.dirname(__file__),
        '..', '..', 'site_tests', CONFIG['TEST_NAME'], 'bundle_url_config.json'))
CONFIG['DOC_TITLE'] = 'Android Compatibility Test Suite (CTS)'
CONFIG['MOBLAB_SUITE_NAME'] = 'suite:cts'
CONFIG['MOBLAB_HARDWARE_SUITE_NAME'] = 'suite:cts-hardware'
CONFIG['COPYRIGHT_YEAR'] = 2022
CONFIG['AUTHKEY'] = ''

# Both arm, x86 tests results normally is below 200MB.
# 1000MB should be sufficient for CTS tests and dump logs for android-cts.
CONFIG['LARGE_MAX_RESULT_SIZE'] = 1000 * 1024

# Individual module normal produces less results than all modules, which is
# ranging from 4MB to 50MB. 500MB should be sufficient to handle all the cases.
CONFIG['NORMAL_MAX_RESULT_SIZE'] = 500 * 1024

CONFIG['TRADEFED_CTS_COMMAND'] = 'cts'
CONFIG['TRADEFED_RETRY_COMMAND'] = 'retry'
CONFIG['TRADEFED_DISABLE_REBOOT'] = False
CONFIG['TRADEFED_DISABLE_REBOOT_ON_COLLECTION'] = True
CONFIG['TRADEFED_MAY_SKIP_DEVICE_INFO'] = False
CONFIG['TRADEFED_EXECUTABLE_PATH'] = 'android-cts/tools/cts-tradefed'
CONFIG['JAVA_EXECUTABLE_PATH'] = 'android-cts/jdk/bin/java'
CONFIG['TRADEFED_IGNORE_BUSINESS_LOGIC_FAILURE'] = False

# On moblab everything runs in the same suite.
CONFIG['INTERNAL_SUITE_NAMES'] = ['suite:arc-cts']
CONFIG['QUAL_SUITE_NAMES'] = ['suite:arc-cts-qual']
CONFIG['HARDWARE_SUITE_NAME'] = 'suite:arc-cts-hardware'
CONFIG['VM_SUITE_NAME'] = 'suite:arc-cts-vm'
CONFIG['STABLE_VM_SUITE_NAME'] = 'suite:arc-cts-vm-stable'

CONFIG['CONTROLFILE_TEST_FUNCTION_NAME'] = 'run_TS'
CONFIG['CONTROLFILE_WRITE_SIMPLE_QUAL_AND_REGRESS'] = False
CONFIG['CONTROLFILE_WRITE_CAMERA'] = True
CONFIG['CONTROLFILE_WRITE_EXTRA'] = True

# The dashboard suppresses upload to APFE for GS directories (based on autotest
# tag) that contain 'tradefed-run-collect-tests'. b/119640440
# Do not change the name/tag without adjusting the dashboard.
_COLLECT = 'tradefed-run-collect-tests-only-internal'
_PUBLIC_COLLECT = 'tradefed-run-collect-tests-only'

CONFIG['LAB_DEPENDENCY'] = {'x86': ['cts_abi_x86']}

CONFIG['CTS_JOB_RETRIES_IN_PUBLIC'] = 1
CONFIG['CTS_QUAL_RETRIES'] = 9
CONFIG['CTS_MAX_RETRIES'] = {
}

# Timeout in hours.
CONFIG['CTS_TIMEOUT_DEFAULT'] = 1.0
CONFIG['CTS_TIMEOUT'] = {
        'CtsAppSecurityHostTestCases': 2.0,
        'CtsAutoFillServiceTestCases': 2.5,  # TODO(b/134662826)
        'CtsCameraTestCases': 1.5,
        'CtsDeqpTestCases': 30.0,
        'CtsDeqpTestCases.dEQP-EGL': 2.0,
        'CtsDeqpTestCases.dEQP-GLES2': 2.0,
        'CtsDeqpTestCases.dEQP-GLES3': 6.0,
        'CtsDeqpTestCases.dEQP-GLES31': 6.0,
        'CtsDeqpTestCases.dEQP-VK': 15.0,
        'CtsFileSystemTestCases': 3.0,
        'CtsHardwareTestCases': 2.0,
        'CtsIcuTestCases': 2.0,
        'CtsKeystoreTestCases': 2.0,
        'CtsLibcoreOjTestCases': 2.0,
        'CtsMediaStressTestCases': 5.0,
        'CtsMediaPlayerTestCases': 2.0,
        'CtsMediaDecoderTestCases': 2.0,
        'CtsNNAPIBenchmarkTestCases': 2.0,
        'CtsPrintTestCases': 1.5,
        'CtsSecurityTestCases': 20.0,
        'CtsSecurityTestCases[instant]': 20.0,
        'CtsSensorTestCases': 2.0,
        'CtsStatsdHostTestCases': 2.0,
        'CtsVideoTestCases': 1.5,
        'CtsViewTestCases': 2.5,
        'CtsWidgetTestCases': 2.0,
        _COLLECT: 2.5,
        _PUBLIC_COLLECT: 2.5,
}

# Any test that runs as part as blocking BVT needs to be stable and fast. For
# this reason we enforce a tight timeout on these modules/jobs.
# Timeout in hours. (0.1h = 6 minutes)
CONFIG['BVT_TIMEOUT'] = 0.1
# We allow a very long runtime for qualification (2 days).
CONFIG['QUAL_TIMEOUT'] = 48

CONFIG['QUAL_BOOKMARKS'] = sorted([
        'A',  # A bookend to simplify partition algorithm.
        'CtsAccessibilityServiceTestCases',  # TODO(ihf) remove when b/121291711 fixed. This module causes problems. Put it into its own control file.
        'CtsAccessibilityServiceTestCasesz',
        'CtsCameraTestCases',  # Flaky
        'CtsCameraTestCasesz',
        'CtsDeqpTestCases',
        'CtsDeqpTestCasesz',  # Put Deqp in one control file. Long enough, fairly stable.
        'CtsFileSystemTestCases',  # Runs long enough. (3h)
        'CtsFileSystemTestCasesz',
        'CtsMediaStressTestCases',  # Put heavy  Media module in its own control file. Long enough.
        'CtsMediaTestCases',
        'CtsMediaTestCasesz',
        'CtsJvmti',
        'CtsProvider',  # TODO(b/184680306): Remove once the USB stick issue is resolved.
        'CtsSecurityHostTestCases',  # TODO(ihf): remove when passing cleanly.
        'CtsSecurityHostTestCasesz',
        'CtsSensorTestCases',  # TODO(ihf): Remove when not needing 30 retries.
        'CtsSensorTestCasesz',
        'CtsSystem',  # TODO(b/183170604): Remove when flakiness is fixed.
        'CtsViewTestCases',  # TODO(b/126741318): Fix performance regression and remove this.
        'CtsViewTestCasesz',
        'zzzzz'  # A bookend to simplify algorithm.
])

CONFIG['SMOKE'] = []

CONFIG['BVT_ARC'] = []

CONFIG['BVT_PERBUILD'] = [
        'CtsAccelerationTestCases',
        'CtsMidiTestCases',
]

CONFIG['NEEDS_POWER_CYCLE'] = [
        'CtsAppTestCases',
        'CtsSensorTestCases',
]

CONFIG['HARDWARE_DEPENDENT_MODULES'] = [
        'CtsSensorTestCases',
        'CtsCameraTestCases',
        'CtsBluetoothTestCases',
]

# The suite is divided based on the run-time hint in the *.config file.
CONFIG['VMTEST_INFO_SUITES'] = collections.OrderedDict()

# Modules that are known to download and/or push media file assets.
CONFIG['MEDIA_MODULES'] = [
        'CtsMediaTestCases',
        'CtsMediaStressTestCases',
        'CtsMediaBitstreamsTestCases',
]

CONFIG['NEEDS_PUSH_MEDIA'] = CONFIG['MEDIA_MODULES'] + [
        'CtsMediaStressTestCases.camera',
        'CtsMediaTestCases.audio',
        'CtsMediaTestCases.perf',
        'CtsMediaTestCases.video',
]

CONFIG['NEEDS_CTS_HELPERS'] = [
        'CtsPrintTestCases',
]

CONFIG['SPLIT_BY_BITS_MODULES'] = [
        'CtsDeqpTestCases',
        'CtsDeqpTestCases.dEQP-VK',
        'CtsMediaTestCases',
]

CONFIG['X86_SKIP_SUITES'] = ['suite:arc-cts-vm']
# List of modules that skip x86 runs.
CONFIG['SKIP_X86_MODULE_RULES'] = [
        '+.*',
]

# Syntax:
# - First character is either '+' (include) or '-' (exclude).
# - Remaining is a regex that matches the CTS module name.
# Rules are evaluated in list order, and the first match is returned.
CONFIG['VM_MODULES_RULES'] = [
        # Exception to CtsUi.* below.
        '+CtsUidIsolation.*',

        # HW-dependent tests to exclude.
        '-CtsBluetooth.*',
        '-CtsCamera.*',
        '-CtsDeqp.*',
        '-CtsFileSystem.*',
        '-CtsGpu.*',
        '-CtsGraphics.*',
        '-CtsHardware.*',
        '-CtsMedia.*',
        '-CtsNNAPI.*',
        '-CtsNative.*',
        '-CtsOpenG.*',
        '-CtsSample.*',
        '-CtsSecurity.*',
        '-CtsSensor.*',
        '-CtsSimpleCpu.*',
        '-CtsSkQP.*',
        '-CtsUi.*',
        '-CtsVideo.*',
        '-CtsView.*',
        '-CtsWifi.*',

        # Add everything else.
        '+.*',
]

# Same Syntax as VM_MODULES_RULES.
# These VM testing are unstable, and will also run at regular frequency on
# hardware.
CONFIG['VM_UNSTABLE_MODULES_RULES'] = [
        # Uncomment the line below to add all tests back to hardware.
        # TODO(fqj): comment out once arc-cts-vm is running.
        "+.*",

        # These tests failed more than once between Oct/13 and Nov/09 2022 on R.
        "+CtsApp.*",
        "+CtsBionic.*",
        "+CtsCamera.*",
        "+CtsJobScheduler.*",
        "+CtsNet.*",
        "+CtsOs.*",
        "+CtsProvider.*",
        "+CtsSimpleperfTestCases",
        "+CtsStatsdHost.*",

        # These tests has suspicious bug reports on R.
        '+CtsAccessibility.*',  # b/192310577, b/196934844
        '+CtsApp.*',  # b/216741475
        '+CtsAssist.*',  # b/160541876
        '+CtsAutoFillService.*',  # b/216897339
        '+CtsBionic.*',  # b/160851611
        '+CtsBlobStore.*',  # b/180681350
        '+CtsBootStats.*',  # b/174224484
        '+CtsDownloadManager.*',  # b/163729385
        '+CtsDropBoxManagerTestCases.*',  # b/177029550
        '+CtsDynamic.*',  # b/163121640
        '+CtsFragment.*',  # b/251276296
        '+CtsIke.*',  # b/160541882
        '+CtsInputMethod.*',  # b/253540001, b/191413875
        '+CtsJni.*',  # b/160867403
        '+CtsJobScheduler.*',  # b/226422237
        '+CtsMidiTestCases.*',  # b/222242213
        '+CtsNdkBinder.*',  # b/163123128
        '+CtsNet.*',  # b/258074918
        '+CtsOs.*',  # b/b/187745471
        '+CtsPerfetto.*',  # b/203614416
        '+CtsProvider.*',  # b/212194116
        '+CtsRs.*',  # b/166168119
        '+CtsScopedStorageHostTest.*',  # b/232055847
        '+CtsSimpleperfTestCases.*',  # b/247434877
        '+CtsTransition.*',  # b/160544400
        '+CtsWidget.*',  # b/214332007
        '+LegacyStorageTest.*',  # b/190457907
        '+ScopedStorageTest.*',  # b/190457907
        '+vm-tests-tf.*',  # b/158533921

        # May depend on HW ?
        '+CtsDisplay.*',
        '+CtsDpi.*',
        # This suite include tests sensitive to graphics performance
        # (GraphicsStatsValidationTest) so we probably need HW coverage.
        '+CtsIncidentHost.*',
        # We do see device-specfic failure from CtsWM (e.g., b/264339925) and
        # formfactor dependence (5 or 6 kukui/nocturne-only failures must have
        # been addressed before they become launch ready.) It is safer to leave
        # this to the hw-dependence family at least until we have tablet/laptop
        # coverage by Betty
        '+CtsWindowManager.*',
        '+signed-Cts.*',

        # All others tests are stable on VM.
        '-.*',
]

# Modules that are known to need the default apps of Chrome (eg. Files.app).
CONFIG['ENABLE_DEFAULT_APPS'] = [
        'CtsAppSecurityHostTestCases',
        'CtsContentTestCases',
]

_WIFI_CONNECT_COMMANDS = [
        # These needs to be in order.
        "'/usr/local/autotest/cros/scripts/wifi connect %s %s\' % (ssid, wifipass)",
        "'android-sh -c \\'dumpsys wifi transports -eth\\''"
]

_WIFI_CONNECT_COMMANDS_V2 = [
        # These needs to be in order.
        "'adb shell cmd wifi add-network %s %s %s' % (pipes.quote(ssid), 'open' if wifipass == '' else 'wpa', pipes.quote(wifipass))",
        "'adb shell cmd wifi connect-network %s' % pipes.quote(ssid)",
        "'adb shell dumpsys wifi transports -eth'",
]

_DISPLAY_REFRESH_COMMANDS = [
        "'sleep 20'",  # Wait for the intent helper mojo connection established
        "'android-sh -c \\'am start -a android.intent.action.VIEW -d https://webglsamples.org/electricflower/electricflower.html\\''"
]

CONFIG['WIFI_MODULES'] = [
        'CtsLibcoreTestCases',
        'CtsNetApi23TestCases',
        'CtsNetTestCases',
        'CtsJobSchedulerTestCases',
        'CtsStatsdHostTestCases',
        'CtsWifiTestCases',
]

# Preconditions applicable to public and internal tests.
CONFIG['PRECONDITION'] = {
        'CtsCameraTestCases.NativeCameraDeviceTest': _DISPLAY_REFRESH_COMMANDS,
}

CONFIG['LOGIN_PRECONDITION'] = {
}

# Preconditions applicable to public tests.
CONFIG['PUBLIC_PRECONDITION'] = {
        'CtsCameraTestCases.NativeCameraDeviceTest': _DISPLAY_REFRESH_COMMANDS,
}

for m in CONFIG['WIFI_MODULES']:
    CONFIG['PUBLIC_PRECONDITION'][m] = _WIFI_CONNECT_COMMANDS
    CONFIG['PRECONDITION'][m] = _WIFI_CONNECT_COMMANDS_V2

CONFIG['PUBLIC_DEPENDENCIES'] = {
        'CtsCameraTestCases': ['lighting'],
        'CtsMediaTestCases': ['noloopback'],
}

CONFIG['PUBLIC_OVERRIDE_TEST_PRIORITY'] = {
        _PUBLIC_COLLECT: 70,
        'CtsDeqpTestCases': 70,
        'CtsDeqpTestCases': 70,
        'CtsMediaTestCases': 70,
        'CtsMediaStressTestCases': 70,
        'CtsSecurityTestCases': 70,
        'CtsCameraTestCases': 70
}

# This information is changed based on regular analysis of the failure rate on
# partner moblabs.
CONFIG['PUBLIC_MODULE_RETRY_COUNT'] = {
        # TODO(b/183196062): Remove once the flakiness is fixed.
        'CtsHardwareTestCases': 30,
        # TODO(b/168262403): Remove once the flakiness is fixed.
        'CtsIncidentHostTestCases': 10,
        # TODO(b/181543065): Remove once the flakiness is fixed.
        'CtsWindowManagerDeviceTestCases': 10,
}

# This information is changed based on regular analysis of the job run time on
# partner moblabs.

CONFIG['OVERRIDE_TEST_LENGTH'] = {
        'CtsDeqpTestCases': 4,  # LONG
        'CtsMediaTestCases': 4,
        'CtsMediaStressTestCases': 4,
        'CtsSecurityTestCases': 4,
        'CtsCameraTestCases': 4,
        # Even though collect tests doesn't run very long, it must be the very first
        # job executed inside of the suite. Hence it is the only 'LENGTHY' test.
        _COLLECT: 5,  # LENGTHY
        _PUBLIC_COLLECT: 5,  # LENGTHY
}

# Enabling --logcat-on-failure can extend total run time significantly if
# individual tests finish in the order of 10ms or less (b/118836700). Specify
# modules here to not enable the flag.
CONFIG['DISABLE_LOGCAT_ON_FAILURE'] = set([
        'all',
        'CtsDeqpTestCases',
        'CtsDeqpTestCases.dEQP-EGL',
        'CtsDeqpTestCases.dEQP-GLES2',
        'CtsDeqpTestCases.dEQP-GLES3',
        'CtsDeqpTestCases.dEQP-GLES31',
        'CtsDeqpTestCases.dEQP-VK',
        'CtsLibcoreTestCases',
])

# This list of modules will be used for reduced set of testing for build
# variant process. Suites: cts_hardware & arc-cts-hardware.
CONFIG['HARDWARE_MODULES'] = [
        'CtsPerfettoTestCases',
        'CtsSustainedPerformanceHostTestCases',
        'CtsCameraTestCases',
        'CtsViewTestCases',
        'CtsMediaTestCases',
        'CtsNativeMediaAAudioTestCases',
        'CtsNetTestCases',
        'CtsWifiTestCases',
        'CtsUsageStatsTestCases',
        'CtsSensorTestCases',
]


R_REGRESSION_SUITES = ['suite:arc-cts']
R_REGRESSION_AND_QUAL_SUITES = CONFIG['QUAL_SUITE_NAMES'] + R_REGRESSION_SUITES

CONFIG['EXTRA_MODULES'] = { }

# In addition to EXTRA_MODULES, these modules do require separate control files
# for internal and moblab.
CONFIG['HARDWAREONLY_EXTRA_MODULES'] = {
        'CtsAppTestCases': {
                'CtsAppTestCases.feature': [],
        },
        'CtsCameraTestCases': {
                'CtsCameraTestCases.NativeCameraDeviceTest': [],
        },
        'CtsDeqpTestCases': {
                'CtsDeqpTestCases.dEQP-GLES3.functional.prerequisite': [],
        },
        'CtsMediaStressTestCases': {
                'CtsMediaStressTestCases.camera': [],
        },
        'CtsPermissionTestCases': {
                'CtsPermissionTestCases.camera': [],
        },
}

_firmware_sensor_tests = {
        'CtsSensorTestCases.faft': ['suite:faft_experimental']
}

CONFIG['PUBLIC_EXTRA_MODULES'] = {
        'arm': {
                'CtsSensorTestCases': _firmware_sensor_tests,
        },
}

CONFIG['EXTRA_SUBMODULE_OVERRIDE'] = {
}

CONFIG['EXTRA_COMMANDLINE'] = {
        'CtsAppTestCases.feature': [
                '--module', 'CtsAppTestCases', '--test',
                'android.app.cts.SystemFeaturesTest'
        ],
        'CtsCameraTestCases.NativeCameraDeviceTest': [
                '--include-filter',
                'CtsCameraTestCases android.hardware.camera2.cts.NativeCameraDeviceTest',
                '--include-filter',
                'CtsCameraTestCases[instant] android.hardware.camera2.cts.NativeCameraDeviceTest',
                '--include-filter',
                'CtsCameraTestCases android.hardware.camera2.cts.RecordingTest#testVideoPreviewSurfaceSharing[1]',
                '--include-filter',
                'CtsCameraTestCases[instant] android.hardware.camera2.cts.RecordingTest#testVideoPreviewSurfaceSharing[1]',
        ],
        'CtsDeqpTestCases.dEQP-EGL': [
                '--include-filter', 'CtsDeqpTestCases', '--module',
                'CtsDeqpTestCases', '--test', 'dEQP-EGL.*'
        ],
        'CtsDeqpTestCases.dEQP-GLES2': [
                '--include-filter', 'CtsDeqpTestCases', '--module',
                'CtsDeqpTestCases', '--test', 'dEQP-GLES2.*'
        ],
        'CtsDeqpTestCases.dEQP-GLES3': [
                '--include-filter', 'CtsDeqpTestCases', '--module',
                'CtsDeqpTestCases', '--test', 'dEQP-GLES3.*'
        ],
        'CtsDeqpTestCases.dEQP-GLES3.functional.prerequisite': [
                '--module', 'CtsDeqpTestCases', '--test',
                'dEQP-GLES3.functional.prerequisite#*'
        ],
        'CtsDeqpTestCases.dEQP-GLES31': [
                '--include-filter', 'CtsDeqpTestCases', '--module',
                'CtsDeqpTestCases', '--test', 'dEQP-GLES31.*'
        ],
        'CtsDeqpTestCases.dEQP-VK': [
                '--include-filter', 'CtsDeqpTestCases', '--module',
                'CtsDeqpTestCases', '--test', 'dEQP-VK.*'
        ],
        'CtsDeqpTestCases.dEQP-VK.api': [
                '--include-filter', 'CtsDeqpTestCases', '--module',
                'CtsDeqpTestCases', '--test', 'dEQP-VK.api.*'
        ],
        'CtsDeqpTestCases.dEQP-VK.binding_model': [
                '--include-filter', 'CtsDeqpTestCases', '--module',
                'CtsDeqpTestCases', '--test', 'dEQP-VK.binding_model.*'
        ],
        'CtsDeqpTestCases.dEQP-VK.clipping': [
                '--include-filter', 'CtsDeqpTestCases', '--module',
                'CtsDeqpTestCases', '--test', 'dEQP-VK.clipping.*'
        ],
        'CtsDeqpTestCases.dEQP-VK.compute': [
                '--include-filter', 'CtsDeqpTestCases', '--module',
                'CtsDeqpTestCases', '--test', 'dEQP-VK.compute.*'
        ],
        'CtsDeqpTestCases.dEQP-VK.device_group': [
                '--include-filter',
                'CtsDeqpTestCases',
                '--module',
                'CtsDeqpTestCases',
                '--test',
                'dEQP-VK.device_group*'  # Not ending on .* like most others!
        ],
        'CtsDeqpTestCases.dEQP-VK.draw': [
                '--include-filter', 'CtsDeqpTestCases', '--module',
                'CtsDeqpTestCases', '--test', 'dEQP-VK.draw.*'
        ],
        'CtsDeqpTestCases.dEQP-VK.dynamic_state': [
                '--include-filter', 'CtsDeqpTestCases', '--module',
                'CtsDeqpTestCases', '--test', 'dEQP-VK.dynamic_state.*'
        ],
        'CtsDeqpTestCases.dEQP-VK.fragment_operations': [
                '--include-filter', 'CtsDeqpTestCases', '--module',
                'CtsDeqpTestCases', '--test', 'dEQP-VK.fragment_operations.*'
        ],
        'CtsDeqpTestCases.dEQP-VK.geometry': [
                '--include-filter', 'CtsDeqpTestCases', '--module',
                'CtsDeqpTestCases', '--test', 'dEQP-VK.geometry.*'
        ],
        'CtsDeqpTestCases.dEQP-VK.glsl': [
                '--include-filter', 'CtsDeqpTestCases', '--module',
                'CtsDeqpTestCases', '--test', 'dEQP-VK.glsl.*'
        ],
        'CtsDeqpTestCases.dEQP-VK.image': [
                '--include-filter', 'CtsDeqpTestCases', '--module',
                'CtsDeqpTestCases', '--test', 'dEQP-VK.image.*'
        ],
        'CtsDeqpTestCases.dEQP-VK.info': [
                '--include-filter',
                'CtsDeqpTestCases',
                '--module',
                'CtsDeqpTestCases',
                '--test',
                'dEQP-VK.info*'  # Not ending on .* like most others!
        ],
        'CtsDeqpTestCases.dEQP-VK.memory': [
                '--include-filter', 'CtsDeqpTestCases', '--module',
                'CtsDeqpTestCases', '--test', 'dEQP-VK.memory.*'
        ],
        'CtsDeqpTestCases.dEQP-VK.multiview': [
                '--include-filter', 'CtsDeqpTestCases', '--module',
                'CtsDeqpTestCases', '--test', 'dEQP-VK.multiview.*'
        ],
        'CtsDeqpTestCases.dEQP-VK.pipeline': [
                '--include-filter', 'CtsDeqpTestCases', '--module',
                'CtsDeqpTestCases', '--test', 'dEQP-VK.pipeline.*'
        ],
        'CtsDeqpTestCases.dEQP-VK.protected_memory': [
                '--include-filter', 'CtsDeqpTestCases', '--module',
                'CtsDeqpTestCases', '--test', 'dEQP-VK.protected_memory.*'
        ],
        'CtsDeqpTestCases.dEQP-VK.query_pool': [
                '--include-filter', 'CtsDeqpTestCases', '--module',
                'CtsDeqpTestCases', '--test', 'dEQP-VK.query_pool.*'
        ],
        'CtsDeqpTestCases.dEQP-VK.rasterization': [
                '--include-filter', 'CtsDeqpTestCases', '--module',
                'CtsDeqpTestCases', '--test', 'dEQP-VK.rasterization.*'
        ],
        'CtsDeqpTestCases.dEQP-VK.renderpass': [
                '--include-filter', 'CtsDeqpTestCases', '--module',
                'CtsDeqpTestCases', '--test', 'dEQP-VK.renderpass.*'
        ],
        'CtsDeqpTestCases.dEQP-VK.renderpass2': [
                '--include-filter', 'CtsDeqpTestCases', '--module',
                'CtsDeqpTestCases', '--test', 'dEQP-VK.renderpass2.*'
        ],
        'CtsDeqpTestCases.dEQP-VK.robustness': [
                '--include-filter', 'CtsDeqpTestCases', '--module',
                'CtsDeqpTestCases', '--test', 'dEQP-VK.robustness.*'
        ],
        'CtsDeqpTestCases.dEQP-VK.sparse_resources': [
                '--include-filter', 'CtsDeqpTestCases', '--module',
                'CtsDeqpTestCases', '--test', 'dEQP-VK.sparse_resources.*'
        ],
        'CtsDeqpTestCases.dEQP-VK.spirv_assembly': [
                '--include-filter', 'CtsDeqpTestCases', '--module',
                'CtsDeqpTestCases', '--test', 'dEQP-VK.spirv_assembly.*'
        ],
        'CtsDeqpTestCases.dEQP-VK.ssbo': [
                '--include-filter', 'CtsDeqpTestCases', '--module',
                'CtsDeqpTestCases', '--test', 'dEQP-VK.ssbo.*'
        ],
        'CtsDeqpTestCases.dEQP-VK.subgroups': [
                '--include-filter', 'CtsDeqpTestCases', '--module',
                'CtsDeqpTestCases', '--test', 'dEQP-VK.subgroups.*'
        ],
        # Splitting VK.subgroups to smaller pieces to workaround b/138622686.
        # TODO(kinaba,haddowk): remove them once the root cause is fixed, or
        # reconsider the sharding strategy.
        'CtsDeqpTestCases.dEQP-VK.subgroups.b': [
                '--include-filter', 'CtsDeqpTestCases', '--module',
                'CtsDeqpTestCases', '--test', 'dEQP-VK.subgroups.b*'
        ],
        'CtsDeqpTestCases.dEQP-VK.subgroups.s': [
                '--include-filter', 'CtsDeqpTestCases', '--module',
                'CtsDeqpTestCases', '--test', 'dEQP-VK.subgroups.s*'
        ],
        'CtsDeqpTestCases.dEQP-VK.subgroups.vote': [
                '--include-filter', 'CtsDeqpTestCases', '--module',
                'CtsDeqpTestCases', '--test', 'dEQP-VK.subgroups.vote#*'
        ],
        'CtsDeqpTestCases.dEQP-VK.subgroups.arithmetic': [
                '--include-filter', 'CtsDeqpTestCases', '--module',
                'CtsDeqpTestCases', '--test', 'dEQP-VK.subgroups.arithmetic#*'
        ],
        # TODO(haddowk,kinaba): Hack for b/138622686. Clean up later.
        'CtsDeqpTestCases.dEQP-VK.subgroups.arithmetic.32': [
                '--include-filter', 'CtsDeqpTestCases', '--module',
                'CtsDeqpTestCases', '--test', 'dEQP-VK.subgroups.arithmetic#*',
                '--abi', 'x86'
        ],
        # TODO(haddowk,kinaba): Hack for b/138622686. Clean up later.
        'CtsDeqpTestCases.dEQP-VK.subgroups.arithmetic.64': [
                '--include-filter', 'CtsDeqpTestCases', '--module',
                'CtsDeqpTestCases', '--test', 'dEQP-VK.subgroups.arithmetic#*',
                '--abi', 'x86_64'
        ],
        'CtsDeqpTestCases.dEQP-VK.subgroups.clustered': [
                '--include-filter', 'CtsDeqpTestCases', '--module',
                'CtsDeqpTestCases', '--test', 'dEQP-VK.subgroups.clustered#*'
        ],
        'CtsDeqpTestCases.dEQP-VK.subgroups.quad': [
                '--include-filter', 'CtsDeqpTestCases', '--module',
                'CtsDeqpTestCases', '--test', 'dEQP-VK.subgroups.quad#*'
        ],
        'CtsDeqpTestCases.dEQP-VK.synchronization': [
                '--include-filter', 'CtsDeqpTestCases', '--module',
                'CtsDeqpTestCases', '--test', 'dEQP-VK.synchronization.*'
        ],
        'CtsDeqpTestCases.dEQP-VK.tessellation': [
                '--include-filter', 'CtsDeqpTestCases', '--module',
                'CtsDeqpTestCases', '--test', 'dEQP-VK.tessellation.*'
        ],
        'CtsDeqpTestCases.dEQP-VK.texture': [
                '--include-filter', 'CtsDeqpTestCases', '--module',
                'CtsDeqpTestCases', '--test', 'dEQP-VK.texture.*'
        ],
        'CtsDeqpTestCases.dEQP-VK.ubo': [
                '--include-filter', 'CtsDeqpTestCases', '--module',
                'CtsDeqpTestCases', '--test', 'dEQP-VK.ubo.*'
        ],
        'CtsDeqpTestCases.dEQP-VK.wsi': [
                '--include-filter', 'CtsDeqpTestCases', '--module',
                'CtsDeqpTestCases', '--test', 'dEQP-VK.wsi.*'
        ],
        'CtsDeqpTestCases.dEQP-VK.ycbcr': [
                '--include-filter', 'CtsDeqpTestCases', '--module',
                'CtsDeqpTestCases', '--test', 'dEQP-VK.ycbcr.*'
        ],
        'CtsMediaStressTestCases.camera': [
                '--module',
                'CtsMediaStressTestCases',
                '--test',
                'android.mediastress.cts.MediaRecorderStressTest',
        ],
        'CtsMediaTestCases.audio': [
                '--include-filter',
                'CtsMediaTestCases android.media.cts.AudioAttributesTest',
                '--include-filter',
                'CtsMediaTestCases android.media.cts.AudioEffectTest',
                '--include-filter',
                'CtsMediaTestCases android.media.cts.AudioAttributesTest',
                '--include-filter',
                'CtsMediaTestCases android.media.cts.AudioEffectTest',
                '--include-filter',
                'CtsMediaTestCases android.media.cts.AudioFocusTest',
                '--include-filter',
                'CtsMediaTestCases android.media.cts.AudioFormatTest',
                '--include-filter',
                'CtsMediaTestCases android.media.cts.AudioManagerTest',
                '--include-filter',
                'CtsMediaTestCases android.media.cts.AudioMetadataTest',
                '--include-filter',
                'CtsMediaTestCases android.media.cts.AudioNativeTest',
                '--include-filter',
                'CtsMediaTestCases android.media.cts.AudioPlayRoutingNative',
                '--include-filter',
                'CtsMediaTestCases android.media.cts.AudioPlaybackCaptureTest',
                '--include-filter',
                'CtsMediaTestCases android.media.cts.AudioPlaybackConfigurationTest',
                '--include-filter',
                'CtsMediaTestCases android.media.cts.AudioPreProcessingTest',
                '--include-filter',
                'CtsMediaTestCases android.media.cts.AudioPresentationTest',
                '--include-filter',
                'CtsMediaTestCases android.media.cts.AudioRecordAppOpTest',
                '--include-filter',
                'CtsMediaTestCases android.media.cts.AudioRecordRoutingNative',
                '--include-filter',
                'CtsMediaTestCases android.media.cts.AudioRecordTest',
                '--include-filter',
                'CtsMediaTestCases android.media.cts.AudioRecord_BufferSizeTest',
                '--include-filter',
                'CtsMediaTestCases android.media.cts.AudioRecordingConfigurationTest',
                '--include-filter',
                'CtsMediaTestCases android.media.cts.AudioSystemTest',
                '--include-filter',
                'CtsMediaTestCases android.media.cts.AudioSystemUsageTest',
                '--include-filter',
                'CtsMediaTestCases android.media.cts.AudioTrackLatencyTest',
                '--include-filter',
                'CtsMediaTestCases android.media.cts.AudioTrackOffloadTest',
                '--include-filter',
                'CtsMediaTestCases android.media.cts.AudioTrackSurroundTest',
                '--include-filter',
                'CtsMediaTestCases android.media.cts.AudioTrackTest',
                '--include-filter',
                'CtsMediaTestCases android.media.cts.AudioTrack_ListenerTest',
                '--include-filter',
                'CtsMediaTestCases android.media.cts.SoundPoolAacTest',
                '--include-filter',
                'CtsMediaTestCases android.media.cts.SoundPoolHapticTest',
                '--include-filter',
                'CtsMediaTestCases android.media.cts.SoundPoolMidiTest',
                '--include-filter',
                'CtsMediaTestCases android.media.cts.SoundPoolOggTest',
                '--include-filter',
                'CtsMediaTestCases android.media.cts.VolumeShaperTest',
        ],
        'CtsMediaTestCases.perf': [
                '--include-filter',
                'CtsMediaTestCases android.media.cts.VideoDecoderPerfTest',
        ],
        'CtsMediaTestCases.video': [
                '--include-filter',
                'CtsMediaTestCases android.media.cts.AdaptivePlaybackTest',
                '--include-filter',
                'CtsMediaTestCases android.media.cts.DecodeAccuracyTest',
                '--include-filter',
                'CtsMediaTestCases android.media.cts.DecodeEditEncodeTest',
                '--include-filter',
                'CtsMediaTestCases android.media.cts.DecoderConformanceTest',
                '--include-filter',
                'CtsMediaTestCases android.media.cts.EncodeDecodeTest',
                '--include-filter',
                'CtsMediaTestCases android.media.cts.ExtractDecodeEditEncodeMuxTest',
                '--include-filter',
                'CtsMediaTestCases android.media.cts.MediaCodecPlayerTest',
                '--include-filter',
                'CtsMediaTestCases android.media.cts.MediaCodecPlayerTest',
                '--include-filter',
                'CtsMediaTestCases android.media.cts.MediaDrmClearkeyTest',
                '--include-filter',
                'CtsMediaTestCases android.media.cts.MediaRecorderTest',
                '--include-filter',
                'CtsMediaTestCases android.media.cts.MediaSynctest#testPlayVideo',
                '--include-filter',
                'CtsMediaTestCases android.media.cts.VideoCodecTest',
                '--include-filter',
                'CtsMediaTestCases android.media.cts.VideoEncoderTest',
        ],
        'CtsPermissionTestCases.camera': [
                '--include-filter',
                'CtsPermissionTestCases android.permission.cts.CameraPermissionTest',
                '--include-filter',
                'CtsPermissionTestCases android.permission.cts.Camera2PermissionTest',
        ],
        'CtsSensorTestCases.faft': [
                '--include-filter',
                'CtsSensorTestCases',
                '--abi',
                'armeabi-v7a',
        ],
        'CtsWindowManager.A': [
                '--include-filter',
                'CtsWindowManagerDeviceTestCases android.server.wm.ActivityManagerGetConfigTests',
                '--include-filter',
                'CtsWindowManagerDeviceTestCases android.server.wm.ActivityMetricsLoggerTests',
                '--include-filter',
                'CtsWindowManagerDeviceTestCases android.server.wm.ActivityTaskAffinityTests',
                '--include-filter',
                'CtsWindowManagerDeviceTestCases android.server.wm.ActivityTransitionTests',
                '--include-filter',
                'CtsWindowManagerDeviceTestCases android.server.wm.ActivityViewTest',
                '--include-filter',
                'CtsWindowManagerDeviceTestCases android.server.wm.ActivityVisibilityTests',
                '--include-filter',
                'CtsWindowManagerDeviceTestCases android.server.wm.AddWindowAsUserTest',
                '--include-filter',
                'CtsWindowManagerDeviceTestCases android.server.wm.AlertWindowsAppOpsTests',
                '--include-filter',
                'CtsWindowManagerDeviceTestCases android.server.wm.AlertWindowsImportanceTests',
                '--include-filter',
                'CtsWindowManagerDeviceTestCases android.server.wm.AlertWindowsTests',
                '--include-filter',
                'CtsWindowManagerDeviceTestCases android.server.wm.AmProfileTests',
                '--include-filter',
                'CtsWindowManagerDeviceTestCases android.server.wm.AmStartOptionsTests',
                '--include-filter',
                'CtsWindowManagerDeviceTestCases android.server.wm.AnrTests',
                '--include-filter',
                'CtsWindowManagerDeviceTestCases android.server.wm.AppConfigurationTests',
                '--include-filter',
                'CtsWindowManagerDeviceTestCases android.server.wm.AspectRatioTests',
                '--include-filter',
                'CtsWindowManagerDeviceTestCases android.server.wm.AssistantStackTests',
        ],
        'CtsWindowManager.C': [
                '--include-filter',
                'CtsWindowManagerDeviceTestCases android.server.wm.CloseOnOutsideTests',
                '--include-filter',
                'CtsWindowManagerDeviceTestCases android.server.wm.ConfigChangeTests',
                '--include-filter',
                'CtsWindowManagerDeviceTestCases android.server.wm.CrossAppDragAndDropTests',
        ],
        'CtsWindowManager.D': [
                '--include-filter',
                'CtsWindowManagerDeviceTestCases android.server.wm.DecorInsetTests',
                '--include-filter',
                'CtsWindowManagerDeviceTestCases android.server.wm.DeprecatedTargetSdkTest',
                '--include-filter',
                'CtsWindowManagerDeviceTestCases android.server.wm.DialogFrameTests',
                '--include-filter',
                'CtsWindowManagerDeviceTestCases android.server.wm.DisplayCutoutTests',
                '--include-filter',
                'CtsWindowManagerDeviceTestCases android.server.wm.DisplaySizeTest',
                '--include-filter',
                'CtsWindowManagerDeviceTestCases android.server.wm.DisplayTests',
                '--include-filter',
                'CtsWindowManagerDeviceTestCases android.server.wm.DragDropTest',
                '--include-filter',
                'CtsWindowManagerDeviceTestCases android.server.wm.DreamManagerServiceTests',
        ],
        'CtsWindowManager.F': [
                '--include-filter',
                'CtsWindowManagerDeviceTestCases android.server.wm.ForceRelayoutTest',
                '--include-filter',
                'CtsWindowManagerDeviceTestCases android.server.wm.FreeformWindowingModeTests',
        ],
        'CtsWindowManager.L': [
                '--include-filter',
                'CtsWindowManagerDeviceTestCases android.server.wm.LayoutTests',
                '--include-filter',
                'CtsWindowManagerDeviceTestCases android.server.wm.LocationInWindowTests',
                '--include-filter',
                'CtsWindowManagerDeviceTestCases android.server.wm.LocationOnScreenTests',
        ],
        'CtsWindowManager.M': [
                '--include-filter',
                'CtsWindowManagerDeviceTestCases android.server.wm.ManifestLayoutTests',
                '--include-filter',
                'CtsWindowManagerDeviceTestCases android.server.wm.MinimalPostProcessingTests',
                '--include-filter',
                'CtsWindowManagerDeviceTestCases android.server.wm.MultiDisplayActivityLaunchTests',
                '--include-filter',
                'CtsWindowManagerDeviceTestCases android.server.wm.MultiDisplayClientTests',
                '--include-filter',
                'CtsWindowManagerDeviceTestCases android.server.wm.MultiDisplayKeyguardTests',
                '--include-filter',
                'CtsWindowManagerDeviceTestCases android.server.wm.MultiDisplayLockedKeyguardTests',
                '--include-filter',
                'CtsWindowManagerDeviceTestCases android.server.wm.MultiDisplayPolicyTests',
                '--include-filter',
                'CtsWindowManagerDeviceTestCases android.server.wm.MultiDisplayPrivateDisplayTests',
                '--include-filter',
                'CtsWindowManagerDeviceTestCases android.server.wm.MultiDisplaySecurityTests',
                '--include-filter',
                'CtsWindowManagerDeviceTestCases android.server.wm.MultiDisplaySystemDecorationTests',
        ],
        'CtsWindowManager.Override': [
                '--include-filter',
                'CtsWindowManagerDeviceTestCases android.server.wm.OverrideConfigTests',
        ],
        'CtsWindowManager.P': [
                '--include-filter',
                'CtsWindowManagerDeviceTestCases android.server.wm.PinnedStackTests',
                '--include-filter',
                'CtsWindowManagerDeviceTestCases android.server.wm.PrereleaseSdkTest',
                '--include-filter',
                'CtsWindowManagerDeviceTestCases android.server.wm.PresentationTest',
        ],
        'CtsWindowManager.R': [
                '--include-filter',
                'CtsWindowManagerDeviceTestCases android.server.wm.ReplaceWindowTests',
                '--include-filter',
                'CtsWindowManagerDeviceTestCases android.server.wm.RobustnessTests',
        ],
        'CtsWindowManager.S': [
                '--include-filter',
                'CtsWindowManagerDeviceTestCases android.server.wm.SplashscreenTests',
                '--include-filter',
                'CtsWindowManagerDeviceTestCases android.server.wm.SplitScreenTests',
                '--include-filter',
                'CtsWindowManagerDeviceTestCases android.server.wm.StartActivityAsUserTests',
                '--include-filter',
                'CtsWindowManagerDeviceTestCases android.server.wm.StartActivityTests',
                '--include-filter',
                'CtsWindowManagerDeviceTestCases android.server.wm.SurfaceControlTest',
                '--include-filter',
                'CtsWindowManagerDeviceTestCases android.server.wm.SurfaceControlViewHostTests',
                '--include-filter',
                'CtsWindowManagerDeviceTestCases android.server.wm.SurfaceViewSurfaceValidatorTest',
                '--include-filter',
                'CtsWindowManagerDeviceTestCases android.server.wm.SurfaceViewTest',
        ],
        'CtsWindowManager.T': [
                '--include-filter',
                'CtsWindowManagerDeviceTestCases android.server.wm.ToastWindowTest',
                '--include-filter',
                'CtsWindowManagerDeviceTestCases android.server.wm.TransitionSelectionTests',
        ],
        'CtsWindowManager.Window': [
                '--include-filter',
                'CtsWindowManagerDeviceTestCases android.server.wm.WindowContextPolicyTests',
                '--include-filter',
                'CtsWindowManagerDeviceTestCases android.server.wm.WindowContextTests',
                '--include-filter',
                'CtsWindowManagerDeviceTestCases android.server.wm.WindowFocusTests',
                '--include-filter',
                'CtsWindowManagerDeviceTestCases android.server.wm.WindowInputTests',
                '--include-filter',
                'CtsWindowManagerDeviceTestCases android.server.wm.WindowInsetsAnimationCallbackTests',
                '--include-filter',
                'CtsWindowManagerDeviceTestCases android.server.wm.WindowInsetsAnimationControllerTests',
                '--include-filter',
                'CtsWindowManagerDeviceTestCases android.server.wm.WindowInsetsAnimationImeTests',
                '--include-filter',
                'CtsWindowManagerDeviceTestCases android.server.wm.WindowInsetsAnimationSynchronicityTests',
                '--include-filter',
                'CtsWindowManagerDeviceTestCases android.server.wm.WindowInsetsAnimationTests',
                '--include-filter',
                'CtsWindowManagerDeviceTestCases android.server.wm.WindowInsetsControllerTests',
                '--include-filter',
                'CtsWindowManagerDeviceTestCases android.server.wm.WindowInsetsLayoutTests',
                '--include-filter',
                'CtsWindowManagerDeviceTestCases android.server.wm.WindowInsetsPolicyTest',
                '--include-filter',
                'CtsWindowManagerDeviceTestCases android.server.wm.WindowInsetsTest',
                '--include-filter',
                'CtsWindowManagerDeviceTestCases android.server.wm.WindowManager_BadTokenExceptionTest',
                '--include-filter',
                'CtsWindowManagerDeviceTestCases android.server.wm.WindowManager_LayoutParamsTest',
                '--include-filter',
                'CtsWindowManagerDeviceTestCases android.server.wm.WindowMetricsTests',
                '--include-filter',
                'CtsWindowManagerDeviceTestCases android.server.wm.WindowTest',
        ],
        'CtsWindowManager.intent': [
                '--include-filter',
                'CtsWindowManagerDeviceTestCases android.server.wm.intent.IntentGenerationTests',
                '--include-filter',
                'CtsWindowManagerDeviceTestCases android.server.wm.intent.IntentTests',
        ],
        'CtsWindowManager.lifecycle': [
                '--include-filter',
                'CtsWindowManagerDeviceTestCases android.server.wm.lifecycle.ActivityLifecycleFreeformTests',
                '--include-filter',
                'CtsWindowManagerDeviceTestCases android.server.wm.lifecycle.ActivityLifecycleKeyguardTests',
                '--include-filter',
                'CtsWindowManagerDeviceTestCases android.server.wm.lifecycle.ActivityLifecyclePipTests',
                '--include-filter',
                'CtsWindowManagerDeviceTestCases android.server.wm.lifecycle.ActivityLifecycleSplitScreenTests',
                '--include-filter',
                'CtsWindowManagerDeviceTestCases android.server.wm.lifecycle.ActivityLifecycleTests',
                '--include-filter',
                'CtsWindowManagerDeviceTestCases android.server.wm.lifecycle.ActivityLifecycleTopResumedStateTests',
                '--include-filter',
                'CtsWindowManagerDeviceTestCases android.server.wm.lifecycle.ActivityStarterTests',
                '--include-filter',
                'CtsWindowManagerDeviceTestCases android.server.wm.lifecycle.ActivityTests',
        ],
}

CONFIG['EXTRA_ATTRIBUTES'] = {}

CONFIG['EXTRA_ARTIFACTS'] = {}
CONFIG['PREREQUISITES'] = {}

from generate_controlfiles_common import main

if __name__ == '__main__':
    main(CONFIG)
