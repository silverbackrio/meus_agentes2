"""Configurações de produção."""
from .base import *

DEBUG = False
ALLOWED_HOSTS = []
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
# Em produção, configure DATABASES com engine adequada (PostgreSQL, etc.)
# DATABASES = {...}
