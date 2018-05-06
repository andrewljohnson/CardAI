from constants import *
from re import finditer
import sys


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
		return class_map[name]

	def state_repr(self):
		"""Return a hashable tuple representing the Card."""
		return (
			self.__class__.__name__,
			self.owner, 
			self.id, 
			self.tapped, 
			self.turn_played, 
			self.card_type, 
		)

	@staticmethod
	def owner(state):
		return state[1]

	@staticmethod
	def name(state):
		return state[0]

	@staticmethod
	def id(state):
		return state[2]

	@staticmethod
	def tapped(state):
		return state[3]

	@staticmethod
	def turn_played(state):
		return state[4]

	@staticmethod
	def card_type(state):
		return state[5]

	@staticmethod
	def set_turn_played(state, current_turn):
		mutable_tuple = list(state)
		mutable_tuple[4] = current_turn
		return tuple(mutable_tuple)

	@staticmethod
	def total_mana_cost(state):
		return name_to_mana_cost[Card.name(state)]


	@staticmethod
	def ascii_image(state, show_back=False):
		cols = 11
		rows = 5
		image_grid = []

		for x in range(0, rows):
			image_grid.append([])
			for y in range(0, cols):
				if x == 0 or x == rows - 1:
					image_grid[-1].append('-')
				elif y == 0 or y == cols - 1:
					image_grid[-1].append('|')
				else:
					image_grid[-1].append(' ')

		initial_index = 2

		if show_back:
			middle_x = cols / 2
			middle_y = rows / 2

			noon = (middle_x, middle_y - 1, '*')
			two = (middle_x + 2, middle_y, '*')
			ten = (middle_x - 2, middle_y, '*')
			seven = (middle_x - 1, middle_y + 1, '*')
			four = (middle_x + 1, middle_y + 1, '*')

			points = [noon, two, four, seven, ten]

			for p in points:
				image_grid[p[1]][p[0]] = p[2]
		
		if not show_back:
			cc_row = 1
			cc_string = Card.casting_cost_string(state)
			for x in range(initial_index, len(cc_string) + initial_index):
				image_grid[cc_row][x] = cc_string[x-initial_index]

		if not show_back:
			name_row = 2
			words = Card.display_name(state).split(" ")
			for word in words:
				word_width = min(3, len(word))
				if len(words) == 1:
					word_width = min(len(word), cols - 4)
				for x in range(initial_index, word_width + initial_index):
					image_grid[name_row][x] = word[x-initial_index]
				initial_index += word_width + 1
				if initial_index >= cols - word_width - 1:
					break

		if not show_back:
			if Card.name(state) in [
				'SilhanaLedgewalker', 
				'NettleSentinel',
				'QuirionRanger',
				'SkarrganPitSkulk',
				'NestInvader',
				'VaultSkirge',
				'ElephantToken',
				'EldraziSpawnToken',
			]:
				initial_index = 2
				stats_row = 3
				stats_string = "{}/{}".format(Creature.total_damage(state), Creature.total_hit_points(state))
				for x in range(initial_index, len(stats_string) + initial_index):
					image_grid[stats_row][x] = stats_string[x-initial_index]

		if not show_back:
			if Card.tapped(state):
				tapped_row = 0
				initial_index = 0
				tapped_string = "TAPPED"
				for x in range(initial_index, len(tapped_string) + initial_index):
					image_grid[tapped_row][x] = tapped_string[x-initial_index]

		return image_grid

	@staticmethod
	def print_hand(cards, owner=None, show_hand=True):
		images = []
		for c in cards:
			if owner != None and Card.owner(c) != owner:
				continue
			images.append(Card.ascii_image(c, show_back=(not show_hand)))
		if len(images) == 0:
			return
		row_to_print = 0
		width = SCREEN_WIDTH
		while row_to_print < len(images[0]):
			for x in range(0, max(0,(width-len(images)*12)/2)):
				sys.stdout.write(" ") 
			for image in images:
				for char in image[row_to_print]:
					sys.stdout.write(char) 
				sys.stdout.write(' ') 
			print ''
			row_to_print += 1

	@staticmethod
	def set_tapped(state, tapped):
		mutable_tuple = list(state)
		mutable_tuple[3] = tapped
		return tuple(mutable_tuple)

	@staticmethod
	def set_temp_strength(state, strength):
		mutable_tuple = list(state)
		mutable_tuple[7] = strength
		return tuple(mutable_tuple)

	@staticmethod
	def set_temp_hit_points(state, hit_points):
		mutable_tuple = list(state)
		mutable_tuple[8] = hit_points
		return tuple(mutable_tuple)

	@staticmethod
	def set_temp_targettable(state, targettable):
		mutable_tuple = list(state)
		mutable_tuple[9] = targettable
		return tuple(mutable_tuple)

	@staticmethod
	def set_activated_ability(state, activated):
		mutable_tuple = list(state)
		mutable_tuple[10] = activated
		return tuple(mutable_tuple)

	@staticmethod
	def adjust_for_untap_phase(state):
		if Card.name(state) == 'QuirionRanger':
			state = Card.set_activated_ability(state, False)

		if Card.name(state) != 'NettleSentinel':
			state = Card.set_tapped(state, False)
		return state

	@staticmethod
	def react_to_spell(state, card):
		if Card.name(state) == "NettleSentinel":
			return NettleSentinel.react_to_spell(state, card)
		return state

	@staticmethod
	def adjust_for_end_turn(state):
		return state

	@staticmethod
	def mana_cost(state):
		colorless = 0
		for mana in Card.total_mana_cost(state):
			if isinstance(mana, int):
				colorless += mana
			else:
				colorless += 1
		return colorless

	@staticmethod
	def activate_ability(state, game, mana_to_use, target_creature_id, target_land_id, card_in_play):
		if Card.name(state) == 'QuirionRanger':
			QuirionRanger.activate_ability(state, game, mana_to_use, target_creature_id, target_land_id, card_in_play)
		elif Card.name(state) == 'EldraziSpawnToken':
			EldraziSpawnToken.activate_ability(state, game, mana_to_use, target_creature_id, target_land_id, card_in_play)

	@staticmethod
	def play(state, game, mana_to_use, target_creature_id):
		"""Returns [] if the player doesn't have enough mana, other returns the action to play the card."""
		if Card.name(state) in ['Land', 'Forest', 'Mountain']:
			Land.play(state, game, mana_to_use, target_creature_id)
		elif Card.name(state) == 'VinesOfVastwood':
			VinesOfVastwood.play(state, game, mana_to_use, target_creature_id)
		elif Card.name(state) == 'HungerOfTheHowlpack':
			HungerOfTheHowlpack.play(state, game, mana_to_use, target_creature_id)
		elif Card.name(state) == 'Fireball':
			Fireball.play(state, game, mana_to_use, target_creature_id)
		elif Card.name(state) in [
			'SilhanaLedgewalker', 
			'NettleSentinel',
			'QuirionRanger',
			'VaultSkirge']:
			Creature.play(state, game, mana_to_use, target_creature_id)
		elif Card.name(state) == 'BurningTreeEmissary':
			BurningTreeEmissary.play(state, game, mana_to_use, target_creature_id)
		elif Card.name(state) == 'SkarrganPitSkulk':
			SkarrganPitSkulk.play(state, game, mana_to_use, target_creature_id)
		elif Card.name(state) == 'NestInvader':
			NestInvader.play(state, game, mana_to_use, target_creature_id)
		elif Card.name(state) in ['Rancor', 'ElephantGuide']:
			CreatureEnchantment.play(state, game, mana_to_use, target_creature_id)


	@staticmethod
	def possible_moves(state, game):
		"""Returns [] if the player doesn't have enough mana, other returns the action to play the card."""
		if Card.name(state) in ['Land', 'Forest', 'Mountain']:
			return Land.possible_moves(state, game)
		elif Card.name(state) == 'VinesOfVastwood':
			return VinesOfVastwood.possible_moves(state, game)
		elif Card.name(state) == 'HungerOfTheHowlpack':
			return HungerOfTheHowlpack.possible_moves(state, game)
		elif Card.name(state) == 'Fireball':
			return Fireball.possible_moves(state, game)
		elif Card.name(state) in [
			'SilhanaLedgewalker', 
			'NettleSentinel',
			'QuirionRanger',
			'SkarrganPitSkulk',
			'NestInvader']:
			return Creature.possible_moves(state, game)
		elif Card.name(state) == 'VaultSkirge':
			return VaultSkirge.possible_moves(state, game)
		elif Card.name(state) == 'BurningTreeEmissary':
			return BurningTreeEmissary.possible_moves(state, game)
		elif Card.name(state) == 'ElephantGuide':
			return CreatureEnchantment.possible_moves(state, game)
		elif Card.name(state) == 'Rancor':
			return Rancor.possible_moves(state, game)

	@staticmethod
	def display_name(state, display_stats=True):
		name = None
		if Card.name(state) == "BurningTreeEmissary":
			name = "Burning-Tree Emissary"
		else:
			"""Split the name on uppercase letter and add spaces."""
			matches = finditer('.+?(?:(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|$)',Card.name(state))
			name = " ".join([m.group(0) for m in matches])

		if Card.name(state) in [ # creatures get stats added
			"SilhanaLedgewalker",
			'NettleSentinel',
			'QuirionRanger',
			'SkarrganPitSkulk',
			'NestInvader',
			'VaultSkirge',
			'ElephantToken',
			'EldraziSpawnToken',
			]:
			name += " ({}/{})".format(Creature.total_damage(state), Creature.total_hit_points(state))
		return name

	@staticmethod
	def action_word(state):
		if Card.name(state) == "QuirionRanger":
			return QuirionRanger.action_word(state)
		elif Card.name(state) == "EldraziSpawnToken":
			return EldraziSpawnToken.action_word(state)
		return "Use"

	@staticmethod
	def casting_cost_string(state, move=None):
		casting_cost = ""
		cc = move[2] if move else Card.total_mana_cost(state)
		for c in cc:
			if type(c) == int:
				casting_cost += str(c)
			elif 'L' in c:
				casting_cost += " and {} life".format(c.split('L')[1])
			elif type(c) == str:
				casting_cost += c
		return casting_cost

	@staticmethod
	def cast_moves(state, game, card_index):
		if len(Card.possible_moves(state, game)) > 0:
			return [('card-cast-{}'.format(
				Card.name(state)), 
				card_index, 
				(), 
				None,
				None,
				game.player_with_priority)]
		return []

	@staticmethod
	def on_graveyard(state, game):
		if Card.name(state) == 'Rancor':
			game.players[Card.owner(state)].get_hand().append(state)
		elif Card.name(state) == 'ElephantGuide':
			token = ElephantToken(Card.owner(state), None, tapped=False, turn_played=game.current_turn)
			token.id = game.new_card_id
			game.new_card_id += 1
			token_state = token.state_repr()
			game.get_players()[Card.owner(state)].get_hand().append(token_state)
			token.play(token_state, game, 0, None)


