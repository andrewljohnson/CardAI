from re import finditer

"""Card encapsulates the actions of a fantasy card."""

class Card(object):
	"""A fantasy card instance."""

	def __init__(self, owner, card_id, tapped=False, turn_played=False):	
		"""Set the initial card_id and owner."""	
		self.id = card_id

		# the player_number of the owner
		self.owner = owner

		# whether the card is in tapped, only applies to permanents in play
		self.tapped = tapped

		# what turn number teh card last came into play
		self.turn_played = turn_played

		# "instant" or "creature" or "land"
		self.card_type = None

	@staticmethod
	def class_for_name(name):
		"""Return a dict mapping card name to class."""	
		card_classes = [
			BurningTreeEmissary,
			EldraziSpawnToken,
			ElephantGuide,
			Forest,
			HungerOfTheHowlpack,
			NestInvader,
			NettleSentinel,			
			QuirionRanger,
			Rancor,
			SilhanaLedgewalker,
			SkarrganPitSkulk,
			VaultSkirge,
			VinesOfVastwood,
		]
		class_map = {}
		for c in card_classes:
			class_map[c.__name__] = c
		return class_map[name]

	@staticmethod
	def card_for_state(state):
		return Card.class_for_name(state[0])(state[1], state[2], tapped=state[3], turn_played=state[4])

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
		return ()

	def mana_cost(self):
		colorless = 0
		for mana in self.total_mana_cost():
			if isinstance(mana, int):
				colorless += mana
			else:
				colorless += 1
		return colorless

	def possible_moves(self, game):
		"""Returns [] if the player doesn't have enough mana, other returns the action to play the bear."""
		available_mana = game.available_mana()
		total_mana = 0
		for color, count in available_mana.iteritems():
			total_mana += count
		if total_mana >= self.mana_cost():
			card_index = game.get_players()[game.player_with_priority].get_hand().index(self)
			return [('card-{}'.format(self.__class__.__name__), 
					card_index, 
					self.total_mana_cost(), 
					None,
					None,
					game.player_with_priority)]
		return []

	def display_name(self):
		"""Split the name on uppercase letter and add spaces."""
		matches = finditer('.+?(?:(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|$)',self.__class__.__name__)
		return " ".join([m.group(0) for m in matches])

	def action_word(self):
		return "Use"


class Land(Card):
	"""A card that produces any color mana."""

	def __init__(self, owner, card_id, tapped=False, turn_played=None):
		super(Land, self).__init__(owner, card_id, tapped=tapped, turn_played=turn_played)
		self.card_type = "land"

	@staticmethod
	def land_for_state(state):
		classname = state[0]
		# eval is slow
		'''
		land = eval("{}".format(classname))(
			state[1],
			state[2], 
			tapped=state[3],
			turn_played=state[4],
		)
		'''
		if classname == 'Forest':
			return Forest(
				state[1],
				state[2], 
				tapped=state[3],
				turn_played=state[4],
			)
		return Mountain(
			state[1],
			state[2], 
			tapped=state[3],
			turn_played=state[4],
		)

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
		card_index = game.get_players()[game.player_with_priority].get_hand().index(self)
		return [('card-{}'.format(
			self.__class__.__name__), 
			card_index, 
			(), 
			None,
			None,
			game.player_with_priority)]

	def play(self, game, mana_to_use, target_creature_id):
		"""Remove this from the player's hand and add it to game.lands."""
		self.turn_played = game.current_turn
		game.get_lands().append(self)
		player = game.get_players()[game.player_with_priority]
		player.get_hand().remove(self)
		if game.print_moves:
			print "> {} {} played a {}." \
				.format(player.__class__.__name__, game.get_players().index(player), self.__class__.__name__, self.id, )

	def mana_provided(self):
		"""The amount and kind of mana provided."""
		return {'BUGRW': 1}

	def return_to_hand(self, game):
		game.get_players()[self.owner].get_hand().append(self)
		self.tapped = False
		game.get_lands().remove(self)


	def possible_ability_moves(self, game):
		if self.tapped == True:
			return []
		return [
			(
				'land_ability-{}'.format(self.__class__.__name__), 
				game.get_lands().index(self), 
				(), 
				None, 
				None,
				game.player_with_priority
			)
		 ]

	def activate_ability(self, game, mana_to_use, target_creature_id, target_land_id):
		self.tapped = True
		player = game.get_players()[game.player_with_priority]
		player.temp_mana += list(self.mana_provided_list())
		if game.print_moves:
			print "> {} {} tapped {} for {}, has {} floating." \
				.format(
					player.__class__.__name__, 
					game.get_players().index(player), 
					self.__class__.__name__, 
					self.mana_provided_list(),
					player.temp_mana,
					game.player_with_priority

				)

