import asyncio as aio
import time
import random

import numpy as np

import server as se
import aabb

import entity
import world

class Game:

  def __init__(self, config):
    self.config = config
    self.first_tick = True

    # TODO read world data from file/generate it procedurally instead of
    # this temporary init here
    arr = np.zeros((30, 30))
    arr[1::4, 1::4] = 1
    arr[2::4, 1::4] = 3
    arr[3::4, 1::4] = 1
    def to_colour(tile):
      if tile == 3:
        return 5
      elif tile == 1:
        return 4
      else:
        return 3
    self.world = world.World(arr, to_colour)

    self.entities = set()
    # since we cannot modify a set while we iterate over it,
    # we buffer all changes we would like to make to a set until after the
    # current tick is over
    self.add_entities_buffer = set()
    self.remove_entities_buffer = set()
    self.players = {}
    self.add_players_buffer = []
    self.remove_players_buffer = []

  def new_player(self, player_id):
    player = entity.Player(self, player_id)
    self.add_players_buffer.append(player)
    self.add_entity(player)

  def remove_player(self, player_id):
    self.remove_players_buffer.append(player_id)

  def add_entity(self, entity):
    self.add_entities_buffer.add(entity)

  def remove_entity(self, entity):
    self.remove_entities_buffer.add(entity)

  def flush_add_entities_buffer(self):
    self.entities |= self.add_entities_buffer
    self.add_entities_buffer.clear()

    for player in self.add_players_buffer:
      self.players[player.player_id] = player
    self.add_players_buffer.clear()

  def flush_remove_entities_buffer(self):
    for entity in self.remove_entities_buffer:
      if entity in self.entities:
        self.entities.remove(entity)
    self.remove_entities_buffer.clear()

    for player_id in self.remove_players_buffer:
      player = self.players[player_id]
      if player in self.entities:
        self.entities.remove(player)
      self.players.pop(player_id)
    self.remove_players_buffer.clear()

  def flush_entities_buffer(self):
    self.flush_add_entities_buffer()
    self.flush_remove_entities_buffer()

  def update_player_keys(self, player_id, keys):
    if player_id in self.players:
      self.players[player_id].keys.update(
        {key for key, val in keys.items() if val == True}
      )

  def spawn_enemy(self, player):
    enemy = entity.Mouse(self, player)
    self.add_entity(enemy)

  async def tick(self, delta):
    if self.first_tick:
      await se.sio.emit('world', self.world.render)
    self.flush_entities_buffer()
    for entity in self.entities:
      entity.tick(delta)
    # can only flush add entities buffer here
    # this way, entities that only live for 1 frame will be displayed temporarily
    # self.flush_add_entities_buffer()
    self.flush_entities_buffer()
    for entity in self.entities:
      entity.update_aabb()
      int = self.world.intersect(
        entity.aabb_x, entity.aabb_y, entity.aabb_w, entity.aabb_h
      )
      if int:
        entity.collide_tile(int)
    # same note as above here, we can only flush add entities here if we want
    self.flush_entities_buffer()
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
    # tick player i/o
    for player in self.players.values():
      player.keys.tick()
    entity_list = list(self.entities)
    entity_data = [[e.x, e.y, e.w, e.h, e.sprite_id, False] for e in entity_list]
    for i, entity in enumerate(entity_list):
      if hasattr(entity, 'player_id'):
        entity_data[i][5] = True
        await se.sio.emit('entities',
          entity_data,
          room=se.player_id_map_inv[entity.player_id],
        )
        entity_data[i][5] = False
    await se.sio.emit('health',
      # hasattr sketch?
      [(e.x, e.y, e.w, e.h, e.hp) for e in self.entities if hasattr(e, 'hp')]
    )

  async def game_loop(self):
    # all times in seconds
    dt = 1. / self.config.tps
    next_tick_target = time.time() + dt
    ticks = 0
    last_print_time = time.time()

    while 1:
      await self.tick(dt)
      ticks += 1
      if ticks % 60 == 0:
        now = time.time()
        print(f"TPS: {self.config.tps / (now - last_print_time):.2f}")
        last_print_time = now
      now = time.time()
      while now < next_tick_target:
        await aio.sleep(0.001)
        now = time.time()
      next_tick_target += dt

