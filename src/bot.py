"""The base Bot class, plays randomly."""

from random import choice


class Bot(object):
	def __init__(self, hit_points=0):
		"""Set the initial stats and cards."""
		self.hit_points = hit_points
		self.hand = []
		self.temp_mana = []

	def play_move(self, game):
		"""Play a random move in game."""
		move = choice(game.legal_plays(game.states[:]))
		game.do_move(move)

	def state_repr(self):
		"""Return a hashable tuple representing the Bot."""
		return (
			self.hit_points, 
			tuple([c.state_repr() for c in self.hand]),
			tuple(self.temp_mana)
		)

	def adjust_for_end_turn(self):
		self.temp_mana = []