class Forest(Land):
	"""A card that produces green mana."""

	def mana_provided_list(self):
		"""The amount and kind of mana provided."""
		return ('G', )

	def mana_provided(self):
		"""The amount and kind of mana provided."""
		return {'G': 1}


class Mountain(Land):
	"""A card that produces red mana."""

	def mana_provided_list(self):
		"""The amount and kind of mana provided."""
		return ('R', )

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
		available_mana = game.available_mana()
		possible_moves = []
		card_index = game.get_players()[game.player_with_priority].get_hand().index(self)
		
		green_count = 0
		for color, count in available_mana.iteritems():
			if type (color) == str and 'G' in color:
				green_count += count

		for c in game.get_creatures():
			if not c.targettable:
				continue
			if c.hexproof and c.owner != game.player_with_priority:
				continue
			if green_count > 0:
				possible_moves.append(
					('card-{}'.format(self.__class__.__name__), 
					card_index, 
					('G', ), 
					c.id,
					None,
					game.player_with_priority))
			if green_count > 1:
				possible_moves.append(
					('card-{}'.format(self.__class__.__name__), 
					card_index, 
					('G', 'G'), 
					c.id,
					None,
					game.player_with_priority))

		return possible_moves

	def play(self, game, mana_to_use, target_creature_id):
		"""Pump a creature based on how much mana is used."""
		creature = game.creature_with_id(target_creature_id)
		if not creature:  # it died
			if game.print_moves:
				print "VinesOfVastwood fizzled, no creature with id {}.".format(target_creature_id)
			return
		creature.temp_targettable = False
		caster = game.get_players()[game.player_with_priority]
		if mana_to_use == ('G', 'G'):
			creature.temp_strength += 4
			creature.temp_hit_points += 4
		if game.print_moves:
			if mana_to_use == ('G', ):
				print "> {} {} played VinesOfVastwood on {}." \
					.format(
						caster.__class__.__name__, 
						game.get_players().index(caster), 
						creature.__class__.__name__)
			else:
				print "> {} {} played kicked VinesOfVastwood on {}, total power now {}." \
					.format(
						caster.__class__.__name__, 
						game.get_players().index(caster), 
						creature.__class__.__name__,
						creature.total_damage())


class HungerOfTheHowlpack(Card):
	"""
		Put a +1/+1 counter on target creature.
		Morbid - Put three +1/+1 counters on that creature instead if a creature died this turn.
	"""
	def __init__(self, owner, card_id, tapped=False, turn_played=None):
		super(HungerOfTheHowlpack, self).__init__(owner, card_id, tapped=tapped, turn_played=turn_played)
		self.card_type = 'instant'

	def possible_moves(self, game):
		"""Returns possible VinesOfVastwood targets."""
		available_mana = game.available_mana()
		possible_moves = []
		card_index = game.get_players()[game.player_with_priority].get_hand().index(self)
		
		green_count = 0
		for color, count in available_mana.iteritems():
			if type(color) == str:
				if 'G' in color:
					green_count += count
					break

		for c in game.get_creatures():
			if not c.targettable:
				continue
			if c.hexproof and c.owner != game.player_with_priority:
				continue
			if green_count > 0:
				possible_moves.append(('card-{}'.format(self.__class__.__name__), 
										card_index, 
										('G', ), 
										c.id,
										None,
										game.player_with_priority))

		return possible_moves

	def play(self, game, mana_to_use, target_creature_id):
		"""Pump a creature based on how much mana is used."""
		creature = game.creature_with_id(target_creature_id)
		morbid = False
		if creature:
			creature.strength_counters += 1
			creature.hit_point_counters += 1
		if game.print_moves:
			format_str = None
			if morbid:
				format_str = "> Player {} played {} on {}, with morbid, total stats now {}/{}.."
			else:
				format_str = "> Player {} played {} on {}, total stats now {}/{}."
			print format_str.format( 
				self.owner, 
				self.__class__.__name__,
				creature.__class__.__name__,
				creature.total_damage(),
				creature.total_hit_points(),
			)


