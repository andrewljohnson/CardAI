"""Card encapsulates the actions of a fantasy card."""

class Card(object):
	"""A fantasy card instance."""

	def __init__(self, owner, card_id, tapped=False, turn_played=False):	
		"""Set the initial card_id and owner."""	
		self.id = card_id

		# the player_number of the owner
		self.owner = owner

		self.tapped = tapped

		self.turn_played = turn_played

		self.card_type = None

	@staticmethod
	def available_cards():
		"""All possible cards in the game."""
		return [
			#Mountain(moving_player, self.new_card_id),
			#Fireball(moving_player, self.new_card_id),
			#Forest(moving_player),
			#NettleSentinel(moving_player, current_turn),
			#VinesOfVastwood(moving_player, current_turn),
			#Mountain,
			#Fireball,
			Forest,
			NettleSentinel,
			VinesOfVastwood,
		]

	@staticmethod
	def card_for_state(state):
		return eval("{}".format(state[0]))(state[1], state[2], tapped=state[3], turn_played=state[4])


	def state_repr(self):
		"""Return a hashable tuple representing the Card."""
		return (
			self.__class__.__name__,
			self.owner, 
			self.id, 
			self.tapped, 
			self.turn_played, 
		)

	def adjust_for_untap_phase(self):
		self.tapped = False

	def react_to_spell(self, card):
		pass

	def adjust_for_end_turn(self):
		pass

	def total_mana_cost(self):
		return []


class Land(Card):
	"""A card that produces any color mana."""

	def __init__(self, owner, card_id, tapped=False, turn_played=None):
		super(Land, self).__init__(owner, card_id, tapped=tapped, turn_played=turn_played)

	@staticmethod
	def land_for_state(state):
		classname = state[0]
		land = eval("{}".format(classname))(
			state[1],
			state[2], 
			tapped=state[3],
			turn_played=state[4],
		)
		return land

	def state_repr(self):
		"""Return a hashable tuple representing the Land."""
		return (
			self.__class__.__name__,
			self.owner, 
			self.id, 
			self.tapped, 
			self.turn_played, 
		)

	def possible_moves(self, game):
		"""Returns [] if the player already played a land, other returns the action to play tapped."""
		if game.played_land():
			return []
		card_index = game.players[game.player_with_priority].hand.index(self)
		return [('card-{}'.format(self.__class__.__name__), card_index, [], None)]

	def play(self, game, mana_to_use, target_creature_id):
		"""Remove this from the player's hand and add it to game.lands."""
		self.turn_played = game.current_turn
		game.lands.append(self)
		player = game.players[game.player_with_priority]
		player.hand.remove(self)
		if game.print_moves:
			print "> {} {} played a {}!" \
				.format(player.__class__.__name__, game.players.index(player), self.__class__.__name__, self.id, )

	def mana_provided(self):
		"""The amount and kind of mana provided."""
		return {'BUGRW': 1}


class Forest(Land):
	"""A card that produces green mana."""

	def mana_provided(self):
		"""The amount and kind of mana provided."""
		return {'G': 1}


class Mountain(Land):
	"""A card that produces red mana."""

	def mana_provided(self):
		"""The amount and kind of mana provided."""
		return {'R': 1}


class VinesOfVastwood(Card):
	"""A card that buffs a creature."""

	def __init__(self, owner, card_id, tapped=False, turn_played=None):
		super(VinesOfVastwood, self).__init__(owner, card_id, tapped=tapped, turn_played=turn_played)
		self.card_type = 'instant'

	def possible_moves(self, game):
		"""Returns possible VinesOfVastwood targets."""
		if game.phase != 'combat_resolution':
			return []
		available_mana = game.available_mana()
		possible_moves = []
		card_index = game.players[game.player_with_priority].hand.index(self)
		
		green_count = 0
		for color, count in available_mana.iteritems():
			if 'G' in color:
				green_count += count

		for c in game.creatures:
			if green_count > 0:
				possible_moves.append(('card-{}'.format(self.__class__.__name__), card_index, ['G'], c.id))
			if green_count > 1:
				possible_moves.append(('card-{}'.format(self.__class__.__name__), card_index, ['G', 'G'], c.id))

		return possible_moves

	def play(self, game, mana_to_use, target_creature_id):
		"""Pump a creature based on how much mana is used."""
		creature = game.creature_with_id(target_creature_id)
		creature.temp_targettable = False
		caster = game.players[game.player_with_priority]
		if mana_to_use == ['G', 'G']:
			creature.temp_strength += 4
			creature.temp_hit_points += 4
		if game.print_moves:
			if mana_to_use == ['G']:
				print "> {} {} played VinesOfVastwood on {}." \
					.format(
						caster.__class__.__name__, 
						game.players.index(caster), 
						creature.__class__.__name__)
			else:
				print "> {} {} played kicked VinesOfVastwood on {}, total power now {}." \
					.format(
						caster.__class__.__name__, 
						game.players.index(caster), 
						creature.__class__.__name__,
						creature.total_damage())

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
				possible_moves.append(('card-fireball', card_index, ['R', mana-1], None))
			for c in game.creatures:
				if c.targettable and c.temp_targettable:
					for mana in range(2, total_mana+1):
						possible_moves.append(('card-fireball-creature', card_index, ['R', mana-1], c.id))
		return possible_moves

	def play(self, game, mana_to_use, target_creature_id):
		"""Decrement hit_points equal to blaster's mana from blastee."""
		blaster = game.players[game.player_with_priority]
		blaster.hand.remove(self)

		colorless = 0
		for mana in mana_to_use:
			if isinstance(mana, int):
				colorless = mana
				break
		if target_creature_id:
			blaster = game.players[game.player_with_priority]
			creature = game.creature_with_id(target_creature_id)
			if (colorless) >= creature.hit_points:
				if creature.id in game.attackers:
					game.attackers.remove(creature.id)
				game.creatures.remove(creature)
			else:
				creature.hit_points -= colorless

			if game.print_moves:
				print "> {} {} fireballed {} for {} damage." \
				.format(blaster.__class__.__name__, game.players.index(blaster), creature.__class__.__name__, colorless)
		else:
			blastee = game.opponent(blaster)
			blastee.hit_points -= (colorless)

			if game.print_moves:
				print "> {} {} FIREBALLED for {} damage!" \
				.format(blaster.__class__.__name__, game.players.index(blaster), colorless)


