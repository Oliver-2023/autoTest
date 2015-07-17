# pylint: disable-msg=C0111

import os, shlex, sys, optparse

from autotest_lib.client.common_lib import host_protections, utils


class base_autoserv_parser(object):
    """Custom command-line options parser for autoserv.

    We can't use the general getopt methods here, as there will be unknown
    extra arguments that we pass down into the control file instead.
    Thus we process the arguments by hand, for which we are duly repentant.
    Making a single function here just makes it harder to read. Suck it up.
    """
    def __init__(self):
        self.args = sys.argv[1:]
        self.parser = optparse.OptionParser(usage="%prog [options] [control-file]")
        self.setup_options()

        # parse an empty list of arguments in order to set self.options
        # to default values so that codepaths that assume they are always
        # reached from an autoserv process (when they actually are not)
        # will still work
        self.options, self.args = self.parser.parse_args(args=[])


    def setup_options(self):
        self.parser.add_option("-m", action="store", type="string",
                               dest="machines",
                               help="list of machines")
        self.parser.add_option("-M", action="store", type="string",
                               dest="machines_file",
                               help="list of machines from file")
        self.parser.add_option("-c", action="store_true",
                               dest="client", default=False,
                               help="control file is client side")
        self.parser.add_option("-s", action="store_true",
                               dest="server", default=False,
                               help="control file is server side")
        self.parser.add_option("-r", action="store", type="string",
                               dest="results", default=None,
                               help="specify results directory")
        self.parser.add_option("-l", action="store", type="string",
                               dest="label", default='',
                               help="label for the job")
        self.parser.add_option("-G", action="store", type="string",
                               dest="group_name", default='',
                               help="The host_group_name to store in keyvals")
        self.parser.add_option("-u", action="store", type="string",
                               dest="user",
                               default=os.environ.get('USER'),
                               help="username for the job")
        self.parser.add_option("-P", action="store", type="string",
                               dest="parse_job",
                               default='',
                               help="Parse the results of the job using this "
                                    "execution tag.  Accessable in control "
                                    "files as job.tag.")
        self.parser.add_option("--execution-tag", action="store", type="string",
                               dest="execution_tag", default='',
                               help="Accessable in control files as job.tag; "
                                    "Defaults to the value passed to -P.")
        self.parser.add_option("-i", action="store_true",
                               dest="install_before", default=False,
                       help="reinstall machines before running the job")
        self.parser.add_option("-I", action="store_true",
                               dest="install_after", default=False,
                        help="reinstall machines after running the job")
        self.parser.add_option("-v", action="store_true",
                               dest="verify", default=False,
                               help="verify the machines only")
        self.parser.add_option("-R", action="store_true",
                               dest="repair", default=False,
                               help="repair the machines")
        self.parser.add_option("-C", "--cleanup", action="store_true",
                               default=False,
                               help="cleanup all machines after the job")
        self.parser.add_option("--provision", action="store_true",
                               default=False,
                               help="Provision the machine.")
        self.parser.add_option("--job-labels", action="store",
                               help="Comma seperated job labels.")
        self.parser.add_option("-T", "--reset", action="store_true",
                               default=False,
                               help="Reset (cleanup and verify) all machines"
                               "after the job")
        self.parser.add_option("-n", action="store_true",
                               dest="no_tee", default=False,
                               help="no teeing the status to stdout/err")
        self.parser.add_option("-N", action="store_true",
                               dest="no_logging", default=False,
                               help="no logging")
        self.parser.add_option('--verbose', action='store_true',
                               help='Include DEBUG messages in console output')
        self.parser.add_option('--no_console_prefix', action='store_true',
                               help='Disable the logging prefix on console '
                               'output')
        self.parser.add_option("-p", "--write-pidfile", action="store_true",
                               dest="write_pidfile", default=False,
                               help="write pidfile (pidfile name is determined "
                                    "by --pidfile-label")
        self.parser.add_option("--pidfile-label", action="store",
                               default="autoserv",
                               help="Determines filename to use as pidfile (if "
                                    "-p is specified).  Pidfile will be "
                                    ".<label>_execute.  Default to autoserv.")
        self.parser.add_option("--use-existing-results", action="store_true",
                               help="Indicates that autoserv is working with "
                                    "an existing results directory")
        self.parser.add_option("-a", "--args", dest='args',
                               help="additional args to pass to control file")
        protection_levels = [host_protections.Protection.get_attr_name(s)
                             for i, s in host_protections.choices]
        self.parser.add_option("--host-protection", action="store",
                               type="choice", dest="host_protection",
                               default=host_protections.default,
                               choices=protection_levels,
                               help="level of host protection during repair")
        self.parser.add_option("--ssh-user", action="store",
                               type="string", dest="ssh_user",
                               default="root",
                               help=("specify the user for ssh"
                               "connections"))
        self.parser.add_option("--ssh-port", action="store",
                               type="int", dest="ssh_port",
                               default=22,
                               help=("specify the port to use for "
                                     "ssh connections"))
        self.parser.add_option("--ssh-pass", action="store",
                               type="string", dest="ssh_pass",
                               default="",
                               help=("specify the password to use "
                                     "for ssh connections"))
        self.parser.add_option("--install-in-tmpdir", action="store_true",
                               dest="install_in_tmpdir", default=False,
                               help=("by default install autotest clients in "
                                     "a temporary directory"))
        self.parser.add_option("--collect-crashinfo", action="store_true",
                               dest="collect_crashinfo", default=False,
                               help="just run crashinfo collection")
        self.parser.add_option("--control-filename", action="store",
                               type="string", default=None,
                               help=("filename to use for the server control "
                                     "file in the results directory"))
        self.parser.add_option("--test-retry", action="store",
                               type="int", default=0,
                               help=("Num of times to retry a test that failed "
                                     "[default: %default]"))
        self.parser.add_option("--verify_job_repo_url", action="store_true",
                               dest="verify_job_repo_url", default=False,
                               help=("Verify that the job_repo_url of the host "
                                     "has staged packages for the job."))
        self.parser.add_option("--no_collect_crashinfo", action="store_true",
                               dest="skip_crash_collection", default=False,
                               help=("Turns off crash collection to shave time "
                                     "off test runs."))
        self.parser.add_option("--disable_sysinfo", action="store_true",
                               dest="disable_sysinfo", default=False,
                               help="Turns off sysinfo collection to shave "
                                    "time off test runs.")
        self.parser.add_option("--ssh_verbosity", action="store",
                               dest="ssh_verbosity", default=0,
                               type="choice", choices=["0", "1", "2", "3"],
                               help=("Verbosity level for ssh, between 0 "
                                     "and 3 inclusive. [default: 0]"))
        self.parser.add_option("--ssh_options", action="store",
                               dest="ssh_options", default='',
                               help=("A string giving command line flags "
                                     "that will be included in ssh commands"))
        self.parser.add_option("--require-ssp", action="store_true",
                               dest="require_ssp", default=False,
                               help=("Force the autoserv process to run with "
                                     "server-side packaging"))
        self.parser.add_option("--warn-no-ssp", action="store_true",
                               dest="warn_no_ssp", default=False,
                               help=("Post a warning in autoserv log that the "
                                     "process runs in a drone without server-"
                                     "side packaging support, even though the "
                                     "job requires server-side packaging"))
        self.parser.add_option("--no_use_packaging", action="store_true",
                               dest="no_use_packaging", default=False,
                               help=("Disable install modes that use the "
                                     "packaging system."))
        self.parser.add_option('--test_source_build', action='store',
                               type='string', default='',
                               dest='test_source_build',
                               help=('Name of the build that contains the '
                                     'test code. Default is empty, that is, '
                                     'use the build specified in --image to '
                                     'retrieve tests.'))
        self.parser.add_option('--parent_job_id', action='store',
                               type='string', default=None,
                               dest='parent_job_id',
                               help=('ID of the parent job. Default to None if '
                                     'the job does not have a parent job'))


    def parse_args(self):
        self.options, self.args = self.parser.parse_args()
        if self.options.args:
            self.args += shlex.split(self.options.args)


site_autoserv_parser = utils.import_site_class(
    __file__, "autotest_lib.server.site_autoserv_parser",
    "site_autoserv_parser", base_autoserv_parser)

class autoserv_parser(site_autoserv_parser):
    pass


# create the one and only one instance of autoserv_parser
autoserv_parser = autoserv_parser()
