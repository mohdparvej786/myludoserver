import asyncio
import json
import websockets
import socket
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

# Dictionary to store connected players
clients = {}

# Render PORT
PORT = int(os.environ.get("PORT", 8765))

# ---------------- HEALTH CHECK SERVER ----------------
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"SERVER OK")

def start_health_server():
    http_server = HTTPServer(("0.0.0.0", PORT), HealthHandler)
    http_server.serve_forever()

# ---------------- UTILITY ----------------
def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

# ---------------- WEBSOCKET HANDLER ----------------
async def handler(websocket):
    addr = websocket.remote_address
    print(f"\n[+] CONNECTION: {addr}")

    try:
        async for message in websocket:
            data = json.loads(message)
            msg_type = data.get("type")
            msg_data = data.get("data", {})

            # PLAYER JOIN
            if msg_type == "PLAYER_JOINED":
                player_name = msg_data.get("player", "Unknown")
                clients[websocket] = player_name
                print(f">>> GAME: {player_name} joined from {addr}")

                await broadcast(message, websocket)

            # WEBRTC SIGNALING
            elif msg_type in ["OFFER", "ANSWER", "ICE_CANDIDATE"]:
                target_player = msg_data.get("to")

                data["data"]["from"] = clients.get(websocket, "Unknown")

                target_ws = next((ws for ws, name in clients.items() if name == target_player), None)

                if target_ws:
                    await target_ws.send(json.dumps(data))

            # NORMAL GAME ACTION
            else:
                await broadcast(message, websocket)

    except Exception as e:
        print(f"Error: {e}")

    finally:
        player_name = clients.pop(websocket, "Unknown")
        print(f"[-] DISCONNECT: {player_name} | Total: {len(clients)}")

# ---------------- BROADCAST ----------------
async def broadcast(message, sender_ws):
    if clients:
        await asyncio.gather(
            *[ws.send(message) for ws in clients if ws != sender_ws],
            return_exceptions=True
        )

# ---------------- MAIN SERVER ----------------
async def main():

    ip = get_local_ip()

    print("\n========================================")
    print(" LUDO PREMIUM RTC SERVER LIVE")
    print(" IP Address :", ip)
    print(" PORT       :", PORT)
    print("========================================\n")

    async with websockets.serve(handler, "0.0.0.0", PORT):
        await asyncio.Future()

# ---------------- START ----------------
if __name__ == "__main__":

    # Start health server for uptime monitoring
    threading.Thread(target=start_health_server, daemon=True).start()

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nServer Stopped.")