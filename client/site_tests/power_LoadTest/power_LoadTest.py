# Lint as: python3
# Copyright 2012 The ChromiumOS Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import base64
import collections
import hashlib
import json
import logging
import numpy
import os
import re
import time

import grpc

from autotest_lib.client.bin import utils
from autotest_lib.client.common_lib import error
from autotest_lib.client.common_lib import utils as _utils
from autotest_lib.client.common_lib.cros import arc
from autotest_lib.client.common_lib.cros import power_load_util
from autotest_lib.client.common_lib.cros.network import interface
from autotest_lib.client.common_lib.cros.network import multicast_disabler
from autotest_lib.client.common_lib.cros.network import xmlrpc_datatypes
from autotest_lib.client.common_lib.cros.network import xmlrpc_security_types
from autotest_lib.client.cros import backchannel
from autotest_lib.client.cros import httpd
from autotest_lib.client.cros import memory_bandwidth_logger
from autotest_lib.client.cros import tast
from autotest_lib.client.cros import service_stopper
from autotest_lib.client.cros.audio import audio_helper
from autotest_lib.client.cros.networking import cellular_proxy
from autotest_lib.client.cros.networking import shill_proxy
from autotest_lib.client.cros.networking import wifi_proxy
from autotest_lib.client.cros.power import power_dashboard
from autotest_lib.client.cros.power import power_status
from autotest_lib.client.cros.power import power_utils
from autotest_lib.client.cros.power import force_discharge_utils
from autotest_lib.client.cros.tast.ui import chrome_service_pb2
from autotest_lib.client.cros.tast.ui import conn_service_pb2
from autotest_lib.client.cros.tast.ui import conn_tab
from google.protobuf import empty_pb2

params_dict = {
    'test_time_ms': '_mseconds',
    'should_scroll': '_should_scroll',
    'should_scroll_up': '_should_scroll_up',
    'scroll_loop': '_scroll_loop',
    'scroll_interval_ms': '_scroll_interval_ms',
    'scroll_by_pixels': '_scroll_by_pixels',
    'tasks': '_tasks',
}

