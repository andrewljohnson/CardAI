"""The base Bot class."""

class Bot(object):
	def __init__(self, starting_hit_points=0, current_mana=0, starting_mana=0, hand=[]):
		self.hand = hand
		self.hit_points = starting_hit_points
		self.mana = starting_mana
		self.current_mana = current_mana

	def update(self, state):
		pass