class Fireball(Card):
	"""A card that deal X damage to anything."""

	def possible_moves(self, game):
		"""Returns possible fireballs targets and amounts."""
		available_mana = game.available_mana()
		possible_moves = []
		card_index = game.get_players()[game.player_with_priority].get_hand().index(self)
		
		has_red = False
		total_mana = 0
		for color, count in available_mana.iteritems():
			total_mana += count
			if 'R' in color:
				has_red = True

		if has_red and total_mana > 1:
			for mana in range(2, total_mana+1):
				possible_moves.append(('card-fireball', 
										card_index, 
										('R', mana-1), 
										None,
										None,
										game.player_with_priority))
			for c in game.get_creatures():
				if c.hexproof and c.owner != game.player_with_priority:
					continue
				if c.targettable and c.temp_targettable:
					for mana in range(2, total_mana+1):
						possible_moves.append(('card-fireball-creature', 
							card_index, 
							('R', mana-1), 
							c.id,
							None,
							game.player_with_priority))
		return possible_moves

	def play(self, game, mana_to_use, target_creature_id):
		"""Decrement hit_points equal to blaster's mana from blastee."""
		blaster = game.get_players()[game.player_with_priority]
		blaster.get_hand().remove(self)

		colorless = 0
		for mana in mana_to_use:
			if isinstance(mana, int):
				colorless = mana
				break
		if target_creature_id:
			blaster = game.get_players()[game.player_with_priority]
			creature = game.creature_with_id(target_creature_id)
			if (colorless) >= creature.hit_points:
				if creature.id in game.attackers:
					game.attackers.remove(creature.id)
				game.get_creatures().remove(creature)
			else:
				creature.hit_points -= colorless

			if game.print_moves:
				print "> {} {} fireballed {} for {} damage." \
				.format(blaster.__class__.__name__, game.get_players().index(blaster), creature.__class__.__name__, colorless)
		else:
			blastee = game.opponent(blaster)
			blastee.hit_points -= colorless
			game.damage_to_players[game.players.index(blastee)] += colorless

			if game.print_moves:
				print "> {} {} fireballed for {} damage." \
				.format(blaster.__class__.__name__, game.get_players().index(blaster), colorless)


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
		self.activated_ability = False
		self.activated_ability_type = 'instant'
		self.strength_counters = 0
		self.hit_point_counters = 0
		self.flying = False
		self.hexproof = False
		self.lifelink = False
		self.enchantments = []
		self.card_type = "creature"

	@staticmethod
	def creature_for_state(state):
		c = Card.class_for_name(state[0])(state[1], state[2], tapped=state[3], turn_played=state[4])
		c.targettable = state[5]
		c.temp_strength = state[6]
		c.temp_hit_points = state[7]
		c.temp_targettable =state[8]
		c.activated_ability = state[9]
		c.activated_ability_type = state[10]
		c.strength_counters = state[11]
		c.hit_point_counters = state[12]
		c.flying = state[13]
		c.hexproof = state[14]
		c.lifelink = state[15]

		for enchantment in state[16]:
			c.enchantments.append(Card.card_for_state(enchantment))

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
				self.activated_ability,
				self.activated_ability_type,
				self.strength_counters,
				self.hit_point_counters,
				self.flying,
				self.hexproof,
				self.lifelink,
				tuple([e.state_repr() for e in self.enchantments]),
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
		enchantment_damage = 0
		for e in self.enchantments:
			enchantment_damage += e.attack_bonus()
		return self.strength + self.temp_strength + self.strength_counters + enchantment_damage

	def total_hit_points(self):
		enchantment_hit_points = 0
		for e in self.enchantments:
			enchantment_hit_points += e.defense_bonus()
		return self.hit_points + self.temp_hit_points + self.hit_point_counters + enchantment_hit_points

	def can_attack(self, game):
		"""Returns False if the creature was summoned this turn."""
		return self.turn_played < game.current_turn and self.tapped == False

	def play(self, game, mana_to_use, target_creature_id):
		"""Summon the bear for the player_with_priority."""
		summoner = game.get_players()[game.player_with_priority]
		summoner.get_hand().remove(self)
		self.turn_played = game.current_turn
		game.get_creatures().append(self)
		if game.print_moves:
			player = game.get_players()[game.player_with_priority]
			print "> {} {} summoned a {}/{} {}." \
				.format(
					player.__class__.__name__, 
					game.players.index(player), 
					self.total_damage(), 
					self.total_hit_points(), 
					self.__class__.__name__
				)

	def possible_ability_moves(self, game):
		return []

	def can_be_blocked_by(self, creature):
		if self.flying and not creature.flying:
			return False
		return True

	def creature_types(self):
		return []

	def did_deal_damage(self, game):
		if self.lifelink:
			owner = game.get_players()[self.owner] 
			owner.hit_points += self.total_damage()
			if game.print_moves:
				print "> {} {} gained {} life from {}." \
					.format(
						owner.__class__.__name__, 
						self.owner, 
						self.total_damage(), 
						self.__class__.__name__
					)