class power_LoadTest(arc.ArcTest):
    """test class"""
    version = 2

    def initialize(self,
                   percent_initial_charge_min=None,
                   check_network=True,
                   loop_time=3600,
                   loop_count=1,
                   should_scroll='true',
                   should_scroll_up='true',
                   scroll_loop='false',
                   scroll_interval_ms='10000',
                   scroll_by_pixels='600',
                   test_low_batt_p=3,
                   verbose=True,
                   force_wifi=False,
                   wifi_ap='',
                   wifi_sec='none',
                   wifi_pw='',
                   wifi_timeout=60,
                   use_cellular_network=False,
                   tasks='',
                   volume_level=10,
                   mic_gain=10,
                   low_batt_margin_p=2,
                   ac_ok=False,
                   log_mem_bandwidth=False,
                   gaia_login=None,
                   force_discharge='false',
                   pdash_note='',
                   run_arc=True):
        """
        percent_initial_charge_min: min battery charge at start of test
        check_network: check that Ethernet interface is not running
        loop_time: length of time to run the test for in each loop
        loop_count: number of times to loop the test for
        should_scroll: should the extension scroll pages
        should_scroll_up: should scroll in up direction
        scroll_loop: continue scrolling indefinitely
        scroll_interval_ms: how often to scoll
        scroll_by_pixels: number of pixels to scroll each time
        test_low_batt_p: percent battery at which test should stop
        verbose: add more logging information
        force_wifi: should we force to test to run on wifi
        wifi_ap: the name (ssid) of the wifi access point
        wifi_sec: the type of security for the wifi ap
        wifi_pw: password for the wifi ap
        wifi_timeout: The timeout for wifi configuration
        use_cellular_network: use the cellular network connection instead of wifi
        volume_level: percent audio volume level
        mic_gain: percent audio microphone gain level
        low_batt_margin_p: percent low battery margin to be added to
            sys_low_batt_p to guarantee test completes prior to powerd shutdown
        ac_ok: boolean to allow running on AC
        log_mem_bandwidth: boolean to log memory bandwidth during the test
        gaia_login: whether real GAIA login should be attempted.  If 'None'
            (default) then boolean is determined from URL.
        force_discharge: string of whether to tell ec to discharge battery even
            when the charger is plugged in. 'false' means no forcing discharge;
            'true' means forcing discharge and raising an error when it fails;
            'optional' means forcing discharge when possible but not raising an
            error when it fails, which is more friendly to devices without a
            battery.
        pdash_note: note of the current run to send to power dashboard.
        run_arc: enable ARC when available.
        """
        self._backlight = None
        self._services = None
        self._browser = None
        self._loop_time = loop_time
        self._loop_count = loop_count
        self._mseconds = self._loop_time * 1000
        self._verbose = verbose

        self._sys_low_batt_p = 0.
        self._sys_low_batt_s = 0.
        self._test_low_batt_p = test_low_batt_p
        self._should_scroll = should_scroll
        self._should_scroll_up = should_scroll_up
        self._scroll_loop = scroll_loop
        self._scroll_interval_ms = scroll_interval_ms
        self._scroll_by_pixels = scroll_by_pixels
        self._tmp_keyvals = {}
        self._power_status = None
        self._force_wifi = force_wifi
        self._use_cellular_network = use_cellular_network
        self._testServer = None
        self._tasks = tasks
        self._backchannel = None
        self._shill_proxy = None
        self._volume_level = volume_level
        self._mic_gain = mic_gain
        self._ac_ok = ac_ok
        self._log_mem_bandwidth = log_mem_bandwidth
        self._wait_time = 60
        self._stats = collections.defaultdict(list)
        self._pdash_note = pdash_note
        self._run_arc = run_arc

        self._power_status = power_status.get_status()

        self._force_discharge_success = force_discharge_utils.process(
                force_discharge, self._power_status)
        if self._force_discharge_success:
            self._ac_ok = True

        if not self._power_status.battery:
            if ac_ok and (power_utils.has_powercap_support() or
                          power_utils.has_rapl_support()):
                logging.info("Device has no battery but has powercap data.")
            else:
                rsp = "Skipping test for device without battery and powercap."
                raise error.TestNAError(rsp)

        self._tmp_keyvals['b_on_ac'] = int(not self._force_discharge_success
                                           and self._power_status.on_ac())
        self._tmp_keyvals['force_discharge'] = int(
                self._force_discharge_success)

        self._gaia_login = gaia_login
        if gaia_login is None:
            self._gaia_login = power_load_util.use_gaia_login()

        self._username = power_load_util.get_username()
        self._password = power_load_util.get_password()

        if not self._ac_ok:
            self._power_status.assert_battery_state(percent_initial_charge_min)

        # If force wifi enabled, convert eth0 to backchannel and connect to the
        # specified WiFi AP.
        if self._force_wifi:
            if self._use_cellular_network:
                raise error.TestError("Can't force WiFi AP when cellular network"
                                      "is used");

            sec_config = None
            # TODO(dbasehore): Fix this when we get a better way of figuring out
            # the wifi security configuration.
            if wifi_sec == 'rsn' or wifi_sec == 'wpa':
                sec_config = xmlrpc_security_types.WPAConfig(
                        psk=wifi_pw,
                        wpa_mode=xmlrpc_security_types.WPAConfig.MODE_PURE_WPA2,
                        wpa2_ciphers=
                                [xmlrpc_security_types.WPAConfig.CIPHER_CCMP])
            wifi_config = xmlrpc_datatypes.AssociationParameters(
                    ssid=wifi_ap, security_config=sec_config,
                    configuration_timeout=wifi_timeout)
            # If backchannel is already running, don't run it again.
            self._backchannel = backchannel.Backchannel()
            if not self._backchannel.setup():
                raise error.TestError('Could not setup Backchannel network.')

            self._shill_proxy = wifi_proxy.WifiProxy()
            self._shill_proxy.remove_all_wifi_entries()
            for i in range(1, 4):
                raw_output = self._shill_proxy.connect_to_wifi_network(
                        wifi_config.ssid,
                        wifi_config.security,
                        wifi_config.security_parameters,
                        wifi_config.save_credentials,
                        station_type=wifi_config.station_type,
                        hidden_network=wifi_config.is_hidden,
                        discovery_timeout_seconds=
                                wifi_config.discovery_timeout,
                        association_timeout_seconds=
                                wifi_config.association_timeout,
                        configuration_timeout_seconds=
                                wifi_config.configuration_timeout * i)
                result = xmlrpc_datatypes.AssociationResult. \
                        from_dbus_proxy_output(raw_output)
                if result.success:
                    break
                logging.warning('wifi connect: disc:%d assoc:%d config:%d fail:%s',
                             result.discovery_time, result.association_time,
                             result.configuration_time, result.failure_reason)
            else:
                raise error.TestError('Could not connect to WiFi network.')

        else:
            # Find all wired ethernet interfaces.
            ifaces = [ iface for iface in interface.get_interfaces()
                if (not iface.is_wifi_device() and
                    iface.name.startswith('eth')) ]
            logging.debug(str([iface.name for iface in ifaces]))
            for iface in ifaces:
                if check_network and iface.is_lower_up:
                    raise error.TestError('Ethernet interface is active. ' +
                                          'Please remove Ethernet cable')

        if self._use_cellular_network:
            self._shill_proxy = cellular_proxy.CellularProxy()
            cdev = self._shill_proxy.find_cellular_device_object()
            if cdev is None:
                raise error.TestError("No cellular device found")

            self._shill_proxy.manager.DisableTechnology(
                shill_proxy.ShillProxy.TECHNOLOGY_WIFI)

            self._shill_proxy.wait_for_cellular_service_object()

        # record the max backlight level
        self._backlight = power_utils.Backlight(
                force_battery=self._force_discharge_success)
        self._tmp_keyvals['level_backlight_max'] = \
            self._backlight.get_max_level()

        self._services = service_stopper.ServiceStopper(
            service_stopper.ServiceStopper.POWER_DRAW_SERVICES)
        self._multicast_disabler = multicast_disabler.MulticastDisabler()
        self._multicast_disabler.disable_network_multicast()

        self._detachable_handler = power_utils.BaseActivitySimulator()

        # fix up file perms for the power test extension so that chrome
        # can access it
        os.system('chmod -R 755 %s' % self.bindir)

        # setup a HTTP Server to listen for status updates from the power
        # test extension
        self._testServer = httpd.HTTPListener(8001, docroot=self.bindir)
        self._testServer.run()

        # initialize various interesting power related stats
        self._statomatic = power_status.StatoMatic()

        self._power_status.refresh()
        self._sys_low_batt_p = float(utils.system_output(
                 'check_powerd_config --low_battery_shutdown_percent'))
        self._sys_low_batt_s = int(utils.system_output(
                 'check_powerd_config --low_battery_shutdown_time'))

        if self._sys_low_batt_p and self._sys_low_batt_s:
            raise error.TestError(
                    "Low battery percent and seconds are non-zero.")

        min_low_batt_p = min(self._sys_low_batt_p + low_batt_margin_p, 100)
        if self._sys_low_batt_p and (min_low_batt_p > self._test_low_batt_p):
            logging.warning("test low battery threshold is below system "\
                         "low battery requirement.  Setting to %f",
                         min_low_batt_p)
            self._test_low_batt_p = min_low_batt_p

        if self._power_status.battery:
            self._ah_charge_start = self._power_status.battery.charge_now
            self._wh_energy_start = self._power_status.battery.energy

        self.task_monitor_file = open(os.path.join(self.resultsdir,
                                                   'task-monitor.json'),
                                      mode='wt',
                                      **power_utils.encoding_kwargs())


    def run_once(self, tast_bundle_path=None, use_lacros=False):
        """Test main loop."""
        t0 = time.time()

        # record the PSR related info.
        psr = power_utils.DisplayPanelSelfRefresh(init_time=t0)

        try:
            self._keyboard_backlight = power_utils.KbdBacklight()
            self._set_keyboard_backlight_level()
        except power_utils.KbdBacklightException as e:
            logging.info("Assuming no keyboard backlight due to :: %s", str(e))
            self._keyboard_backlight = None

        self._checkpoint_logger = power_status.CheckpointLogger()
        seconds_period = 20.0
        self._meas_logs = power_status.create_measurement_loggers(
                seconds_period, self._checkpoint_logger)
        for log in self._meas_logs:
            log.start()
        if self._log_mem_bandwidth:
            self._mlog = memory_bandwidth_logger.MemoryBandwidthLogger(
                raw=False, seconds_period=2)
            self._mlog.start()

        # record start time and end time for each task
        self._task_tracker = []

        ext_path = os.path.join(os.path.dirname(__file__), 'extension')
        self._tmp_keyvals['username'] = self._username

        with tast.GRPC(tast_bundle_path) as tast_grpc,\
            tast.ChromeService(tast_grpc.channel) as chrome_service,\
            tast.LacrosService(tast_grpc.channel) as lacros_service,\
            tast.ConnService(tast_grpc.channel) as conn_service:

            chrome_new_request = chrome_service_pb2.NewRequest(
                    # b/228256145 to avoid powerd restart
                    disable_features = ['FirmwareUpdaterApp'],
                    # --disable-sync disables test account info sync, eg. Wi-Fi credentials,
                    # so that each test run does not remember info from last test run.
                    extra_args = ['--disable-sync'],
                    login_mode = (chrome_service_pb2.LOGIN_MODE_GAIA_LOGIN
                                if self._gaia_login else
                                chrome_service_pb2.LOGIN_MODE_UNSPECIFIED),
                    credentials = chrome_service_pb2.NewRequest.Credentials(
                        username=self._username,
                        password=self._password,
                    ),
                    arc_mode = (chrome_service_pb2.ARC_MODE_ENABLED
                                if self._run_arc and utils.is_arc_available()
                                else chrome_service_pb2.ARC_MODE_DISABLED),
                )

            if use_lacros:
                chrome_new_request.lacros_unpacked_extensions.append(ext_path)
                chrome_new_request.lacros.mode = chrome_service_pb2.Lacros.Mode.MODE_ONLY
            else:
                chrome_new_request.unpacked_extensions.append(ext_path)

            try:
                chrome_service.New(chrome_new_request)
            except grpc.RpcError as rpc_error:
                if self._gaia_login and ('login failed' in rpc_error.details()):
                    logging.warning("Unable to use GAIA acct %s.  Using GUEST instead.\n", self._username)
                    chrome_new_request.login_mode = \
                        chrome_service_pb2.LOGIN_MODE_UNSPECIFIED
                    chrome_service.New(chrome_new_request)
                    self._gaia_login = False
                else:
                    raise rpc_error
            if not self._gaia_login:
                self._tmp_keyvals['username'] = 'GUEST'
            self._tmp_keyvals['gaia_login'] = int(self._gaia_login)

            if use_lacros:
                # Launch Lacros. The window opened will be closed when startTest
                # is run.
                lacros_service.Launch(empty_pb2.Empty())

            response = conn_service.NewConnForTarget(conn_service_pb2.NewConnRequest(
                url = _get_extension_bg_url(ext_path),
                call_on_lacros = use_lacros,
            ))
            extension = conn_tab.ConnTab(conn_service, response.id)
            set_var_script = ''
            for k, v in params_dict.items():
                if getattr(self, v) is not '':
                    set_var_script += 'var %s = %s;' % (k, getattr(self, v))
            extension.EvaluateJavaScript(set_var_script)

            # Stop services and disable multicast again as Chrome might have
            # restarted them.
            self._services.stop_services()
            self._multicast_disabler.disable_network_multicast()

            # This opens a trap start page to capture tabs opened for first login.
            # It will be closed when startTest is run.
            extension.EvaluateJavaScript('chrome.windows.create(null, null);')

            for i in range(self._loop_count):
                start_time = time.time()
                extension.EvaluateJavaScript('startTest();')
                # the power test extension will report its status here
                latch = self._testServer.add_wait_url('/status')

                # this starts a thread in the server that listens to log
                # information from the script
                script_logging = self._testServer.add_wait_url(url='/log')

                # dump any log entry that comes from the script into
                # the debug log
                self._testServer.add_url_handler(url='/log',\
                    handler_func=(lambda handler, forms, loop_counter=i:\
                        _extension_log_handler(handler, forms, loop_counter)))

                pagetime_tracking = self._testServer.add_wait_url(url='/pagetime')

                self._testServer.add_url_handler(url='/pagetime',\
                    handler_func=(lambda handler, forms, test_instance=self,
                                loop_counter=i:\
                        _extension_page_time_info_handler(handler, forms,
                                                        loop_counter,
                                                        test_instance)))

                keyvalues_tracking = self._testServer.add_wait_url(url='/keyvalues')

                self._testServer.add_url_handler(url='/keyvalues',\
                    handler_func=(lambda handler, forms, test_instance=self,
                                loop_counter=i:\
                        _extension_key_values_handler(handler, forms,
                                                    loop_counter,
                                                    test_instance)))
                self._testServer.add_url(url='/task-monitor')
                self._testServer.add_url_handler(
                    url='/task-monitor',
                    handler_func=lambda handler, forms:
                        self._extension_task_monitor_handler(handler, forms)
                )

                # setup a handler to simulate waking up the base of a detachable
                # on user interaction. On scrolling, wake for 1s, on page
                # navigation, wake for 10s.
                self._testServer.add_url(url='/pagenav')
                self._testServer.add_url(url='/scroll')

                self._testServer.add_url_handler(url='/pagenav',
                    handler_func=(lambda handler, args, plt=self:\
                        _extension_wake_base_handler(handler, args, plt, 10000)))

                self._testServer.add_url_handler(url='/scroll',
                    handler_func=(lambda handler, args, plt=self:\
                        _extension_wake_base_handler(handler, args, plt, 1000)))
                # reset backlight level since powerd might've modified it
                # based on ambient light
                self._set_backlight_level(i)
                self._set_lightbar_level()
                if self._keyboard_backlight:
                    self._set_keyboard_backlight_level(loop=i)
                audio_helper.set_volume_levels(self._volume_level,
                                            self._mic_gain)

                low_battery = self._do_wait(self._verbose, self._loop_time,
                                            latch)
                script_logging.set()
                pagetime_tracking.set()
                keyvalues_tracking.set()

                # log at end of loop in case it was changed
                self._log_backlight_level(i)
                self._log_loop_checkpoint(i, start_time, time.time())

                if self._verbose:
                    logging.debug('loop %d completed', i)

                if low_battery:
                    logging.info('Exiting due to low battery')
                    break

            # done with logging from the script, so we can collect that thread
            t1 = time.time()
            psr.refresh()
            self._tmp_keyvals['minutes_battery_life_tested'] = (t1 - t0) / 60
            self._tmp_keyvals.update(psr.get_keyvals())
            self._start_time = t0
            self._end_time = t1

            self._multicast_disabler.enable_network_multicast()

    def postprocess_iteration(self):
        """Postprocess: write keyvals / log and send data to power dashboard."""
        def _log_stats(prefix, stats):
            if not len(stats):
                return
            np = numpy.array(stats)
            logging.debug("%s samples: %d", prefix, len(np))
            logging.debug("%s mean:    %.2f", prefix, np.mean())
            logging.debug("%s stdev:   %.2f", prefix, np.std())
            logging.debug("%s max:     %.2f", prefix, np.max())
            logging.debug("%s min:     %.2f", prefix, np.min())


        def _log_per_loop_stats():
            samples_per_loop = int(self._loop_time / self._wait_time) + 1
            for kname in self._stats:
                start_idx = 0
                loop = 1
                for end_idx in range(samples_per_loop, len(self._stats[kname]),
                                     samples_per_loop):
                    _log_stats("%s loop %d" % (kname, loop),
                               self._stats[kname][start_idx:end_idx])
                    loop += 1
                    start_idx = end_idx


        def _log_all_stats():
            for kname in self._stats:
                _log_stats(kname, self._stats[kname])


        for task, tstart, tend in self._task_tracker:
            self._checkpoint_logger.checkpoint('_' + task, tstart, tend)

        keyvals = {}
        for log in self._meas_logs:
            keyvals.update(log.calc())
        keyvals.update(self._statomatic.publish())

        if self._log_mem_bandwidth:
            self._mlog.stop()
            self._mlog.join()

        _log_all_stats()
        _log_per_loop_stats()

        # record battery stats
        if self._power_status.battery:
            keyvals['a_current_now'] = self._power_status.battery.current_now
            keyvals['ah_charge_full'] = \
                    self._power_status.battery.charge_full
            keyvals['ah_charge_full_design'] = \
                    self._power_status.battery.charge_full_design
            keyvals['ah_charge_start'] = self._ah_charge_start
            keyvals['ah_charge_now'] = self._power_status.battery.charge_now
            keyvals['ah_charge_used'] = keyvals['ah_charge_start'] - \
                                        keyvals['ah_charge_now']
            keyvals['wh_energy_start'] = self._wh_energy_start
            keyvals['wh_energy_now'] = self._power_status.battery.energy
            keyvals['wh_energy_used'] = keyvals['wh_energy_start'] - \
                                        keyvals['wh_energy_now']
            keyvals['v_voltage_min_design'] = \
                    self._power_status.battery.voltage_min_design
            keyvals['wh_energy_full_design'] = \
                    self._power_status.battery.energy_full_design
            keyvals['v_voltage_now'] = self._power_status.battery.voltage_now

        keyvals.update(self._tmp_keyvals)

        keyvals['percent_sys_low_battery'] = self._sys_low_batt_p
        keyvals['seconds_sys_low_battery'] = self._sys_low_batt_s
        voltage_np = numpy.array(self._stats['v_voltage_now'])
        voltage_mean = voltage_np.mean()
        keyvals['v_voltage_mean'] = voltage_mean

        keyvals['wh_energy_powerlogger'] = \
                             self._energy_use_from_powerlogger(keyvals)

        if (self._force_discharge_success or not self._power_status.on_ac()
            ) and keyvals['ah_charge_used'] > 0:
            # For full runs, we should use charge to scale for battery life,
            # since the voltage swing is accounted for.
            # For short runs, energy will be a better estimate.
            # TODO(b/188082306): some devices do not provide
            # 'wh_energy_powerlogger' so use charge in this case to scale for
            # battery life.
            if self._loop_count > 1 or keyvals['wh_energy_powerlogger'] <= 0:
                estimated_reps = (keyvals['ah_charge_full_design'] /
                                  keyvals['ah_charge_used'])
            else:
                estimated_reps = (keyvals['wh_energy_full_design'] /
                                  keyvals['wh_energy_powerlogger'])

            bat_life_scale =  estimated_reps * \
                              ((100 - keyvals['percent_sys_low_battery']) / 100)

            keyvals['minutes_battery_life'] = bat_life_scale * \
                keyvals['minutes_battery_life_tested']
            # In the case where sys_low_batt_s is non-zero subtract those
            # minutes from the final extrapolation.
            if self._sys_low_batt_s:
                keyvals['minutes_battery_life'] -= self._sys_low_batt_s / 60

            keyvals['a_current_rate'] = keyvals['ah_charge_used'] * 60 / \
                                        keyvals['minutes_battery_life_tested']
            keyvals['w_energy_rate'] = keyvals['wh_energy_used'] * 60 / \
                                       keyvals['minutes_battery_life_tested']
            if self._gaia_login:
                self.output_perf_value(description='minutes_battery_life',
                                       value=keyvals['minutes_battery_life'],
                                       units='minute',
                                       higher_is_better=True)

        minutes_battery_life_tested = keyvals['minutes_battery_life_tested']

        # TODO(coconutruben): overwrite write_perf_keyvals for all power
        # tests and replace this once power_LoadTest inherits from power_Test.
        # Dump all keyvals into debug keyvals.
        _utils.write_keyval(os.path.join(self.resultsdir, 'debug_keyval'),
                            keyvals)
        # Avoid polluting the keyvals with non-core domains.
        core_keyvals = power_utils.get_core_keyvals(keyvals)
        for key, value in core_keyvals.items():
            if re.match(r'percent_[cg]pu(idle|pkg).*_R?C0(_C1)?_time', key):
                self.output_perf_value(description=key,
                                       value=value,
                                       units='percent',
                                       higher_is_better=False)
        for key, values in keyvals.items():
            if key.endswith('system_pwr_avg'):
                self.output_perf_value(description=key,
                                       value=values,
                                       units='W',
                                       higher_is_better=False,
                                       graph='power')

        logger = power_dashboard.KeyvalLogger(self._start_time, self._end_time)
        for key in [
                'b_on_ac', 'force_discharge', 'gaia_login',
                'percent_usb_suspended_time'
        ]:
            logger.add_item(key, keyvals[key], 'point', 'perf')

        # Add audio/docs/email/web fail load details to power dashboard and to keyval
        for task in ('audio', 'docs', 'email', 'web'):
            total_key = 'total_%s_loads' % (task)
            failed_key = 'failed_%s_loads' % (task)
            percent_key = 'percent_failed_%s_loads' % (task)
            core_keyvals[total_key] = 0
            core_keyvals[failed_key] = 0
            key = 'ext_%s_failed_loads' % task
            if key not in keyvals:
                continue
            vals = (int(x) for x in keyvals[key].split('_'))
            for index, val in enumerate(vals):
                log_name = 'loop%02d_%s_failed_load' % (index, task)
                logger.add_item(log_name, val, 'point', 'perf')
                core_keyvals[log_name] = val
                core_keyvals[total_key] += val
                if val > 0:
                    core_keyvals[failed_key] += val
            key = 'ext_%s_successful_loads' % task
            if key in keyvals:
                vals = (int(x) for x in keyvals[key].split('_'))
                for index, val in enumerate(vals):
                    # total loads is sum of failures and successes
                    core_keyvals[total_key] += val

            if core_keyvals[total_key] > 0:
                core_keyvals[percent_key] = (core_keyvals[failed_key] * 100.0 /
                                             core_keyvals[total_key])
            else:
                # if we have no total loads something went wrong so set
                # percent failed loads to 100%
                core_keyvals[percent_key] = 100

        # Add ext_ms_page_load_time_mean to power dashboard
        if 'ext_ms_page_load_time_mean' in keyvals:
            vals = (float(x)
                    for x in keyvals['ext_ms_page_load_time_mean'].split('_'))
            for index, val in enumerate(vals):
                log_name = 'loop%02d_ms_page_load_time' % index
                logger.add_item(log_name, val, 'point', 'perf')

        # Add battery life and power to power dashboard
        for key in ('minutes_battery_life_tested', 'minutes_battery_life',
                    'w_energy_rate'):
            if key in keyvals:
                logger.add_item(key, keyvals[key], 'point', 'perf')

        self._meas_logs.append(logger)

        self.write_perf_keyval(core_keyvals)
        for log in self._meas_logs:
            log.save_results(self.resultsdir)
        self._checkpoint_logger.save_checkpoint_data(self.resultsdir)

        if minutes_battery_life_tested * 60 < self._loop_time :
            logging.info('Data is less than 1 loop, skip sending to dashboard.')
            return

        dashboard_factory = power_dashboard.get_dashboard_factory()
        for log in self._meas_logs:
            dashboard = dashboard_factory.createDashboard(log,
                self.tagged_testname, self.resultsdir, note=self._pdash_note)
            dashboard.upload()

        power_dashboard.generate_parallax_report(self.outputdir)

    def cleanup(self):
        force_discharge_utils.restore(self._force_discharge_success)
        if self._backlight:
            self._backlight.restore()
        if self._services:
            self._services.restore_services()
        audio_helper.set_default_volume_levels()
        self._detachable_handler.restore()

        if self.task_monitor_file:
            self.task_monitor_file.close()
            self._generate_task_monitor_html()

        if self._shill_proxy:
            if self._force_wifi:
                # cleanup backchannel interface
                # Prevent wifi congestion in test lab by forcing machines to forget the
                # wifi AP we connected to at the start of the test.
                self._shill_proxy.remove_all_wifi_entries()

            if self._use_cellular_network:
                self._shill_proxy.manager.EnableTechnology(
                    shill_proxy.ShillProxy.TECHNOLOGY_WIFI)

        if self._backchannel:
            self._backchannel.teardown()
        if self._testServer:
            self._testServer.stop()


    def _do_wait(self, verbose, seconds, latch):
        latched = False
        low_battery = False
        total_time = seconds + self._wait_time
        elapsed_time = 0

        while elapsed_time < total_time:
            time.sleep(self._wait_time)
            elapsed_time += self._wait_time

            self._power_status.refresh()

            if not self._ac_ok and self._power_status.on_ac():
                raise error.TestError('Running on AC power now.')

            if self._power_status.battery:
                if (not self._ac_ok and
                    self._power_status.battery.status != 'Discharging'):
                    raise error.TestFail('The battery is not discharging.')
                charge_now = self._power_status.battery.charge_now
                energy_rate = self._power_status.battery.energy_rate
                voltage_now = self._power_status.battery.voltage_now
                self._stats['w_energy_rate'].append(energy_rate)
                self._stats['v_voltage_now'].append(voltage_now)
                if verbose:
                    logging.debug('ah_charge_now %f', charge_now)
                    logging.debug('w_energy_rate %f', energy_rate)
                    logging.debug('v_voltage_now %f', voltage_now)

                low_battery = (self._power_status.percent_current_charge() <
                               self._test_low_batt_p)

            latched = latch.is_set()

            if latched or low_battery:
                break

        if latched:
            # record chrome power extension stats
            form_data = self._testServer.get_form_entries()
            logging.debug(form_data)
            for e in form_data:
                key = 'ext_' + e
                if key in self._tmp_keyvals:
                    self._tmp_keyvals[key] += "_%s" % form_data[e]
                else:
                    self._tmp_keyvals[key] = form_data[e]
        else:
            logging.debug("Didn't get status back from power extension")

        return low_battery


    def _set_backlight_level(self, loop=None):
        self._backlight.set_default()

    def _log_backlight_level(self, loop=None):
        # record brightness level
        self._tmp_keyvals[_loop_keyname(loop, 'level_backlight')] = \
            self._backlight.get_level()
        self._tmp_keyvals[_loop_keyname(loop, 'level_backlight_percent')] = \
            self._backlight.get_percent()


    def _set_lightbar_level(self, level='off'):
        """Set lightbar level.

        Args:
          level: string value to set lightbar to.  See ectool for more details.
        """
        rv = utils.system('which ectool', ignore_status=True)
        if rv:
            return
        rv = utils.system('ectool lightbar %s' % level, ignore_status=True)
        if rv:
            logging.info('Assuming no lightbar due to non-zero exit status')
        else:
            logging.info('Setting lightbar to %s', level)
            self._tmp_keyvals['level_lightbar_current'] = level


    def _has_light_sensor(self):
        """
        Determine if there is a light sensor on the board.

        @returns True if this host has a light sensor or
                 False if it does not.
        """
        # If the command exits with a failure status,
        # we do not have a light sensor
        cmd = 'check_powerd_config --ambient_light_sensor'
        result = utils.run(cmd, ignore_status=True)
        if result.exit_status:
            logging.debug('Ambient light sensor not present')
            return False
        logging.debug('Ambient light sensor present')
        return True


    def _energy_use_from_powerlogger(self, keyval):
        """
        Calculates the energy use, in Wh, used over the course of the run as
        reported by the PowerLogger.

        Args:
          keyval: the dictionary of keyvals containing PowerLogger output

        Returns:
          energy_wh: total energy used over the course of this run

        """
        energy_wh = 0
        loop = 0
        while True:
            duration_key = _loop_keyname(loop, 'system_duration')
            avg_power_key = _loop_keyname(loop, 'system_pwr_avg')
            if duration_key not in keyval or avg_power_key not in keyval:
                break
            energy_wh += keyval[duration_key] * keyval[avg_power_key] / 3600
            loop += 1
        return energy_wh


    def _has_hover_detection(self):
        """
        Checks if hover is detected by the device.

        Returns:
            Returns True if the hover detection support is enabled.
            Else returns false.
        """

        cmd = 'check_powerd_config --hover_detection'
        result = utils.run(cmd, ignore_status=True)
        if result.exit_status:
            logging.debug('Hover not present')
            return False
        logging.debug('Hover present')
        return True


    def _set_keyboard_backlight_level(self, loop=None):
        """
        Sets keyboard backlight based on light sensor and hover.
        These values are based on UMA as mentioned in
        https://bugs.chromium.org/p/chromium/issues/detail?id=603233#c10

        ALS  | hover | keyboard backlight level
        ---------------------------------------
        No   | No    | default
        ---------------------------------------
        Yes  | No    | 40% of default
        --------------------------------------
        No   | Yes   | System with this configuration does not exist
        --------------------------------------
        Yes  | Yes   | 30% of default
        --------------------------------------

        Here default is no Ambient Light Sensor, no hover,
        default always-on brightness level.
        """

        default_level = self._keyboard_backlight.get_default_level()
        level_to_set = default_level
        has_light_sensor = self._has_light_sensor()
        has_hover = self._has_hover_detection()
        # TODO(ravisadineni):if (crbug: 603233) becomes default
        # change this to reflect it.
        if has_light_sensor and has_hover:
            level_to_set = (30 * default_level) / 100
        elif has_light_sensor:
            level_to_set = (40 * default_level) / 100
        elif has_hover:
            logging.warning('Device has hover but no light sensor')

        logging.info('Setting keyboard backlight to %d', level_to_set)
        self._keyboard_backlight.set_level(level_to_set)
        keyname = _loop_keyname(loop, 'percent_kbd_backlight')
        self._tmp_keyvals[keyname] = self._keyboard_backlight.get_percent()


    def _log_loop_checkpoint(self, loop, start, end):
        loop_str = _loop_prefix(loop)
        self._checkpoint_logger.checkpoint(loop_str, start, end)

        # Don't log section if we run custom tasks.
        if self._tasks != '':
            return

        sections = [
            ('browsing', (0, 0.6)),
            ('email', (0.6, 0.8)),
            ('document', (0.8, 0.9)),
            ('video', (0.9, 1)),
        ]

        # Use start time from extension if found by look for google.com start.
        goog_str = loop_str + '_web_page_www.google.com'
        for item, start_extension, _ in self._task_tracker:
            if item == goog_str:
                if start_extension >= start:
                    start = start_extension
                    break
                logging.warning('Timestamp from extension (%.2f) is earlier than'
                             'timestamp from autotest (%.2f).',
                             start_extension, start)

        # Use default loop duration for incomplete loop.
        duration = max(end - start, self._loop_time)

        for section, fractions in sections:
            s_start, s_end = (start + duration * fraction
                              for fraction in fractions)
            if s_start > end:
                break
            if s_end > end:
                s_end = end
            self._checkpoint_logger.checkpoint(section, s_start, s_end)
            loop_section = '_' + loop_str + '_' + section
            self._checkpoint_logger.checkpoint(loop_section, s_start, s_end)


    def _extension_task_monitor_handler(self, handler, form):
        """
        We use the httpd library to allow us to log chrome processes usage.
        """
        if form:
            logging.debug("[task-monitor] got %d samples", len(form))
            for idx in sorted(form.keys()):
                json = form[idx].value
                self.task_monitor_file.write(json)
                self.task_monitor_file.write(",\n")
                # we don't want to add url information to our keyvals.
                # httpd adds them automatically so we remove them again
                if idx in handler.server._form_entries:
                    del handler.server._form_entries[idx]
        handler.send_simple_response(200)


    def _generate_task_monitor_html(self):
        json_decoder = json.JSONDecoder()
        # regex pattern to simplify the url
        pattern = re.compile(r'.*https?://(www[.])?(?P<site>[^.]*[.][^/]*)')
        data = []
        min_ts = None
        process_dict = {}
        process_id = 1
        with open(os.path.join(self.resultsdir, 'task-monitor.json'), 'r',
                  **power_utils.encoding_kwargs()) as f:
            json_strs = f.read().splitlines()
            for json_str in json_strs[1:]:
                if len(json_str) < 10:
                    continue
                entry_dict, _ = json_decoder.raw_decode(json_str, 0)
                if not min_ts:
                    min_ts = entry_dict['timestamp']
                ts = (entry_dict['timestamp'] - min_ts) / 1000

                items = {}
                for p in entry_dict['processes']:
                    if 'cpu' not in p:
                        continue
                    tab = p['tasks'][0]
                    key = tab['title']
                    if 'tabId' in tab:
                        tabInfo = [
                                t for t in entry_dict['tabInfo']
                                if t['tabId'] == tab['tabId']
                        ]
                        if len(tabInfo) > 0 and 'url' in tabInfo[0]:
                            url = tabInfo[0]['url']
                            site = pattern.search(url)
                            if site:
                                key = 'Tab: ' + site.group('site')

                    if key.startswith('Service Worker'):
                        key = 'Service Worker: ' + \
                            pattern.search(key).group('site')

                    items[key] = p['cpu']
                    if key not in process_dict:
                        process_dict[key] = process_id
                        process_id += 1

                data.append((ts, items))

        cols = ['timestamp'] + list(process_dict.keys())
        rows = [cols]

        # This data is logged every seconds but graph would be too dense.
        # So we average data in |avg_window| seconds window.
        avg_window = 3
        if len(data) > 1000:
            avg_window = 20

        for index, (ts, items) in enumerate(data):
            if index % avg_window == 0:
                row = [0] * len(cols)
                row[0] = ts
            for name, cpu in items.items():
                row[process_dict[name]] += cpu / avg_window
            if index % avg_window == avg_window - 1:
                rows.append(row)

        row_indent = ' ' * 12
        data_str = ',\n'.join([row_indent + json.dumps(row) for row in rows])

        out_str = power_dashboard._HTML_CHART_STR.format(
                data=data_str, unit='percent', type='process cpu usage',
                id=hash(data_str))

        with open(os.path.join(self.resultsdir, 'task-monitor.html'),
                  'w') as f:
            f.write(out_str)


