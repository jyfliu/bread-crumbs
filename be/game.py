import asyncio
import time

import server as se

class Player: # TODO move this

  def __init__(self, game):
    self.x = 0
    self.y = 0
    self.speed = 0.8
    self.game = game

  def tick(self, delta):
    if 'w' in self.game.keys:
      self.y += delta * self.speed
    if 'a' in self.game.keys:
      self.x -= delta * self.speed
    if 's' in self.game.keys:
      self.y -= delta * self.speed
    if 'd' in self.game.keys:
      self.x += delta * self.speed

class Game:

  def __init__(self, config):
    self.config = config
    self.entities = [Player(self)]
    self.keys = set()

  def key_pressed(self, keys):
    self.keys = {key for key, val in keys.items() if val == True}

  async def tick(self, delta):
    for entity in self.entities:
      entity.tick(delta)
    await se.sio.emit('update', (self.entities[0].x, self.entities[0].y))

  async def game_loop(self):
    # all times in seconds
    dt = 1. / self.config.tps
    next_tick_target = time.time() + dt

    while 1:
      await self.tick(dt)
      now = time.time()
      while now < next_tick_target:
        await asyncio.sleep(0.001)
        now = time.time()
      next_tick_target += dt

