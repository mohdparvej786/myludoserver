import asyncio
import json
import websockets
import socket
import os

clients = {}

PORT = int(os.environ.get("PORT", 8765))

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

async def handler(websocket):
    addr = websocket.remote_address
    print(f"\n[+] CONNECTION: {addr}")

    try:
        async for message in websocket:

            data = json.loads(message)
            msg_type = data.get("type")
            msg_data = data.get("data", {})

            if msg_type == "PLAYER_JOINED":

                player_name = msg_data.get("player", "Unknown")
                clients[websocket] = player_name

                print(f">>> {player_name} joined")

                await broadcast(message, websocket)

            elif msg_type in ["OFFER","ANSWER","ICE_CANDIDATE"]:

                target = msg_data.get("to")

                data["data"]["from"] = clients.get(websocket,"Unknown")

                target_ws = next((ws for ws,name in clients.items() if name == target),None)

                if target_ws:
                    await target_ws.send(json.dumps(data))

            else:
                await broadcast(message, websocket)

    except Exception as e:
        print("Error:",e)

    finally:

        player = clients.pop(websocket,"Unknown")

        print(f"[-] DISCONNECT {player}")

async def broadcast(message,sender):

    if clients:

        await asyncio.gather(
            *[ws.send(message) for ws in clients if ws != sender],
            return_exceptions=True
        )

async def main():

    ip = get_local_ip()

    print("\n================================")
    print("LUDO SERVER RUNNING")
    print("IP:",ip)
    print("PORT:",PORT)
    print("================================\n")

    async with websockets.serve(handler,"0.0.0.0",PORT):

        await asyncio.Future()

if __name__ == "__main__":

    asyncio.run(main())
