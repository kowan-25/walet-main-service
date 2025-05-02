from .settings import *

ALLOWED_HOSTS = ["localhost", "127.0.0.1", "main-service", "https://kelompok-80-main-service.pkpl.cs.ui.ac.id", "http://main-service.kelompok-80-ns.svc.cluster.local"]
DEBUG = False
DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("DB_NAME"),
            "USER": os.getenv("DB_USERNAME"),
            "PASSWORD": os.getenv("DB_PASSWORD"),
            "HOST": os.getenv("DB_HOST"),
            "PORT": os.getenv("DB_PORT", "5432"),
            "OPTIONS": {
                "sslmode": "require",
                "options": os.getenv("DB_OPTIONS"),
            },
        }
    }

SIMPLE_JWT = {
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=5)
}