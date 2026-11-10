import os
from urllib.parse import quote_plus

from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-change-me")

    _user = os.getenv("DB_USER", "root")
    _password = quote_plus(os.getenv("DB_PASSWORD", ""))
    _host = os.getenv("DB_HOST", "localhost")
    _port = os.getenv("DB_PORT", "3306")
    _name = os.getenv("DB_NAME", "online_learning")

    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{_user}:{_password}@{_host}:{_port}/{_name}?charset=utf8mb4"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
