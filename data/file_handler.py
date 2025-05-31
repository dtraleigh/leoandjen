import logging
import os
import tempfile
from datetime import datetime
from django.core.files import File
from django.core.files.storage import default_storage

logger = logging.getLogger("django")

def save_uploaded_file_to_temporary(uploaded_file):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        for chunk in uploaded_file.chunks():
            tmp_file.write(chunk)

        logger.info(f"Original temp file saved to: {tmp_file.name}")

        return tmp_file.name

def rename_file_on_disk(original_temp_path, new_filename):
        temp_dir = os.path.dirname(original_temp_path)
        new_local_temp_path = os.path.join(temp_dir, new_filename)
        os.rename(original_temp_path, new_local_temp_path)
        logger.info(f"Renamed file from {original_temp_path} to {new_local_temp_path}")
        return new_local_temp_path

def create_unique_filename(uploaded_file_name):
    original_name, ext = os.path.splitext(uploaded_file_name)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{original_name}_{timestamp}{ext}"