"""
Lookup table for all the device policies. Moved from enterprise_policy_base.py
to a stand alone file for readability/maintainability. Source is
policy_templates.json, and this file will need to be periodically updated if new
device policies are added to the proto.
"""
# TODO b:169251326 terms below are set outside of this codebase
# and should be updated when possible.
# ("whitelist" -> "allowlist", "blacklist" --> "blocklist" or "denylist") # nocheck
DEVICE_POLICY_DICT = {
    'DeviceGuestModeEnabled': 'guest_mode_enabled.guest_mode_enabled',
    'DeviceRebootOnShutdown': 'reboot_on_shutdown.reboot_on_shutdown',
    'DeviceShowUserNamesOnSignin': 'show_user_names.show_user_names',
    'DeviceAllowNewUsers': 'allow_new_users.allow_new_users',
    'DeviceUserWhitelist': 'user_whitelist.user_whitelist', # nocheck
    'DeviceEphemeralUsersEnabled': 'ephemeral_users_enabled.ephemeral_users_enabled',
    'LoginAuthenticationBehavior': 'login_authentication_behavior.login_authentication_behavior',
    'DeviceAllowBluetooth': 'allow_bluetooth.allow_bluetooth',
    'DeviceLoginScreenExtensions': 'device_login_screen_extensions.device_login_screen_extensions',
    'DeviceLoginScreenDomainAutoComplete': 'login_screen_domain_auto_complete.login_screen_domain_auto_complete',
    'DeviceLoginScreenLocales': 'login_screen_locales.login_screen_locales',
    'DeviceLoginScreenInputMethods': 'login_screen_input_methods.login_screen_input_methods',
    'DeviceSamlLoginAuthenticationType': 'saml_login_authentication_type.saml_login_authentication_type',
    'DeviceDataRoamingEnabled': 'data_roaming_enabled.data_roaming_enabled',
    'AllowKioskAppControlChromeVersion': 'allow_kiosk_app_control_chrome_version.allow_kiosk_app_control_chrome_version',
    'DevicePolicyRefreshRate': 'device_policy_refresh_rate.device_policy_refresh_rate',
    'DeviceMetricsReportingEnabled': 'metrics_enabled.metrics_enabled',
    'SystemUse24HourClock': 'use_24hour_clock.use_24hour_clock',
    'UptimeLimit': 'uptime_limit.uptime_limit',
    'DeviceAllowRedeemChromeOsRegistrationOffers': 'allow_redeem_offers.allow_redeem_offers',
    'ExtensionCacheSize': 'extension_cache_size.extension_cache_size',
    'DisplayRotationDefault': 'display_rotation_default.display_rotation_default',
    'DeviceQuirksDownloadEnabled': 'quirks_download_enabled.quirks_download_enabled',
    'UnaffiliatedArcAllowed': 'unaffiliated_arc_allowed.unaffiliated_arc_allowed',
    'VirtualMachinesAllowed': 'virtual_machines_allowed.virtual_machines_allowed',
    'DeviceUnaffiliatedCrostiniAllowed': 'device_unaffiliated_crostini_allowed.device_unaffiliated_crostini_allowed',
    'PluginVmAllowed': 'plugin_vm_allowed.plugin_vm_allowed',
    'DeviceLoginScreenAutoSelectCertificateForUrls': 'device_login_screen_auto_select_certificate_for_urls.login_screen_auto_select_certificate_rules',
    'DeviceWiFiFastTransitionEnabled': 'device_wifi_fast_transition_enabled.enabled',
    'DeviceTransferSAMLCookies': 'saml_settings.transfer_saml_cookies',
    'LoginVideoCaptureAllowedUrls': 'login_video_capture_allowed_urls.urls',
    'DeviceHostnameTemplate': 'network_hostname.device_hostname_template',
    'DeviceKerberosEncryptionTypes': 'device_kerberos_encryption_types.types',
    'LogUploadEnabled': 'device_log_upload_settings.system_log_upload_enabled',
    'DeviceVariationsRestrictParameter': 'variations_parameter.parameter',
    'DeviceBlockDevmode': 'system_settings.block_devmode',
    'DeviceSecondFactorAuthentication': 'device_second_factor_authentication.mode',
    'CastReceiverName': 'cast_receiver_name.name',
    'DeviceNativePrintersAccessMode': 'native_device_printers_access_mode.access_mode',
    'MinimumRequiredChromeVersion': 'minimum_required_version.chrome_version',
    'DeviceUserPolicyLoopbackProcessingMode': 'device_user_policy_loopback_processing_mode.mode',
    'DeviceLoginScreenIsolateOrigins': 'device_login_screen_isolate_origins.isolate_origins',
    'DeviceLoginScreenSitePerProcess': 'device_login_screen_site_per_process.site_per_process',
    'DeviceMachinePasswordChangeRate': 'device_machine_password_change_rate.rate_days',
    'DeviceNativePrintersBlacklist': 'native_device_printers_blacklist.blacklist', # nocheck
    'DeviceNativePrintersWhitelist': 'native_device_printers_whitelist.whitelist', # nocheck
    'DevicePrintersBlocklist': 'device_printers_blocklist.blocklist',
    'DevicePrintersAllowlist': 'device_printers_allowlist.allowlist',
    'HeartbeatEnabled': 'device_heartbeat_settings.heartbeat_enabled',
    'HeartbeatFrequency': 'device_heartbeat_settings.heartbeat_frequency',
    'ChromeOsReleaseChannel': 'release_channel.release_channel',
    'ChromeOsReleaseChannelDelegated': 'release_channel.release_channel_delegated',
    'DeviceAutoUpdateDisabled': 'auto_update_settings.update_disabled',
    'DeviceTargetVersionPrefix': 'auto_update_settings.target_version_prefix',
    'DeviceRollbackToTargetVersion': 'auto_update_settings.rollback_to_target_version',
    'DeviceRollbackAllowedMilestones': 'auto_update_settings.rollback_allowed_milestones',
    'DeviceUpdateScatterFactor': 'auto_update_settings.scatter_factor_in_seconds',
    'DeviceUpdateHttpDownloadsEnabled': 'auto_update_settings.http_downloads_enabled',
    'RebootAfterUpdate': 'auto_update_settings.reboot_after_update',
    'DeviceAutoUpdateP2PEnabled': 'auto_update_settings.p2p_enabled',
    'DeviceLoginScreenDefaultLargeCursorEnabled': 'accessibility_settings.login_screen_default_large_cursor_enabled',
    'DeviceLoginScreenLargeCursorEnabled': 'accessibility_settings.login_screen_large_cursor_enabled',
    'DeviceLoginScreenDefaultSpokenFeedbackEnabled': 'accessibility_settings.login_screen_default_spoken_feedback_enabled',
    'DeviceLoginScreenDefaultHighContrastEnabled': 'accessibility_settings.login_screen_default_high_contrast_enabled',
    'DeviceLoginScreenDefaultScreenMagnifierType': 'accessibility_settings.login_screen_default_screen_magnifier_type',
    'DeviceLoginScreenDefaultVirtualKeyboardEnabled': 'accessibility_settings.login_screen_default_virtual_keyboard_enabled',
    'AttestationEnabledForDevice': 'attestation_settings.attestation_enabled',
    'AttestationForContentProtectionEnabled': 'attestation_settings.content_protection_enabled',
    'SystemTimezone': 'system_timezone.timezone',
    'SystemTimezoneAutomaticDetection': 'system_timezone.timezone_detection_type',
    'ReportDeviceActivityTimes': 'device_reporting.report_activity_times',
    'ReportDeviceBootMode': 'device_reporting.report_boot_mode',
    'ReportDeviceLocation': 'device_reporting.report_location',
    'ReportDeviceNetworkInterfaces': 'device_reporting.report_network_interfaces',
    'ReportDeviceUsers': 'device_reporting.report_users',
    'ReportDeviceHardwareStatus': 'device_reporting.report_hardware_status',
    'ReportDeviceSessionStatus': 'device_reporting.report_session_status',
    'ReportDeviceVersionInfo': 'device_reporting.report_version_info',
    'ReportUploadFrequency': 'device_reporting.device_status_frequency',
    'NetworkThrottlingEnabled': 'network_throttling.enabled',
    'NetworkThrottlingEnabled': 'network_throttling.upload_rate_kbits',
    'NetworkThrottlingEnabled': 'network_throttling.download_rate_kbits',
    'DeviceLoginScreenPowerManagement': 'login_screen_power_management.login_screen_power_management',
    'DeviceDisplayResolution': 'device_display_resolution.device_display_resolution',
    'DeviceWallpaperImage': 'device_wallpaper_image.device_wallpaper_image',
    'DeviceNativePrinters': 'native_device_printers.external_policy',
    'DeviceAutoUpdateTimeRestrictions': 'auto_update_settings.disallowed_time_intervals',
    'DeviceUpdateStagingSchedule': 'auto_update_settings.staging_schedule',
    'DeviceLocalAccounts': 'device_local_accounts.account',
    'DeviceLocalAccountAutoLoginId': 'device_local_accounts.auto_login_id',
    'DeviceLocalAccountAutoLoginDelay': 'device_local_accounts.auto_login_delay',
    'DeviceLocalAccountAutoLoginBailoutEnabled': 'device_local_accounts.enable_auto_login_bailout',
    'DeviceLocalAccountPromptForNetworkWhenOffline': 'device_local_accounts.prompt_for_network_when_offline',
    'DevicePowerPeakShiftEnabled': 'device_power_peak_shift.enabled',
    'DevicePowerPeakShiftBatteryThreshold': 'device_power_peak_shift.battery_threshold',
    'DevicePowerPeakShiftDayConfig': 'device_power_peak_shift.day_configs',
    'DeviceWilcoDtcAllowed': 'device_wilco_dtc_allowed.device_wilco_dtc_allowed',
    'DeviceWilcoDtcConfiguration': 'device_wilco_dtc_configuration.device_wilco_dtc_configuration',
    'PluginVmLicenseKey': 'plugin_vm_license_key.plugin_vm_license_key',
    'DeviceAuthDataCacheLifetime': 'device_auth_data_cache_lifetime.lifetime_hours',
    'DeviceGpoCacheLifetime': 'device_gpo_cache_lifetime.lifetime_hours',
    'DeviceRebootOnUserSignout': 'device_reboot_on_user_signout.reboot_on_signout_mode',
    'DeviceEcryptfsMigrationStrategy': 'device_ecryptfs_migration_strategy.migration_strategy',
    'DeviceWiFiFastTransitionEnabled': 'device_wifi_fast_transition_enabled.device_wifi_fast_transition_enabled',
    'DeviceWiFiAllowed': 'device_wifi_allowed.device_wifi_allowed',
    'AutoCleanUpStrategy': 'auto_clean_up_settings.clean_up_strategy',
    'SupervisedUsersEnabled': 'supervised_users_settings.supervised_users_enabled',
    'DeviceStartUpFlags': 'start_up_flags.flags',
    'ReportDeviceBoardStatus': 'device_reporting.report_board_status',
    'ReportDeviceStorageStatus': 'device_reporting.report_storage_status',
    'ReportDevicePowerStatus': 'device_reporting.report_power_status',
    'DeviceOpenNetworkConfiguration': 'open_network_configuration.open_network_configuration',
    'DeviceBootOnAcEnabled': 'device_boot_on_ac.enabled',
    'DeviceQuickFixBuildToken': 'auto_update_settings.device_quick_fix_build_token',
    'DeviceDockMacAddressSource': 'device_dock_mac_address_source.source',
    'DeviceUsbPowerShareEnabled': 'device_usb_power_share.enabled',
    'DeviceAdvancedBatteryChargeModeEnabled': 'device_advanced_battery_charge_mode.enabled',
    'DeviceAdvancedBatteryChargeModeDayConfig': 'device_advanced_battery_charge_mode.day_configs',
    'DeviceBatteryChargeMode': 'device_battery_charge_mode.battery_charge_mode',
    'DeviceBatteryChargeCustomStartCharging': 'device_battery_charge_mode.custom_charge_start',
    'DeviceBatteryChargeCustomStopCharging': 'device_battery_charge_mode.custom_charge_stop',
    'DeviceScheduledUpdateCheck': 'device_scheduled_update_check.device_scheduled_update_check_settings',
    'DevicePrinters': 'device_printers.external_policy',
    'DevicePrintersAccessMode': 'device_printers_access_mode.access_mode',
    'DevicePrintersBlocklist': 'device_printers_blocklist.blocklist',
    'DevicePrintersAllowlist': 'device_printers_allowlist.allowlist'
}
