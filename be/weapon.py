import math
import random

import entity

class Pistol:

  def __init__(self, game, user):
    self.game = game
    self.user = user
    self.user.shoot_cooldown = 0
    self.max_shoot_cooldown = 20

  def use(self, shoot_dx, shoot_dy):
    if self.user.shoot_cooldown:
      self.user.shoot_cooldown -= 1
      return

    if shoot_dx and shoot_dy:
      return
    if not shoot_dx and not shoot_dy:
      return

    self.game.add_entity(entity.Bullet(
      self.game, self.user,
      self.user.x, self.user.y,
      (shoot_dx, shoot_dy),
      # impart momentum in the direction we are not firing
      (self.user.dx if shoot_dy else 0, self.user.dy if shoot_dx else 0)
    ))
    self.user.shoot_cooldown = self.max_shoot_cooldown

class Shotgun:

  def __init__(self, game, user):
    # settings
    self.game = game
    self.user = user
    self.user.shoot_cooldown = 0
    self.max_shoot_cooldown = 30
    self.num_pellets = 7
    self.max_spread_angle = math.radians(15.)
    self.bullet_lifespan = 20
    self.bullet_dmg = 3

    # precomputation
    self.max_spread = math.tan(self.max_spread_angle)

  def use(self, shoot_dx, shoot_dy):
    if self.user.shoot_cooldown:
      self.user.shoot_cooldown -= 1
      return
    if shoot_dx and shoot_dy:
      return
    if not shoot_dx and not shoot_dy:
      return

    momentum = (self.user.dx if shoot_dy else 0, self.user.dy if shoot_dx else 0)
    for i in range(self.num_pellets):
      if i == 0:
        # first pellet is always perfectly accurate, otherwise have spread
        spread = 0
      else:
        spread = random.uniform(-self.max_spread, self.max_spread)
      bullet = entity.Bullet(
        self.game, self.user,
        self.user.x, self.user.y,
        (shoot_dx + (spread if shoot_dy else 0),
        shoot_dy + (spread if shoot_dx else 0)),
        momentum,
      )
      bullet.lifespan = self.bullet_lifespan
      bullet.dmg = self.bullet_dmg
      self.game.add_entity(bullet)

    self.user.shoot_cooldown = self.max_shoot_cooldown

class Sniper:

  def __init__(self, game, user):
    # settings
    self.game = game
    self.user = user
    self.user.shoot_cooldown = 0
    self.max_shoot_cooldown = 60
    self.bullet_dmg = 25
    self.bullet_speed = 40
    self.bullet_aspect_ratio = 4

  def use(self, shoot_dx, shoot_dy):
    if self.user.shoot_cooldown:
      self.user.shoot_cooldown -= 1
      return
    if shoot_dx and shoot_dy:
      return
    if not shoot_dx and not shoot_dy:
      return

    momentum = (self.user.dx if shoot_dy else 0, self.user.dy if shoot_dx else 0)
    bullet = entity.Bullet(
      self.game, self.user,
      self.user.x, self.user.y,
      (shoot_dx , shoot_dy),
      momentum,
    )
    bullet.dmg = self.bullet_dmg
    bullet.speed = self.bullet_speed
    if shoot_dx:
      bullet.w *= self.bullet_aspect_ratio
      bullet.x += bullet.w * shoot_dx
    if shoot_dy:
      bullet.h *= self.bullet_aspect_ratio
      bullet.y += bullet.h * shoot_dy
    self.game.add_entity(bullet)

    self.user.shoot_cooldown = self.max_shoot_cooldown

class Laser:

  def __init__(self, game, user):
    # settings
    self.game = game
    self.user = user
    self.user.shoot_cooldown = 0
    self.max_shoot_cooldown = 90
    self.laser_dmg = 2
    self.laser_lifespan = 30
    self.laser_length = 100

  def use(self, shoot_dx, shoot_dy):
    if self.user.shoot_cooldown:
      self.user.shoot_cooldown -= 1
      return
    if shoot_dx and shoot_dy:
      return
    if not shoot_dx and not shoot_dy:
      return

    bullet = entity.Bullet(
      self.game, self.user,
      self.user.x, self.user.y,
      (0, 0),
    )
    bullet.lifespan = self.laser_lifespan
    bullet.dmg = self.laser_dmg
    bullet.pierce = 1000
    bullet.speed = 0
    if shoot_dx:
      bullet.w *= self.laser_length
      bullet.x += bullet.w * shoot_dx
    if shoot_dy:
      bullet.h *= self.laser_length
      bullet.y += bullet.h * shoot_dy
    def modified_collide(other):
      if bullet.src == other:
        return
      other.damage(bullet.dmg)
    def modified_collide_tile(other):
      pass

    bullet.collide = modified_collide
    bullet.collide_tile = modified_collide_tile
    self.game.add_entity(bullet)

    self.user.shoot_cooldown = self.max_shoot_cooldown

# for testing purposes, have a list of all possible weapon classes
# then we can just iterate through it to test all the weapons
weapons = [Pistol, Shotgun, Sniper, Laser]

