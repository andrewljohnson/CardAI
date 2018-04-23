"""Card encapsulates the actions of a fantasy card."""

class Card(object):
	"""A fantasy card instance."""

	def __init__(self, owner, card_id, tapped=False):	
		"""Set the initial card_id and owner."""	
		self.id = card_id

		# the player_number of the owner
		self.owner = owner

		self.tapped = tapped

		self.color = ''

	def adjust_for_untap_phase(self):
		self.tapped = False

	def react_to_spell(self, card):
		pass

	def state_repr(self):
		"""Return a hashable tuple representing the Card."""
		return (
			self.__class__.__name__,
			self.id, 
			self.owner, 
			self.tapped, 
		)


class AnyManaLand(Card):
	"""A card that produces any color mana."""

	def __init__(self, owner, card_id, tapped=False, turn_played=None):
		super(AnyManaLand, self) \
			.__init__(owner, card_id, tapped=tapped)
		self.turn_played = turn_played

	def possible_moves(self, game):
		"""Returns [] if the player already played a land, other returns the action to play tapped."""
		if game.played_land():
			return []
		card_index = game.players[game.player_with_priority].hand.index(self)
		return [('card-land', card_index, 0, None)]

	def play(self, game, mana_to_use, target_creature_id):
		"""Remove this from the player's hand and add it to game.lands."""
		self.turn_played = game.current_turn
		game.lands.append(self)
		player = game.players[game.player_with_priority]
		player.hand.remove(self)
		if game.print_moves:
			print "> {} {} played a {}!" \
				.format(player.__class__.__name__, game.players.index(player), self.__class__.__name__, self.id, )

	def state_repr(self):
		"""Return a hashable tuple representing the AnyManaLand."""
		return (
			self.__class__.__name__,
			self.id, 
			self.owner, 
			self.turn_played, 
			self.tapped, 
		)

	def mana_provided(self):
		"""The amount and kind of mana provided."""
		return {'BUGRW': 1}


class Forest(AnyManaLand):
	"""A card that produces green mana."""

	def mana_provided(self):
		"""The amount and kind of mana provided."""
		return {'G': 1}


class Mountain(AnyManaLand):
	"""A card that produces red mana."""

	def mana_provided(self):
		"""The amount and kind of mana provided."""
		return {'R': 1}


class Fireball(Card):
	"""A card that deal X damage to anything."""

	def possible_moves(self, game):
		"""Returns possible fireballs targets and amounts."""
		available_mana = game.available_mana()
		possible_moves = []
		card_index = game.players[game.player_with_priority].hand.index(self)
		
		has_red = False
		total_mana = 0
		for color, count in available_mana.iteritems():
			total_mana += count
			if 'R' in color:
				has_red = True

		if has_red and total_mana > 1:
			for mana in range(2, total_mana+1):
				possible_moves.append(('card-fireball', card_index, mana, None))
			for c in game.creatures:
				for mana in range(2, total_mana+1):
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
				print "> {} {} fireballed {} for {} damage.".format(blaster.__class__.__name__, game.players.index(blaster), creature.__class__.__name__, mana_to_use - 1)
		else:
			blastee = game.opponent(blaster)
			blastee.hit_points -= (mana_to_use - 1)

			if game.print_moves:
				print "> {} {} FIREBALLED for {} damage!".format(blaster.__class__.__name__, game.players.index(blaster), mana_to_use - 1)


class Creature(Card):
	"""A fantasy creature card instance."""

	def __init__(self, owner, card_id, turn_played):
		super(Creature, self).__init__(owner, card_id)
		# the turn number this came into play
		self.turn_played = turn_played

	def state_repr(self):
		"""Return a hashable representation of the creature."""
		return (self.__class__.__name__,
			 	self.owner, 
				self.id, 
				self.turn_played,
		)

	def can_attack(self, game):
		"""Returns False if the creature was summoned this turn."""
		return self.turn_played < game.current_turn and self.tapped == False


class Bear(Creature):
	"""A 2/2 creature."""

	def __init__(self, owner, card_id, turn_played):
		super(Bear, self).__init__(owner, card_id, turn_played)
		self.strength = 2
		self.hit_points = 2
		self.color = 'G'

	def total_mana_cost(self):
		return 2

	def possible_moves(self, game):
		"""Returns [] if the player has less than 2 man, other returns the action to play the bear."""
		available_mana = game.available_mana()
		has_green = False
		total_mana = 0
		for color, count in available_mana.iteritems():
			total_mana += count
			if 'G' in color:
				has_green = True
		if has_green and total_mana >= self.total_mana_cost():
			card_index = game.players[game.player_with_priority].hand.index(self)
			return [('card-bear', card_index, self.total_mana_cost(), None)]
		return []

	def play(self, game, mana_to_use, target_creature_id):
		"""Summon the bear for the player_with_priority."""
		self.id = game.new_card_id
		summoner = game.players[game.player_with_priority]
		summoner.hand.remove(self)
		game.new_card_id += 1
		self.turn_played = game.current_turn
		game.creatures.append(self)
		if game.print_moves:
			player = game.players[game.player_with_priority]
			print "> {} {} summoned a {}/{} {}.".format(player.__class__.__name__, game.players.index(player), self.strength, self.hit_points, self.__class__.__name__)

class NettleSentinel(Bear):

	def total_mana_cost(self):
		return 1

	def adjust_for_untap_phase(self):
		pass

	def react_to_spell(self, card):
		if 'G' in card.color:
			self.tapped = False

