from django.contrib import admin
from .models import Judge

class JudgeAdmin(admin.ModelAdmin):
    fields = ('user', 'title')

admin.site.register(Judge, JudgeAdmin)