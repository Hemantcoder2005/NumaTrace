from channels.generic.websocket import AsyncWebsocketConsumer
import json
from datetime import datetime,timedelta
import os
from asgiref.sync import sync_to_async
from .models import Project, LogEntry

master_key = "1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"

class LogConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        self.project = None
        self.log_path = None
        self.latest_log_timestamp = None
        self.is_master_active = False
        self.group_name = None
        self.prev_message = None
        self.start_time = datetime.now()

    async def receive(self, text_data):
        if  not self.is_master_active and  ((datetime.now() - self.start_time) > timedelta(minutes=1)) :
            self.start_time = datetime.now()
            if not await self.get_status():
                print("Disconnecting due to inactivity")
                await self.disconnect(1000)
        try:
            data = json.loads(text_data)
            # If master connection is active, just relay
            if self.is_master_active:
                await self.channel_layer.group_send(
                    self.group_name,
                    {
                        'type': 'log_message',
                        'message': data
                    }
                )
                return

            # First-time authentication
            if not self.project:
                project_id = data.get('project_id')
                secret_key = data.get('secret_key')

                if secret_key == master_key:
                    self.is_master_active = True
                    self.group_name = f"project_{project_id}"
                    await self.channel_layer.group_add(self.group_name, self.channel_name)
                    print("Master connected to group:", self.group_name)
                    return

                self.project = await self.authenticate(project_id, secret_key)
                if not self.project:
                    await self.send(json.dumps({"error": "Unauthorized"}))
                    await self.close()
                    return
                if not self.project.is_active:
                    await self.send(json.dumps({"error": "Project is inactive"}))
                    await self.close()
                    return

                self.group_name = f"project_{self.project.project_id}"
                await self.channel_layer.group_add(self.group_name, self.channel_name)

                await self.initialize_log_file()
                return
            if self.prev_message == data:
                return
            self.prev_message = data
            # Handle log
            log_level = data.get('log_level')
            timestamp_str = data.get('timestamp')
            file_path = data.get('file_path')
            message = data.get('message')

            timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
            self.latest_log_timestamp = timestamp

            await self.write_to_file(timestamp, log_level, file_path, message)

            # Optional DB store
            if log_level and log_level.lower() in ['error', 'critical']:
                await self.save_to_db(timestamp, log_level, file_path, message)

            # Broadcast to all in group (like master monitor)
            await self.channel_layer.group_send(
                self.group_name,
                {
                    'type': 'log_message',
                    'message': {
                        "timestamp": timestamp_str,
                        "log_level": log_level,
                        "file_path": file_path,
                        "message": message
                    }
                }
            )

        except Exception as e:
            await self.send(json.dumps({"error": str(e)}))
            await self.close()

    async def disconnect(self, close_code):
        print(self.group_name and not self.is_master_active)
        if self.group_name and not self.is_master_active:

            await self.channel_layer.group_send(
                self.group_name,
                {
                    'type': 'log_message',
                    'message': {
                        'log_level': 'WARNING',
                        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'file_path': 'system',
                        'message': 'Client code exited'
                    }
                }
            )
        print("Disconnected from WebSocket")
        if self.group_name:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

        if self.project and self.latest_log_timestamp:
            await self.update_last_log_time(datetime.now())
            

        self.project = None
        self.log_path = None
        self.latest_log_timestamp = None
        self.group_name = None

    async def log_message(self, event):
        await self.send(text_data=json.dumps(event['message']))

    @sync_to_async
    def authenticate(self, project_id, secret_key):
        try:
            project = Project.objects.get(project_id=project_id)
            if project.secret_key != secret_key and secret_key != master_key:
                return None
            return project
        except Project.DoesNotExist:
            return None

    @sync_to_async
    def initialize_log_file(self):
        now = datetime.now()
        timestamp_str = now.strftime('%Y-%m-%d_%H-%M-%S')
        project_name = self.project.project_id.replace(" ", "_").lower()

        log_dir = os.path.join("logs", project_name)
        os.makedirs(log_dir, exist_ok=True)

        filename = f"{timestamp_str}.log"
        self.log_path = os.path.join(log_dir, filename)

    @sync_to_async
    def write_to_file(self, timestamp, log_level, file_path, message):
        if not self.log_path:
            return
        log_line = f"{timestamp.strftime('%Y-%m-%d %H:%M:%S')} [{log_level.upper()}] {file_path} - {message}\n"
        with open(self.log_path, 'a') as f:
            f.write(log_line)

    @sync_to_async
    def save_to_db(self, timestamp, log_level, file_path, message):
        LogEntry.objects.create(
            project=self.project,
            timestamp=timestamp,
            log_level=log_level,
            file_path=file_path,
            message=message
        )

    @sync_to_async
    def update_last_log_time(self, timestamp):
        self.project = Project.objects.get(project_id=self.project.project_id)
        self.project.last_log_at = datetime.now()
        self.project.save()

    @sync_to_async
    def get_status(self):
        self.project = Project.objects.get(project_id=self.project.project_id)
        return self.project.is_active
