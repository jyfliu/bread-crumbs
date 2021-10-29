import asyncio
import time
import random

import server as se
import aabb

import entity

class Game:

  def __init__(self, config):
    self.config = config
    self.players = {}
    self.entities = set()
    # since we cannot modify a set while we iterate over it,
    # we buffer all changes we would like to make to a set until after the
    # current tick is over
    self.add_entities_buffer = set()
    self.remove_entities_buffer = set()
    self.keys = set()
    # self.add_entity(entity.Bullet(self, None, 1, 0, (0, 0)))
    # self.add_entity(entity.Bullet(self, None, 0, 1, (0, 0)))
    # self.add_entity(entity.Bullet(self, None, -1, 0, (0, 0)))
    # self.add_entity(entity.Bullet(self, None, 0, -1, (0, 0)))
    # self.add_entity(entity.Bullet(self, None, 1, 1, (0, 0)))
    # self.add_entity(entity.Bullet(self, None, -1, 1, (0, 0)))
    # self.add_entity(entity.Bullet(self, None, 1, -1, (0, 0)))
    # self.add_entity(entity.Bullet(self, None, -1, -1, (0, 0)))

  def new_player(self, player_id):
    self.players[player_id] = entity.Player(self, player_id)
    self.add_entity(self.players[player_id])

  def remove_player(self, player_id):
    player = self.players.pop(player_id)
    self.remove_entity(player)

  def add_entity(self, entity):
    self.add_entities_buffer.add(entity)

  def remove_entity(self, entity):
    self.remove_entities_buffer.add(entity)

  def flush_add_entities_buffer(self):
    self.entities |= self.add_entities_buffer
    self.add_entities_buffer.clear()

  def flush_remove_entities_buffer(self):
    for entity in self.remove_entities_buffer:
      if entity in self.entities:
        self.entities.remove(entity)
    self.remove_entities_buffer.clear()

  def flush_entities_buffer(self):
    self.flush_add_entities_buffer()
    self.flush_remove_entities_buffer()

  def key_pressed(self, player_id, keys):
    self.players[player_id].keys = {key for key, val in keys.items() if val == True}

  async def tick(self, delta):
    self.flush_entities_buffer()
    for entity in self.entities:
      entity.tick(delta)
    # only flush add entities buffer here
    # this way, entities that only live for 1 frame will be displayed temporarily
    self.flush_add_entities_buffer()
    for entity in self.entities:
      entity.update_aabb()
    for e1 in self.entities:
      for e2 in self.entities:
        if e1 is e2:
          # don't collide with itself
          continue
        if aabb.intersect(
            e1.aabb_x, e1.aabb_y, e1.aabb_w, e1.aabb_h,
            e2.aabb_x, e2.aabb_y, e2.aabb_w, e2.aabb_h,
        ):
          e1.collide(e2)
    await se.sio.emit('update',
      [(e.x, e.y, e.w, e.h, e.sprite_id) for e in self.entities]
    )
    await se.sio.emit('health',
      # hasattr sketch?
      [(e.x, e.y, e.w, e.h, e.hp) for e in self.entities if hasattr(e, 'hp')]
    )

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