class GreenCreature(Creature):

	def possible_moves(self, game):
		"""Returns [] if the player doesn't have enough mana, other returns the action to play the bear."""
		available_mana = game.available_mana()
		has_green = False
		total_mana = 0
		for color, count in available_mana.iteritems():
			total_mana += count
			if type(color) != int and 'G' in color:
				has_green = True
		if has_green and total_mana >= self.mana_cost():
			card_index = game.get_players()[game.player_with_priority].get_hand().index(self)
			return [('card-{}'.format(self.__class__.__name__), 
				card_index, 
				self.total_mana_cost(), 
				None,
				None,
				game.player_with_priority)]
		return []


class Bear(GreenCreature):
	"""A 2/2 creature."""

	def initial_strength():
		return 2

	def initial_hit_points():
		return 2

	def total_mana_cost(self):
		return ('G', 1)


class NettleSentinel(GreenCreature):
	"""
		Nettle Sentinel doesn't untap during your untap step.
		
		Whenever you cast a green spell, you may untap Nettle Sentinel.
	"""

	def total_mana_cost(self):
		return ('G', )

	def initial_strength(self):
		return 2

	def initial_hit_points(self):
		return 2

	def adjust_for_untap_phase(self):
		pass

	def react_to_spell(self, card):
		total_mana_cost = card.total_mana_cost()
		if type(total_mana_cost) == str and 'G' in card.total_mana_cost():
			self.tapped = False

	def creature_types(self):
		return ['Elf', 'Warrior']


