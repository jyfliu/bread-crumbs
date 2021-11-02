import numpy as np

import aabb

class World:

  def __init__(self, tiles, tile_to_sprite_id=lambda x: x):
    tiles = np.asarray(tiles) # convert to array if not already
    self.tiles = tiles

    # compute bounding boxes
    xi, yi = (tiles % 2).nonzero() # odd tiles have collision boxes
    self.aabbs = [] # TODO turn into quad tree, and maybe merge adjacent tiles to one aabb
    for x, y in zip(xi, yi):
      self.aabbs.append((x - 0.5, y - 0.5))

    # compute renderable data
    self.render = np.vectorize(tile_to_sprite_id)(self.tiles).tolist()


  def intersect(self, aabb_x, aabb_y, aabb_w, aabb_h):
    for x, y in self.aabbs:
      if aabb.intersect(aabb_x, aabb_y, aabb_w, aabb_h, x, y, 1, 1):
        return True
    return False

