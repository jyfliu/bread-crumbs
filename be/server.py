import asyncio
import socketio

from aiohttp import web

import game as ge # should be game_engine?

sio = socketio.AsyncServer(cors_allowed_origins='*')
app = web.Application()
sio.attach(app)

player_id_map = {}
player_id_map_inv = []

@sio.event
def connect(sid, environ):
  print("connect ", sid)
  player_id_map[sid] = len(player_id_map)
  player_id_map_inv.append(sid)
  game.new_player(player_id_map[sid])

@sio.event
async def update_keys(sid, data):
  game.update_player_keys(player_id_map[sid], data)

@sio.event
def disconnect(sid):
  print("disconnect", sid)
  game.remove_player(player_id_map[sid])

async def run(config):
  global game # spaghetti
  game = ge.Game(config)

  # hack to run aiohttp with our game loop in the same event loop
  # uses a private function _run_app (works in aiohttp==3.8)
  await asyncio.gather(
    web._run_app(app, port=config.server_port),
    game.game_loop(),
  )

  # The proper way of doing it (doesn't work for me :|)
  # runner = web.AppRunner(app)
  # await runner.setup()
  # site = web.TCPSite(runner, 'localhost', port=config.server_port)
  # await site.start()

  # await game.game_loop()

