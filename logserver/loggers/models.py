from django.db import models
import secrets

class Project(models.Model):
    name = models.CharField(max_length=100, unique=True)
    project_id = models.CharField(max_length=50, unique=True, editable=False)
    secret_key = models.CharField(max_length=128, editable=False)
    developer_email = models.EmailField()
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_log_at = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.project_id:
            self.project_id = secrets.token_hex(8)  # e.g., "f3a5c9de0b1a73e2"
        if not self.secret_key:
            self.secret_key = secrets.token_urlsafe(32)  # e.g., "hGqz9W1V3Y..."
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.project_id})"
class LogEntry(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='logs')
    timestamp = models.DateTimeField()
    log_level = models.CharField(max_length=10)  # e.g., INFO, DEBUG, ERROR
    file_path = models.CharField(max_length=255)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"[{self.log_level}] {self.file_path} - {self.message[:50]}"