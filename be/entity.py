from game import *

class Entity:

  def __init__(self):
    # position
    self.x = 0.
    self.y = 0.
    # size (width and height radius, ie., the true width is twice of self.w)
    self.w = 0.
    self.h = 0.
    # dimensions for collision detection (recomputed each tick by engine)
    self.aabb_x = 0.
    self.aabb_y = 0.
    self.aabb_w = 0.
    self.aabb_h = 0.
    # graphics
    self.sprite_id = 0

  def update_aabb(self):
    self.aabb_x = self.x - self.w
    self.aabb_y = self.y - self.h
    self.aabb_w = 2 * self.w
    self.aabb_h = 2 * self.h

  def tick(self, delta):
    pass

  def damage(self, dmg):
    # returns if the object can be damaged or not
    return True

  def collide(self, other):
    pass

class Player(Entity): # TODO move this

  def __init__(self, game, player_id):
    super().__init__()
    # position
    self.x = 0.
    self.y = 0.
    self.w = 0.05
    self.h = 0.05
    # movement
    self.dx = 0
    self.dy = 0
    self.pressed = {key: False for key in ['w', 'a', 's', 'd']}
    self.speed = 0.6
    # rolling
    self.roll_cooldown = 0
    self.max_roll_cooldown = 60
    self.roll_duration = 8
    # shooting
    self.shoot_cooldown = 0
    self.max_shoot_cooldown = 20
    # combat
    self.hp = 100
    # graphics
    self.sprite_id = 1 + player_id % 2
    # game stuff
    self.keys = {}
    self.player_id = player_id
    self.game = game

  def compute_reactive_wasd(self, key_p, key_n):
    # accepts key_p (key in positive dir) and key_n (key in negative dir)
    # if two opposite keys are pressed at the same time, then prefer to go
    # in the direction that was NOT last pressed (ie., that self.pressed[key]=False)
    if key_p in self.keys and key_n in self.keys:
      # if both pressed then go in the opposite direction currently going
      if self.pressed[key_p]:
        return -1
      elif self.pressed[key_n]:
        return +1
      else:
        # if its a tie, then prefer to go up and right (to the positive dir)
        self.pressed[key_n] = True
        return +1
    elif key_p in self.keys:
      self.pressed[key_p] = True
      self.pressed[key_n] = False
      return +1
    elif key_n in self.keys:
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
    if 'shift' in self.keys and not self.roll_cooldown and (self.dx or self.dy):
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
    if 'arrowup'    in self.keys:
      shoot_dy += 1
    if 'arrowleft'  in self.keys:
      shoot_dx -= 1
    if 'arrowdown'  in self.keys:
      shoot_dy -= 1
    if 'arrowright' in self.keys:
      shoot_dx += 1

    if (shoot_dx + shoot_dy) % 2:
      # shoot if exactly one key is pressed (no diagonal shooting)
      self.game.add_entity(Bullet(
        self.game, self,
        self.x, self.y,
        (shoot_dx, shoot_dy),
        # impart momentum in the direction we are not firing
        (self.dx if shoot_dy else 0, self.dy if shoot_dx else 0)
      ))
      self.shoot_cooldown = self.max_shoot_cooldown

  def damage(self, dmg):
    self.hp -= dmg
    self.sprite_id = 3 - self.sprite_id
    return True

  def tick(self, delta):
    self.move(delta)
    self.shoot()

class Bullet(Entity):

  def __init__(self, game, src, x, y, dir, momentum=(0, 0)):
    self.x = x
    self.y = y
    self.w = 0.025
    self.h = 0.025
    self.dx, self.dy = dir
    self.mx, self.my = momentum
    # game info
    self.speed = 2.5
    self.dmg = 5 # do 5 damage
    self.lifespan = 120
    # graphics
    self.sprite_id = 0
    # misc
    self.src = src
    self.game = game

  def tick(self, delta):
    if self.lifespan:
      self.lifespan -= 1
    else:
      self.game.remove_entity(self)
    self.x += (self.speed * self.dx + self.mx) * delta
    self.y += (self.speed * self.dy + self.my) * delta

  def collide(self, other):
    if self.src == other:
      return
    if other.damage(self.dmg):
      self.game.remove_entity(self)

  def damage(self, dmg):
    return False


