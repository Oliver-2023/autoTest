import commands, math, re
from autotest_lib.client.bin import test
from autotest_lib.client.common_lib import error

class build_RootFilesystemSize(test.test):
    version = 1


    def run_once(self):
        # Report the production size
        f = open('/root/bytes-rootfs-prod', 'r')
        self.write_perf_keyval({'bytes_rootfs_prod': float(f.read())})
        f.close()

        # Report the current (test) size
        (status, output) = commands.getstatusoutput(
            'df -B1 / | tail -1')
        if status != 0:
            raise error.TestFail('Could not get size of rootfs')

        # Expected output format:
        # rootfs    1056858112 768479232 288378880 73% /
        output_columns = output.split()
        used = output_columns[2]
        free = output_columns[3]

        self.write_perf_keyval({'bytes_rootfs_test': float(used)})

        # Make sure we have at least 100M free on rootfs as warning if
        # we are running out.
        required_free_space = 100 * 1024 * 1024

        if int(free) < required_free_space:
          raise error.TestFail('%s bytes free is less than the %s required.' %
                               (free, required_free_space))
