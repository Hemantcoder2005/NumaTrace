import websockets
import asyncio
import json

async def send_logs():
    uri = "ws://127.0.0.1:8000/ws/logs/"
    async with websockets.connect(uri) as websocket:
        await websocket.send(json.dumps({
            "project_id": "abcd1234...",
            "secret_key": "xyz..."
        }))

        await websocket.send(json.dumps({
            "timestamp": "2025-06-20 09:04:32",
            "log_level": "INFO",
            "file_path": "LiveTrading/LiveTrade.py",
            "message": "Broker connected"
        }))

asyncio.run(send_logs())
