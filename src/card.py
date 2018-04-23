"""Card encapsulates the actions of a fantasy card."""

class Card(object):
	"""A fantasy card instance."""

	def __init__(self, owner, card_id=None):	
		"""Set the initial card_id and owner."""	
		self.id = card_id

		# the player_number of the owner
		self.owner = owner

	def state_repr(self):
		"""Return a hashable tuple representing the Card."""
		return (self.__class__.__name__,
				self.id, 
			 	self.owner, 
		)


class AnyManaLand(Card):
	"""A card that produces any color mana."""

	def __init__(self, owner, card_id=None, turn_played=None, is_tapped=False):
		super(AnyManaLand, self) \
			.__init__(owner, card_id=card_id)
		self.turn_played = turn_played
		self.is_tapped = is_tapped

	def possible_moves(self, game):
		"""Returns [] if the player already played a land, other returns the action to play tapped."""
		if game.played_land():
			return []
		card_index = game.players[game.player_with_priority].hand.index(self)
		return [('card-land', card_index, 0, None)]

	def play(self, game, mana_to_use, target_creature_id):
		"""Increment mana for the player with priority."""
		self.turn_played = game.current_turn
		game.lands.append(self)
		game.played_land = True
		player = game.players[game.player_with_priority]
		player.hand.remove(self)
		if game.print_moves:
			print "> {} {} played a LAND!".format(player.__class__.__name__, game.players.index(player))

	def state_repr(self):
		"""Return a hashable tuple representing the AnyManaLand."""
		return (self.__class__.__name__,
				self.id, 
			 	self.owner, 
			 	self.turn_played, 
			 	self.is_tapped, 
		)

class Fireball(Card):
	"""A card that deal X damage to anything."""

	def possible_moves(self, game):
		"""Returns possible fireballs targets and amounts."""
		available_mana = game.available_mana()
		possible_moves = []
		card_index = game.players[game.player_with_priority].hand.index(self)
		
		if available_mana > 1:
			for mana in range(2, available_mana+1):
				possible_moves.append(('card-fireball', card_index, mana, None))
			for c in game.creatures:
				for mana in range(2, available_mana+1):
					possible_moves.append(('card-fireball-creature', card_index, mana, c.id))
		return possible_moves

	def play(self, game, mana_to_use, target_creature_id):
		"""Decrement hit_points equal to blaster's mana from blastee."""
		blaster = game.players[game.player_with_priority]
		blaster.hand.remove(self)

		if target_creature_id:
			blaster = game.players[game.player_with_priority]
			creature = game.creature_with_id(target_creature_id)
			if (mana_to_use - 1) >= creature.hit_points:
				if creature.id in game.attackers:
					game.attackers.remove(creature.id)
				game.creatures.remove(creature)
			else:
				creature.hit_points -= (mana_to_use - 1)

			if game.print_moves:
				print "> {} {} FIREBALLED CREATURE {} for {} damage!".format(blaster.__class__.__name__, game.players.index(blaster), creature.id, mana_to_use - 1)
		else:
			blastee = game.opponent(blaster)
			blastee.hit_points -= (mana_to_use - 1)

			if game.print_moves:
				print "> {} {} FIREBALLED for {} damage!".format(blaster.__class__.__name__, game.players.index(blaster), mana_to_use - 1)


class Bear(Card):
	"""A 2/2 creature."""

	def possible_moves(self, game):
		"""Returns [] if the player has less than 2 man, other returns the action to play the bear."""
		available_mana = game.available_mana()
		if available_mana > 1:
			card_index = game.players[game.player_with_priority].hand.index(self)
			return [('card-bear', card_index, 2, None)]
		return []

	def play(self, game, mana_to_use, target_creature_id):
		"""Summon the bear for the player_with_priority."""
		c = Creature(game.player_with_priority, game.current_turn, strength=5, hit_points=1, creature_id=game.new_card_id)
		summoner = game.players[game.player_with_priority]
		summoner.hand.remove(self)
		game.new_card_id += 1
		c.turn_played = game.current_turn
		game.creatures.append(c)
		if game.print_moves:
			player = game.players[game.player_with_priority]
			print "> {} {} SUMMONED a {}/{} BEAR.".format(player.__class__.__name__, game.players.index(player), c.strength, c.hit_points)


class Creature():
	"""A fantasy creature card instance."""

	def __init__(self, owner, turn_played, strength=0, hit_points=0, creature_id=None):
		
		# an id that is unique among creatures in the game
		self.id = creature_id

		# the player_number of the owner
		self.owner = owner

		# how much hit points this removes when it attacks
		self.strength = strength 

		# how many hit_points this takes to kill it
		self.hit_points = hit_points

		# the turn number this came into play
		self.turn_played = turn_played

	def state_repr(self):
		"""Return a hashable representation of the creature."""
		return (self.id, 
			 	self.owner, 
			 	self.strength, 
				self.hit_points,
				self.turn_played,
		)

	def can_attack(self, game):
		"""Returns False if the creature was summoned this turn."""
		return self.turn_played < game.current_turn