class Land(Card):
	"""A card that produces any color mana."""

	def __init__(self, owner, card_id, tapped=False, turn_played=None):
		super(Land, self).__init__(owner, card_id, tapped=tapped, turn_played=turn_played)
		self.card_type = "land"

	def state_repr(self):
		"""Return a hashable tuple representing the Land."""
		return (
			self.__class__.__name__,
			self.owner, 
			self.id, 
			self.tapped, 
			self.turn_played, 
			self.card_type, 
		)

	@staticmethod
	def possible_moves(state, game):
		"""Returns [] if the player already played a land, other returns the action to play tapped."""
		if game.played_land():
			return []
		card_index = game.get_players()[game.player_with_priority].get_hand().index(state)
		return [('card-{}'.format(
			Card.name(state)), 
			card_index, 
			(), 
			None,
			None,
			game.player_with_priority)]

	@staticmethod
	def play(state, game, mana_to_use, target_creature_id):
		"""Remove this from the player's hand and add it to game.lands."""
		player = game.get_players()[game.player_with_priority]
		player.get_hand().remove(state)
		state = Card.set_turn_played(state, game.current_turn)
		game.get_lands().append(state)
		if game.print_moves:
			print "> {} played a {}." \
				.format(player.display_name(game.player_with_priority), Card.name(state), Card.owner(state), )

	@staticmethod
	def return_to_hand(state, game):
		game.get_players()[Card.owner(state)].get_hand().append(state)
		game.get_lands().remove(state)
		state = Card.set_tapped(state, False)

	@staticmethod
	def possible_ability_moves(state, game):
		if Card.tapped(state) == True:
			return []
		return [
			(
				'land_ability-{}'.format(Card.name(state)), 
				game.get_lands().index(state), 
				(), 
				None, 
				None,
				game.player_with_priority
			)
		 ]

	@staticmethod
	def activate_ability(state, game):
		state = Card.set_tapped(state, True)

		new_lands = []
		for land_state in game.lands:
			if Card.id(land_state) == Card.id(state):
				new_lands.append(state)
			else:
				new_lands.append(land_state)
		game.lands = new_lands

		player = game.get_players()[game.player_with_priority]
		player.temp_mana += list(Land.mana_provided_list(state))
		if game.print_moves:
			print "> {} tapped {} for {}, has {} floating." \
				.format(
					player.display_name(game.player_with_priority), 
					Card.name(state), 
					Land.mana_provided_list(state),
					player.temp_mana,
					game.player_with_priority

				)

	@staticmethod
	def mana_provided(state):
		return mana_provided_map[Card.name(state)]

	@staticmethod
	def mana_provided_list(state):
		return mana_provided_list_map[Card.name(state)]


