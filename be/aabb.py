import math

def intersect(ax, ay, aw, ah, bx, by, bw, bh):
  # returns if two AABBs intersect
  return ax < bx + bw and ax + aw > bx and ay < by + bh and ay + ah > by


def _fix_rounding_error(x):
  if abs(x) < 0.000001:
    return 0
  else:
    return x

def collide_and_slide(
    dx, dy, # velocity
    ax, ay, aw, ah,
    bx, by, bw, bh,
):
  # compute centres
  acx = ax + aw / 2.
  acy = ay + ah / 2.
  bcx = bx + bw / 2.
  bcy = by + bh / 2.
  # compute overlaps
  xoverlap = (aw + bw) / 2. - abs(acx - bcx)
  yoverlap = (ah + bh) / 2. - abs(acy - bcy)

  xt = abs(xoverlap / (dx + 0.000001))
  yt = abs(yoverlap / (dy + 0.000001))

  if xt < yt:
    return (_fix_rounding_error(dx - math.copysign(xoverlap, dx)), dy)
  else:
    return (dx, _fix_rounding_error(dy - math.copysign(yoverlap, dy)))

