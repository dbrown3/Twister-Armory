#this belongs at the root project folder, probably solutionsfactory in our case

"""
Django settings for solutionsfactory project.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.7/ref/settings/

# See https://docs.djangoproject.com/en/1.7/howto/deployment/checklist/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os

# SECURITY WARNING: don't run with debug turned on in production!
# Config wsgi and apache to serve static files
DEBUG = True
TEMPLATE_DEBUG = True

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

# Templates
TEMPLATE_DIRS = (
    os.path.join(BASE_DIR, 'solutionsfactory/templates'),
    os.path.join(BASE_DIR, 'dbtables/templates'),
    os.path.join(BASE_DIR, 'hadoop/templates'),
    os.path.join(BASE_DIR, 'matching/templates'),
    os.path.join(BASE_DIR, 'satool/templates'),
    os.path.join(BASE_DIR, 'profilecreation/templates'),
    os.path.join(BASE_DIR, 'automatedpowerpoint/templates'),
    os.path.join(BASE_DIR, 'cloudanalytics/templates'),
    os.path.join(BASE_DIR, 'teamchemistry/templates'),
    os.path.join(BASE_DIR, 'bigtex/templates'),
    os.path.join(BASE_DIR, 'twister/templates'),
)

print("TEMPLATE_DIRS : %s" % (TEMPLATE_DIRS,))

STATICFILES_DIRS = (
    ("assets", os.path.join(BASE_DIR, 'solutionsfactory/templates/static')),
    ("matching", os.path.join(BASE_DIR, 'matching/static/matching')),
    ("satool", os.path.join(BASE_DIR, 'satool/static/satool')),
    ("profilecreation", os.path.join(BASE_DIR, 'profilecreation/static/profilecreation')),
    ("automatedpowerpoint", os.path.join(BASE_DIR, 'automatedpowerpoint/static/automatedpowerpoint')),
    ("cloudanalytics", os.path.join(BASE_DIR, 'cloudanalytics/static/cloudanalytics')),
    ("teamdynamics", os.path.join(BASE_DIR, 'teamdynamics/static/teamdynamics')),
    ("teamchemistry", os.path.join(BASE_DIR, 'teamchemistry/static/teamchemistry')),
    ("bigtex", os.path.join(BASE_DIR, 'bigtex/static/bigtex')),
    ("twister", os.path.join(BASE_DIR, 'twister/static/twister')),
)
print("STATICFILES_DIRS : %s" % (STATICFILES_DIRS,))



# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '%1bhqzc95n$-c2kub8dfzi1^69_9vip+)_u*zpoi=n0h&%nl&z'

ALLOWED_HOSTS = ['10.48.24.112', '127.0.0.1']

# Application definition
INSTALLED_APPS = (
    'grappelli',
    'filebrowser',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # 'progressbarupload',
    'satool',
    'dbtables',
    'hadoop',
    'matching',
    'profilecreation',
    'automatedpowerpoint',
    'solutionsfactory',
    'axes',
    'cloudanalytics',
    'teamdynamics',
    'teamchemistry',
    'bigtex',
    'twister',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'axes.middleware.FailedLoginMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

# Added for File Uploading

FILE_UPLOAD_HANDLERS = (
    'django.core.files.uploadhandler.MemoryFileUploadHandler',
    'django.core.files.uploadhandler.TemporaryFileUploadHandler',
)

# Added to prevent jquery from being included with progress bar
PROGRESSBARUPLOAD_INCLUDE_JQUERY = False

ROOT_URLCONF = 'solutionsfactory.urls'

WSGI_APPLICATION = 'solutionsfactory.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'django_db',
        'USER': 'django',
        'PASSWORD': 'dj@ng0gr3s',
        'HOST': '10.48.24.112',
        'PORT': '5432',
        },

    'pa_io': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'panswers_io_dev',
        'USER': 'django',
        'PASSWORD': 'dj@ng0gr3s',
        'HOST': '10.48.24.112',
        'PORT': '5432',
        },
    }

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

STATIC_ROOT = '/var/www/django/static/'
STATIC_URL = '/static/'
#STATIC_URL = 'static/'

# Add customization for uploading files
MEDIA_ROOT = '/var/www/django/media/'
#MEDIA_ROOT = getattr(settings, "FILEBROWSER_MEDIA_ROOT", settings.MEDIA_ROOT)
#MEDIA_URL = '/media/'
MEDIA_URL = '/static/twister/sound/'

#MEDIA_URL = getattr(settings, "FILEBROWSER_MEDIA_URL", settings.MEDIA_URL)
DIRECTORY = 'uploads/'
#DIRECTORY = getattr(settings, "FILEBROWSER_DIRECTORY", 'uploads/')
EXTENSIONS = {
    'Document': ['.pdf','.doc','.rtf','.txt','.xls','.csv'],
    }
#EXTENSIONS = getattr(settings, "FILEBROWSER_EXTENSIONS", {
#    'Document': ['.pdf','.doc','.rtf','.txt','.xls','.csv'],
#})

#Other extension types
#'Folder': [''],
#'Image': ['.jpg','.jpeg','.gif','.png','.tif','.tiff'],
#'Video': ['.mov','.wmv','.mpeg','.mpg','.avi','.rm'],
#'Audio': ['.mp3','.mp4','.wav','.aiff','.midi','.m4p'],

SELECT_FORMATS = {
    'document': ['Document'],
    }
#SELECT_FORMATS = getattr(settings, "FILEBROWSER_SELECT_FORMATS", {
#    'document': ['Document'],
#})

#Other formats
#'file': ['Folder','Image','Document','Video','Audio'],
#'image': ['Image'],
#'media': ['Video','Audio'],


# ***********************django-axes settings **************
AXES_LOGIN_FAILURE_LIMIT = 3
AXES_LOCK_OUT_AT_FAILURE = True
AXES_USE_USER_AGENT = False
from datetime import timedelta
AXES_COOLOFF_TIME = timedelta(seconds=300)
AXES_LOCKOUT_TEMPLATE = "toomanyattempts.html"
AXES_LOCKOUT_URL = "/lockout/"
# ***********************END django-axes settings **********