class QuirionRanger(GreenCreature):
	"""
		Nettle Sentinel doesn't untap during your untap step.
		
		Whenever you cast a green spell, you may untap Nettle Sentinel.
	"""

	def __init__(self, owner, card_id, tapped=False, turn_played=-1):
		super(QuirionRanger, self).__init__(owner, card_id, tapped=tapped, turn_played=turn_played)
		self.activated = False

	def total_mana_cost(self):
		return ('G', )

	def initial_strength(self):
		return 1

	def initial_hit_points(self):
		return 1

	def possible_ability_moves(self, game):
		if self.activated_ability or self.turn_played == game.current_turn:
			return []
		untapped_forest = None
		tapped_forest = None
		for land in game.get_lands():
			if land.owner != self.owner:
				continue
			if land.__class__.__name__ == "Forest" and land.tapped:
				tapped_forest = land

			if land.__class__.__name__ == "Forest" and not land.tapped:
				untapped_forest = land
		different_forest_targets = []
		if tapped_forest:
			different_forest_targets.append(tapped_forest)
		if untapped_forest:
			different_forest_targets.append(untapped_forest)
		possible_moves = []
		for land in different_forest_targets:
				for creature in game.get_creatures():
					if creature.owner == self.owner:
						possible_moves.append(
							(
								'ability-{}'.format(self.__class__.__name__), 
								game.get_creatures().index(self), 
								(), 
								creature.id, 
								land.id,
								game.player_with_priority,
												self.state_repr(), 

							)
						)
		return possible_moves

	def activate_ability(self, game, mana_to_use, target_creature_id, target_land_id, card_in_play):
		"""Return a forest to player's hand and untap a creature."""
		self.activated_ability = True

		for creature in game.get_creatures():
			if creature.id == target_creature_id:
				creature.tapped = False
				break

		land_to_return = None
		for land in game.get_lands():
			if land.id == target_land_id:
				land_to_return = land
				break
		land.return_to_hand(game)

		if game.print_moves:
			player = game.get_players()[game.player_with_priority]
			print "> {} {} untapped {} with {} returning {}." \
				.format(
					player.__class__.__name__, 
					game.get_players().index(player), 
					creature.__class__.__name__, 
					self.__class__.__name__,
					land_to_return.__class__.__name__,
				)

	def adjust_for_untap_phase(self):
		super(QuirionRanger, self).adjust_for_untap_phase()
		self.activated_ability = False

	def creature_types(self):
		return ['Elf']

	def action_word(self):
		return "Untap"

class BurningTreeEmissary(GreenCreature):
	"""When Burning-Tree Emissary enters the battlefield, add RedGreen."""

	def __init__(self, owner, card_id, tapped=False, turn_played=-1):
		super(BurningTreeEmissary, self).__init__(owner, card_id, tapped=tapped, turn_played=turn_played)
		self.activated = False

	def total_mana_cost(self):
		return ('RG', 'RG')

	def initial_strength(self):
		return 2

	def initial_hit_points(self):
		return 2

	def possible_moves(self, game):
		"""Returns [] if the player has less than 2 mana, other returns the action to play the bear."""
		available_mana = game.available_mana()
		either_count = 0
		for color, count in available_mana.iteritems():
			if type(color) == str:
				if 'G' in color or 'R' in color: 
					either_count += count
		if either_count >= self.mana_cost():
			card_index = game.get_players()[game.player_with_priority].get_hand().index(self)
			return [('card-{}'.format(
				self.__class__.__name__), 
			card_index, 
			self.total_mana_cost(), 
			None,
			None,
			game.player_with_priority)]
		return []

	def play(self, game, mana_to_use, target_creature_id):
		super(BurningTreeEmissary, self).play(game, mana_to_use, target_creature_id)
		player = game.get_players()[self.owner]
		player.temp_mana += list(('G', 'R'))

	def creature_types(self):
		return ['Human', 'Shaman']

	def display_name(self):
		return "Burning-Tree Emissary"

class SkarrganPitSkulk(GreenCreature):
	"""
		Bloodthirst 1 (If an opponent was dealt damage this turn, this creature enters the 
		battlefield with a +1/+1 counter on it.)
		Creatures with power less than Skarrgan Pit-Skulk's power can't block it.
	"""

	def total_mana_cost(self):
		return ('G',)

	def initial_strength(self):
		return 1

	def initial_hit_points(self):
		return 1

	def play(self, game, mana_to_use, target_creature_id):
		if game.opponent_was_dealt_damage():
			self.strength_counters += 1
			self.hit_point_counters += 1
		super(SkarrganPitSkulk, self).play(game, mana_to_use, target_creature_id)

	def can_be_blocked_by(self, creature):
		if creature.total_damage() < self.total_damage():
			return False
		return True

	def creature_types(self):
		return ['Human', 'Warrior']


