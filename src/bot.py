"""The base Bot class."""

class Bot():
	def __init__(self, starting_hit_points=0, starting_mana=0):
		self.hit_points = starting_hit_points
		self.mana = starting_mana

	def update(self, state):
		pass
