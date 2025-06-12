from django.core.management.base import BaseCommand
from django.core.files.uploadedfile import InMemoryUploadedFile
from pathlib import Path
from django.core.files.uploadedfile import SimpleUploadedFile

from auth_app.utils import upload_to_cloudinary


class Command(BaseCommand):
    help = 'Test Cloudinary image upload'

    def handle(self, *args, **kwargs):
        # Simulate reading an image file (replace with a real image path)
        with open("auth_app/management/commands/test_image.png", "rb") as f:
            file_data = SimpleUploadedFile("auth_app/management/commands/test_image.png", f.read(), content_type="image/png")
            try:
                url = upload_to_cloudinary(file_data)
                print("Upload successful! URL:", url)
            except Exception as e:
                print("Upload failed:", e)