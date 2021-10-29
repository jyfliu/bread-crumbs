

def intersect(ax, ay, aw, ah, bx, by, bw, bh):
  # returns if two AABBs intersect
  return ax < bx + bw and ax + aw > bx and ay < by + bh and ay + ah > by