class NestInvader(GreenCreature):
	"""
		When Nest Invader enters the battlefield, create a 0/1 colorless Eldrazi Spawn creature token. 
		It has "Sacrifice this creature: Add Colorless."
	"""

	def total_mana_cost(self):
		return ('G', 1)

	def initial_strength(self):
		return 2

	def initial_hit_points(self):
		return 2

	def play(self, game, mana_to_use, target_creature_id):
		super(NestInvader, self).play(game, mana_to_use, target_creature_id)
		token = EldraziSpawnToken(self.owner, None, tapped=False, turn_played=game.current_turn)
		token.id = game.new_card_id
		game.new_card_id += 1
		game.get_players()[self.owner].hand.append(token)
		token.play(game, 0, target_creature_id)

	def creature_types(self):
		return ['Eldrazi', 'Drone']


class EldraziSpawnToken(Creature):
	"""
		An 0/1 colorless Eldrazi Spawn creature token. 
		It has "Sacrifice this creature: Add Colorless."
	"""

	def total_mana_cost(self):
		return (0)

	def initial_strength(self):
		return 0

	def initial_hit_points(self):
		return 1

	def possible_ability_moves(self, game):
		return [
			(
				'ability-{}'.format(self.__class__.__name__), 
				game.get_creatures().index(self), 
				(), 
				None, 
				None,
				game.player_with_priority,
				self.state_repr(), 
			)
		]

	def activate_ability(self, game, mana_to_use, target_creature_id, target_land_id, card_in_play):
		if self.id in game.attackers:
			game.attackers.remove(self.id)
		if self.id in game.blockers:
			game.blockers.remove(self.id)

		block_where_attacking = None
		block_where_blocking = None

		for block in game.blocks:
			if block[0] == self.id:
				block_where_attacking = block
			if self.id in block[1]:
				block_where_blocking = block

		if block_where_attacking:
			game.blocks.remove(block_where_attacking)
		if block_where_blocking:
			list_tuple = list(block_where_blocking[1])
			list_tuple.remove(self.id)
			list_block = list(block_where_blocking)
			list_block[1] = list_tuple
			block_where_blocking = tuple(list_block)

		for c in game.get_creatures():
			if c.id == self.id:
				game.get_creatures().remove(c)
				break

		player = game.get_players()[game.player_with_priority]
		player.temp_mana += [1]

		if game.print_moves:
			print "> {} {} sacrificed {}." \
				.format(
					player.__class__.__name__, 
					game.player_with_priority, 
					self.__class__.__name__, 
				)

	def creature_types(self):
		return ['Eldrazi', 'Token']

	def action_word(self):
		return "Sacrifice"

class SilhanaLedgewalker(GreenCreature):
	"""
		Hexproof (This creature can't be the target of spells or abilities your opponents control.)
		Silhana Ledgewalker can't be blocked except by creatures with flying.
	"""
	def __init__(self, owner, card_id, tapped=False, turn_played=-1):
		super(GreenCreature, self).__init__(owner, card_id, tapped=tapped, turn_played=turn_played)
		self.hexproof = True

	def total_mana_cost(self):
		return ('G', 1)

	def initial_strength(self):
		return 1

	def initial_hit_points(self):
		return 1

	def can_be_blocked_by(self, creature):
		return creature.flying

	def creature_types(self):
		return ['Elf', 'Rogue']


class VaultSkirge(GreenCreature):
	"""
		(Phyrexian Black can be paid with either Black or 2 life.)
		Flying
		Lifelink (Damage dealt by this creature also causes you to gain that much life.)
	"""
	def __init__(self, owner, card_id, tapped=False, turn_played=-1):
		super(GreenCreature, self).__init__(owner, card_id, tapped=tapped, turn_played=turn_played)
		self.flying = True
		self.lifelink = True

	def total_mana_cost(self):
		return ('G', 1)

	def initial_strength(self):
		return 1

	def initial_hit_points(self):
		return 1

	def creature_types(self):
		return ['Artifact', 'Imp']

	def possible_moves(self, game):
		"""Returns [] if the player doesn't have enough mana, other returns the action to play the bear."""
		available_mana = game.available_mana()
		has_green = False
		total_mana = 0
		for color, count in available_mana.iteritems():
			total_mana += count
			if type(color) != int and 'G' in color:
				has_green = True
		possible_moves = []
		casting_player = game.get_players()[game.player_with_priority]
		if has_green and total_mana >= self.mana_cost():
			card_index = casting_player.get_hand().index(self)
			possible_moves.append(('card-{}'.format(self.__class__.__name__), 
				card_index, 
				self.total_mana_cost(), 
				None,
				None,
				game.player_with_priority))
		if casting_player.hit_points >= 2 and total_mana >= 1:
			card_index = casting_player.get_hand().index(self)
			possible_moves.append(('card-{}'.format(self.__class__.__name__), 
				card_index, 
				(1, 'L2'), 
				None,
				None,
				game.player_with_priority))
		return possible_moves


