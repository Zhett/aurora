# Django settings for aurora project.
import os
import ConfigParser

SITE_ROOT = "/".join(os.path.dirname(os.path.realpath(__file__)).split("/")[:-1])

# *************************************
# LOAD CONFIG FILE
# *************************************
Config = ConfigParser.ConfigParser()
Config.read(SITE_ROOT + "/v2/config.cnf")

SERVER = Config.get('main', 'SERVER')
DOMAIN = Config.get('main', 'DOMAIN')
TEMPLATE_WEBSITE = Config.get('templates', 'TEMPLATE_WEBSITE')
DEBUG = Config.getboolean('main', 'DEBUG')
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    ('Zhett', 'stratos33290@gmail.com'),
)

MANAGERS = ADMINS

BDD_NAME = Config.get('database', 'BDD_NAME')
BDD_USER = Config.get('database', 'BDD_USER')
BDD_PASSWORD = Config.get('database', 'BDD_PWD')
BDD_HOST = Config.get('database', 'BDD_HOST')
BDD_PORT = Config.get('database', 'BDD_PORT')

# *************************************
# DATABASES
# *************************************
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': BDD_NAME,
        'USER': BDD_USER,
        'PASSWORD': BDD_PASSWORD,
        'HOST': BDD_HOST,
        'PORT': BDD_PORT,
        'STORAGE_ENGINE': 'InnoDB',
        'OPTIONS': {'init_command': 'SET character_set_connection=utf8, collation_connection=utf8_unicode_ci'}
    },
}

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Europe/Paris'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'fr-FR'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = os.path.join(SITE_ROOT, 'medias/')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = ''

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = ''

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/medias/'

# Additional locations of static files
STATICFILES_DIRS = (
    os.path.join(SITE_ROOT, 'medias'),
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'j!a_y&amp;*q*=#)2e--!3rh5830#s5t-dtuq8jha1l!y$#+%k*r^j'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'aurora.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'aurora.wsgi.application'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(SITE_ROOT, 'website/templates/'+TEMPLATE_WEBSITE),
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'website',
    #'south',
    # Uncomment the next line to enable admin documentation:
    # 'django.contrib.admindocs',
)
INTERNAL_IPS = ('127.0.0.1',)
# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'verbose': {
            'format': '%(asctime)s - %(levelname)s | %(filename)s - %(funcName)s() - Line %(lineno)s | %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'formatter': 'verbose',
            'filename': SITE_ROOT + "/logs/cprodirect.log",
        },
    },
    'loggers': {
        'logview.userlogins': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': True,
        },
    }
}
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
