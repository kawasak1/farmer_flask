import os
from werkzeug.utils import secure_filename
from flask import current_app
import uuid

def allowed_file(filename, allowed_extensions):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in allowed_extensions

def save_image(file, upload_folder):
    filename = secure_filename(file.filename)
    file_ext = os.path.splitext(filename)[1].lower()
    if file_ext not in current_app.config['ALLOWED_EXTENSIONS']:
        raise ValueError('Invalid file type')

    # Generate a unique filename (optional)
    unique_filename = f"{uuid.uuid4().hex}{file_ext}"
    file_path = os.path.join(upload_folder, unique_filename)
    file.save(file_path)
    return unique_filename