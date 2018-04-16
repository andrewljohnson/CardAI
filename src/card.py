class Card(object):
	"""A fantasy card instance."""

	def __init__(self, owner, mana_cost=None, guid=None):
		
		self.guid = guid

		# the player_number of the owner
		self.owner = owner

		# the amount of mana this card costs to cast
		self.mana_cost = mana_cost


	def state_repr(self):
		return (self.__class__.__name__,
				self.guid, 
			 	self.owner, 
				self.mana_cost
		)


class AnyManaLand(Card):
	"""A fantasy card instance."""

	def __init__(self, owner, mana_cost=None, guid=None):
		super(AnyManaLand, self).__init__(owner, guid=guid)

	def possible_moves(self, game):
		if game.played_land:
			return []
		card_index = game.players[game.player_with_priority].hand.index(self)
		if card_index != 0:
			print card_index
		return [('play_land', game.player_with_priority, card_index, 'play_tapped')]

	def play_tapped(self, game):
		"""Increment a mana from player_number."""
		player = game.players[game.player_with_priority]
		player.mana += 1
		game.played_land = True

		land_to_play = None
		for card in player.hand:
			if card.guid == self.guid:
				land_to_play = card
				break

		player.hand.remove(land_to_play)
		if game.print_moves:
			print "> {} {} played a TAPPED LAND!".format(player.__class__.__name__, game.players.index(player))


class Creature():
	"""A fantasy creature card instance."""

	def __init__(self, owner, strength=0, hit_points=0, guid=None):
		
		self.guid = guid

		# the player_number of the owner
		self.owner = owner

		# how much hit points this removes when it attacks
		self.strength = strength 

		# how many hit_points this takes to kill it
		self.hit_points = hit_points

	def state_repr(self):
		return (self.guid, 
			 	self.owner, 
			 	self.strength, 
				self.hit_points
		)