class Forest(Land):
	"""A card that produces green mana."""

	pass


class Mountain(Land):
	"""A card that produces red mana."""

	pass


class VinesOfVastwood(Card):
	"""A card that buffs a creature."""

	def __init__(self, owner, card_id, tapped=False, turn_played=None):
		super(VinesOfVastwood, self).__init__(owner, card_id, tapped=tapped, turn_played=turn_played)
		self.card_type = 'instant'

	@staticmethod
	def possible_moves(state, game):
		"""Returns possible VinesOfVastwood targets."""
		available_mana = game.available_mana()
		possible_moves = []
		card_index = game.get_players()[game.player_with_priority].get_hand().index(state)
		
		green_count = 0
		for color, count in available_mana.iteritems():
			if type (color) == str and 'G' in color:
				green_count += count

		for creature_state in game.get_creatures():
			if not Creature.targettable(creature_state):
				continue
			if Creature.hexproof(creature_state) and Card.owner(creature_state) != game.player_with_priority:
				continue
			if green_count > 0:
				possible_moves.append(
					('card-{}'.format(Card.name(creature_state)), 
					card_index, 
					('G', ), 
					Card.id(creature_state),
					None,
					game.player_with_priority))
			if green_count > 1:
				possible_moves.append(
					('card-{}'.format(Card.name(creature_state)), 
					card_index, 
					('G', 'G'), 
					Card.id(creature_state),
					None,
					game.player_with_priority))

		return possible_moves

	@staticmethod
	def play(state, game, mana_to_use, target_creature_id):
		"""Pump a creature based on how much mana is used."""
		target_creature_state = game.creature_with_id(target_creature_id)
		if not target_creature_state:  # it died
			if game.print_moves:
				print "VinesOfVastwood fizzled, no creature with id {}.".format(target_creature_id)
			return

		target_creature_state = Card.set_temp_targettable(target_creature_state, False)

		new_creatures = []
		for creature_state in game.creatures:
			if Card.id(creature_state) == Card.id(target_creature_state):
				new_creatures.append(target_creature_state)
			else:
				new_creatures.append(creature_state)
		game.creatures = new_creatures

		caster = game.get_players()[Card.owner(state)]
		if mana_to_use == ('G', 'G'):
			target_creature_state = Creature.increment_temp_strength(target_creature_state, 4)
			target_creature_state = Creature.increment_temp_hit_points(target_creature_state, 4)

			new_creatures = []
			for creature_state in game.creatures:
				if Card.id(creature_state) == Card.id(target_creature_state):
					new_creatures.append(target_creature_state)
				else:
					new_creatures.append(creature_state)
			game.creatures = new_creatures

		caster.get_hand().remove(state)
		if game.print_moves:
			if mana_to_use == ('G', ):
				print "> {} played VinesOfVastwood on {}." \
					.format(
						caster.display_name(game.player_with_priority), 
						Creature.name(target_creature_state))
			else:
				print "> {} played kicked VinesOfVastwood on {}, total power now {}." \
					.format(
						caster.display_name(game.player_with_priority), 
						Creature.name(state),
						Creature.total_damage(target_creature_state))
		return state


