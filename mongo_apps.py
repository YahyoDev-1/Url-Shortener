"""
Django contrib ilovalarini MongoDB'ga moslashtirish.

Standart contrib ilovalar (admin, auth, contenttypes) AutoField ishlatadi,
MongoDB esa faqat ObjectIdAutoField'ni qo'llab-quvvatlaydi. Shu sababli
ularning AppConfig'lari override qilinadi (rasmiy django-mongodb-project
shabloniga asosan).
"""

from django.contrib.admin.apps import AdminConfig
from django.contrib.auth.apps import AuthConfig
from django.contrib.contenttypes.apps import ContentTypesConfig


class MongoAdminConfig(AdminConfig):
    default_auto_field = 'django_mongodb_backend.fields.ObjectIdAutoField'


class MongoAuthConfig(AuthConfig):
    default_auto_field = 'django_mongodb_backend.fields.ObjectIdAutoField'


class MongoContentTypesConfig(ContentTypesConfig):
    default_auto_field = 'django_mongodb_backend.fields.ObjectIdAutoField'
