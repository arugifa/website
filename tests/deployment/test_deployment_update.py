from datetime import datetime

import pytest

from website.deployment import exceptions


class TestCloudFilesManager:
    @pytest.fixture
    def static_files(self, tmp_path):
        file_1 = tmp_path / 'hello_world.txt'
        file_1.write_text("Hello, World!")

        file_2 = tmp_path / 'john_doe.txt'
        file_2.write_text("I'm John Doe.")

        file_3 = tmp_path / 'house_music.txt'
        file_3.write_text("I love to dance all night long...")

        return [file_1, file_2, file_3]

    # Upload file.

    async def test_upload_file(self, object_store, static_files):
        upload = await object_store.upload(static_files[0])
        assert upload.name == str(static_files[0])

    async def test_upload_file_with_different_name(self, object_store, static_files):
        upload = await object_store.upload(static_files[0], 'static/new_name.txt')  # noqa: E501
        assert upload.name == 'static/new_name.txt'

    async def test_upload_not_existing_file(self, object_store, tmp_path):
        static_file = tmp_path / 'missing.txt'

        with pytest.raises(OSError):
            await object_store.upload(static_file)

    async def test_error_happening_during_file_upload(
            self, network, object_store, static_files):
        with network.unplug(), pytest.raises(exceptions.CloudUploadError):
            await object_store.upload(static_files[0])

    # Download file.

    async def test_download_file(self, object_store, static_files):
        await object_store.upload(static_files[0], 'download.txt')
        data = await object_store.download('download.txt')
        assert data == b"Hello, World!"

    async def test_download_not_existing_file(self, object_store):
        with pytest.raises(exceptions.CloudFileNotFound):
            await object_store.download('missing.txt')

    async def test_error_happening_during_download(self, network, object_store):
        with network.unplug(), pytest.raises(exceptions.CloudError):
            await object_store.download('outage.txt')

    # Compute file's MD5 hash.

    async def test_compute_md5_hash(self, object_store, static_files):
        md5_hash = await object_store.md5sum(static_files[0])
        assert md5_hash == '65a8e27d8879283831b664bd8b7f0ad4'

    async def test_compute_md5_hash_of_not_existing_file(
            self, object_store, tmp_path):
        static_file = tmp_path / 'missing.txt'

        with pytest.raises(OSError):
            await object_store.md5sum(static_file)

    # Add files.

    def test_add_files(self, object_store, static_files):
        objs = object_store.add(static_files)

        assert len(objs) == 3

        assert objs[0].name == str(static_files[0])
        assert objs[0].data == b"Hello, World!"

        assert objs[1].name == str(static_files[2])
        assert objs[1].data == b"I love to dance all night long..."

        assert objs[2].name == str(static_files[1])
        assert objs[2].data == b"I'm John Doe."

    def test_add_files_with_new_names(self, object_store, static_files):
        static_files = [
            (static_files[0], 'static/hello_world.txt'),
            (static_files[1], 'static/john_doe.txt'),
        ]

        objs = object_store.add(static_files)

        assert len(objs) == 2

        assert objs[0].name == 'static/hello_world.txt'
        assert objs[0].data == b"Hello, World!"

        assert objs[1].name == 'static/john_doe.txt'
        assert objs[1].data == b"I'm John Doe."

    def test_add_file_with_missing_source(self, object_store, tmp_path):
        static_file = tmp_path / 'missing.txt'

        with pytest.raises(OSError):
            object_store.add([static_file])

    # Replace files.

    def test_replace_files(self, object_store, static_files):
        # Fixtures
        object_store.add(static_files)
        timestamp = datetime.now().isoformat()

        static_files[0].write_text("Hello, Galaxy!")
        static_files[1].write_text("I'm Jane Doe.")

        # Test
        objs = object_store.replace(static_files)

        assert len(objs) == 2

        assert objs[0].name == str(static_files[0])
        assert objs[0].data == b"Hello, Galaxy!"
        assert objs[0].last_modified_at > timestamp

        assert objs[1].name == str(static_files[1])
        assert objs[1].data == b"I'm Jane Doe."
        assert objs[1].last_modified_at > timestamp

    def test_replace_files_with_different_names(
            self, object_store, static_files):
        # Fixtures
        static_files = [
            (static_files[0], 'static/hello_world.txt'),
            (static_files[1], 'static/john_doe.txt'),
        ]
        object_store.add(static_files)
        timestamp = datetime.now().isoformat()

        # Test
        static_files[0][0].write_text("Hello, Galaxy!")
        static_files[1][0].write_text("I'm Jane Doe.")

        objs = object_store.replace(static_files)

        assert len(objs) == 2

        assert objs[0].name == 'static/hello_world.txt'
        assert objs[0].data == b"Hello, Galaxy!"
        assert objs[0].last_modified_at > timestamp

        assert objs[1].name == 'static/john_doe.txt'
        assert objs[1].data == b"I'm Jane Doe."
        assert objs[1].last_modified_at > timestamp

    def test_only_replace_files_with_changes(self, object_store, static_files):
        assert len(static_files) > 1
        object_store.add(static_files)
        timestamp = datetime.now().isoformat()

        static_files[0].write_text("Hello, Galaxy!")
        objs = object_store.replace(static_files)

        assert len(objs) == 1
        assert objs[0].name == str(static_files[0])
        assert objs[0].data == b"Hello, Galaxy!"
        assert objs[0].last_modified_at > timestamp

    def test_replace_not_existing_files(self, object_store, static_files):
        with pytest.raises(exceptions.CloudFileNotFound):
            object_store.replace(static_files)

    def test_replace_file_with_missing_source(self, object_store, tmp_path):
        static_file = tmp_path / 'deleted.txt'
        static_file.touch()

        object_store.add([static_file])
        static_file.unlink()

        with pytest.raises(OSError):
            object_store.replace([static_file])

    def test_error_happening_during_replacement(
            self, network, object_store, static_files):
        with network.unplug(), pytest.raises(exceptions.CloudError):
            object_store.replace(static_files)

    # Delete files.

    def test_delete_files(self, object_store, static_files):
        object_store.add(static_files)
        object_store.delete(static_files)

        with pytest.raises(exceptions.CloudFileNotFound):
            object_store.delete(static_files[:1])

        with pytest.raises(exceptions.CloudFileNotFound):
            object_store.delete(static_files[-1:])

    def test_delete_not_existing_file(self, object_store):
        with pytest.raises(exceptions.CloudFileNotFound):
            object_store.delete(['missing.txt'])

    def test_error_happening_during_deletion(self, network, object_store):
        with network.unplug(), pytest.raises(exceptions.CloudError):
            object_store.delete(['outage.txt'])