class HungerOfTheHowlpack(Card):
	"""
		Put a +1/+1 counter on target creature.
		Morbid - Put three +1/+1 counters on that creature instead if a creature died this turn.
	"""
	def __init__(self, owner, card_id, tapped=False, turn_played=None):
		super(HungerOfTheHowlpack, self).__init__(owner, card_id, tapped=tapped, turn_played=turn_played)
		self.card_type = 'instant'

	@staticmethod
	def possible_moves(state, game):
		"""Returns possible VinesOfVastwood targets."""
		available_mana = game.available_mana()
		possible_moves = []
		card_index = game.get_players()[game.player_with_priority].get_hand().index(state)
		
		green_count = 0
		for color, count in available_mana.iteritems():
			if type(color) == str:
				if 'G' in color:
					green_count += count
					break

		for creature_state in game.get_creatures():
			if not Creature.targettable(creature_state):
				continue
			if Creature.hexproof(creature_state) and Card.owner(creature_state) != game.player_with_priority:
				continue
			if green_count > 0:
				possible_moves.append(('card-{}'.format(Card.name(creature_state)), 
										card_index, 
										('G', ), 
										Card.id(creature_state),
										None,
										game.player_with_priority))

		return possible_moves


	@staticmethod
	def play(state, game, mana_to_use, target_creature_id):
		"""Pump a creature based on how much mana is used."""
		target_creature_state = game.creature_with_id(target_creature_id)
		if target_creature_state:
			target_creature_state = Creature.increment_strength_counters(target_creature_state, 1)
			target_creature_state = Creature.increment_hit_point_counters(target_creature_state, 1)
			if game.creature_died_this_turn:
				target_creature_state = Creature.increment_strength_counters(target_creature_state, 2)
				target_creature_state = Creature.increment_hit_point_counters(target_creature_state, 2)

		new_creatures = []
		for creature_state in game.creatures:
			if target_creature_state and Card.id(creature_state) == Card.id(target_creature_state):
				new_creatures.append(target_creature_state)
			else:
				new_creatures.append(creature_state)
		game.creatures = new_creatures

		game.get_players()[Card.owner(state)].get_hand().remove(state)
		if game.print_moves:
			format_str = None
			if game.creature_died_this_turn:
				format_str = "> Player {} played {} on {}, with morbid, total stats now {}/{}.."
			else:
				format_str = "> Player {} played {} on {}, total stats now {}/{}."
			print format_str.format( 
				Card.owner(state), 
				Card.name(state),
				Card.name(target_creature_state),
				Creature.total_damage(target_creature_state),
				Creature.total_hit_points(target_creature_state),
			)


