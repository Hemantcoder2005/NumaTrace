from django.urls import path
from .views import *
from django.conf.urls import handler404

def custom_404_view(request, exception):
    return render(request, '404.html', status=404)

handler404 = custom_404_view

urlpatterns = [
    path("dashboard/",dashboard_view,name="dashboard"),
    path('api/projects/', create_project, name='create_project'),
    path('api/projects/<int:id>/', delete_project, name='delete_project'),
    path('api/projects/<int:id>/toggle-status/', toggle_project_status, name='toggle_project_status'),
    path('api/projects/<str:project_id>/download-logs/', download_logs, name='download_logs'),
    path('view-project/<str:project_id>/', terminal_view, name='view_project'),
    path('api/hourly-task/', hourly_task, name='hourly_task'),
]
