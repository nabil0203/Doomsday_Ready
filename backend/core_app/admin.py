from django.contrib import admin

from .models import BundleSize, Cinema, Movie

admin.site.register(Movie)
admin.site.register(Cinema)
admin.site.register(BundleSize)