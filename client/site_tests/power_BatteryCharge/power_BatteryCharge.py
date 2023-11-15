# Lint as: python2, python3
# Copyright 2010 The ChromiumOS Authors
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import logging, time
from autotest_lib.client.bin import utils
from autotest_lib.client.common_lib import error
from autotest_lib.client.cros import service_stopper
from autotest_lib.client.cros.power import power_status
from autotest_lib.client.cros.power import power_test
from autotest_lib.client.cros.power import power_utils


class power_BatteryCharge(power_test.power_Test):
    """class power_BatteryCharge."""
    version = 1

    def initialize(self, pdash_note=''):
        """Perform necessary initialization prior to test run."""
        if not power_utils.has_battery():
            raise error.TestNAError('DUT has no battery. Test Skipped')

        # Temporarily disable Charge Limit if it's enabled.
        if power_utils.is_charge_limit_enabled():
            prefs = {'charge_limit_enabled': 0}
            self.power_pref_changer = power_utils.PowerPrefChanger(prefs)

        # Charge Limit may take slightly longer to disable, so poll for AC
        # charging.
        utils.poll_for_condition(condition=power_status.get_status().on_ac,
                                 timeout=10,
                                 sleep_interval=1.0,
                                 desc='Charging enabled')

        self.status = power_status.get_status()

        super(power_BatteryCharge, self).initialize(seconds_period=20,
                                                    pdash_note=pdash_note,
                                                    force_discharge=False)

        self._services_other = service_stopper.ServiceStopper(['ui'])
        self._services_other.stop_services()

    def run_once(self,
                 max_run_time=180,
                 percent_charge_to_add=1,
                 percent_initial_charge_max=None,
                 percent_target_charge=None,
                 use_design_charge_capacity=True,
                 test_for_charging_speed=False):
        """
        max_run_time: maximum time the test will run for
        percent_charge_to_add: percentage of the charge capacity charge to
                  add. The target charge will be capped at the charge capacity.
        percent_initial_charge_max: maxium allowed initial charge.
        use_design_charge_capacity: If set, use charge_full_design rather than
                  charge_full for calculations. charge_full represents
                  wear-state of battery, vs charge_full_design representing
                  ideal design state.
        test_for_charging_speed: If set to true, the test will be used to measure
                  charging speed rather than charge battery to the target percent.
        """

        time_to_sleep = 60

        self._backlight = power_utils.Backlight()
        if test_for_charging_speed:
            logging.info('Setting backlight to default linear percentage for'
                         'measuring charging speed')
            self._backlight.set_default()
            logging.info(
                    'Default linear percentage is %.2f, and current linear'
                    'percentage is %.2f',
                    self._backlight.default_brightness_percent,
                    self._backlight.get_percent())
            if round(self._backlight.get_percent(), 2) != round(
                    self._backlight.default_brightness_percent, 2):
                raise error.TestError('For charging speed measurement test, '
                                      'current brightness should be equal to'
                                      'default brightness')
        else:
            self._backlight.set_percent(0)

        self.remaining_time = self.max_run_time = max_run_time

        self.charge_full_design = self.status.battery.charge_full_design
        self.charge_full = self.status.battery.charge_full
        if use_design_charge_capacity:
            self.charge_capacity = self.charge_full_design
        else:
            self.charge_capacity = self.charge_full

        if self.charge_capacity == 0:
            raise error.TestError('Failed to determine charge capacity')

        self.initial_charge = self.status.battery.charge_now
        percent_initial_charge = self.initial_charge * 100 / \
                                 self.charge_capacity
        if percent_initial_charge_max and round(percent_initial_charge, 2) > \
                                          round(float(percent_initial_charge_max), 2):
            raise error.TestError(
                    'Initial charge (%.2f) higher than initial max(%.2f)' %
                    (round(percent_initial_charge,
                           2), round(float(percent_initial_charge_max), 2)))

        current_charge = self.initial_charge
        if percent_target_charge is None:
            charge_to_add = self.charge_capacity * \
                            float(percent_charge_to_add) / 100
            target_charge = current_charge + charge_to_add
        else:
            target_charge = self.charge_capacity * \
                            float(percent_target_charge) / 100

        # trim target_charge if it exceeds charge capacity
        if target_charge > self.charge_capacity:
            target_charge = self.charge_capacity

        logging.info('max_run_time: %d', self.max_run_time)
        logging.info('initial_charge: %f', self.initial_charge)
        logging.info('target_charge: %f', target_charge)

        self.start_measurements()
        while self.remaining_time and current_charge < target_charge:
            if time_to_sleep > self.remaining_time:
                time_to_sleep = self.remaining_time
            self.remaining_time -= time_to_sleep

            time.sleep(time_to_sleep)

            self.status.refresh()

            new_charge = self.status.battery.charge_now
            logging.info('time_to_sleep: %d', time_to_sleep)
            logging.info('charge_added: %f', (new_charge - current_charge))

            current_charge = new_charge
            logging.info('current_charge: %f', current_charge)

            if self.status.battery_full():
                logging.info('Battery full, aborting!')
                break
            elif self.status.battery_discharging():
                if self.status.battery_discharge_ok_on_ac():
                    logging.info('Battery full (Discharge on AC), aborting!')
                    break
                else:
                    raise error.TestError('This test needs to be run with the '
                                          'battery charging on AC.')
        self._end_time = time.time()

    def postprocess_iteration(self):
        """"Collect and log keyvals."""
        keyvals = {}
        keyvals['ah_charge_full'] = self.charge_full
        keyvals['ah_charge_full_design'] = self.charge_full_design
        keyvals['ah_charge_capacity'] = self.charge_capacity
        keyvals['ah_initial_charge'] = self.initial_charge
        keyvals['ah_final_charge'] = self.status.battery.charge_now
        s_time_taken = self.max_run_time - self.remaining_time
        min_time_taken = s_time_taken / 60.
        keyvals['s_time_taken'] = s_time_taken
        keyvals['percent_initial_charge'] = self.initial_charge * 100 / \
                                            keyvals['ah_charge_capacity']
        keyvals['percent_final_charge'] = keyvals['ah_final_charge'] * 100 / \
                                          keyvals['ah_charge_capacity']

        percent_charge_added = keyvals['percent_final_charge'] - \
            keyvals['percent_initial_charge']
        # Conditionally write charge current keyval only when the amount of
        # charge added is > 50% to remove samples when test is run but battery
        # is already mostly full.  Otherwise current will be ~0 and not
        # meaningful.
        if percent_charge_added > 50:
            hrs_charging = keyvals['s_time_taken'] / 3600.
            keyvals['a_avg50_charge_current'] = \
                (keyvals['ah_final_charge'] - self.initial_charge) / \
                hrs_charging

        self.keyvals.update(keyvals)

        self._keyvallogger.add_item('time_to_charge_min', min_time_taken,
                                    'point', 'perf')
        self._keyvallogger.add_item('initial_charge_ah', self.initial_charge,
                                    'point', 'perf')
        self._keyvallogger.add_item('final_charge_ah',
                                    self.status.battery.charge_now, 'point',
                                    'perf')
        self._keyvallogger.add_item('charge_full_ah', self.charge_full,
                                    'point', 'perf')
        self._keyvallogger.add_item('charge_full_design_ah',
                                    self.charge_full_design, 'point', 'perf')
        self._keyvallogger.set_end(self._end_time)

        super(power_BatteryCharge, self).postprocess_iteration()

    def cleanup(self):
        """Restore stop services and backlight level."""
        if hasattr(self, '_services_other') and self._services_other:
            self._services_other.restore_services()
        if hasattr(self, '_backlight') and self._backlight:
            self._backlight.restore()
        super(power_BatteryCharge, self).cleanup()
