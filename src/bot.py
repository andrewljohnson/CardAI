"""The base Bot class, plays randomly."""

from constants import *
from game import Game
from random import choice

class Bot(object):

	def play_move(self, game_state, statcache):
		"""Play a random move in game."""
		#print "BOT starting in gs {}".format(decarded_state(game_state))
		move = choice(list(Game.legal_plays(game_state)))
		game_state = Game.apply_move(game_state, move)
		statcache.past_states.append(game_state)
		# print "BOT chose {}".format(move)
		#print "BOT moved to gs {}".format(decarded_state(game_state))
		return move, game_state


def decarded_state(state_clone):
	mutable_player = list(state_clone[4][0])
	mutable_player[1] = ()
	mutable_player[4] = ()

	mutable_players = list(state_clone[4])
	mutable_players[0] = tuple(mutable_player)

	mutable_player = list(state_clone[4][1])
	mutable_player[1] = ()
	mutable_player[4] = ()

	mutable_players[1] = tuple(mutable_player)

	mutable_state = list(state_clone)
	mutable_state[4] = tuple(mutable_players)
	mutable_state[14] = True
	return tuple(mutable_state)


