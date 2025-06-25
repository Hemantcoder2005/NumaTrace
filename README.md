# Numatix Logger Setup and Usage Guide

This guide explains how to set up and use the `Numatix_logger.py` module for logging in your Python application. The logger supports both local file logging and remote logging via WebSocket when a project is active on the Numatix dashboard.

## Prerequisites
- Python 3.6+
- Required packages: `colorama`, `websocket-client`
- Access to the Numatix dashboard at `http://94.136.191.209:8000/dashboard`

## Setup Instructions

### Step 1: Create a Project on the Numatix Dashboard
1. Navigate to `http://94.136.191.209:8000/dashboard`.
2. Click on **Create Project** to generate a new project.
3. Once created, note down the **project_id** and **secret_key** from the dashboard under your project details.

### Step 2: Configure `Numatix_logger.py`
1. Open the `Numatix_logger.py` file.
2. Locate the following section at the top of the file:
   ```python
   uri = "ws://94.136.191.209:8000/ws/logs/"
   project_id = "project_id"
   secret_key = "SecretKey"
   ```
3. Replace `"project_id"` and `"SecretKey"` with the values obtained from the Numatix dashboard.

### Step 3: Integrate the Logger in Your Application

#### Main Application (`main.py`)
To initialize the logger in your main application, follow these steps:

1. Import the `get_logger` function from `Numatix_logger` and the `globals` module.
2. Initialize the logger with a name and a local log storage path.
3. Register the logger instance in the `globals` module to make it accessible across multiple files.

Example `main.py`:
```python
from Numatix_logger import get_logger
import globals

# Initialize logger with name and local log path
logger = get_logger(name="server_logs", path="storage/logs")

# Register logger in globals for use in other files
globals.logger = logger
```

- **name**: A string identifier for the logger (e.g., `"server_logs"`).
- **path**: The directory where local log files will be stored (e.g., `"storage/logs"`).
- **Note**: Registering the logger in `globals` ensures a single instance is used across files. Accessing `globals.logger` before initialization will raise an error.

#### Using the Logger in Other Files (`test.py`)
To use the logger in other files, import it from the `globals` module and call its methods.

Example `test.py`:
```python
from globals import logger

# Log an info message
logger.info("This is a test info message")
```

### Step 4: Understand Logging Behavior
- **NumaTrace Activation**: If the project associated with the `project_id` is active on the Numatix dashboard, logs are sent to the WebSocket server at `ws://94.136.191.209:8000/ws/logs/`. The logger will automatically attempt to connect and send logs.
- **Local Logging**: If the project is inactive or the WebSocket connection fails, logs are stored locally in the specified `path` (e.g., `storage/logs/YYYY-MM-DD/app_log_HH-MM-SS.log`).
- **Log Format**: Logs include timestamp, log level, source file, and message, with colored console output for better readability.

### Step 5: Multiprocessing Considerations
If your application uses Python's `multiprocessing` module, create a new logger instance in each process to ensure independent WebSocket connections. For example:

```python
from Numatix_logger import get_logger

# In each process
logger = get_logger(name="process_logs", path="storage/logs/process")
logger.info("Log message from process")
```

Each instance will establish its own WebSocket connection if NumaTrace is active.

## Logger Methods
The logger supports the following methods:
- `logger.debug(message, source_file="Unknown")`: Log a debug message.
- `logger.info(message, source_file="Unknown")`: Log an info message.
- `logger.warning(message, source_file="Unknown")`: Log a warning message.
- `logger.error(message, exc_info=None, source_file="Unknown")`: Log an error message with optional exception info.
- `logger.critical(message, exc_info=None, source_file="Unknown")`: Log a critical message with optional exception info.
- `logger.exception(message, source_file="Unknown")`: Log an exception with full traceback.
- `logger.log_function_entry(func_name, *args, source_file="Unknown", **kwargs)`: Log function entry with parameters.
- `logger.log_function_exit(func_name, result=None, source_file="Unknown")`: Log function exit with optional result.
- `logger.performance_log(operation, duration, source_file="Unknown")`: Log performance metrics for an operation.


## Notes
- Ensure the WebSocket URI (`ws://94.136.191.209:8000/ws/logs/`) is accessible from your environment.
- Local logs are stored in daily folders (e.g., `storage/logs/YYYY-MM-DD/`).
- The logger uses `colorama` for colored console output, with distinct colors for each log level (DEBUG: Cyan, INFO: Green, WARNING: Yellow, ERROR/CRITICAL: Red).
- If the WebSocket connection fails or the project is inactive, logs are still saved locally, ensuring no data loss.

For further assistance, refer to the Numatix dashboard or contact support.