def alphanum_key(s):
    """ Turn a string into a list of string and numeric chunks. This enables a
        sort function to use this list as a key to sort alphanumeric strings
        naturally without padding zero digits.
        "z23a" -> ["z", 23, "a"]
    """
    chunks = re.split('([-.0-9]+)', s)
    for i in range(len(chunks)):
        try:
            chunks[i] = float(chunks[i])
        except ValueError:
            pass
    return chunks


def _extension_wake_base_handler(handler, args, plt, wake_time_ms):
    """
    We use the httpd library to listen to PLT simulated user activities.

    This method will wake up the base for a specific time when there are
    user activities such as page navigation or scrolling.
    """

    plt._detachable_handler.wake_base(wake_time_ms)
    handler.send_simple_response(200)


def _extension_log_handler(handler, form, loop_number):
    """
    We use the httpd library to allow us to log whatever we
    want from the extension JS script into the log files.

    This method is provided to the server as a handler for
    all requests that come for the log url in the testServer

    unused parameter, because httpd passes the server itself
    into the handler.
    """

    if form:
        for field in sorted(list(form.keys()), key=alphanum_key):
            logging.debug("[extension] @ %s %s", _loop_prefix(loop_number),
            form[field].value)
            # we don't want to add url information to our keyvals.
            # httpd adds them automatically so we remove them again
            if field in handler.server._form_entries:
                del handler.server._form_entries[field]
    handler.send_simple_response(200)


