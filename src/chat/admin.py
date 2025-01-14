from django.contrib import admin
from import_export import resources
from import_export.admin import ExportMixin
from import_export.formats import base_formats

from .models import SleepAdvice, Message, Mission

admin.site.register(Message)
admin.site.register(Mission)

class SleepAdviceResource(resources.ModelResource):
    # Modelに対するdjango-import-exportの設定
    class Meta:
        model = SleepAdvice

@admin.register(SleepAdvice)
class SleepAdviceAdmin(ExportMixin, admin.ModelAdmin):
    resource_class = SleepAdviceResource
    formats = [base_formats.CSV]