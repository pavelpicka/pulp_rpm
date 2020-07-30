# coding=utf-8
"""Tests that sync rpm plugin repositories."""
import os
import unittest
from datetime import datetime
from urllib.parse import urljoin

from pulp_smash import api, config
from pulp_smash.pulp3.utils import (
    delete_orphans,
    gen_repo,
    get_added_content_summary,
    get_content,
    get_content_summary,
)

from pulp_rpm.tests.functional.constants import (
    PULP_TYPE_REPOMETADATA,
    RPM_CDN_APPSTREAM_URL,
    RPM_CDN_BASEOS_URL,
    RPM_KICKSTART_CONTENT_NAME,
    RPM_KICKSTART_FIXTURE_SUMMARY,
    RPM_KICKSTART_FIXTURE_URL,
    RPM_REMOTE_PATH,
    RPM_REPO_PATH,
    CENTOS7_URL,
    CENTOS8_APPSTREAM_URL,
    CENTOS8_BASEOS_URL,
    CENTOS8_KICKSTART_APP_URL,
    CENTOS8_KICKSTART_BASEOS_URL,
)
from pulp_rpm.tests.functional.utils import (
    gen_rpm_client,
    monitor_task,
    skip_if
)
from pulpcore.client.pulp_rpm import (
    ContentRepoMetadataFilesApi,
    RemotesRpmApi,
    RepositoriesRpmApi,
    RpmRepositorySyncURL
)
from pulp_rpm.tests.functional.utils import gen_rpm_remote
from pulp_rpm.tests.functional.utils import set_up_module as setUpModule  # noqa:F401


class CDNTestCase(unittest.TestCase):
    """Sync a repository from CDN."""

    @classmethod
    def setUpClass(cls):
        """Create class-wide variables."""
        cls.cfg = config.get_config()
        cls.client = gen_rpm_client()
        cls.repo_api = RepositoriesRpmApi(cls.client)
        cls.remote_api = RemotesRpmApi(cls.client)
        cls.repometadatafiles = ContentRepoMetadataFilesApi(cls.client)
        delete_orphans(cls.cfg)
        # Certificates processing
        cls.cdn_client_cert = False
        if os.environ['CDN_CLIENT_CERT'] \
                and os.environ['CDN_CLIENT_KEY'] \
                and os.environ['CDN_CA_CERT']:
            # strings have escaped newlines from environmental variable
            cls.cdn_client_cert = os.environ['CDN_CLIENT_CERT'].replace('\\n', '\n')
            cls.cdn_client_key = os.environ['CDN_CLIENT_KEY'].replace('\\n', '\n')
            cls.cdn_ca_cert = os.environ['CDN_CA_CERT'].replace('\\n', '\n')

    @skip_if(bool, "cdn_client_cert", False)
    def test_sync_with_certificate(self):
        """Test sync against CDN.

        1. create repository, appstream remote and sync
            - remote using certificates and tls validation
        2. create repository, baseos remote and sync
            - remote using certificates without tls validation
        3. Check both repositories were synced and both have its own 'productid' content
            - this test covering checking same repo metadata files with different relative paths
        """
        # 1. create repo, remote and sync them
        repo_appstream = self.repo_api.create(gen_repo())
        self.addCleanup(self.repo_api.delete, repo_appstream.pulp_href)

        body = gen_rpm_remote(
            url=RPM_CDN_APPSTREAM_URL,
            client_cert=self.cdn_client_cert,
            client_key=self.cdn_client_key,
            ca_cert=self.cdn_ca_cert,
            policy="on_demand"
        )
        appstream_remote = self.remote_api.create(body)
        self.addCleanup(self.remote_api.delete, appstream_remote.pulp_href)

        repository_sync_data = RpmRepositorySyncURL(remote=appstream_remote.pulp_href)
        sync_response = self.repo_api.sync(repo_appstream.pulp_href, repository_sync_data)
        monitor_task(sync_response.task)

        # 2. create remote and re-sync
        repo_baseos = self.repo_api.create(gen_repo())
        self.addCleanup(self.repo_api.delete, repo_baseos.pulp_href)

        body = gen_rpm_remote(
            url=RPM_CDN_BASEOS_URL, tls_validation=False,
            client_cert=self.cdn_client_cert,
            client_key=self.cdn_client_key,
            policy="on_demand"
        )
        baseos_remote = self.remote_api.create(body)
        self.addCleanup(self.remote_api.delete, baseos_remote.pulp_href)

        repository_sync_data = RpmRepositorySyncURL(remote=baseos_remote.pulp_href)
        sync_response = self.repo_api.sync(repo_baseos.pulp_href, repository_sync_data)
        monitor_task(sync_response.task)

        # Get all 'productid' repo metadata files
        productids = [productid for productid in self.repometadatafiles.list().results if
                      productid.data_type == 'productid']

        # Update repositories info
        repo_baseos_dict = self.repo_api.read(repo_baseos.pulp_href).to_dict()
        repo_appstream_dict = self.repo_api.read(repo_appstream.pulp_href).to_dict()

        # Assert there are two productid content units and they have same checksum
        self.assertEqual(
            len(productids), 2
        )
        self.assertEqual(
            productids[0].checksum, productids[1].checksum
        )
        # Assert each repository has latest version 1 (it was synced)
        self.assertEqual(
            repo_appstream_dict['latest_version_href'].rstrip('/')[-1],
            '1'
        )
        self.assertEqual(
            repo_baseos_dict['latest_version_href'].rstrip('/')[-1],
            '1'
        )
        # Assert each repository has its own productid file
        self.assertEqual(
            get_content_summary(repo_appstream_dict)[PULP_TYPE_REPOMETADATA],
            1
        )
        self.assertEqual(
            get_content_summary(repo_baseos_dict)[PULP_TYPE_REPOMETADATA],
            1
        )
        self.assertNotEqual(
            get_content(repo_appstream_dict)[PULP_TYPE_REPOMETADATA][0]['relative_path'],
            get_content(repo_baseos_dict)[PULP_TYPE_REPOMETADATA][0]['relative_path']
        )