class Creature(Card):
	"""A fantasy creature card instance."""

	def __init__(self, owner, card_id, tapped=False, turn_played=-1):
		super(Creature, self).__init__(owner, card_id, tapped=tapped, turn_played=turn_played)
		self.strength = self.initial_strength()
		self.hit_points = self.initial_hit_points()
		self.targettable = True
		self.temp_strength = 0
		self.temp_hit_points = 0
		self.temp_targettable = True

	@staticmethod
	def creature_for_state(state):
		classname = state[0]
		c = eval("{}".format(classname))(
			state[1], 
			state[2], 
			tapped=state[3],
			turn_played=state[4],
		)
		c.targettable = state[5]
		c.temp_strength = state[6]
		c.temp_hit_points = state[7]
		c.temp_targettable =state[8]

		return c

	def state_repr(self):
		"""Return a hashable representation of the creature."""
		return (self.__class__.__name__,
			 	self.owner, 
				self.id, 
				self.tapped, 
				self.turn_played,
				self.targettable, 
				self.temp_strength, 
				self.temp_hit_points,
				self.temp_targettable,
		)

	def initial_strength():
		return 0

	def initial_hit_points():
		return 0

	def adjust_for_end_turn(self):
		self.temp_strength = 0
		self.temp_hit_points = 0
		self.temp_targettable = True

	def total_damage(self):
		return self.strength + self.temp_strength

	def total_hit_points(self):
		return self.hit_points + self.temp_hit_points

	def mana_cost(self):
		colorless = 0
		for mana in self.total_mana_cost():
			if isinstance(mana, int):
				colorless += mana
			else:
				colorless += 1
		return colorless

	def can_attack(self, game):
		"""Returns False if the creature was summoned this turn."""
		return self.turn_played < game.current_turn and self.tapped == False

	def play(self, game, mana_to_use, target_creature_id):
		"""Summon the bear for the player_with_priority."""
		summoner = game.players[game.player_with_priority]
		summoner.hand.remove(self)
		self.turn_played = game.current_turn
		game.creatures.append(self)
		if game.print_moves:
			player = game.players[game.player_with_priority]
			print "> {} {} summoned a {}/{} {}.".format(player.__class__.__name__, game.players.index(player), self.strength, self.hit_points, self.__class__.__name__)

	def possible_moves(self, game):
		"""Returns [] if the player has less than 2 man, other returns the action to play the bear."""
		available_mana = game.available_mana()
		has_green = False
		total_mana = 0
		for color, count in available_mana.iteritems():
			total_mana += count
			if 'G' in color:
				has_green = True
		if has_green and total_mana >= self.mana_cost():
			card_index = game.players[game.player_with_priority].hand.index(self)
			return [('card-{}'.format(self.__class__.__name__), card_index, self.total_mana_cost(), None)]
		return []


class Bear(Creature):
	"""A 2/2 creature."""

	def initial_strength():
		return 2

	def initial_hit_points():
		return 2

	def total_mana_cost(self):
		return ['G', 1]


class NettleSentinel(Creature):
	"""
		Nettle Sentinel doesn't untap during your untap step.
		
		Whenever you cast a green spell, you may untap Nettle Sentinel.
	"""

	def total_mana_cost(self):
		return ['G']

	def initial_strength(self):
		return 2

	def initial_hit_points(self):
		return 2

	def adjust_for_untap_phase(self):
		pass

	def react_to_spell(self, card):
		if 'G' in card.total_mana_cost():
			self.tapped = False

