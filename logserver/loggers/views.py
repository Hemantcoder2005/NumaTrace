from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated,AllowAny
from rest_framework.response import Response
from rest_framework import status
from .models import Project
from .serializer import ProjectSerializer
from logserver.settings import BASE_DIR
import os
import io
import zipfile
from django.http import HttpResponse
import os
import shutil
import glob

@login_required
def dashboard_view(request):
    projects = Project.objects.all().order_by('-created_at')
    return render(request, 'loggers/dashboard.html', {'projects': projects})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_project(request):
    serializer = ProjectSerializer(data=request.data)
    if serializer.is_valid():
        project = serializer.save()
        return Response(ProjectSerializer(project).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_project(request, id):
    try:
        project = Project.objects.get(id=id)
        project.delete()
        return Response({'message': 'Project deleted'}, status=status.HTTP_204_NO_CONTENT)
    except Project.DoesNotExist:
        return Response({'error': 'Project not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def toggle_project_status(request, id):
    try:
        project = Project.objects.get(id=id)
        project.is_active = not project.is_active
        project.save()
        return Response({'message': f"Project status toggled to {'active' if project.is_active else 'inactive'}"}, status=status.HTTP_200_OK)
    except Project.DoesNotExist:
        return Response({'error': 'Project not found'}, status=status.HTTP_404_NOT_FOUND)

@login_required
def terminal_view(request, project_id):
    print(project_id)
    return render(request, 'loggers/terminal.html', {'project_id': project_id})




@api_view(['GET'])
@permission_classes([IsAuthenticated])
def download_logs(request, project_id):
    log_dir = os.path.join(BASE_DIR, "logs", project_id)
    print(log_dir)
    if not os.path.exists(log_dir) or len(os.listdir(log_dir)) == 0:
        return Response({'error': 'Logs not found'}, status=status.HTTP_404_NOT_FOUND)

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(log_dir):
            for file in files:
                abs_file_path = os.path.join(root, file)
                rel_path = os.path.relpath(abs_file_path, log_dir)
                zipf.write(abs_file_path, arcname=rel_path)

    zip_buffer.seek(0)
    response = HttpResponse(zip_buffer, content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename={project_id}_logs.zip'
    return response

@api_view(['GET'])
@permission_classes([AllowAny])
def hourly_task(request):
    projects = Project.objects.all()
    project_ids = [str(project.project_id) for project in projects]  # Convert to strings for folder comparison
    print("Deleting old logs...")
    
    logs_path = os.path.join(BASE_DIR, "logs")
    
    # Check if logs directory exists
    if not os.path.exists(logs_path):
        print("Logs directory does not exist")
        return
    
    # Get all folders in logs directory
    try:
        folders = [f for f in os.listdir(logs_path) 
                  if os.path.isdir(os.path.join(logs_path, f))]
        
        for folder in folders:
            folder_path = os.path.join(logs_path, folder)
            
            # Check if folder name is in project_ids
            if folder not in project_ids:
                print(f"Removing folder: {folder} (not in project_ids)")
                try:
                    shutil.rmtree(folder_path)
                    print(f"Successfully removed folder: {folder}")
                except Exception as e:
                    print(f"Error removing folder {folder}: {str(e)}")
            else:
                # Check log files count in the folder
                log_files = glob.glob(os.path.join(folder_path, "*.log"))
                log_count = len(log_files)
                
                print(f"Folder {folder}: Found {log_count} log files")
                
                if log_count > 20:
                    print(f"Removing old log files from folder: {folder}")
                    
                    # Sort files by modification time (oldest first)
                    log_files.sort(key=lambda x: os.path.getmtime(x))
                    
                    # Keep only the 20 newest files, remove the rest
                    files_to_remove = log_files[:-20]  # All except last 20
                    
                    for file_path in files_to_remove:
                        try:
                            os.remove(file_path)
                            print(f"Removed: {os.path.basename(file_path)}")
                        except Exception as e:
                            print(f"Error removing file {file_path}: {str(e)}")
                    
                    print(f"Removed {len(files_to_remove)} old log files from {folder}")
                else:
                    print(f"Folder {folder}: No cleanup needed ({log_count} <= 20 files)")
                    
    except Exception as e:
        print(f"Error accessing logs directory: {str(e)}")
