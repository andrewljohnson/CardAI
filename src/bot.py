"""The base Bot class, plays randomly."""

from random import choice


class Bot(object):
	def __init__(self, starting_hit_points=0, hand=[]):
		"""Set the initial stats and cards."""
		self.hand = hand
		self.hit_points = starting_hit_points

	def play_move(self, game):
		"""Play a random move in game."""
		move = choice(game.legal_plays([game.state_repr()]))
		game.do_move(move)

	def state_repr(self):
		"""Return a hashable tuple representing the Bot."""
		return (self.hit_points, 
				tuple([c.state_repr() for c in self.hand])
		)
