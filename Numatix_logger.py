
uri = "ws://94.136.191.209:8000/ws/logs/"


project_id = "project_id"
secret_key = "SecretKey"



################################################   Don't edit below this line   ################################################
import logging
import os
from datetime import datetime
from pathlib import Path
import colorama
from colorama import Fore, Back, Style
import traceback
import sys
import asyncio
import websocket
import threading
import json
import time
from queue import Queue
import inspect

# Initialize colorama for cross-platform colored output
colorama.init(autoreset=True)

# WebSocket setup
ws_global = None


sender_thread = None
ws_thread = None
log_queue = Queue()
_threads_started = False
_threads_lock = threading.Lock()

def send_data(timestamp, level, source, message):
    log_queue.put({
        "timestamp": timestamp,
        "log_level": level,
        "file_path": str(source),
        "message": message
    })

def start_threads_once():
    """Start WebSocket and sender threads only once."""
    global _threads_started
    with _threads_lock:
        if not _threads_started:
            run()
            _threads_started = True

def run():
    def on_open(ws):
        global ws_global
        ws_global = ws
        # print("WebSocket opened.")
        payload = {"project_id": project_id, "secret_key": secret_key}
        try:
            ws.send(json.dumps(payload))
        except Exception as e:
            print("Failed to send auth payload:", e)
            time.sleep(300)

    def on_message(ws, message):
        # print("Received:", message)
        response = json.loads(message)
        if "error" in response and response["error"] == "Unauthorized":
            ws.close()
        if "error" in response and response["error"] == "Project is inactive":
            print("Project is inactive")
            time.sleep(300)
        return 

    def on_error(ws, error):
        # 
        return 

    def on_close(ws, close_status_code, close_msg):
        # print("WebSocket closed:", close_status_code, close_msg)
        return

    def run_ws():
        while True:
            try:
                ws = websocket.WebSocketApp(
                    uri,
                    on_open=on_open,
                    on_message=on_message,
                    on_error=on_error,
                    on_close=on_close
                )
                ws.run_forever()
            except Exception as e:
                # print("WebSocket crashed. Reconnecting in 5s:", e)
                time.sleep(5)

    def sender():
        # time.sleep(1)
        while True:
            try:
                if ws_global and ws_global.sock and ws_global.sock.connected:
                    # print("chalo0")
                    msg = log_queue.get()
                    # print(f"mssg: {msg}")
                    ws_global.send(json.dumps(msg))
                # else:
                #     print("WebSocket not connected. Dropping log:")
            except Exception as e:
                # print("Failed to send log:", e)
                pass

    # Start WebSocket thread
    ws_thread = threading.Thread(target=run_ws, daemon=True)
    ws_thread.start()
    # Start sender thread
    sender_thread = threading.Thread(target=sender, daemon=True)
    sender_thread.start()

class ColoredFormatter(logging.Formatter):
    COLORS = {
        'DEBUG': Fore.CYAN,
        'INFO': Fore.GREEN,
        'WARNING': Fore.YELLOW,
        'ERROR': Fore.RED,
        'CRITICAL': Fore.RED + Back.YELLOW + Style.BRIGHT,
    }

    def format(self, record):
        if not hasattr(record, 'source_file'):
            record.source_file = "N/A"
        log_message = super().format(record)
        log_color = self.COLORS.get(record.levelname, Fore.WHITE)
        colored_message = f"{log_color}{log_message}{Style.RESET_ALL}"
        if record.levelname in ['ERROR', 'CRITICAL']:
            colored_message = f"{Style.BRIGHT}{colored_message}"
            colored_message += f"\n{Fore.RED}{'=' * 50}{Style.RESET_ALL}"
        return colored_message

