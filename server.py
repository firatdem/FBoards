# server.py
import asyncio
import websockets
import json

clients = set()

async def handler(websocket, path):
    global clients
    clients.add(websocket)
    try:
        async for message in websocket:
            data = json.loads(message)
            await broadcast(data)
    finally:
        clients.remove(websocket)

async def broadcast(data):
    for client in clients:
        await client.send(json.dumps(data))

start_server = websockets.serve(handler, "localhost", 6789)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