class Fireball(Card):
	"""A card that deal X damage to anything."""

	@staticmethod
	def possible_moves(state, game):
		"""Returns possible fireballs targets and amounts."""
		available_mana = game.available_mana()
		possible_moves = []
		card_index = game.get_players()[game.player_with_priority].get_hand().index(state)
		
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
			for creature_state in game.get_creatures():
				if Creature.hexproof(creature_state) and Card.owner(creature_state) != game.player_with_priority:
					continue
				if Creature.targettable(creature_state) and Creature.temp_targettable(creature_state):
					for mana in range(2, total_mana+1):
						possible_moves.append(('card-fireball-creature', 
							card_index, 
							('R', mana-1), 
							Card.id(creature_state),
							None,
							game.player_with_priority))
		return possible_moves

	@staticmethod
	def play(state, game, mana_to_use, target_creature_id):
		"""Decrement hit_points equal to blaster's mana from blastee."""
		blaster = game.get_players()[game.player_with_priority]
		blaster.get_hand().remove(state)

		colorless = 0
		for mana in mana_to_use:
			if isinstance(mana, int):
				colorless = mana
				break
		if target_creature_id:
			blaster = game.get_players()[game.player_with_priority]
			creature = game.creature_with_id(target_creature_id)
			if (colorless) >= Creature.total_hit_points(creature):
				if creature.id in game.attackers:
					game.attackers.remove(Card.id(creature))
				for e in Creature.enchantments(creature):
					Card.on_graveyard(e, game)
				Card.on_graveyard(creature, game)
				game.get_creatures().remove(creature)
				game.creature_died_this_turn = True
			else:
				target_creature_state = Creature.increment_temp_hit_points(creature, colorless)
				new_creatures = []
				for creature_state in game.creatures:
					if Card.id(creature_state) == Card.id(target_creature_state):
						new_creatures.append(target_creature_state)
					else:
						new_creatures.append(creature_state)
				game.creatures = new_creatures

			if game.print_moves:
				print "> {} fireballed {} for {} damage." \
				.format(blaster.display_name(game.player_with_priority), Card.name(creature), colorless)
		else:
			blastee = game.opponent(blaster)
			blastee.hit_points -= colorless
			game.damage_to_players[game.players.index(blastee)] += colorless

			if game.print_moves:
				print "> {} fireballed for {} damage." \
				.format(blaster.display_name(game.player_with_priority), colorless)


class Creature(Card):
	"""A fantasy creature card instance."""

	def __init__(self, owner, card_id, tapped=False, turn_played=-1):
		super(Creature, self).__init__(owner, card_id, tapped=tapped, turn_played=turn_played)
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

	def state_repr(self):
		"""Return a hashable representation of the creature."""
		return (self.__class__.__name__,
			 	self.owner, 
				self.id, 
				self.tapped, 
				self.turn_played,
				self.card_type,
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
				tuple(self.enchantments),
		)

	@staticmethod
	def adjust_for_end_turn(state):
		state = Creature.set_temp_strength(state, 0)
		state = Creature.set_temp_hit_points(state, 0)
		state = Creature.set_temp_targettable(state, False)
		return state

	@staticmethod
	def total_damage(state):
		enchantment_damage = 0
		for e_state in Creature.enchantments(state):
			enchantment_damage += CreatureEnchantment.attack_bonus(e_state)
		return name_to_stats[Card.name(state)][0] + Creature.temp_strength(state) + Creature.strength_counters(state) + enchantment_damage

	@staticmethod
	def total_hit_points(state):
		enchantment_hit_points = 0
		for e_state in Creature.enchantments(state):
			enchantment_hit_points += CreatureEnchantment.defense_bonus(e_state)
		return name_to_stats[Card.name(state)][1] + Creature.temp_hit_points(state) + Creature.hit_point_counters(state) + enchantment_hit_points

	@staticmethod
	def can_attack(state, game):
		"""Returns False if the creature was summoned this turn."""
		return Card.turn_played(state) < game.current_turn and Card.tapped(state) == False

	@staticmethod
	def play(state, game, mana_to_use, target_creature_id):
		"""Summon the creature for the player_with_priority."""
		summoner = game.get_players()[Card.owner(state)]
		summoner.get_hand().remove(state)
		state = Card.set_turn_played(state, game.current_turn)
		game.get_creatures().append(state)
		if game.print_moves:
			player = game.get_players()[game.player_with_priority]
			print "> {} summoned a {}." \
				.format(
					player.display_name(game.player_with_priority), 
					Card.name(state)
				)

	@staticmethod
	def possible_ability_moves(state, game):
		if Card.name(state) == 'QuirionRanger':
			return QuirionRanger.possible_ability_moves(state, game)
		elif Card.name(state) == 'EldraziSpawnToken':
			return EldraziSpawnToken.possible_ability_moves(state, game)
		return []

	@staticmethod
	def can_be_blocked_by(state, creature):
		if Creature.flying(state) and not Creature.flying(creature):
			return False
		elif Creature.name(state) == 'SkarrganPitSkulk':
			return SkarrganPitSkulk.can_be_blocked_by(state, creature)
		elif Creature.name(state) == 'SilhanaLedgewalker':
			return SilhanaLedgewalker.can_be_blocked_by(state, creature)
		return True

	@staticmethod
	def creature_types(state):
		return []

	@staticmethod
	def did_deal_damage(state, game):
		if Creature.lifelink(state):
			owner = game.get_players()[self.owner] 
			owner.hit_points += Creature.total_damage(state)
			if game.print_moves:
				print "> {} gained {} life from {}." \
					.format(
						owner.display_name(game.player_with_priority), 
						Creature.total_damage(state), 
						Card.name(state)
					)

	@staticmethod
	def possible_moves(state, game):
		"""Returns [] if the player doesn't have enough mana, other returns the action to play the creature."""
		available_mana = game.available_mana()
		
		colored_symbols = []
		for mana in Card.total_mana_cost(state):
			if type(mana) != int and 'L' not in mana:
				colored_symbols.append(mana)
		
		total_mana = 0
		for color, count in available_mana.iteritems():
			total_mana += count
		
		for color, count in available_mana.iteritems():
			if type(color) != int:
				if color in colored_symbols:
					colored_symbols.remove(color)
					if len(colored_symbols) == 0:
						break

		if len(colored_symbols) == 0 and total_mana >= Card.mana_cost(state):
			card_index = game.get_players()[game.player_with_priority].get_hand().index(state)
			return [('card-{}'.format(Card.name(state)), 
				card_index, 
				Card.total_mana_cost(state), 
				None,
				None,
				game.player_with_priority)]
		return []

	@staticmethod
	def has_trample(state):
		for e in Creature.enchantments(state):
			if Card.name(e) == "Rancor":
				return True
		return False

	@staticmethod
	def targettable(state):
		return state[6]

	@staticmethod
	def temp_strength(state):
		return state[7]

	@staticmethod
	def temp_hit_points(state):
		return state[8]

	@staticmethod
	def temp_targettable(state):
		return state[9]

	@staticmethod
	def activated_ability(state):
		return state[10]

	@staticmethod
	def activated_ability_type(state):
		return state[11]

	@staticmethod
	def strength_counters(state):
		return state[12]

	@staticmethod
	def hit_point_counters(state):
		return state[13]

	@staticmethod
	def flying(state):
		return state[14]

	@staticmethod
	def hexproof(state):
		return state[15]

	@staticmethod
	def lifelink(state):
		return state[16]

	@staticmethod
	def enchantments(state):
		return state[17]

	@staticmethod
	def increment_temp_strength(state, increment):
		mutable_tuple = list(state)
		mutable_tuple[7] += increment
		return tuple(mutable_tuple)

	@staticmethod
	def increment_temp_hit_points(state, increment):
		mutable_tuple = list(state)
		mutable_tuple[8] += increment
		return tuple(mutable_tuple)

	@staticmethod
	def increment_strength_counters(state, increment):
		mutable_tuple = list(state)
		mutable_tuple[12] += increment
		return tuple(mutable_tuple)

	@staticmethod
	def increment_hit_point_counters(state, increment):
		mutable_tuple = list(state)
		mutable_tuple[13] += increment
		return tuple(mutable_tuple)

	@staticmethod
	def add_enchantment(target, new_enchantment):
		mutable_tuple = list(target)
		mutable_tuple[17] = list(mutable_tuple[17])
		mutable_tuple[17].append(new_enchantment)
		mutable_tuple[17] = tuple(mutable_tuple[17])
		return tuple(mutable_tuple)


