from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
# Development and tests only; production configuration is outside this phase.
SECRET_KEY = "blabla"
ALLOWED_HOSTS = ["localhost", "127.0.0.1"]
INSTALLED_APPS = ["workflows"]
ROOT_URLCONF = "config.urls"
DATABASES = {
    "default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}
}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
USE_TZ = True
