import weapon
import keys
import aabb

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

  def collide_tile(self, tiles):
    pass

class Player(Entity): # TODO move this

  def __init__(self, game, player_id):
    super().__init__()
    # position
    self.x = 0.
    self.y = 0.
    self.w = 0.5
    self.h = 0.5
    # movement
    self.dx = 0
    self.dy = 0
    self.wasd_pressed = {key: False for key in ['w', 'a', 's', 'd']}
    self.speed = 7.2
    # rolling
    self.roll_cooldown = 0
    self.max_roll_cooldown = 50
    self.roll_duration = 8
    # shooting
    # (for now carry multiple weapons. this may change)
    self.weapons = [Weapon(game, self) for Weapon in weapon.weapons]
    self.cur_weapon_idx = 0
    self.cur_weapon = self.weapons[self.cur_weapon_idx]
    # combat
    self.hp = 100
    self.flash_cooldown = 0 # tmp: damage flash demo purposes
    # graphics
    self.sprite_id = 1 + player_id % 2
    # game stuff
    self.keys = keys.Keys()
    self.player_id = player_id
    self.game = game

  def compute_reactive_wasd(self, key_p, key_n):
    # accepts key_p (key in positive dir) and key_n (key in negative dir)
    # if two opposite keys are pressed at the same time, then prefer to go
    # in the direction that was NOT last pressed (ie., that self.wasd_pressed[key]=False)
    if self.keys.pressed(key_p) and self.keys.pressed(key_n):
      # if both pressed then go in the opposite direction currently going
      if self.wasd_pressed[key_p]:
        return -1
      elif self.wasd_pressed[key_n]:
        return +1
      else:
        # if its a tie, then prefer to go up and right (to the positive dir)
        self.wasd_pressed[key_n] = True
        return +1
    elif self.keys.pressed(key_p):
      self.wasd_pressed[key_p] = True
      self.wasd_pressed[key_n] = False
      return +1
    elif self.keys.pressed(key_n):
      self.wasd_pressed[key_p] = False
      self.wasd_pressed[key_n] = True
      return -1
    else:
      self.wasd_pressed[key_p] = False
      self.wasd_pressed[key_n] = False
      return 0

  def compute_wasd(self):
    # recompute wasd movement
    self.dx = self.compute_reactive_wasd('d', 'a')
    self.dy = self.compute_reactive_wasd('w', 's')

    mult = self.speed
    if self.keys.pressed('shift') and not self.roll_cooldown and (self.dx or self.dy):
      mult *= 3.
      self.roll_cooldown = self.max_roll_cooldown

    if self.dx != 0 and self.dy != 0:
      # don't move faster by moving diagonally
      mult *= 2 ** -0.5

    self.dx *= mult
    self.dy *= mult

  def is_rolling(self):
    return self.max_roll_cooldown - self.roll_cooldown <= self.roll_duration

  def move(self, delta):
    if self.roll_cooldown:
      self.roll_cooldown -= 1

    if self.is_rolling():
      # we are still rolling
      pass
    else:
      self.compute_wasd()

    self.x += delta * self.dx
    self.y += delta * self.dy

  def shoot(self):
    shoot_dx = 0
    shoot_dy = 0
    if self.keys.pressed('arrowup'):
      shoot_dy += 1
    if self.keys.pressed('arrowleft'):
      shoot_dx -= 1
    if self.keys.pressed('arrowdown'):
      shoot_dy -= 1
    if self.keys.pressed('arrowright'):
      shoot_dx += 1

    self.cur_weapon.use(shoot_dx, shoot_dy)

  def damage(self, dmg):
    if self.is_rolling():
      return False
    self.hp -= dmg
    # tmp: damage flash for demp purposes
    self.sprite_id = 0
    self.flash_cooldown = 5
    return True

  def tick(self, delta):
    self.move(delta)
    self.shoot()

    # tmp: switch weapon for demo purposes
    if self.keys.released(' '):
      self.cur_weapon_idx += 1
      self.cur_weapon_idx %= len(self.weapons)
      self.cur_weapon = self.weapons[self.cur_weapon_idx]

    # tmp: damage flash for demo purposes
    if self.flash_cooldown == 0:
      self.sprite_id = 1 + self.player_id % 2
    else:
      self.flash_cooldown -= 1

  def collide_tile(self, tiles):
    for tile_x, tile_y, tile_w, tile_h in tiles:
      # undo prev move
      self.x -= self.dx
      self.y -= self.dy
      # calculate slide
      self.dx, self.dy = aabb.collide_and_slide(
        self.dx, self.dy,
        self.aabb_x, self.aabb_y, self.aabb_w, self.aabb_h,
        tile_x, tile_y, tile_w, tile_h,
      )
      # update pos
      self.x += self.dx
      self.y += self.dy
      self.update_aabb()


class Bullet(Entity):

  def __init__(self, game, src, x, y, dir, momentum=(0, 0)):
    self.x = x
    self.y = y
    self.w = 0.25
    self.h = 0.25
    self.dx, self.dy = dir
    self.mx, self.my = momentum
    # game info
    self.speed = 25
    self.dmg = 5 # do 5 damage
    self.lifespan = 120
    # graphics
    self.sprite_id = 0
    # misc
    self.src = src
    self.game = game

  def destroy(self, x, y):
    # TODO: spawn bullet destroy animation at x, y (eg., sparks) here
    self.game.remove_entity(self)

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
      self.destroy(other.x, other.y)

  def collide_tile(self, tiles):
    self.destroy(self.x, self.y) # TODO return self.x self.y with one calculated from tiles

  def damage(self, dmg):
    return False