def _extension_page_time_info_handler(handler, form, loop_number,
                                      test_instance):
    page_timestamps = []

    stats_ids = ['mean', 'min', 'max', 'std']
    loadtime_measurements = []
    sorted_pagelt = []
    #show up to this number of slow page-loads
    num_slow_page_loads = 5

    if not form:
        logging.debug("no page time information returned")
        handler.send_simple_response(200)
        return

    for field in sorted(form.keys(), key=alphanum_key):
        page = json.loads(form[field].value)
        url = page['url']

        pstr = "[extension] @ %s url: %s" % (_loop_prefix(loop_number), url)
        logging.debug("%s start_time: %d", pstr, page['start_time'])

        if page['end_load_time']:
            logging.debug("%s end_load_time: %d", pstr, page['end_load_time'])

            load_time = page['end_load_time'] - page['start_time']

            loadtime_measurements.append(load_time)
            sorted_pagelt.append((url, load_time))

            logging.debug("%s load time: %d ms", pstr, load_time)

        logging.debug("%s end_browse_time: %d", pstr, page['end_browse_time'])

        page_timestamps.append(page)

        # we don't want to add url information to our keyvals.
        # httpd adds them automatically so we remove them again
        if field in handler.server._form_entries:
            del handler.server._form_entries[field]

    page_base = _loop_keyname(loop_number, 'web_page_')
    for page in page_timestamps:
        page_failed = "_failed"
        # timestamps from javascript are in milliseconds, change to seconds
        scale = 1.0/1000
        if page['end_load_time']:
            tagname = page_base + page['url'] + "_load"
            test_instance._task_tracker.append((tagname,
                page['start_time'] * scale, page['end_load_time'] * scale))

            tagname = page_base + page['url'] + "_browse"
            test_instance._task_tracker.append((tagname,
                page['end_load_time'] * scale, page['end_browse_time'] * scale))

            page_failed = ""

        tagname = page_base + page['url'] + page_failed
        test_instance._task_tracker.append((tagname,
            page['start_time'] * scale, page['end_browse_time'] * scale))

    loadtime_measurements = numpy.array(loadtime_measurements)
    stats_vals = [loadtime_measurements.mean(), loadtime_measurements.min(),
        loadtime_measurements.max(),loadtime_measurements.std()]

    key_base = 'ext_ms_page_load_time_'
    for i in range(len(stats_ids)):
        key = key_base + stats_ids[i]
        if key in test_instance._tmp_keyvals:
            test_instance._tmp_keyvals[key] += "_%.2f" % stats_vals[i]
        else:
            test_instance._tmp_keyvals[key] = "%.2f" % stats_vals[i]


    sorted_pagelt.sort(key=lambda item: item[1], reverse=True)

    message = "The %d slowest page-load-times are:\n" % (num_slow_page_loads)
    for url, msecs in sorted_pagelt[:num_slow_page_loads]:
        message += "\t%s w/ %d ms" % (url, msecs)

    logging.debug("%s\n", message)
    handler.send_simple_response(200)


