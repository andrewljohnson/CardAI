"""RandomBot plays a random legal move on its turn."""

from bot import Bot
from random import choice


class RandomBot(Bot):


	def play_move(self, game):
		"""Play a random move in game."""
		move = choice(game.legal_plays([game.state_repr()], self.mana))
		self.states.append(game.next_state(game.state_repr(), move))
		game.do_move(move)
		
