import os
from pathlib import Path
import dj_database_url

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-demo-secret-key-change-this')

# Read DEBUG from environment (default False). Accepts common truthy values.
DEBUG = str(os.environ.get('DEBUG', 'False')).lower() in ('1', 'true', 'yes')

# ALLOWED_HOSTS may be provided as a comma-separated env var; default to localhost
ALLOWED_HOSTS = [h.strip() for h in os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',') if h.strip()]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'library',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    # Whitenoise middleware (serves static files in production)
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'library_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'library_project.wsgi.application'

DATABASES = {
    # Use DATABASE_URL env var when available (Render/Postgres), otherwise fall back to local sqlite file
    'default': dj_database_url.parse(os.environ.get('DATABASE_URL', f"sqlite:///{BASE_DIR / 'db.sqlite3'}"))
}

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Initialize MongoEngine connection for application data (books, borrows)
# Uses the MONGODB_URI environment variable when provided. We keep Django's
# primary DATABASES configured for SQLite so Django auth/session tables remain
# on a relational DB while application documents live in MongoDB.
try:
    # Optionally load a .env file for local development so MONGODB_URI can
    # be provided from a file instead of the environment. This uses
    # python-dotenv when available.
    try:
        from dotenv import load_dotenv
        load_dotenv(dotenv_path=BASE_DIR / '.env')
    except Exception:
        # python-dotenv not installed; continue — the environment may already
        # have MONGODB_URI set or `mongodb_uri.txt` will be used by the helper.
        pass

    from mongoengine import connect
    # Use the centralized helper which checks the env var first and then
    # `mongodb_uri.txt` at the project root.
    from library.mongo_config import get_mongodb_uri
    import pymongo

    MONGODB_URI = get_mongodb_uri()

    try:
        if MONGODB_URI:
            connect(host=MONGODB_URI)
        else:
            # default local database name: library
            connect('library', host='mongodb://localhost:27017/library')

        # Perform a lightweight verification call so authentication errors
        # surface at startup (MongoClient is lazy about some checks).
        try:
            # get the pymongo MongoClient used by mongoengine and ping the
            # server to ensure credentials are valid.
            from mongoengine import get_connection
            client = get_connection()
            # This will raise on authentication failure or network issues.
            client.admin.command('ping')
            from library.mongo_status import set_status
            set_status(True, None)
        except Exception as e:
            # Authentication failed or server unreachable — mark disconnected
            from library.mongo_status import set_status
            set_status(False, e)
    except Exception as e:
        # Connection attempt failed in an unexpected way. Record the error
        # so views can show a helpful message instead of crashing.
        from library.mongo_status import set_status
        set_status(False, e)
except Exception:
    # If mongoengine isn't installed at all, we still want the server to run.
    MONGO_CONNECTED = False
    MONGO_CONNECT_ERROR = 'mongoengine not installed'
