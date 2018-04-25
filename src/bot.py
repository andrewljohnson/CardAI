"""The base Bot class, plays randomly."""

from card import Card
from random import choice


class Bot(object):
	def __init__(self, hit_points=0, temp_mana=None):
		"""Set the initial stats and cards."""
		self.hit_points = hit_points
		self.hand = []
		self.lazy_hand = False
		self.temp_mana = []
		if temp_mana:
			self.temp_mana = list(temp_mana)

	def play_move(self, game):
		"""Play a random move in game."""
		move = choice(list(game.legal_plays(game.states[:])))
		game.next_state(None, move, game=game)

	def state_repr(self):
		"""Return a hashable tuple representing the Bot."""
		return (
			self.hit_points, 
			tuple([c.state_repr() for c in self.get_hand()]),
			tuple(self.temp_mana)
		)

	def adjust_for_end_turn(self):
		self.temp_mana = []

	def get_hand(self):
		if not self.lazy_hand:
			return self.hand
		self.lazy_hand = False
		instantiated_cards = [] 
		for card_tuple in self.hand:
			instantiated_cards.append(Card.card_for_state(card_tuple))
		self.hand = instantiated_cards
		return self.hand
