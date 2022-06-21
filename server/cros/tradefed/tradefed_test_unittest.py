# Lint as: python2, python3
# Copyright 2022 The Chromium OS Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import unittest
import os
import tempfile
import shutil

from unittest.mock import Mock, ANY, patch
from autotest_lib.server.cros.tradefed import tradefed_test


class TradefedTestTest(unittest.TestCase):
    """Tests for TradefedTest class."""

    def setUp(self):
        self._mockjob_tmpdirs = []
        self._bindir = tempfile.mkdtemp()
        self._outputdir = tempfile.mkdtemp()
        self.tradefed = tradefed_test.TradefedTest(self.create_mock_job(),
                                                   self._bindir,
                                                   self._outputdir)

    def tearDown(self):
        shutil.rmtree(self._bindir)
        shutil.rmtree(self._outputdir)
        for tmpdir in self._mockjob_tmpdirs:
            shutil.rmtree(tmpdir)

    def create_mock_job(self):
        """Creates a mock necessary for constructing tradefed_test instance."""
        mock_job = Mock()
        mock_job.pkgmgr = None
        mock_job.autodir = None
        mock_job.tmpdir = tempfile.mkdtemp()
        self._mockjob_tmpdirs.append(mock_job.tmpdir)
        return mock_job

    # Verify that parsing gsutil ls -L output correctly extracts the ETag and
    # returns in hex.
    @patch('autotest_lib.server.utils.run')
    def test_parse_ETag(self, mock_run):
        mock_run.return_value = Mock(
                stdout="""gs://path/to/a.zip:
                        Creation time:          Wed, 15 Jun 2022 16:53:14 GMT
                        Update time:            Wed, 15 Jun 2022 16:53:14 GMT
                        Storage class:          STANDARD
                        Content-Language:       en
                        Content-Length:         201832881
                        Content-Type:           application/zip
                        Hash (crc32c):          TN1ctw==
                        Hash (md5):             ZArA7Yt7EREmkFmTanLHdA==
                        ETag:                   COOOrtv1r/gCEAE=
                        TOTAL: 1 objects, 201832881 bytes (192.48 MiB) """)
        etag_hex = tradefed_test._GetETagFromGsUri('gs://path/to/a.zip')
        self.assertEqual(etag_hex, '434f4f4f72747631722f67434541453d')

    # For the first time, it should call _download_to_dir to download the
    # bundle.
    @patch('autotest_lib.server.cros.tradefed.tradefed_test.TradefedTest._download_to_dir'
           )
    @patch('autotest_lib.server.utils.run')
    @patch('os.path.exists')
    def test_download_to_cache_initial_download(self, mock_exists, mock_run,
                                                mock_download_to_dir):
        mock_run.return_value = Mock(
                stdout='ETag: COOOrtv1r/gCEAE=')
        mock_exists.return_value = False

        self.tradefed._tradefed_cache = '/any/test/dir'

        self.tradefed._download_to_cache(
                'gs://some-fake-bucket/path/to/bundle.zip')

        mock_download_to_dir.assert_called_with(
                'gs://some-fake-bucket/path/to/bundle.zip',
                os.path.join(self.tradefed._tradefed_cache,
                             '434f4f4f72747631722f67434541453d'))

        mock_run.assert_called_with(
                'gsutil',
                args=('ls', '-L',
                      'gs://some-fake-bucket/path/to/bundle.zip'),
                verbose=ANY)

    # Redownload a same-name-bundle that had been downloaded, but different
    # Etag.
    @patch('autotest_lib.server.cros.tradefed.tradefed_test.TradefedTest._download_to_dir'
           )
    @patch('autotest_lib.server.utils.run')
    @patch('os.path.exists')
    def test_download_to_cache_same_google_storage_path_different_bundle(
            self, mock_exists, mock_run, mock_download_to_dir):
        mock_run.return_value = Mock(
                stdout='ETag: COOOrtv1r/gCEAE=')

        # Let os.path.exist return false. Must also check what value was passed to the mock (below).
        mock_exists.return_value = False

        self.tradefed._tradefed_cache = '/any/test/dir'

        self.tradefed._download_to_cache(
                'gs://some-fake-bucket/path/to/bundle.zip')

        mock_download_to_dir.assert_called_with(
                'gs://some-fake-bucket/path/to/bundle.zip',
                os.path.join(self.tradefed._tradefed_cache,
                             '434f4f4f72747631722f67434541453d'))

        mock_exists.assert_called_with(
                os.path.join(self.tradefed._tradefed_cache,
                             '434f4f4f72747631722f67434541453d'))

        # Now let it return a different hash value, for the same path.
        mock_run.return_value = Mock(
                stdout='ETag: SomeOtherEtag')
        self.tradefed._download_to_cache(
                'gs://some-fake-bucket/path/to/bundle.zip')

        # Verify that os.path.exists was called with different values than the
        # first time.
        mock_exists.assert_called_with(
                os.path.join(self.tradefed._tradefed_cache,
                             '536f6d654f7468657245746167'))

    @patch('autotest_lib.server.cros.tradefed.tradefed_test.TradefedTest._download_to_dir'
           )
    @patch('hashlib.md5')
    @patch('os.path.exists')
    def test_download_to_cache_non_google_storage(self, mock_exists, mock_md5,
                                                  mock_download_to_dir):
        mock_exists.return_value = False
        mock_md5.return_value.hexdigest.return_value = '6ae0e7fc911c1b310d85c0d9fa592c08'

        self.tradefed._tradefed_cache = '/any/test/dir'

        self.tradefed._download_to_cache(
                'https://dl.google.com/dl/android/xts/bundle.zip')

        mock_exists.assert_called_with(
                os.path.join(self.tradefed._tradefed_cache,
                             '6ae0e7fc911c1b310d85c0d9fa592c08'))

        mock_download_to_dir.assert_called_with(
                'https://dl.google.com/dl/android/xts/bundle.zip',
                os.path.join(self.tradefed._tradefed_cache,
                             '6ae0e7fc911c1b310d85c0d9fa592c08'))

    # Verify that downloaded bundles is not redownloaded.
    @patch('autotest_lib.server.cros.tradefed.tradefed_test.TradefedTest._download_to_dir'
           )
    @patch('hashlib.md5')
    @patch('os.path.exists')
    @patch('os.listdir')
    def test_download_to_cache_same_hash(self, mock_listdir, mock_exists,
                                         mock_md5, mock_download_to_dir):
        # os.path.exists returning true means it has been downloaded.
        mock_exists.return_value = True
        mock_md5.return_value.hexdigest.return_value = '6ae0e7fc911c1b310d85c0d9fa592c08'
        mock_listdir.return_value = ['non', 'empty', 'list']

        self.tradefed._tradefed_cache = '/any/test/dir'

        self.tradefed._download_to_cache(
                'https://dl.google.com/dl/android/xts/bundle.zip')

        mock_exists.assert_called_with(
                os.path.join(self.tradefed._tradefed_cache,
                             '6ae0e7fc911c1b310d85c0d9fa592c08'))

        mock_download_to_dir.assert_not_called()

    # The path exists but the output dir is empty. It should redownload.
    @patch('autotest_lib.server.cros.tradefed.tradefed_test.TradefedTest._download_to_dir'
           )
    @patch('hashlib.md5')
    @patch('os.path.exists')
    @patch('os.listdir')
    def test_download_to_cache_same_hash_empty_listdir(self, mock_listdir,
                                                       mock_exists, mock_md5,
                                                       mock_download_to_dir):
        mock_exists.return_value = True
        mock_md5.return_value.hexdigest.return_value = '6ae0e7fc911c1b310d85c0d9fa592c08'
        mock_listdir.return_value = []

        self.tradefed._tradefed_cache = '/any/test/dir'

        self.tradefed._download_to_cache(
                'https://dl.google.com/dl/android/xts/bundle.zip')

        mock_exists.assert_called_with(
                os.path.join(self.tradefed._tradefed_cache,
                             '6ae0e7fc911c1b310d85c0d9fa592c08'))

        mock_download_to_dir.assert_called()

    # Verify that an exception is raised if there isn't an ETag in the gsutil
    # output.
    @patch('autotest_lib.server.utils.run')
    def test_failed_to_find_ETag(self, mock_run):
        mock_run.return_value = Mock(
                stdout='This message does not contain an ETag.')
        self.assertRaises(tradefed_test.ETagNotFoundException,
                          tradefed_test._GetETagFromGsUri,
                          'gs://anything/here')
