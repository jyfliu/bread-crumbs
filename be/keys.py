
class Keys:

  def __init__(self):
    self.keys = {}
    self.last_keys = {}

  def update(self, keys):
    self.keys = keys

  def pressed(self, key):
    return key in self.keys

  def released(self, key):
    return key in self.last_keys and key not in self.keys

  def tick(self):
    self.last_keys = self.keys