class AdvancedLogger:
    def __init__(self, name="AppLogger", base_folder="storage/logs"):
        self.name = name
        self.base_folder = base_folder
        self.logger = None
        self._setup_logger()

    def _create_daily_folder(self):
        today = datetime.now().strftime("%Y-%m-%d")
        log_folder = Path(self.base_folder) / today
        log_folder.mkdir(parents=True, exist_ok=True)
        return log_folder

    def _get_log_filename(self):
        timestamp = datetime.now().strftime("%H-%M-%S")
        return f"app_log_{timestamp}.log"

    def _setup_logger(self):
        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(logging.DEBUG)
        if self.logger.handlers:
            return

        log_folder = self._create_daily_folder()
        log_file = log_folder / self._get_log_filename()

        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(source_file)s | %(filename)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_formatter = ColoredFormatter(
            '%(asctime)s | %(levelname)s | %(source_file)s | %(filename)s:%(lineno)d | %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)

        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        print(f"{Fore.GREEN}✓ Logger initialized! Log file: {log_file}{Style.RESET_ALL}")

    def debug(self, message, source_file="Unknown"):
        self.logger.debug(message, extra={"source_file": source_file})
        send_data(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "DEBUG", source_file, message)

    def info(self, message, source_file="Unknown"):
        self.logger.info(message, extra={"source_file": source_file})
        send_data(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "INFO", source_file, message)

    def warning(self, message, source_file="Unknown"):
        self.logger.warning(message, extra={"source_file": source_file})
        send_data(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "WARNING", source_file, message)

    def error(self, message, exc_info=None, source_file="Unknown"):
        self.logger.error(f"🚨 {message}", exc_info=exc_info or sys.exc_info()[0], extra={"source_file": source_file})
        send_data(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "ERROR", source_file, message)

    def critical(self, message, exc_info=None, source_file="Unknown"):
        self.logger.critical(f"💥 {message}", exc_info=exc_info or sys.exc_info()[0], extra={"source_file": source_file})
        send_data(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "CRITICAL", source_file, message)

    def exception(self, message, source_file="Unknown"):
        exc_message = f"{message}\n{traceback.format_exc()}"
        self.logger.exception(f"💥 {message}", extra={"source_file": source_file})
        send_data(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "EXCEPTION", source_file, exc_message)

    def log_function_entry(self, func_name, *args, source_file="Unknown", **kwargs):
        params = []
        if args:
            params.extend([f"arg{i}={arg}" for i, arg in enumerate(args)])
        if kwargs:
            params.extend([f"{k}={v}" for k, v in kwargs.items()])
        param_str = ", ".join(params) if params else "no parameters"
        self.debug(f"🔹 Entering function '{func_name}' with {param_str}", source_file=source_file)

    def log_function_exit(self, func_name, result=None, source_file="Unknown"):
        if result is not None:
            self.debug(f"🔺 Exiting function '{func_name}' with result: {result}", source_file=source_file)
        else:
            self.debug(f"🔺 Exiting function '{func_name}'", source_file=source_file)

    def performance_log(self, operation, duration, source_file="Unknown"):
        if duration > 1.0:
            self.warning(f"⚠️  Performance: '{operation}' took {duration:.2f}s (slow)", source_file=source_file)
        else:
            self.info(f"⚡ Performance: '{operation}' completed in {duration:.2f}s", source_file=source_file)

_global_logger = None

def get_logger(name="AppLogger", path="storage/logs"):
    global _global_logger
    start_threads_once()
    if _global_logger is None:
        _global_logger = AdvancedLogger(name, path)
    return _global_logger

def debug(message, source_file=None):
    if source_file is None:
        source_file = _get_caller_source()
    get_logger().debug(message, source_file)

def info(message, source_file=None):
    if source_file is None:
        source_file = _get_caller_source()
    get_logger().info(message, source_file)

def warning(message, source_file=None):
    if source_file is None:
        source_file = _get_caller_source()
    get_logger().warning(message, source_file)

def error(message, exc_info=None, source_file=None):
    if source_file is None:
        source_file = _get_caller_source()
    get_logger().error(message, exc_info, source_file)

def critical(message, exc_info=None, source_file=None):
    if source_file is None:
        source_file = _get_caller_source()
    get_logger().critical(message, exc_info, source_file)

def exception(message, source_file=None):
    if source_file is None:
        source_file = _get_caller_source()
    get_logger().exception(message, source_file)

def _get_caller_source():
    """Get the source file of the caller function."""
    try:
        frame = inspect.currentframe().f_back.f_back
        return frame.f_globals.get('__file__', 'Unknown')
    except:
        return 'Unknown'

def log_function(func):
    """Decorator to log function entry and exit."""
    def wrapper(*args, **kwargs):
        logger = get_logger()
        source_file = func.__code__.co_filename
        logger.log_function_entry(func.__name__, *args, source_file=source_file, **kwargs)
        try:
            result = func(*args, **kwargs)
            logger.log_function_exit(func.__name__, result, source_file=source_file)
            return result
        except Exception:
            logger.exception(f"Exception in function '{func.__name__}'", source_file=source_file)
            raise
    return wrapper

class PerformanceTimer:
    def __init__(self, operation_name):
        self.operation_name = operation_name
        self.start_time = None
        self.source_file = _get_caller_source()

    def __enter__(self):
        self.start_time = datetime.now()
        get_logger().info(f"🚀 Starting operation: {self.operation_name}", source_file=self.source_file)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()
        get_logger().performance_log(self.operation_name, duration, source_file=self.source_file)

if __name__ == "__main__":
    logger = get_logger("DemoLogger")
    debug("Debug message test")
    info("Application started")
    warning("This is a warning")
    error("Example error occurred")
    try:
        result = 10 / 0
    except ZeroDivisionError:
        exception("Division by zero error")
    with PerformanceTimer("Sample operation"):
        time.sleep(0.1)
    print(f"{Fore.GREEN}✓ Demo completed!{Style.RESET_ALL}")

#######################################################################################################################################################################