from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from game.models import MediaFile


class MediaFileUploadTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()

    def create_test_file(self, name="test.jpg", size=1024):
        """Create a simple test file in memory."""
        content = b"x" * size
        return SimpleUploadedFile(name, content, content_type="application/octet-stream")

    def test_upload_valid_file(self):
        """Test uploading a valid file."""
        test_file = self.create_test_file("image.jpg", 2048)

        response = self.client.post("/api/media/", {"file": test_file}, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("id", response.data)
        self.assertIn("url", response.data)
        self.assertIn("original_filename", response.data)
        self.assertIn("file_size", response.data)
        self.assertIn("uploaded_at", response.data)

        self.assertEqual(response.data["original_filename"], "image.jpg")
        self.assertEqual(response.data["file_size"], 2048)

        self.assertTrue(MediaFile.objects.filter(id=response.data["id"]).exists())

    def test_upload_large_file(self):
        """Test uploading a file that exceeds size limit."""
        large_file = self.create_test_file("large.jpg", 101 * 1024 * 1024)

        response = self.client.post("/api/media/", {"file": large_file}, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("file", response.data)

    def test_upload_without_file(self):
        """Test uploading without providing a file."""
        response = self.client.post("/api/media/", {}, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_media_files(self):
        """Test listing uploaded media files."""
        file1 = self.create_test_file("file1.jpg", 1024)
        file2 = self.create_test_file("file2.mp4", 2048)

        self.client.post("/api/media/", {"file": file1}, format="multipart")
        self.client.post("/api/media/", {"file": file2}, format="multipart")

        response = self.client.get("/api/media/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

        filenames = [item["original_filename"] for item in response.data]
        self.assertIn("file1.jpg", filenames)
        self.assertIn("file2.mp4", filenames)

    def test_url_generation(self):
        """Test that uploaded files have accessible URLs."""
        test_file = self.create_test_file("test.jpg", 512)

        response = self.client.post("/api/media/", {"file": test_file}, format="multipart")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("url", response.data)
        self.assertIsNotNone(response.data["url"])
        self.assertIn("/media/uploads/", response.data["url"])
        self.assertIn(".jpg", response.data["url"])
