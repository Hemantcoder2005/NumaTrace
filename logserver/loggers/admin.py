from django.contrib import admin
from .models import Project,LogEntry

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'project_id', 'developer_email', 'is_active', 'created_at')
    readonly_fields = ('project_id', 'secret_key', 'created_at', 'last_log_at')
    search_fields = ('name', 'developer_email')


@admin.register(LogEntry)
class LogEntryAdmin(admin.ModelAdmin):
    list_display = ('project', 'log_level', 'file_path', 'timestamp', 'message_preview')
    list_filter = ('log_level', 'timestamp', 'project')
    search_fields = ('file_path', 'message', 'log_level')

    def message_preview(self, obj):
        return obj.message[:50] + ('...' if len(obj.message) > 50 else '')
    message_preview.short_description = "Message"