def _extension_key_values_handler(handler, form, loop_number,
                                      test_instance):
    if not form:
        logging.debug("no key value information returned")
        handler.send_simple_response(200)
        return

    for field in sorted(form.keys(), key=alphanum_key):
        keyval_data = json.loads(form[field].value)

        # Print each key:value pair and associate it with the data
        for key, value in keyval_data.items():
            logging.debug("[extension] @ %s key: %s val: %s",
                _loop_prefix(loop_number), key, value)
            # Add the key:values to the _tmp_keyvals set
            test_instance._tmp_keyvals[_loop_keyname(loop_number, key)] = value

        # we don't want to add url information to our keyvals.
        # httpd adds them automatically so we remove them again
        if field in handler.server._form_entries:
            del handler.server._form_entries[field]
    handler.send_simple_response(200)


def _loop_prefix(loop):
    return "loop%02d" % loop


def _loop_keyname(loop, keyname):
    if loop != None:
        return "%s_%s" % (_loop_prefix(loop), keyname)
    return keyname


def _get_public_key(filename):
    # Assume it's an unpacked extension.
    with open(os.path.join(filename, 'manifest.json'), 'rb') as f:
        manifest = json.load(f)
        if 'key' not in manifest:
            raise Exception("'key' value missing in manifest.json file.")
        return base64.standard_b64decode(manifest['key'])


def _hex_to_mpdecimal(hex_chars):
    """ Convert bytes to an MPDecimal string. Example \x00 -> "aa"
        This gives us the AppID for a chrome extension.
    """
    def chr(x):
        return bytes([x])

    result = b''
    base = b'a'[0]
    for hex_char in hex_chars:
        value = hex_char
        dig1 = value // 16
        dig2 = value % 16
        result += chr(dig1 + base)
        result += chr(dig2 + base)
    return result.decode('utf-8')


def _get_extension_id(filename):
    """
    Given path to unpacked extension directory, it calculates the extension id
    using public key in 'manifest.json'.
    """
    pub_key = _get_public_key(filename)
    pub_key_hash = hashlib.sha256(pub_key).digest()
    # AppID is the MPDecimal of only the first 128 bits of the hash.
    return _hex_to_mpdecimal(pub_key_hash[:128//8])


def _get_extension_bg_url(filename):
    """
    Calculates the url to pg.html page for an unpacked extension in filename
    dir.
    """
    extension_id = _get_extension_id(filename)
    return "chrome-extension://%s/bg.html" % extension_id
