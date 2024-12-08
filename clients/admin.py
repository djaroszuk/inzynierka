from django.contrib import admin

from .models import Client
from .models import Contact

admin.site.register(Client)
admin.site.register(Contact)
