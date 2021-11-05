import asyncio as aio
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

def run(config):
  global game # spaghetti
  game = ge.Game(config)

  loop = aio.get_event_loop()
  loop.create_task(game.game_loop())

  web.run_app(app, port=config.server_port, loop=loop)

