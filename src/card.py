class Card(object):
	"""A fantasy card instance."""

	def __init__(self, owner, guid=None):		
		self.guid = guid

		# the player_number of the owner
		self.owner = owner

	def state_repr(self):
		return (self.__class__.__name__,
				self.guid, 
			 	self.owner, 
		)


class AnyManaLand(Card):
	"""A card that produces any color mana."""

	def __init__(self, owner, guid=None):
		super(AnyManaLand, self).__init__(owner, guid=guid)

	def possible_moves(self, game):
		if game.played_land:
			return []
		card_index = game.players[game.player_with_priority].hand.index(self)
		return [('card-land', card_index, 0, None)]

	def play(self, game, mana_to_use, target_creature_id):
		"""Increment a mana from player_number."""
		player = game.players[game.player_with_priority]
		player.mana += 1
		game.played_land = True

		player.hand.remove(self)

    if game.print_moves:
			print "> {} {} played a TAPPED LAND!".format(player.__class__.__name__, game.players.index(player))


class Fireball(Card):
	"""A card that deal X damage to anything."""

	def __init__(self, owner, guid=None):
		super(Fireball, self).__init__(owner, guid=guid)

	def possible_moves(self, game):
		available_mana = game.players[game.player_with_priority].current_mana
		possible_moves = []
		card_index = game.players[game.player_with_priority].hand.index(self)
		
		if available_mana > 1:
			for mana in range(2, available_mana+1):
				possible_moves.append(('card-fireball', card_index, mana, None))
			for c in game.creatures:
				for mana in range(2, available_mana+1):
					possible_moves.append(('card-fireball-creature', card_index, mana, c.guid))
		return possible_moves

	def play(self, game, mana_to_use, target_creature_id):
		"""Decrement hit_points equal to blaster's mana from blastee."""
		blaster = game.players[game.player_with_priority]
		blaster.hand.remove(self)

		if target_creature_id:
			blaster = game.players[game.player_with_priority]
			creature = game.creature_with_guid(target_creature_id)
			if (mana_to_use - 1) >= creature.hit_points:
				if creature.guid in game.attackers:
					game.attackers.remove(creature.guid)
				game.creatures.remove(creature)
				if creature.guid in game.ready_creatures:
					game.ready_creatures.remove(creature.guid)
			else:
				creature.hit_points -= (mana_to_use - 1)

			if game.print_moves:
				print "> {} {} FIREBALLED CREATURE {} for {} damage!".format(blaster.__class__.__name__, game.players.index(blaster), creature.guid, mana_to_use - 1)
		else:
			blastee = game.opponent(blaster)
			blastee.hit_points -= (mana_to_use - 1)

			if game.print_moves:
				print "> {} {} FIREBALLED for {} damage!".format(blaster.__class__.__name__, game.players.index(blaster), mana_to_use - 1)


class Bear(Card):
	"""A 2/2 creature."""

	def __init__(self, owner, guid=None):
		super(Bear, self).__init__(owner, guid=guid)

	def possible_moves(self, game):
		available_mana = game.players[game.player_with_priority].current_mana
		if available_mana > 1:
			card_index = game.players[game.player_with_priority].hand.index(self)
			return [('card-bear', card_index, 2, None)]
		return []

	def play(self, game, mana_to_use, target_creature_id):
		c = Creature(game.player_with_priority, strength=5, hit_points=2, guid=game.new_card_id)
		summoner = game.players[game.player_with_priority]
		summoner.hand.remove(self)
		game.new_card_id += 1
		game.creatures.append(c)
		if game.print_moves:
			player = game.players[game.player_with_priority]
			print "> {} {} SUMMONED a {}/{} BEAR.".format(player.__class__.__name__, game.players.index(player), c.strength, c.hit_points)


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

''' NEW CARD CODE FOR LATER

	def shock(self, player_number):
		"""Decrement some damage from player_number."""
		player = self.players[player_number]
		damage = 2
		player.hit_points -= damage
		opponent = self.opponent(player)
		if self.print_moves:
			print "> {} {} SHOCKED for {} damage!".format(opponent.__class__.__name__, self.players.index(opponent), damage)

	def edict(self, player_number):
		"""Remove a creature from player_number, FIFO for now."""
		new_creatures = []
		killed = False
		killed_guid = None
		for c in self.creatures:
			if not killed and c.owner == player_number:
				killed = True
				killed_guid = c.guid
			else:
				new_creatures.append(c)
		if self.print_moves:
			opponent = self.players[player_number]
			current_player = self.opponent(opponent)
			print "> {} {} EDICTED.".format(current_player.__class__.__name__, self.players.index(current_player))
		self.creatures = new_creatures
		if killed_guid in self.ready_creatures:
			self.ready_creatures.remove(killed_guid)

	def wrath(self, player_number):
		"""Remove all creature for player_number."""
		if self.print_moves:
			opponent = self.players[player_number]
			current_player = self.opponent(opponent)
			print "> {} {} WRATHED, {} creatures died.".format(current_player.__class__.__name__, self.players.index(current_player), len(self.creatures))
		self.creatures = []
		self.ready_creatures = []
'''
