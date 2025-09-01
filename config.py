import os

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-me-in-production")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///database.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PER_PAGE = int(os.environ.get("PER_PAGE", "12"))
    # Image upload settings
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'static/uploads/cars')
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_IMAGE_MB', '5')) * 1024 * 1024  # default 5MB
    ALLOWED_EXTENSIONS = {'png','jpg','jpeg','gif','webp'}
