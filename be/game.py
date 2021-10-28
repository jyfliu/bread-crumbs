import asyncio
import time
import random

import server as se

class Player: # TODO move this

  def __init__(self, game):
    # position
    self.x = 0
    self.y = 0
    # movement
    self.dx = 0
    self.dy = 0
    self.pressed = {key: False for key in ['w', 'a', 's', 'd']}
    self.speed = 0.8
    # rolling
    self.roll_cooldown = 0
    self.max_roll_cooldown = 60
    self.roll_duration = 15
    # shooting
    self.shoot_cooldown = 0
    self.max_shoot_cooldown = 10
    # misc
    self.game = game

  def compute_reactive_wasd(self, key_p, key_n):
    # accepts key_p (key in positive dir) and key_n (key in negative dir)
    # if two opposite keys are pressed at the same time, then prefer to go
    # in the direction that was NOT last pressed (ie., that self.pressed[key]=False)
    if key_p in self.game.keys and key_n in self.game.keys:
      # if both pressed then go in the opposite direction currently going
      if self.pressed[key_p]:
        return -1
      elif self.pressed[key_n]:
        return +1
      else:
        # if its a tie, then prefer to go up and right (to the positive dir)
        self.pressed[key_n] = True
        return +1
    elif key_p in self.game.keys:
      self.pressed[key_p] = True
      self.pressed[key_n] = False
      return +1
    elif key_n in self.game.keys:
      self.pressed[key_p] = False
      self.pressed[key_n] = True
      return -1
    else:
      self.pressed[key_p] = False
      self.pressed[key_n] = False
      return 0

  def compute_wasd(self):
    # recompute wasd movement
    self.dx = self.compute_reactive_wasd('d', 'a')
    self.dy = self.compute_reactive_wasd('w', 's')

    mult = self.speed
    if 'shift' in self.game.keys and not self.roll_cooldown and (self.dx or self.dy):
      mult *= 3.
      self.roll_cooldown = self.max_roll_cooldown

    if self.dx != 0 and self.dy != 0:
      # don't move faster by moving diagonally
      mult *= 2 ** -0.5

    self.dx *= mult
    self.dy *= mult

  def move(self, delta):
    if self.roll_cooldown:
      self.roll_cooldown -= 1

    if self.max_roll_cooldown - self.roll_cooldown <= self.roll_duration:
      # we are still rolling
      pass
    else:
      self.compute_wasd()

    self.x += delta * self.dx
    self.y += delta * self.dy

  def shoot(self):
    if self.shoot_cooldown:
      self.shoot_cooldown -= 1
      return
    shoot_dx = 0
    shoot_dy = 0
    if 'arrowup'    in self.game.keys:
      shoot_dy += 1
    if 'arrowleft'  in self.game.keys:
      shoot_dx -= 1
    if 'arrowdown'  in self.game.keys:
      shoot_dy -= 1
    if 'arrowright' in self.game.keys:
      shoot_dx += 1

    if (shoot_dx + shoot_dy) % 2:
      # shoot if exactly one key is pressed (no diagonal shooting)
      self.game.entities.append(Bullet(
        self.x, self.y,
        (shoot_dx, shoot_dy),
        # impart momentum in the direction we are not firing
        (self.dx if shoot_dy else 0, self.dy if shoot_dx else 0)
      ))
      self.shoot_cooldown = self.max_shoot_cooldown


  def tick(self, delta):
    self.move(delta)
    self.shoot()

class Bullet:

  def __init__(self, x, y, dir, momentum=(0, 0)):
    self.x = x
    self.y = y
    self.dx, self.dy = dir
    self.mx, self.my = momentum
    self.speed = 3

  def tick(self, delta):
    self.x += (self.speed * self.dx + self.mx) * delta
    self.y += (self.speed * self.dy + self.my) * delta

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
    await se.sio.emit('update', [(e.x, e.y) for e in self.entities])

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

