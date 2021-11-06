import numpy as np

import math
import random

import aabb

class World:

  def __init__(self, tiles, tile_to_sprite_id=lambda x: x, spawnx=0, spawny=0):
    tiles = np.asarray(tiles) # convert to array if not already
    self.tiles = tiles

    # compute bounding boxes
    xi, yi = (tiles % 2).nonzero() # odd tiles have collision boxes
    self.aabbs = [] # TODO turn into quad tree, and maybe merge adjacent tiles to one aabb
    for x, y in zip(xi, yi):
      self.aabbs.append((x - 0.5, y - 0.5))

    # compute renderable data
    self.render = np.vectorize(tile_to_sprite_id)(self.tiles).tolist()

    # default player spawn
    self.spawnx = spawnx
    self.spawny = spawny


  def intersect(self, aabb_x, aabb_y, aabb_w, aabb_h):
    intersects = []
    for x, y in self.aabbs:
      if aabb.intersect(aabb_x, aabb_y, aabb_w, aabb_h, x, y, 1, 1):
        intersects.append((x, y, 1, 1))
    return intersects

def gen_dungeon(
  width=100, height=100,
  min_room_size=10, max_room_size=15, num_rooms=20,
  max_corridor_length=25, corridor_width=3,
):
  # possibly the most spaghetti code i have written in my life begins here
  assert width >= 3, "min width is 3"
  assert height >= 3, "min height is 3"
  assert max_room_size >= min_room_size, "what u doing"
  assert max_room_size <= width
  assert max_room_size <= height
  assert num_rooms >= 1

  # some helper functions
  def in_bounds(x, y):
    return x >= 0 and y >= 0 and x < width and y < width

  def set_if_void(arr, val=0, void=0):
    arr[arr == void] = val

  # begin generation here
  tiles = np.zeros((width, height))
  random.seed(24)

  # ******* room generation *******
  for _ in range(num_rooms):
    room_w = random.randint(min_room_size, max_room_size)
    room_h = random.randint(min_room_size, max_room_size)
    x = random.randrange(0, width-room_w)
    y = random.randrange(0, height-room_h)

    # four walls of the rooms
    # make sure you only overwrite 0 (void) tiles to wall
    set_if_void(tiles[x:x+room_w, y], 3)
    set_if_void(tiles[x:x+room_w, y+room_h-1], 3)
    set_if_void(tiles[x, y:y+room_h], 3)
    set_if_void(tiles[x+room_w-1, y:y+room_h], 3)
    # center of the room
    tiles[x+1:x+room_w-1, y+1:y+room_h-1] = 2

  # find a random start/end point
  for i in range(100005):
    # note: for some unlucky configurations of rooms this can run forever
    if i > 100000:
      raise "Unlucky room generation. Change RNG seed and try again"
    sx, sy = random.randrange(0, width), random.randrange(0, height)
    if tiles[sx, sy] != 2:
      continue
    ex, ey = random.randrange(0, width), random.randrange(0, height)
    if tiles[ex, ey] != 2:
      continue

    if abs(sx - ex) + abs(sy - ey) > (width + height) // 2:
      break

  # give these variables less retarded variable names for later use
  start_x, start_y = sx, sy
  end_x, end_y = ex, ey

  # ******* corridors between rooms *******

  # dfs helper
  visited = np.zeros_like(tiles)
  def dfs(ux, uy, colour, bkgd=0):
    # dfs function that recursively paint buckets a bkgd colour to a different one
    stack = [(ux, uy)]
    while stack:
      ux, uy = stack.pop()
      visited[ux, uy] = colour
      neighbours = [(ux - 1, uy), (ux + 1, uy), (ux, uy - 1), (ux, uy + 1)]
      for vx, vy in neighbours:
        if in_bounds(vx, vy) and tiles[vx, vy] == 2 and visited[vx, vy] == bkgd:
          stack.append((vx, vy))

  # colour each room differently
  colour = 1
  for x in range(width):
    for y in range(width):
      if tiles[x, y] == 2 and not visited[x, y]:
        dfs(x, y, colour)
        colour += 1
  colours = set(range(1, colour)) # remaining colours we haven't merged yet

  # half the width of a corridor
  offset = corridor_width // 2
  # cardinal directions
  dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]
  # all adjacent squares within a radius of offset (manhattan distance)
  adjs = [(x, y) for x in range(-offset, offset+1) for y in range(-offset, offset+1)]
  for _ in range(10005):
    # pick starting point for the corridor
    x, y = random.randrange(offset+1, width-offset-1), random.randrange(offset+1, height-offset-1)

    # make sure that the starting point is inside a room
    cur_colour = visited[x, y]
    if cur_colour == 0:
      # not in a room
      continue
    # if the starting point is in a room, we still need to make sure
    # there is enough room for a corridor
    if not (visited[x-offset:x+offset+1, y-offset:y+offset+1] == cur_colour).all():
      # if we enter here, then there is not enough room for a hallway centred
      # at x, y. However, there may be a valid starting point within the
      # square centred at (x, y) with radius offset, ie., the array adj
      # so let us try all of them by brute force

      # by doing it this way, we increase the likelihood that a corridor
      # can start inside another corridor
      random.shuffle(adjs)
      tmp_x, tmp_y = x, y
      for dx, dy in adjs:
        x, y = tmp_x + dx, tmp_y + y
        if (visited[x-1:x+2, y-1:y+2] == cur_colour).all():
          # found a valid starting point
          break
      else: # for else clause
        # couldn't find any valid adj neighbours
        continue

    done = False
    # try all the possible directions the corridor can go
    random.shuffle(dirs) # remove bias from directions
    for dx, dy in dirs:
      if done:
        break
      # try all the possible lengths the corridor can be
      for step in range(max_corridor_length):
        if done:
          break
        if not in_bounds(x + dx * step, y + dy * step):
          break
        # make sure that the ending point is inside a room
        if visited[x + dx * step, y + dy * step] != cur_colour:
          ox, oy = x + dx * step, y + dy * step
          other_colour = visited[ox, oy]
          if not other_colour:
            continue
          # check to make sure other connection is wide enough
          # corridor width in x and y directions resp.
          cw_x = abs(dy * offset) - 1
          cw_y = abs(dx * offset) - 1
          if (visited[ox-cw_x:ox+cw_x+1, oy-cw_y:oy+cw_y+1] == other_colour).all():
            dir = (dx, dy)
            done = True
            break
    if not done:
      continue
    # fill other room with this colour
    dfs(ox, oy, cur_colour, bkgd=other_colour)
    # fill in the corridor tiles
    dx, dy = dir
    if dx:
      # horizontal
      tiles[x:ox+dx:dx, y-offset:y+offset+1] = 2
      visited[x:ox+dx:dx, y-offset:y+offset+1] = cur_colour
      set_if_void(tiles[x:ox+dx:dx, y-offset-1], 3)
      set_if_void(tiles[x:ox+dx:dx, y+offset+1], 3)
    if dy:
      # horizontal
      tiles[x-offset:x+offset+1, y:oy+dy:dy] = 2
      visited[x-offset:x+offset+1, y:oy+dy:dy] = cur_colour
      set_if_void(tiles[x-offset-1, y:oy+dy:dy], 3)
      set_if_void(tiles[x+offset+1, y:oy+dy:dy], 3)
    colours.remove(other_colour)

  # TODO: after this step there still could be isolated rooms
  if len(colours) > 1:
    raise "bad generation seed? there are still disconnected rooms (todo!)"

  # ******* structures *******
  # TODO (like obstacles and stuff?)


  # start / end tiles
  # (maybe like ladders or something to enter/exit this level)
  tiles[start_x, start_y] = 4
  tiles[end_x, end_y] = 6

  def to_colour(tile):
    # spaghetti hardcoded magic numbers for now, until sprites are done
    if tile == 2:
      return 3
    elif tile == 4:
      return 7 # start
    elif tile == 6:
      return 8 # end
    elif tile == 0:
      return 6
    else:
      return 4

  return World(tiles, to_colour, start_x, start_y)


