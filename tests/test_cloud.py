import pytest

from website import exceptions


class TestCloudManager:
    @pytest.fixture(scope='class')
    def static_file(self, fixtures):
        return fixtures['document.html']

    def test_upload_file(self, cloud_manager, static_file):
        upload = cloud_manager.upload(static_file, 'index.html')
        assert upload.name == 'index.html'

    def test_failure_during_file_upload(
            self, cloud, cloud_manager, static_file):
        with cloud.unplug(), pytest.raises(exceptions.CloudUploadError):
            cloud_manager.upload(static_file, 'failure.html')
