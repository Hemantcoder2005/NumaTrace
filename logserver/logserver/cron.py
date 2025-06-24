from loggers.models import Project
from logserver.settings import BASE_DIR
import os
import shutil
import glob

def hourly_task():
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

# Alternative version with more detailed logging
def hourly_task_detailed():
    projects = Project.objects.all()
    project_ids = [str(project.project_id) for project in projects]
    
    print(f"Starting log cleanup task...")
    print(f"Active project IDs: {project_ids}")
    
    logs_path = os.path.join(BASE_DIR, "logs")
    
    if not os.path.exists(logs_path):
        print(f"Logs directory does not exist: {logs_path}")
        return
    
    try:
        folders = [f for f in os.listdir(logs_path) 
                  if os.path.isdir(os.path.join(logs_path, f))]
        
        print(f"Found {len(folders)} folders in logs directory: {folders}")
        
        for folder in folders:
            folder_path = os.path.join(logs_path, folder)
            
            if folder not in project_ids:
                print(f"❌ Folder '{folder}' not in active projects - removing...")
                try:
                    shutil.rmtree(folder_path)
                    print(f"✅ Successfully removed folder: {folder}")
                except Exception as e:
                    print(f"❌ Error removing folder {folder}: {str(e)}")
            else:
                print(f"✅ Folder '{folder}' is valid - checking log files...")
                
                log_files = glob.glob(os.path.join(folder_path, "*.log"))
                log_count = len(log_files)
                
                if log_count > 20:
                    print(f"📁 Folder {folder}: {log_count} log files (>20) - cleaning up...")
                    
                    # Sort by modification time (oldest first)
                    log_files.sort(key=lambda x: os.path.getmtime(x))
                    files_to_remove = log_files[:-20]
                    
                    removed_count = 0
                    for file_path in files_to_remove:
                        try:
                            os.remove(file_path)
                            removed_count += 1
                        except Exception as e:
                            print(f"❌ Error removing {os.path.basename(file_path)}: {str(e)}")
                    
                    print(f"🗑️ Removed {removed_count} old log files from {folder}")
                else:
                    print(f"📁 Folder {folder}: {log_count} log files (≤20) - no cleanup needed")
        
        print("Log cleanup task completed!")
        
    except Exception as e:
        print(f"❌ Error during log cleanup: {str(e)}")
        
# Usage example:
# hourly_task()  # Use the simple version
# hourly_task_detailed()  # Use for more detailed output