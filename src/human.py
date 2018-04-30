"""MonteCarloBot plays out N iterations, trying out random move sequences affter legal moves."""

from bot import Bot
from game import Game


class Human(Bot):
	def play_move(self, game):
		"""Plays the move in game that wins the most over the test iterations."""
		legal_plays = game.legal_plays(game.states)

		for counter, play in enumerate(legal_plays):
			print "{}: {}".format(counter, play)

		if len(legal_plays) > 1: 
			answered = False
			while not answered:
				choice = input("Type the number of the action you want to play: ")
				if choice >= 0 and choice < len(legal_plays):
					answered = True
		else:
			choice = 0

		game.next_state(None, legal_plays[choice], game=game)