class NettleSentinel(Creature):
	"""
		Nettle Sentinel doesn't untap during your untap step.
		
		Whenever you cast a green spell, you may untap Nettle Sentinel.
	"""

	@staticmethod
	def react_to_spell(state, card):
		total_mana_cost = Card.total_mana_cost(card)
		for item in total_mana_cost:
			if type(item) == str and 'G' in item:
				state = Card.set_tapped(state, False)
				return state
		return state

	def creature_types(self):
		return ['Elf', 'Warrior']


class QuirionRanger(Creature):
	"""
		Nettle Sentinel doesn't untap during your untap step.
		
		Whenever you cast a green spell, you may untap Nettle Sentinel.
	"""

	def __init__(self, owner, card_id, tapped=False, turn_played=-1):
		super(QuirionRanger, self).__init__(owner, card_id, tapped=tapped, turn_played=turn_played)
		self.activated_ability = False

	@staticmethod
	def possible_ability_moves(state, game):
		if Creature.activated_ability(state):
			return []
		untapped_forest = None
		tapped_forest = None
		for land_state in game.get_lands():
			if Card.owner(land_state) != Card.owner(state):
				continue
			if Card.name(land_state) == "Forest" and Card.tapped(land_state):
				tapped_forest = land_state

			if Card.name(land_state) == "Forest" and not Card.tapped(land_state):
				untapped_forest = land_state
		different_forest_targets = []
		if tapped_forest:
			different_forest_targets.append(tapped_forest)
		if untapped_forest:
			different_forest_targets.append(untapped_forest)
		possible_moves = []
		for land_state in different_forest_targets:
				for creature_state in game.get_creatures():
					if Card.owner(creature_state) == Card.owner(state):
						possible_moves.append(
							(
								'ability-{}'.format(Card.name(state)), 
								game.get_creatures().index(state), 
								(), 
								Card.id(creature_state), 
								Card.id(land_state),
								game.player_with_priority,
												state, 

							)
						)
		return possible_moves

	@staticmethod
	def activate_ability(state, game, mana_to_use, target_creature_id, target_land_id, card_in_play):
		"""Return a forest to player's hand and untap a creature."""
		state = Creature.set_activated_ability(state, True)

		for creature_state in game.get_creatures():
			if Card.id(creature_state) == target_creature_id:
				creature_state = Creature.set_tapped(creature_state, False)
				break

		land_to_return = None
		for land_state in game.get_lands():
			if Card.id(land_state) == target_land_id:
				land_to_return = land_state
				break
		Land.return_to_hand(land_to_return, game)

		if game.print_moves:
			player = game.get_players()[game.player_with_priority]
			print "> {} untapped {} with {} returning {}." \
				.format(
					player.display_name(game.player_with_priority), 
					Card.name(creature_state), 
					Card.name(state),
					Card.name(land_to_return),
				)

	def creature_types(self):
		return ['Elf']