class CreatureEnchantment(Card):
	"""A fantasy enchantment card instance."""

	def __init__(self, owner, card_id, tapped=False, turn_played=-1):
		super(CreatureEnchantment, self).__init__(owner, card_id, tapped=False, turn_played=turn_played)
		self.card_type = "enchantment"

	def attack_bonus(self):
		return 0

	def defense_bonus(self):
		return 0

	def possible_moves(self, game):
		"""Returns [] if the player doesn't have enough mana, other returns the action to play the bear."""
		available_mana = game.available_mana()
		has_green = False
		total_mana = 0
		card_index = game.get_players()[game.player_with_priority].get_hand().index(self)
		possible_moves = []
		for color, count in available_mana.iteritems():
			total_mana += count
			if type(color) != int and 'G' in color:
				has_green = True
		if has_green and total_mana >= self.mana_cost():
			for c in game.get_creatures():
				if c.hexproof and c.owner != game.player_with_priority:
					continue
				if c.targettable and c.temp_targettable:
					possible_moves.append(
						('card-rancor', 
						card_index, 
						('G', ), 
						c.id,
						None,
						game.player_with_priority))
		return possible_moves

	def play(self, game, mana_to_use, target_creature_id):
		"""Summon the bear for the player_with_priority."""
		summoner = game.get_players()[game.player_with_priority]
		summoner.get_hand().remove(self)
		self.turn_played = game.current_turn
		target_creature = game.creature_with_id(target_creature_id)
		if target_creature: # if it didn't die
			target_creature.enchantments.append(self)
		if game.print_moves:
			player = game.get_players()[game.player_with_priority]
			print "> {} {} played a {} on {}." \
				.format(
					player.__class__.__name__, 
					game.players.index(player), 
					self.__class__.__name__,
					target_creature.__class__.__name__
				)


class Rancor(CreatureEnchantment):
	"""
		Enchanted creature gets +2/+0 and has trample.
		When Rancor is put into a graveyard from the battlefield, 
		return Rancor to its owner's hand.
	"""

	def __init__(self, owner, card_id, tapped=False, turn_played=-1):
		super(Rancor, self).__init__(owner, card_id, tapped=False, turn_played=turn_played)

	def total_mana_cost(self):
		return ('G', )

	def attack_bonus(self):
		return 2

	def possible_moves(self, game):
		"""Returns [] if the player doesn't have enough mana, other returns the action to play the bear."""
		available_mana = game.available_mana()
		has_green = False
		total_mana = 0
		card_index = game.get_players()[game.player_with_priority].get_hand().index(self)
		possible_moves = []
		for color, count in available_mana.iteritems():
			total_mana += count
			if type(color) != int and 'G' in color:
				has_green = True
		if has_green and total_mana >= self.mana_cost():
			for c in game.get_creatures():
				if c.hexproof and c.owner != game.player_with_priority:
					continue
				if c.targettable and c.temp_targettable:
					possible_moves.append(('card-rancor', 
						card_index, 
						('G', ), 
						c.id,
						None,
						game.player_with_priority))
		return possible_moves


class ElephantGuide(CreatureEnchantment):
	"""
		Enchanted creature gets +3/+3.
		When enchanted creature dies, create a 3/3 green Elephant creature token.
	"""

	def __init__(self, owner, card_id, tapped=False, turn_played=-1):
		super(ElephantGuide, self).__init__(owner, card_id, tapped=False, turn_played=turn_played)

	def total_mana_cost(self):
		return ('G', 2)

	def attack_bonus(self):
		return 3

	def defense_bonus(self):
		return 3