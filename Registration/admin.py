from django.contrib import admin
from .models import Visitor, VisitorLog
import json
# Register your models here.

class adminVisitor(admin.ModelAdmin):
    exclude = ['images_collected']
    list_display = ['name', 'telephone', 'purpose', 'facial_features']
    list_display_links = ['name']

    def facial_features(self, obj:Visitor):
        return len(json.loads(obj.images_collected))

class adminVisitorLog(admin.ModelAdmin):
    pass


admin.site.register(Visitor, adminVisitor)
admin.site.register(VisitorLog, adminVisitorLog)