class BurningTreeEmissary(Creature):
	"""When Burning-Tree Emissary enters the battlefield, add RedGreen."""

	def __init__(self, owner, card_id, tapped=False, turn_played=-1):
		super(BurningTreeEmissary, self).__init__(owner, card_id, tapped=tapped, turn_played=turn_played)
		self.activated = False

	@staticmethod
	def play(state, game, mana_to_use, target_creature_id):
		Creature.play(state, game, mana_to_use, target_creature_id)
		player = game.get_players()[Card.owner(state)]
		player.temp_mana += list(('G', 'R'))

	def creature_types(self):
		return ['Human', 'Shaman']

class SkarrganPitSkulk(Creature):
	"""
		Bloodthirst 1 (If an opponent was dealt damage this turn, this creature enters the 
		battlefield with a +1/+1 counter on it.)
		Creatures with power less than Skarrgan Pit-Skulk's power can't block it.
	"""

	@staticmethod
	def play(state, game, mana_to_use, target_creature_id):
		Creature.play(state, game, mana_to_use, target_creature_id)

		if game.opponent_was_dealt_damage():
			mutable_tuple = list(state)
			mutable_tuple[12] += 1
			mutable_tuple[13] += 1
			state = tuple(mutable_tuple)

			new_creatures = []
			for c_state in game.creatures:
				if Card.id(c_state) == Card.id(state):
					new_creatures.append(state)
				else:
					new_creatures.append(c_state)
			game.creatures = new_creatures

	@staticmethod
	def can_be_blocked_by(state, creature):
		if Creature.total_damage(creature) < Creature.total_damage(state):
			return False
		return True

	def creature_types(self):
		return ['Human', 'Warrior']


class NestInvader(Creature):
	"""
		When Nest Invader enters the battlefield, create a 0/1 colorless Eldrazi Spawn creature token. 
		It has "Sacrifice this creature: Add Colorless."
	"""

	@staticmethod
	def play(state, game, mana_to_use, target_creature_id):
		Creature.play(state, game, mana_to_use, target_creature_id)
		token = EldraziSpawnToken(Card.owner(state), None, tapped=False, turn_played=game.current_turn)
		token.id = game.new_card_id
		game.new_card_id += 1
		token_state = token.state_repr()
		game.get_players()[Card.owner(state)].hand.append(token_state)
		Creature.play(token_state, game, mana_to_use, target_creature_id)

	def creature_types(self):
		return ['Eldrazi', 'Drone']


class EldraziSpawnToken(Creature):
	"""
		An 0/1 colorless Eldrazi Spawn creature token. 
		It has "Sacrifice this creature: Add Colorless."
	"""

	def creature_types(self):
		return ['Eldrazi', 'Token']

	@staticmethod
	def possible_ability_moves(state, game):
		return [
			(
				'ability-{}'.format(Card.name(state)), 
				game.get_creatures().index(state), 
				(), 
				None, 
				None,
				game.player_with_priority,
				state, 
			)
		]

	@staticmethod
	def activate_ability(state, game, mana_to_use, target_creature_id, target_land_id, card_in_play):
		if Creature.id(state) in game.attackers:
			game.attackers.remove(Creature.id(state))
		if Creature.id(state) in game.blockers:
			game.blockers.remove(Creature.id(state))

		block_where_attacking = None
		block_where_blocking = None

		for block in game.blocks:
			if block[0] == Creature.id(state):
				block_where_attacking = block
			if Creature.id(state) in block[1]:
				block_where_blocking = block

		if block_where_attacking:
			game.blocks.remove(block_where_attacking)
		if block_where_blocking:
			list_tuple = list(block_where_blocking[1])
			list_tuple.remove(Creature.id(state))
			list_block = list(block_where_blocking)
			list_block[1] = list_tuple
			block_where_blocking = tuple(list_block)

		for c_state in game.get_creatures():
			if Card.id(c_state) == Creature.id(state):
				game.get_creatures().remove(c_state)
				break

		player = game.get_players()[game.player_with_priority]
		player.temp_mana += [1]

		game.creature_died_this_turn = True

		Card.on_graveyard(state, game)
		for e in Creature.enchantments(state):
			Card.on_graveyard(e, game)
		
		if game.print_moves:
			print "> {} sacrificed {}." \
				.format(
					player.display_name(game.player_with_priority), 
					Card.name(state), 
				)

class SilhanaLedgewalker(Creature):
	"""
		Hexproof (This creature can't be the target of spells or abilities your opponents control.)
		Silhana Ledgewalker can't be blocked except by creatures with flying.
	"""
	def __init__(self, owner, card_id, tapped=False, turn_played=-1):
		super(SilhanaLedgewalker, self).__init__(owner, card_id, tapped=tapped, turn_played=turn_played)
		self.hexproof = True

	@staticmethod
	def can_be_blocked_by(state, creature):
		return Creature.flying(creature)

	def creature_types(self):
		return ['Elf', 'Rogue']


class VaultSkirge(Creature):
	"""
		(Phyrexian Black can be paid with either Black or 2 life.)
		Flying
		Lifelink (Damage dealt by this creature also causes you to gain that much life.)
	"""
	def __init__(self, owner, card_id, tapped=False, turn_played=-1):
		super(VaultSkirge, self).__init__(owner, card_id, tapped=tapped, turn_played=turn_played)
		self.flying = True
		self.lifelink = True

	def creature_types(self):
		return ['Artifact', 'Imp']


