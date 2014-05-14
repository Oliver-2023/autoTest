#pylint: disable-msg=C0111

# Copyright (c) 2014 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

"""Scheduler helper libraries.
"""
import logging

import common

from autotest_lib.client.common_lib import logging_config
from autotest_lib.client.common_lib import logging_manager
from autotest_lib.database import database_connection
from autotest_lib.frontend import setup_django_environment
from autotest_lib.frontend.afe import readonly_connection


DB_CONFIG_SECTION = 'AUTOTEST_WEB'


class SchedulerError(Exception):
    """Raised by the scheduler when an inconsistent state occurs."""


class Singleton(type):
    """Enforce that only one client class is instantiated per process."""
    _instances = {}

    def __call__(cls, *args, **kwargs):
        """Fetch the instance of a class to use for subsequent calls."""
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(
                    *args, **kwargs)
        return cls._instances[cls]


class ConnectionManager(object):
    """Manager for the django database connections.

    The connection is used through scheduler_models and monitor_db.
    """
    __metaclass__ = Singleton

    def __init__(self, readonly=False, autocommit=True):
        """Set global django database options for correct connection handling.

        @param readonly: Globally disable readonly connections.
        @param autocommit: Initialize django autocommit options.
        """
        self.db_connection = None
        # bypass the readonly connection
        readonly_connection.ReadOnlyConnection.set_globally_disabled(readonly)
        if autocommit:
            # ensure Django connection is in autocommit
            setup_django_environment.enable_autocommit()


    @classmethod
    def open_connection(cls):
        """Open a new database connection.

        @return: An instance of the newly opened connection.
        """
        db = database_connection.DatabaseConnection(DB_CONFIG_SECTION)
        db.connect(db_type='django')
        return db


    def get_connection(self):
        """Get a connection.

        @return: A database connection.
        """
        if self.db_connection is None:
            self.db_connection = self.open_connection()
        return self.db_connection


    def disconnect(self):
        """Close the database connection."""
        try:
            self.db_connection.disconnect()
        except Exception as e:
            logging.debug('Could not close the db connection. %s', e)


    def __del__(self):
        self.disconnect()


class SchedulerLoggingConfig(logging_config.LoggingConfig):
    """Configure timestamped logging for a scheduler."""
    GLOBAL_LEVEL = logging.INFO

    @classmethod
    def get_log_name(cls, timestamped_logfile_prefix):
        """Get the name of a logfile.

        @param timestamped_logfile_prefix: The prefix to apply to the
            a timestamped log. Eg: 'scheduler' will create a logfile named
            scheduler.log.2014-05-12-17.24.02.

        @return: The timestamped log name.
        """
        return cls.get_timestamped_log_name(timestamped_logfile_prefix)


    def configure_logging(self, log_dir=None, logfile_name=None,
                          timestamped_logfile_prefix='scheduler'):
        """Configure logging to a specified logfile.

        @param log_dir: The directory to log into.
        @param logfile_name: The name of the log file.
        @timestamped_logfile_prefix: The prefix to apply to the name of
            the logfile, if a log file name isn't specified.
        """
        super(SchedulerLoggingConfig, self).configure_logging(use_console=True)

        if log_dir is None:
            log_dir = self.get_server_log_dir()
        if not logfile_name:
            logfile_name = self.get_log_name(timestamped_logfile_prefix)

        self.add_file_handler(logfile_name, logging.DEBUG, log_dir=log_dir)


def setup_logging(log_dir, log_name, timestamped_logfile_prefix='scheduler'):
    """Setup logging to a given log directory and log file.

    @param log_dir: The directory to log into.
    @param log_name: Name of the log file.
    @param timestamped_logfile_prefix: The prefix to apply to the logfile.
    """
    logging_manager.configure_logging(
            SchedulerLoggingConfig(), log_dir=log_dir, logfile_name=log_name,
            timestamped_logfile_prefix=timestamped_logfile_prefix)
