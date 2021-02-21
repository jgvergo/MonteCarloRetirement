import os
from pathlib import Path


class Config:
    SECRET_KEY = os.environ['SECRET_KEY']

    _project_root = Path(__file__).resolve().parent.parent
    _default_sqlite_db = _project_root / "site.db"

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{_default_sqlite_db}"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 465
    MAIL_USE_TLS = False
    MAIL_USE_SSL = True
    MAIL_USERNAME = os.environ['EMAIL_USER']
    MAIL_PASSWORD = os.environ['EMAIL_PASS']