class CreatureEnchantment(Card):
	"""A fantasy enchantment card instance."""

	def __init__(self, owner, card_id, tapped=False, turn_played=-1):
		super(CreatureEnchantment, self).__init__(owner, card_id, tapped=False, turn_played=turn_played)
		self.card_type = "enchantment"

	@staticmethod
	def attack_bonus(state):
		return attack_bonus_map[Card.name(state)]

	@staticmethod
	def defense_bonus(state):
		return defense_bonus_map[Card.name(state)]

	@staticmethod
	def play(state, game, mana_to_use, target_creature_id):
		"""Summon the enchantment for the player_with_priority."""
		summoner = game.get_players()[game.player_with_priority]
		summoner.get_hand().remove(state)
		state = Card.set_turn_played(state, game.current_turn)
		target_creature_state = game.creature_with_id(target_creature_id)
		if target_creature_state: # if it didn't die
			target_creature_state = Creature.add_enchantment(target_creature_state, state)
			new_creatures = []
			for creature_state in game.creatures:
				if Card.id(creature_state) == Card.id(target_creature_state):
					new_creatures.append(target_creature_state)
				else:
					new_creatures.append(creature_state)
			game.creatures = new_creatures
		if game.print_moves:
			player = game.get_players()[game.player_with_priority]
			print "> {} played a {} on {}." \
				.format(
					player.display_name(game.player_with_priority), 
					Card.name(state),
					Card.name(target_creature_state)
				)


	@staticmethod
	def possible_moves(state, game):
		"""Returns [] if the player doesn't have enough mana, other returns the action to play the enchantment."""
		available_mana = game.available_mana()
		has_green = False
		total_mana = 0
		card_index = game.get_players()[game.player_with_priority].get_hand().index(state)
		possible_moves = []
		for color, count in available_mana.iteritems():
			total_mana += count
			if type(color) != int and 'G' in color:
				has_green = True
		if has_green and total_mana >= Card.mana_cost(state):
			for c_state in game.get_creatures():
				if Creature.hexproof(c_state) and Card.owner(c_state) != game.player_with_priority:
					continue
				if Creature.targettable(c_state) and Creature.temp_targettable(c_state):
					possible_moves.append(
						('card-rancor', 
						card_index, 
						('G', ), 
						Card.id(c_state),
						None,
						game.player_with_priority))
		return possible_moves


class Rancor(CreatureEnchantment):
	"""
		Enchanted creature gets +2/+0 and has trample.
		When Rancor is put into a graveyard from the battlefield, 
		return Rancor to its owner's hand.
	"""

	def __init__(self, owner, card_id, tapped=False, turn_played=-1):
		super(Rancor, self).__init__(owner, card_id, tapped=False, turn_played=turn_played)


class ElephantGuide(CreatureEnchantment):
	"""
		Enchanted creature gets +3/+3.
		When enchanted creature dies, create a 3/3 green Elephant creature token.
	"""

	def __init__(self, owner, card_id, tapped=False, turn_played=-1):
		super(ElephantGuide, self).__init__(owner, card_id, tapped=False, turn_played=turn_played)


class ElephantToken(Creature):
	"""
		An 3/3 green Elephant Spawn creature token. 
	"""

	def creature_types(self):
		return ['Elephant', 'Token']


card_classes = [
			BurningTreeEmissary,
			EldraziSpawnToken,
			ElephantGuide,
			ElephantToken,
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


name_to_mana_cost = {
			'NestInvader':('G', 1),
			'SilhanaLedgewalker':('G', 1),
			'VaultSkirge': ('B', 1),
			'VinesOfVastwood': ('G', ),
			'HungerOfTheHowlpack': ('G', ),
			'NettleSentinel': ('G', ),
			'QuirionRanger': ('G', ),
			'BurningTreeEmissary': ('RG', 'RG'),
			'SkarrganPitSkulk': ('G',),
			'Rancor': ('G', ),
			'EldraziSpawnToken': (0,),
			'ElephantGuide': ('G', 2),	
			'ElephantToken': (0,),	
			'Forest': (),	
			'Mountain': (),	
		}


name_to_stats = {
			'NestInvader':(2, 2),
			'SilhanaLedgewalker':(1, 1),
			'VaultSkirge': (1, 1),
			'NettleSentinel': (2, 2),
			'QuirionRanger': (1, 1),
			'BurningTreeEmissary': (2, 2),
			'SkarrganPitSkulk': (1,1),
			'EldraziSpawnToken': (0,1),
			'ElephantToken': (3,3),	
		}


mana_provided_list_map = {
	'Forest':('G', ),
	'Mountain':('R', ),
	'Land':('BUGRW', ),
}

mana_provided_map = {
	'Forest':{'G': 1},
	'Mountain':{'R': 1},
	'Land':{'BUGRW': 1},
}


attack_bonus_map = {
	'ElephantGuide': 3,
	'Rancor': 2,
}

defense_bonus_map = {
	'ElephantGuide': 3,
	'Rancor': 0,
}