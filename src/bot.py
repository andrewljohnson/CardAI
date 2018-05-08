"""The base Bot class, plays randomly."""

from constants import *
from game import Game
from random import choice

class Bot(object):

	def play_move(self, game_state, statcache):
		"""Play a random move in game."""
		move = choice(list(Game.legal_plays(game_state)))
		game_state = Game.apply_move(game_state, move)
		statcache.past_states.append(game_state)
		print "bot played, states lennow {}".format(len(statcache.past_states))
		return move, game_state
