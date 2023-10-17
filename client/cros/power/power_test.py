# Lint as: python2, python3
# Copyright 2018 The ChromiumOS Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.
import logging
import re
import time

from autotest_lib.client.bin import test
from autotest_lib.client.bin import utils
from autotest_lib.client.common_lib import error
from autotest_lib.client.common_lib.cros import arc_common
from autotest_lib.client.common_lib.cros import force_discharge_utils
from autotest_lib.client.common_lib.cros import retry
from autotest_lib.client.common_lib.cros.network import interface
from autotest_lib.client.common_lib.cros.network import multicast_disabler
from autotest_lib.client.cros import service_stopper
from autotest_lib.client.cros.camera import camera_utils
from autotest_lib.client.cros.power import power_dashboard
from autotest_lib.client.cros.power import power_status
from autotest_lib.client.cros.power import power_telemetry_utils
from autotest_lib.client.cros.power import power_utils
from autotest_lib.client.cros.video import histogram_verifier

class power_Test(test.test):
    """Optional base class power related tests."""
    version = 1

    # TODO(crbug.com/1054021): The older Event.Latency.EndToEnd.KeyPress metric
    # is deprecated in favor of the newer EventLatency.KeyPressed.TotalLatency.
    # We will start by reporting both here until the team has enough data to
    # compare them and update their thresholds for the new metric. Then we can
    # remove the old one entirely.
    deprecated_keypress_histogram = 'Event.Latency.EndToEnd.KeyPress'
    keypress_histogram = 'EventLatency.KeyPressed.TotalLatency'
    histogram_re = 'Histogram: %s recorded (\d+) samples, mean = (\d+\.\d+)'
    hist_percentile_re = '^(\d+).+\{(\d+)\.\d+\%\}'

    def initialize(self,
                   seconds_period=20.,
                   pdash_note='',
                   force_discharge='false',
                   check_network=False,
                   run_arc=True,
                   disable_hdrnet=False):
        """Perform necessary initialization prior to power test run.

        @param seconds_period: float of probing interval in seconds.
        @param pdash_note: note of the current run to send to power dashboard.
        @param force_discharge: string of whether to tell ec to discharge
                battery even when the charger is plugged in. 'false' means no
                forcing discharge; 'true' means forcing discharge and raising an
                error when it fails; 'optional' means forcing discharge when
                possible but not raising an error when it fails, which is more
                friendly to devices without a battery.
        @param check_network: check that Ethernet interface is not running.
        @param run_arc: bool, whether to run with ARC (if available)

        @var backlight: power_utils.Backlight object.
        @var kbd_backlight: power_utils.KbdBacklight object.
        @var keyvals: dictionary of result keyvals.
        @var status: power_status.SysStat object.

        @var _checkpoint_logger: power_status.CheckpointLogger to track
                                 checkpoint data.
        @var _psr: power_utils.DisplayPanelSelfRefresh object to monitor PSR.
        @var _services: service_stopper.ServiceStopper object.
        @var _start_time: float of time in seconds since Epoch test started.
        @var _stats: power_status.StatoMatic object.
        @var _meas_logs: list of power_status.MeasurementLoggers
        """
        super(power_Test, self).initialize()
        self.keyvals = dict()
        self.status = power_status.get_status()

        self._checkpoint_logger = power_status.CheckpointLogger()
        self._seconds_period = seconds_period

        self._force_discharge = force_discharge
        self._force_discharge_errors = 0
        self._force_discharge_success = force_discharge_utils.process(
                self._force_discharge, self.status)

        ifaces = [iface for iface in interface.get_interfaces()
                if (not iface.is_wifi_device() and
                iface.name.startswith('eth'))]
        logging.debug('Ethernet interfaces include: %s',
                      str([iface.name for iface in ifaces]))
        for iface in ifaces:
            if check_network and iface.is_lower_up:
                raise error.TestError('Ethernet interface is active. '
                                      'Please remove Ethernet cable.')

        self._psr = power_utils.DisplayPanelSelfRefresh()
        self._services = service_stopper.ServiceStopper(
                service_stopper.ServiceStopper.POWER_DRAW_SERVICES)
        self._services.stop_services()

        self.backlight = power_utils.Backlight(
                force_battery=self._force_discharge_success)
        self.backlight.set_default()
        try:
            self.kbd_backlight = power_utils.KbdBacklight()
            self.kbd_backlight.set_level(0)
        except power_utils.KbdBacklightException as e:
            logging.info('Test will proceed with understanding: %s', e)
            self.kbd_backlight = None

        self._multicast_disabler = multicast_disabler.MulticastDisabler()
        self._multicast_disabler.disable_network_multicast()
        self._stats = power_status.StatoMatic()

        self._meas_logs = power_status.create_measurement_loggers(
                seconds_period, self._checkpoint_logger)
        logging.debug('measurement loggers (%d):', len(self._meas_logs))
        for log in self._meas_logs:
            logging.debug('%s: %s', type(log).__name__, ", ".join(log.domains))

        self._pdash_note = pdash_note
        self._failure_messages = []

        self._arc_mode = arc_common.ARC_MODE_DISABLED
        if run_arc and utils.is_arc_available():
            self._arc_mode = arc_common.ARC_MODE_ENABLED
        self.keyvals['arc_mode'] = self._arc_mode

        self._disable_hdrnet = False
        if disable_hdrnet:
            power_utils.disable_camera_hdrnet()
            self._disable_hdrnet = True
        self.keyvals['disable_hdrnet'] = self._disable_hdrnet

    def get_extra_browser_args_for_camera_test(self):
        """Return Chrome args for camera power test."""
        ret = [
                # No pop up to ask permission to record video.
                '--use-fake-ui-for-media-stream',
                # Allow 2 windows side by side.
                '--force-tablet-mode=clamshell',
                # Prefer using constant frame rate for camera streaming.
                '--enable-features=PreferConstantFrameRate',
                # Bypass HID detection for Chromebox / Chromebase.
                '--disable-hid-detection-on-oobe',
                # Disable test account info sync, eg. Wi-Fi credentials,
                # so that each test run does not remember info from last test
                # run.
                '--disable-sync'
        ]

        # Use fake camera for DUT without camera, e.g. chromebox.
        if not camera_utils.has_builtin_or_vivid_camera():
            ret.append('--use-fake-device-for-media-stream')
            self.keyvals['use_fake_camera'] = 1
        else:
            self.keyvals['use_fake_camera'] = 0
        return ret

    def warmup(self, warmup_time=30):
        """Warm up.

        Wait between initialization and run_once for new settings to stabilize.

        @param warmup_time: integer of seconds to warmup.
        """
        time.sleep(warmup_time)

    def start_measurements(self):
        """Start measurements."""
        for log in self._meas_logs:
            log.start()
        self._start_time = time.time()
        if self.status.battery:
            self._start_energy = self.status.battery.energy
        self._keyvallogger = power_dashboard.KeyvalLogger(self._start_time)
        power_telemetry_utils.start_measurement()

    def loop_sleep(self, loop, sleep_secs):
        """Jitter free sleep with a discharge check.

        @param loop: integer of loop (1st is zero).
        @param sleep_secs: integer of desired sleep seconds.
        """
        next_time = self._start_time + (loop + 1) * sleep_secs
        check_interval = self._seconds_period
        while time.time() < next_time:
            self.check_force_discharge()
            sleep_interval = min(max(next_time - time.time(), 0),
                                 check_interval)
            time.sleep(sleep_interval)

    def check_force_discharge(self):
        """Watchdog device is still discharging.
        """
        if not self.status.battery_discharging():
            if (self._force_discharge_success
                        and force_discharge_utils.process(
                                self._force_discharge, self.status)):
                self._force_discharge_errors += 1
                logging.warning('Force discharge temporarily stopped'
                                'working, possibly due to a charger'
                                'connection reset')
            elif self._force_discharge == 'true':
                raise error.TestError('Running on AC power now.')

    def notify_ash_discharge_status(self):
        """Notify current discharge status to ash
        """

        # PowerSupplyProperties_ExternalPower: AC = 0, DISCONNECTED = 2
        property = 0
        if self.status.battery_discharging():
            property = 2
        utils.run('sudo -u power send_debug_power_status --external_power=%d' %
                  property)

    def checkpoint_measurements(self, name, start_time=None):
        """Checkpoint measurements.

        @param name: string name of measurement being checkpointed.
        @param start_time: float of time in seconds since Epoch that
                measurements being checkpointed began.
        """
        if not start_time:
            start_time = self._start_time
        self.status.refresh()
        self._checkpoint_logger.checkpoint(name, start_time)
        self._psr.refresh()

    @retry.retry(Exception, timeout_min=1, delay_sec=2)
    def collect_keypress_latency_for(self, tab, histogram, prefix):
        """Collect keypress latency information from Histograms.

        @param tab: object, Chrome tab instance
        @param histogram: string name of the histogram
        @param prefix: string prefix for the output key names
        """
        keypress_histogram_end = histogram_verifier.get_histogram(
                tab, histogram)
        matches = re.search((self.histogram_re % histogram),
                            keypress_histogram_end)

        if matches:
            count = int(matches.group(1))
            mean_latency = float(matches.group(2))
            logging.info('%slatency count %d mean %f', prefix, count,
                         mean_latency)
            self.keyvals[prefix + 'keypress_cnt'] = count
            self.keyvals[prefix + 'keypress_latency_us_avg'] = mean_latency
            self.output_perf_value(description=prefix + 'keypress_cnt',
                                   value=count,
                                   higher_is_better=True)
            self.output_perf_value(description=prefix +
                                   'keypress_latency_us_avg',
                                   value=mean_latency,
                                   higher_is_better=False)
            self._keyvallogger.add_item(prefix + 'keypress_cnt', count,
                                        'point', 'keypress')
            self._keyvallogger.add_item(prefix + 'keypress_latency_us_avg',
                                        mean_latency, 'point', 'keypress')

        # Capture the first bucket >= 90th percentile
        for s in keypress_histogram_end.splitlines():
            matches = re.search((self.hist_percentile_re), s)
            if matches:
                lat = int(matches.group(1))
                perc = int(matches.group(2))
                if perc >= 90:
                    self.keyvals[prefix + 'keypress_latency_us_high'] = lat
                    self.keyvals[prefix + 'keypress_high_percentile'] = perc
                    self.output_perf_value(description=prefix +
                                           'keypress_latency_us_high',
                                           value=lat,
                                           higher_is_better=False)
                    self.output_perf_value(description=prefix +
                                           'keypress_high_percentile',
                                           value=perc,
                                           higher_is_better=False)
                    self._keyvallogger.add_item(
                            prefix + 'keypress_latency_us_high', lat, 'point',
                            'keypress')
                    self._keyvallogger.add_item(
                            prefix + 'keypress_high_percentile', perc, 'point',
                            'keypress')
                    break

    def collect_keypress_latency(self, tab):
        """Collect old and new keypress latency information from Histograms.

        @param tab: object, Chrome tab instance
        """
        self.collect_keypress_latency_for(tab, self.keypress_histogram, '')
        self.collect_keypress_latency_for(tab,
                                          self.deprecated_keypress_histogram,
                                          'deprecated_')


    def publish_keyvals(self):
        """Publish power result keyvals."""
        keyvals = self._stats.publish()
        keyvals['level_backlight_max'] = self.backlight.get_max_level()
        keyvals['level_backlight_current'] = self.backlight.get_level()
        keyvals['level_backlight_percent'] = self.backlight.get_percent()
        keyvals['level_backlight_nonlinear'] = \
            self.backlight.linear_to_nonlinear(keyvals['level_backlight_percent'])
        if self.kbd_backlight:
            keyvals['level_kbd_backlight_max'] = \
                    self.kbd_backlight.get_max_level()
            keyvals['level_kbd_backlight_current'] = \
                    self.kbd_backlight.get_level()

        # record battery stats if battery exists
        keyvals['b_on_ac'] = int(not self._force_discharge_success
                                 and self.status.on_ac())
        keyvals['force_discharge'] = int(self._force_discharge_success)
        for key in [
                'b_on_ac', 'force_discharge', 'percent_usb_suspended_time',
                'level_backlight_percent', 'level_backlight_nonlinear'
        ]:
            self._keyvallogger.add_item(key, keyvals[key], 'point', 'perf')

        if self._force_discharge_success:
            keyvals['force_discharge_errors'] = self._force_discharge_errors

        max_force_discharge_errors = 3
        if (
                self.status.battery
                and self._force_discharge_errors < max_force_discharge_errors):
            keyvals['ah_charge_full'] = self.status.battery.charge_full
            keyvals['ah_charge_full_design'] = \
                                self.status.battery.charge_full_design
            keyvals['ah_charge_now'] = self.status.battery.charge_now
            keyvals['a_current_now'] = self.status.battery.current_now

            keyvals['wh_energy_full'] = self.status.battery.energy_full
            keyvals['wh_energy_full_design'] = \
                                self.status.battery.energy_full_design
            keyvals['wh_energy_now'] = self.status.battery.energy
            keyvals['wh_energy_start'] = self._start_energy
            energy_used = self._start_energy - self.status.battery.energy
            runtime_minutes = (time.time() - self._start_time) / 60.
            keyvals['wh_energy_used'] = energy_used
            keyvals['minutes_tested'] = runtime_minutes
            self._keyvallogger.add_item('minutes_tested',
                                        keyvals['minutes_tested'], 'point',
                                        'perf')

            low_batt = power_utils.get_low_battery_shutdown_percent()
            keyvals['percent_sys_low_battery'] = low_batt

            if energy_used > 0 and runtime_minutes > 1:
                keyvals['w_energy_rate'] = energy_used * 60. / runtime_minutes
                self._keyvallogger.add_item('w_energy_rate',
                                            keyvals['w_energy_rate'], 'point',
                                            'perf')
                energy_avail = self.status.battery.energy_full_design * \
                    ((100. - low_batt) / 100.)
                keyvals['minutes_battery_life'] = energy_avail / energy_used * \
                    runtime_minutes
                self._keyvallogger.add_item('minutes_battery_life',
                                            keyvals['minutes_battery_life'],
                                            'point', 'perf')
                keyvals['hours_battery_life'] = \
                    keyvals['minutes_battery_life'] / 60.
                self._keyvallogger.add_item('hours_battery_life',
                                            keyvals['hours_battery_life'],
                                            'point', 'perf')

            keyvals['v_voltage_min_design'] = \
                                self.status.battery.voltage_min_design
            keyvals['v_voltage_now'] = self.status.battery.voltage_now

        for log in self._meas_logs:
            keyvals.update(log.calc())
        keyvals.update(self._psr.get_keyvals())

        self.keyvals.update(keyvals)

        core_keyvals = power_utils.get_core_keyvals(self.keyvals)
        self.write_perf_keyval(core_keyvals)

    def publish_dashboard(self):
        """Report results to chromeperf & power dashboard."""

        self.publish_keyvals()

        # publish battery minutes values
        if 'minutes_battery_life' in self.keyvals:
            self.output_perf_value(description='minutes_battery_life',
                                   value=self.keyvals['minutes_battery_life'],
                                   units='minute',
                                   higher_is_better=True)

        # Avoid polluting the keyvals with non-core domains.
        core_keyvals = power_utils.get_core_keyvals(self.keyvals)
        for key, values in core_keyvals.items():

            # publish power values
            if key.endswith('pwr_avg'):
                self.output_perf_value(description=key, value=values, units='W',
                        higher_is_better=False, graph='power')
            # publish temperature values
            if key.endswith('temp_avg'):
                self.output_perf_value(description=key, value=values, units='C',
                        higher_is_better=False, graph='temperature')
            # publish fps values
            if key.endswith('fps_avg'):
                self.output_perf_value(description=key, value=values,
                        units='fps', higher_is_better=True, graph='fps')
            # publish CPU activity values
            if re.match(r'percent_[cg]pu(idle|pkg).*_R?C0(_C1)?_time', key):
                self.output_perf_value(description=key,
                                       value=values,
                                       units='percent',
                                       higher_is_better=False)

        # include KeyvalLogger in dashboard
        self._meas_logs.append(self._keyvallogger)

        # publish to power dashboard
        dashboard_factory = power_dashboard.get_dashboard_factory()
        for log in self._meas_logs:
            dashboard = dashboard_factory.createDashboard(log,
                self.tagged_testname, self.resultsdir, note=self._pdash_note)
            dashboard.upload()

    def _save_results(self):
        """Save results of each logger in resultsdir."""
        for log in self._meas_logs:
            log.save_results(self.resultsdir)
        self._checkpoint_logger.save_checkpoint_data(self.resultsdir)

    def postprocess_iteration(self):
        """Write keyval and send data to dashboard."""
        power_telemetry_utils.end_measurement()
        self.status.refresh()
        for log in self._meas_logs:
            log.done = True
        super(power_Test, self).postprocess_iteration()
        self.publish_dashboard()
        self._save_results()
        power_dashboard.generate_parallax_report(self.outputdir)
        if self._failure_messages:
            raise error.TestFail('Test has failed with messages: %s' %
                                 self._failure_messages)

    def cleanup(self):
        """Reverse setting change in initialization."""
        if self._disable_hdrnet:
            power_utils.remove_camera_hdrnet_override()
        force_discharge_utils.restore(self._force_discharge_success)
        if self.backlight:
            self.backlight.restore()
        if self.kbd_backlight:
            self.kbd_backlight.restore()
        self._multicast_disabler.enable_network_multicast()
        started_services = self._services.get_started_services()
        self._services.restore_services()
        super(power_Test, self).cleanup()
        if started_services:
            raise error.TestWarn("Following services are not stopped: %s" %
                                 str(started_services))
