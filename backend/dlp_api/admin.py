from django.contrib import admin
from .models import Pattern, DetectedLeak

admin.site.register(Pattern)
admin.site.register(DetectedLeak)