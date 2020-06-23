

from django.contrib import admin
from app.models.judge import Judge

class JudgeAdmin(admin.ModelAdmin):
    fields = ('user', 'title')

admin.sites.register(Judge, JudgeAdmin)