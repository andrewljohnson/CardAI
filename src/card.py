from constants import *
from re import finditer
import sys


"""Card encapsulates the actions of a fantasy card."""

class Card(object):
	"""A fantasy card instance."""

	@staticmethod
	def class_for_name(name):
		"""Return a dict mapping card name to class."""	
		return class_map[name]

	@staticmethod
	def get_tuple(classname, owner, new_id, turn_played, card_type=None):
		"""Return a hashable tuple representing the Card."""
		return (
			classname,
			owner, 
			new_id, 
			False, # tapped 
			turn_played, 
			name_to_card_type[classname], 
		)

	@staticmethod
	def owner(card_state):
		return card_state[1]

	@staticmethod
	def name(card_state):
		return card_state[0]

	@staticmethod
	def id(card_state):
		return card_state[2]

	@staticmethod
	def tapped(card_state):
		return card_state[3]

	@staticmethod
	def turn_played(card_state):
		return card_state[4]

	@staticmethod
	def card_type(card_state):
		return card_state[5]

	@staticmethod
	def set_turn_played(card_state, current_turn):
		mutable_tuple = list(card_state)
		mutable_tuple[4] = current_turn
		return tuple(mutable_tuple)

	@staticmethod
	def total_mana_cost(card_state):
		return name_to_mana_cost[Card.name(card_state)]

	@staticmethod
	def ascii_image(card_state, show_back=False):
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
			cc_string = Card.casting_cost_string(card_state)
			for x in range(initial_index, len(cc_string) + initial_index):
				image_grid[cc_row][x] = cc_string[x-initial_index]

		if not show_back:
			name_row = 2
			words = Card.display_name(card_state).split(" ")
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
			if Card.name(card_state) in [
				'SilhanaLedgewalker', 
				'NettleSentinel',
				'QuirionRanger',
				'SkarrganPitSkulk',
				'NestInvader',
				'VaultSkirge',
				'ElephantToken',
				'BurningTreeEmissary',
				'EldraziSpawnToken',
			]:
				initial_index = 2
				stats_row = 3
				stats_string = "{}/{}".format(Creature.total_damage(card_state), Creature.total_hit_points(card_state))
				for x in range(initial_index, len(stats_string) + initial_index):
					image_grid[stats_row][x] = stats_string[x-initial_index]

		if not show_back:
			if Card.tapped(card_state):
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
	def set_tapped(card_state, tapped):
		mutable_tuple = list(card_state)
		mutable_tuple[3] = tapped
		return tuple(mutable_tuple)

	@staticmethod
	def set_temp_strength(card_state, strength):
		mutable_tuple = list(card_state)
		mutable_tuple[7] = strength
		return tuple(mutable_tuple)

	@staticmethod
	def set_temp_hit_points(card_state, hit_points):
		mutable_tuple = list(card_state)
		mutable_tuple[8] = hit_points
		return tuple(mutable_tuple)

	@staticmethod
	def set_temp_targettable(card_state, targettable):
		mutable_tuple = list(card_state)
		mutable_tuple[9] = targettable
		return tuple(mutable_tuple)

	@staticmethod
	def set_activated_ability(card_state, activated):
		mutable_tuple = list(card_state)
		mutable_tuple[10] = activated
		return tuple(mutable_tuple)

	@staticmethod
	def adjust_for_untap_phase(card_state):
		if Card.name(card_state) == 'QuirionRanger':
			card_state = Card.set_activated_ability(card_state, False)

		if Card.name(card_state) != 'NettleSentinel':
			card_state = Card.set_tapped(card_state, False)
		return card_state

	@staticmethod
	def react_to_spell(game_state, reacting_card, spell, Game):
		if Card.name(reacting_card) == "NettleSentinel":
			return NettleSentinel.react_to_spell(game_state, reacting_card, spell, Game)
		return game_state

	@staticmethod
	def adjust_for_end_turn(card_state):
		return card_state

	@staticmethod
	def mana_cost(card_state):
		colorless = 0
		mana_cost = Card.total_mana_cost(card_state)
		for mana in mana_cost[0]:
			colorless += 1
		if mana_cost[1] != None:
			colorless += mana_cost[1]
		return colorless

	@staticmethod
	def activate_ability(card_state, game_state, mana_to_use, target_creature_id, target_land_id, card_in_play, Game):
		if Card.name(card_state) == 'QuirionRanger':
			game_state = QuirionRanger.activate_ability(card_state, game_state, mana_to_use, target_creature_id, target_land_id, card_in_play, Game)
		elif Card.name(card_state) == 'EldraziSpawnToken':
			game_state = EldraziSpawnToken.activate_ability(card_state, game_state, mana_to_use, target_creature_id, target_land_id, card_in_play, Game)
		return game_state

	@staticmethod
	def play(card_state, game_state, mana_to_use, target_creature_id, Game):
		"""Returns [] if the player doesn't have enough mana, other returns the action to play the card."""
		if Card.name(card_state) in ['Land', 'Forest', 'Mountain']:
			return Land.play(card_state, game_state, mana_to_use, target_creature_id, Game)
		elif Card.name(card_state) == 'VinesOfVastwood':
			return VinesOfVastwood.play(card_state, game_state, mana_to_use, target_creature_id, Game)
		elif Card.name(card_state) == 'HungerOfTheHowlpack':
			return HungerOfTheHowlpack.play(card_state, game_state, mana_to_use, target_creature_id, Game)
		elif Card.name(card_state) == 'Fireball':
			return Fireball.play(card_state, game_state, mana_to_use, target_creature_id, Game)
		elif Card.name(card_state) in [
			'SilhanaLedgewalker', 
			'NettleSentinel',
			'QuirionRanger',
			'VaultSkirge']:
			return Creature.play(card_state, game_state, mana_to_use, target_creature_id, Game)
		elif Card.name(card_state) == 'BurningTreeEmissary':
			return BurningTreeEmissary.play(card_state, game_state, mana_to_use, target_creature_id, Game)
		elif Card.name(card_state) == 'SkarrganPitSkulk':
			return SkarrganPitSkulk.play(card_state, game_state, mana_to_use, target_creature_id, Game)
		elif Card.name(card_state) == 'NestInvader':
			return NestInvader.play(card_state, game_state, mana_to_use, target_creature_id, Game)
		elif Card.name(card_state) in ['Rancor', 'ElephantGuide']:
			return CreatureEnchantment.play(card_state, game_state, mana_to_use, target_creature_id, Game)


	@staticmethod
	def possible_moves(card_state, game_state, Game):
		"""Returns [] if the player doesn't have enough mana, other returns the action to play the card."""
		if Card.name(card_state) in ['Land', 'Forest', 'Mountain']:
			return Land.possible_moves(card_state, game_state, Game)
		elif Card.name(card_state) == 'VinesOfVastwood':
			return VinesOfVastwood.possible_moves(card_state, game_state, Game)
		elif Card.name(card_state) == 'HungerOfTheHowlpack':
			return HungerOfTheHowlpack.possible_moves(card_state, game_state, Game)
		elif Card.name(card_state) == 'Fireball':
			return Fireball.possible_moves(card_state, game_state, Game)
		elif Card.name(card_state) in [
			'SilhanaLedgewalker', 
			'NettleSentinel',
			'QuirionRanger',
			'SkarrganPitSkulk',
			'NestInvader']:
			return Creature.possible_moves(card_state, game_state, Game)
		elif Card.name(card_state) == 'VaultSkirge':
			return VaultSkirge.possible_moves(card_state, game_state, Game)
		elif Card.name(card_state) == 'BurningTreeEmissary':
			return BurningTreeEmissary.possible_moves(card_state, game_state, Game)
		elif Card.name(card_state) == 'ElephantGuide':
			return CreatureEnchantment.possible_moves(card_state, game_state, Game)
		elif Card.name(card_state) == 'Rancor':
			return Rancor.possible_moves(card_state, game_state, Game)

	@staticmethod
	def display_name(card_state, display_stats=True):
		name = None
		if Card.name(card_state) == "BurningTreeEmissary":
			name = "Burning-Tree Emissary"
		else:
			"""Split the name on uppercase letter and add spaces."""
			matches = finditer('.+?(?:(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|$)',Card.name(card_state))
			name = " ".join([m.group(0) for m in matches])

		if Card.name(card_state) in [ # creatures get stats added
			"SilhanaLedgewalker",
			'NettleSentinel',
			'QuirionRanger',
			'SkarrganPitSkulk',
			'NestInvader',
			'VaultSkirge',
			'ElephantToken',
			'EldraziSpawnToken',
			]:
			name += " ({}/{})".format(Creature.total_damage(card_state), Creature.total_hit_points(card_state))
		return name

	@staticmethod
	def action_word(card_state):
		if Card.name(card_state) == "QuirionRanger":
			return QuirionRanger.action_word(card_state)
		elif Card.name(card_state) == "EldraziSpawnToken":
			return EldraziSpawnToken.action_word(card_state)
		return "Use"

	@staticmethod
	def casting_cost_string(card_state, move=None):
		casting_cost = ""
		cc = move[2] if move else Card.total_mana_cost(card_state)
		casting_cost = str(cc[1])
		if casting_cost == 'None':
			casting_cost = ''
		for c in cc[0]:
			if 'L' in c:
				casting_cost += " and {} life".format(c.split('L')[1])
			elif type(c) == str:
				casting_cost += c
		return casting_cost

	@staticmethod
	def cast_moves(card_state, game_state, card_index, Game):
		if len(Card.possible_moves(card_state, game_state, Game)) > 0:
			return [('card-cast-{}'.format(
				Card.name(card_state)), 
				card_index, 
				(), 
				None,
				None,
				Game.player_with_priority(game_state))]
		return []

	@staticmethod
	def on_graveyard(card_state, game_state, Game):
		if Card.name(card_state) == 'Rancor':
			game_state = Game.add_card_to_hand(game_state, card_state)
		elif Card.name(card_state) == 'ElephantGuide':
			pwp = Card.owner(card_state)
			token_state = Creature.get_tuple(
				'ElephantToken', 
				pwp, 
				Game.get_new_card_id(game_state), 
				Game.get_current_turn(game_state)
			)
			game_state = Game.increment_new_card_id(game_state)
			game_state = Game.add_card_to_hand(game_state, token_state)
			game_state = Creature.play(token_state, game_state, 0, None, Game)

		return game_state


class Land(Card):
	"""A card that produces any color mana."""

	@staticmethod
	def possible_moves(card_state, game_state, Game):
		"""Returns [] if the player already played a land, other returns the action to play tapped."""
		if Game.played_land(game_state):
			return []
		pwp = Game.player_with_priority(game_state)
		card_index = Game.get_hand(game_state, pwp).index(card_state)
		return [('card-{}'.format(
			Card.name(card_state)), 
			card_index, 
			((), None, ), 
			None,
			None,
			pwp)]

	@staticmethod
	def play(land_state, game_state, mana_to_use, target_creature_id, Game):
		"""Remove this from the player's hand and add it to game_state lands."""
		pwp = Game.player_with_priority(game_state)
		player = Game.get_player_states(game_state)[pwp]
		game_state = Game.remove_card_from_hand(game_state, pwp, land_state)

		land_state = Card.set_turn_played(land_state, Game.get_current_turn(game_state))
		game_state = Game.add_land(game_state, land_state)
		if Game.print_moves(game_state):
			print "> {} played a {}." \
				.format(Game.player_display_name(player, pwp), Card.name(land_state), Card.owner(land_state), )
		return game_state

	@staticmethod
	def return_to_hand(game_state, land_state, Game):
		pwp = Card.owner(land_state)
		game_state = Game.remove_land(game_state, land_state)
		land_state = Card.set_tapped(land_state, False)
		game_state = Game.add_card_to_hand(game_state, land_state)
		return game_state

	@staticmethod
	def possible_ability_moves(card_state, game_state, Game):
		if Card.tapped(card_state) == True:
			return []
		return [
			(
				'land_ability-{}'.format(Card.name(card_state)), 
				Game.get_lands(game_state).index(card_state), 
				((), None, ), 
				None, 
				None,
				Game.player_with_priority(game_state)
			)
		 ]

	@staticmethod
	def activate_ability(card_state, game_state, Game):
		pwp = Game.player_with_priority(game_state)
		game_state = Game.set_land_tapped(game_state, card_state, True)
		game_state = Game.add_temp_mana(game_state, pwp, Land.mana_provided_list(card_state))
		if Game.print_moves(game_state):
			player_state = Game.get_player_states(game_state)[pwp]
			print "> {} tapped {} for {}, has {} floating." \
				.format(
					Game.player_display_name(player_state, pwp), 
					Card.name(card_state), 
					Land.mana_provided_list(card_state),
					Game.temp_mana(player_state),
				)
		return game_state

	@staticmethod
	def mana_provided(land_state):
		return mana_provided_map[Card.name(land_state)]

	@staticmethod
	def mana_provided_list(land_state):
		return mana_provided_list_map[Card.name(land_state)]

class Forest(Land):
	"""A card that produces green mana."""

	pass


class Mountain(Land):
	"""A card that produces red mana."""

	pass


class VinesOfVastwood(Card):
	"""A card that buffs a creature."""

	@staticmethod
	def possible_moves(card_state, game_state, Game):
		"""Returns possible VinesOfVastwood targets."""
		available_mana = Game.available_mana(game_state)
		possible_moves = []
		pwp = Game.player_with_priority(game_state)
		card_index = Game.get_hand(game_state, pwp).index(card_state)
		
		green_count = 0
		for color, count in available_mana.iteritems():
			if type (color) == str and 'G' in color:
				green_count += count

		for creature_state in Game.get_creatures(game_state):
			if not Creature.targettable(creature_state):
				continue
			if Creature.hexproof(creature_state) and Card.owner(creature_state) != pwp:
				continue
			if green_count > 0:
				possible_moves.append(
					('card-{}'.format(Card.name(creature_state)), 
					card_index, 
					(('G', ), None), 
					Card.id(creature_state),
					None,
					pwp))
			if green_count > 1:
				possible_moves.append(
					('card-{}'.format(Card.name(creature_state)), 
					card_index, 
					(('G', 'G',), None), 
					Card.id(creature_state),
					None,
					pwp))

		return possible_moves

	@staticmethod
	def play(card_state, game_state, mana_to_use, target_creature_id, Game):
		"""Pump a creature based on how much mana is used."""
		target_creature_state = Game.creature_with_id(game_state, target_creature_id)
		if not target_creature_state:  # it died
			if Game.print_moves(game_state):
				print "VinesOfVastwood fizzled, no creature with id {}.".format(target_creature_id)
			return

		target_creature_state = Card.set_temp_targettable(target_creature_state, False)
		game_state = Game.set_creature_with_id(game_state, target_creature_state, target_creature_id)

		new_creatures = []
		for creature_state in Game.get_creatures(game_state):
			if Card.id(creature_state) == Card.id(target_creature_state):
				new_creatures.append(target_creature_state)
			else:
				new_creatures.append(creature_state)
		game_state = Game.set_creatures(game_state, tuple(new_creatures))

		if mana_to_use == ('G', 'G'):
			target_creature_state = Creature.increment_temp_strength(target_creature_state, 4)
			target_creature_state = Creature.increment_temp_hit_points(target_creature_state, 4)
			game_state = Game.set_creature_with_id(game_state, target_creature_state, target_creature_id)

			new_creatures = []
			for creature_state in Game.get_creatures(game_state):
				if Card.id(creature_state) == Card.id(target_creature_state):
					new_creatures.append(target_creature_state)
				else:
					new_creatures.append(creature_state)
			game_state = Game.set_creatures(game_state, tuple(new_creatures))

		pwp = Card.owner(card_state)
		game_state = Game.remove_card_from_hand(game_state, pwp, card_state)
		if Game.print_moves(game_state):
			caster_state = Game.get_player_states(game_state)[pwp]
			if mana_to_use == ('G', ):
				print "> {} played VinesOfVastwood on {}." \
					.format(
						BoGamet.player_display_name(caster_state, pwp), 
						Creature.name(target_creature_state))
			else:
				print "> {} played kicked VinesOfVastwood on {}, total power now {}." \
					.format(
						Game.player_display_name(caster_state, pwp), 
						Creature.name(target_creature_state),
						Creature.total_damage(target_creature_state))
		return game_state


class HungerOfTheHowlpack(Card):
	"""
		Put a +1/+1 counter on target creature.
		Morbid - Put three +1/+1 counters on that creature instead if a creature died this turn.
	"""

	@staticmethod
	def possible_moves(card_state, game_state, Game):
		"""Returns possible VinesOfVastwood targets."""
		available_mana = Game.available_mana(game_state)
		possible_moves = []
		pwp = Game.player_with_priority(game_state)
		
		green_count = 0
		for color, count in available_mana.iteritems():
			if type(color) == str:
				if 'G' in color:
					green_count += count
					break

		for creature_state in Game.get_creatures(game_state):
			if not Creature.targettable(creature_state):
				continue
			if Creature.hexproof(creature_state) and Card.owner(creature_state) != pwp:
				continue
			if green_count > 0:
				card_index = Game.get_hand(game_state, pwp).index(card_state)
				possible_moves.append(('card-{}'.format(Card.name(creature_state)), 
										card_index, 
										(('G', ), None), 
										Card.id(creature_state),
										None,
										pwp))

		return possible_moves


	@staticmethod
	def play(card_state, game_state, mana_to_use, target_creature_id, Game):
		"""Pump a creature based on how much mana is used."""
		target_creature_state = Game.creature_with_id(game_state, target_creature_id)
		if target_creature_state:
			target_creature_state = Creature.increment_strength_counters(target_creature_state, 1)
			target_creature_state = Creature.increment_hit_point_counters(target_creature_state, 1)
			if Game.get_creature_died_this_turn(game_state):
				target_creature_state = Creature.increment_strength_counters(target_creature_state, 2)
				target_creature_state = Creature.increment_hit_point_counters(target_creature_state, 2)
			game_state = Game.set_creature_with_id(game_state, target_creature_state, target_creature_id)

		new_creatures = []
		for creature_state in Game.get_creatures(game_state):
			if target_creature_state and Card.id(creature_state) == Card.id(target_creature_state):
				new_creatures.append(target_creature_state)
			else:
				new_creatures.append(creature_state)
		game_state = Game.set_creatures(game_state,new_creatures)

		game_state = Game.remove_card_from_hand(game_state, Game.player_with_priority(game_state), card_state)

		if Game.print_moves(game_state):
			format_str = None
			if Game.creature_died_this_turn(game_state):
				format_str = "> Player {} played {} on {}, with morbid, total stats now {}/{}.."
			else:
				format_str = "> Player {} played {} on {}, total stats now {}/{}."
			print format_str.format( 
				Card.owner(card_state), 
				Card.name(card_state),
				Card.name(target_creature_state),
				Creature.total_damage(target_creature_state),
				Creature.total_hit_points(target_creature_state),
			)
		return game_state


class Fireball(Card):
	"""A card that deal X damage to anything."""

	@staticmethod
	def possible_moves(card_state, game_state, Game):
		"""Returns possible fireballs targets and amounts."""
		available_mana = Game.available_mana(game_state)
		possible_moves = []
		pwp = Game.player_with_priority(game_state)
		
		has_red = False
		total_mana = 0
		for color, count in available_mana.iteritems():
			total_mana += count
			if 'R' in color:
				has_red = True

		if has_red and total_mana > 1:
			card_index = Game.get_hand(game_state, pwp).index(card_state)
			for mana in range(2, total_mana+1):
				possible_moves.append(('card-fireball', 
										card_index,
										(('R', ), mana-1),
										None,
										None,
										pwp))
			for creature_state in Game.get_creatures(game_state):
				if Creature.hexproof(creature_state) and Card.owner(creature_state) != pwp:
					continue
				if Creature.targettable(creature_state) and Creature.temp_targettable(creature_state):
					for mana in range(2, total_mana+1):
						possible_moves.append(('card-fireball-creature', 
							card_index, 
							(('R', ), mana-1), 
							Card.id(creature_state),
							None,
							pwp))
		return possible_moves

	@staticmethod
	def play(card_state, game_state, mana_to_use, target_creature_id, Game):
		"""Decrement hit_points equal to blaster's mana from blastee."""
		pwp = Game.player_with_priority(game_state)
		blaster = Game.get_player_states(game_state)[pwp]
		game_state = Game.remove_card_from_hand(game_state, pwp, card_state)

		colorless = 0
		if mana_to_use[1] != None:
			colorless = mana_to_use[1]
		if target_creature_id:
			creature = Game.creature_with_id(game_state, target_creature_id)
			if (colorless) >= Creature.total_hit_points(creature):
				if creature.id in Game.get_attackers(game_state):
					game_state = Game.remove_attacker(game_state, Card.id(creature))
				for e in Creature.enchantments(creature):
					game_state = Card.on_graveyard(e, game_state, Game)
				game_state = Card.on_graveyard(creature, game_state, Game)
				game_state = Game.remove_creature(game_state, creature)
				game_state = Game.set_creature_died_this_turn(game_state, True)
			else:
				target_creature_state = Creature.increment_temp_hit_points(creature, colorless)
				new_creatures = []
				for creature_state in Game.get_creatures(game_state):
					if Card.id(creature_state) == Card.id(target_creature_state):
						new_creatures.append(target_creature_state)
					else:
						new_creatures.append(creature_state)
				game_state = Game.set_creatures(game_state, new_creatures)

			if Game.print_moves(game_state):
				print "> {} fireballed {} for {} damage." \
				.format(bot.display_name(blaster, pwp), Card.name(creature), colorless)
		else:
			blastee = Game.opponent(game_state, blaster)
			game_state = Game.increment_hit_points(game_state, Game.get_player_states(game_state).index(blastee), -colorless)
			game_state = Game.increment_damage_to_player(game_state, Game.get_player_states(game_state).index(blastee), colorless)

			if Game.print_moves(game_state):
				print "> {} fireballed for {} damage." \
				.format(Game.player_display_name(blaster, pwp), colorless)

		return game_state


class Creature(Card):
	"""A fantasy creature card instance."""

	@staticmethod
	def get_tuple(classname, owner, new_id, turn_played, 
		flying=False,
		hexproof=False,
		lifelink=False):
		"""Return a hashable tuple representing the Card."""
		return (
			classname,
			owner, 
			new_id, 
			False, # tapped 
			turn_played, 
			name_to_card_type[classname], 
			False, #targettable, 
			0, # temp_strength, 
			0, # temp_hit_points,
			False, # temp_targettable,
			False, # activated_ability,
			'instant', # activated_ability_type,
			0, # strength_counters,
			0, #hit_point_counters,
			flying,
			hexproof,
			lifelink,
			(),
		)

	@staticmethod
	def adjust_for_end_turn(card_state):
		state = Creature.set_temp_strength(card_state, 0)
		state = Creature.set_temp_hit_points(card_state, 0)
		state = Creature.set_temp_targettable(card_state, False)
		return card_state

	@staticmethod
	def total_damage(card_state):
		enchantment_damage = 0
		for e_state in Creature.enchantments(card_state):
			enchantment_damage += CreatureEnchantment.attack_bonus(e_state)
		return name_to_stats[Card.name(card_state)][0] + Creature.temp_strength(card_state) + Creature.strength_counters(card_state) + enchantment_damage

	@staticmethod
	def total_hit_points(card_state):
		enchantment_hit_points = 0
		for e_state in Creature.enchantments(card_state):
			enchantment_hit_points += CreatureEnchantment.defense_bonus(e_state)
		return name_to_stats[Card.name(card_state)][1] + Creature.temp_hit_points(card_state) + Creature.hit_point_counters(card_state) + enchantment_hit_points

	@staticmethod
	def can_attack(card_state, game_state, Game):
		"""Returns False if the creature was summoned this turn."""
		return Card.turn_played(card_state) < Game.get_current_turn(game_state) and Card.tapped(card_state) == False

	@staticmethod
	def play(card_state, game_state, mana_to_use, target_creature_id, Game):
		"""Summon the creature for the player_with_priority."""
		pwp = Card.owner(card_state)
		game_state = Game.remove_card_from_hand(game_state, pwp, card_state)
		card_state = Card.set_turn_played(card_state, Game.get_current_turn(game_state))
		game_state = Game.add_creature(card_state, game_state)
		if Game.print_moves(game_state):
			summoner = Game.get_player_states(game_state)[pwp]
			print "> {} summoned a {}." \
				.format(
					Game.player_display_name(summoner, pwp), 
					Card.name(card_state)
				)
		return game_state

	@staticmethod
	def possible_ability_moves(card_state, game_state, Game):
		if Card.name(card_state) == 'QuirionRanger':
			return QuirionRanger.possible_ability_moves(card_state, game_state, Game)
		elif Card.name(card_state) == 'EldraziSpawnToken':
			return EldraziSpawnToken.possible_ability_moves(card_state, game_state, Game)
		return []

	@staticmethod
	def can_be_blocked_by(card_state, creature):
		if Creature.flying(card_state) and not Creature.flying(creature):
			return False
		elif Creature.name(card_state) == 'SkarrganPitSkulk':
			return SkarrganPitSkulk.can_be_blocked_by(card_state, creature)
		elif Creature.name(card_state) == 'SilhanaLedgewalker':
			return SilhanaLedgewalker.can_be_blocked_by(card_state, creature)
		return True

	@staticmethod
	def creature_types(card_state):
		return []

	@staticmethod
	def did_deal_damage(card_state, game_state):
		if Creature.lifelink(card_state):
			pwp = Card.owner(card_state)
			game_state = Game.increment_hit_point(game_state, pwp, Creature.total_damage(card_state))
			if Game.print_moves(game_state):
				print "> {} gained {} life from {}." \
					.format(
						Game.player_display_name(owner, pwp), 
						Creature.total_damage(card_state), 
						Card.name(card_state)
					)
		return game_state

	@staticmethod
	def possible_moves(card_state, game_state, Game):
		"""Returns [] if the player doesn't have enough mana, other returns the action to play the creature."""
		available_mana = Game.available_mana(game_state)
		
		colored_symbols = []
		for mana in Card.total_mana_cost(card_state)[0]:
			if 'L' not in mana:
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

		if len(colored_symbols) == 0 and total_mana >= Card.mana_cost(card_state):
			pwp = Game.player_with_priority(game_state)
			card_index = Game.get_hand(game_state, pwp).index(card_state)
			return [('card-{}'.format(Card.name(card_state)), 
				card_index, 
				Card.total_mana_cost(card_state), 
				None,
				None,
				pwp)]
		return []

	@staticmethod
	def has_trample(card_state):
		for e in Creature.enchantments(card_state):
			if Card.name(e) == "Rancor":
				return True
		return False

	@staticmethod
	def targettable(card_state):
		return card_state[6]

	@staticmethod
	def temp_strength(card_state):
		return card_state[7]

	@staticmethod
	def temp_hit_points(card_state):
		return card_state[8]

	@staticmethod
	def temp_targettable(card_state):
		return card_state[9]

	@staticmethod
	def activated_ability(card_state):
		return card_state[10]

	@staticmethod
	def activated_ability_type(card_state):
		return card_state[11]

	@staticmethod
	def strength_counters(card_state):
		return card_state[12]

	@staticmethod
	def hit_point_counters(card_state):
		return card_state[13]

	@staticmethod
	def flying(card_state):
		return card_state[14]

	@staticmethod
	def hexproof(card_state):
		return card_state[15]

	@staticmethod
	def lifelink(card_state):
		return card_state[16]

	@staticmethod
	def enchantments(card_state):
		return card_state[17]

	@staticmethod
	def increment_temp_strength(card_state, increment):
		mutable_tuple = list(card_state)
		mutable_tuple[7] += increment
		return tuple(mutable_tuple)

	@staticmethod
	def increment_temp_hit_points(card_state, increment):
		mutable_tuple = list(card_state)
		mutable_tuple[8] += increment
		return tuple(mutable_tuple)

	@staticmethod
	def increment_strength_counters(card_state, increment):
		mutable_tuple = list(card_state)
		mutable_tuple[12] += increment
		return tuple(mutable_tuple)

	@staticmethod
	def increment_hit_point_counters(card_state, increment):
		mutable_tuple = list(card_state)
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
	def react_to_spell(game_state, reacting_self, spell, Game):
		total_mana_cost = Card.total_mana_cost(spell)
		for item in total_mana_cost[0]:
			if 'G' in item:
				card_state = Card.set_tapped(reacting_self, False)
				game_state = Game.set_creature_with_id(game_state, card_state, Card.id(card_state))
				return game_state
		return game_state

	@staticmethod
	def creature_types(self):
		return ['Elf', 'Warrior']


class QuirionRanger(Creature):
	"""
		Nettle Sentinel doesn't untap during your untap step.
		
		Whenever you cast a green spell, you may untap Nettle Sentinel.
	"""

	#TODO is activated_ability getting tuple set to False?
	'''
	def __init__(self, owner, card_id, tapped=False, turn_played=-1):
		super(QuirionRanger, self).__init__(owner, card_id, tapped=tapped, turn_played=turn_played)
		self.activated_ability = False
	'''

	@staticmethod
	def possible_ability_moves(card_state, game_state, Game):
		if Creature.activated_ability(card_state):
			return []
		untapped_forest = None
		tapped_forest = None
		for land_state in Game.get_lands(game_state):
			if Card.owner(land_state) != Card.owner(card_state):
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
				for creature_state in Game.get_creatures(game_state):
					if Card.owner(creature_state) == Card.owner(card_state):
						possible_moves.append(
							(
								'ability-{}'.format(Card.name(card_state)), 
								Game.get_creatures(game_state).index(card_state), 
								((), None), 
								Card.id(creature_state), 
								Card.id(land_state),
								Game.player_with_priority(game_state),
								card_state, 

							)
						)
		return possible_moves

	@staticmethod
	def activate_ability(card_state, game_state, mana_to_use, target_creature_id, target_land_id, card_in_play, Game):
		"""Return a forest to player's hand and untap a creature."""
		card_state = Creature.set_activated_ability(card_state, True)
		for creature_state in Game.get_creatures(game_state):
			if Card.id(creature_state) == target_creature_id:
				creature_state = Creature.set_tapped(creature_state, False)
				break
		game_state = Game.set_creature_with_id(game_state, card_state, target_creature_id)

		land_to_return = None
		for land_state in Game.get_lands(game_state):
			if Card.id(land_state) == target_land_id:
				land_to_return = land_state
				break
		game_state = Land.return_to_hand(game_state, land_to_return, Game)

		if Game.print_moves(game_state):
			pwp = Game.player_with_priority(game_state)
			player = Game.get_player_states(game_state)[pwp]
			print "> {} untapped {} with {} returning {}." \
				.format(
					Game.player_display_name(player, pwp), 
					Card.name(creature_state), 
					Card.name(card_state),
					Card.name(land_to_return),
				)

		return game_state

	@staticmethod
	def creature_types(self):
		return ['Elf']


class BurningTreeEmissary(Creature):
	"""When Burning-Tree Emissary enters the battlefield, add RedGreen."""

	@staticmethod
	def play(card_state, game_state, mana_to_use, target_creature_id, Game):
		game_state = Creature.play(card_state, game_state, mana_to_use, target_creature_id, Game)
		player = Game.get_player_states(game_state)[Card.owner(card_state)]
		game_state = Game.add_temp_mana(game_state, pwp, ('G', 'R'))
		return game_state

	@staticmethod
	def creature_types(self):
		return ['Human', 'Shaman']


class SkarrganPitSkulk(Creature):
	"""
		Bloodthirst 1 (If an opponent was dealt damage this turn, this creature enters the 
		battlefield with a +1/+1 counter on it.)
		Creatures with power less than Skarrgan Pit-Skulk's power can't block it.
	"""

	@staticmethod
	def play(card_state, game_state, mana_to_use, target_creature_id, Game):
		game_state = Creature.play(card_state, game_state, mana_to_use, target_creature_id, Game)

		if Game.opponent_was_dealt_damage(game_state):
			mutable_tuple = list(card_state)
			mutable_tuple[12] += 1
			mutable_tuple[13] += 1
			card_state = tuple(mutable_tuple)

			new_creatures = []
			for c_state in Game.get_creatures(game_state):
				if Card.id(c_state) == Card.id(card_state):
					new_creatures.append(card_state)
				else:
					new_creatures.append(c_state)
			game_state = Game.set_creatures(game_state, new_creatures)			
		return game_state

	@staticmethod
	def can_be_blocked_by(card_state, creature):
		if Creature.total_damage(creature) < Creature.total_damage(card_state):
			return False
		return True

	@staticmethod
	def creature_types(self):
		return ['Human', 'Warrior']


class NestInvader(Creature):
	"""
		When Nest Invader enters the battlefield, create a 0/1 colorless Eldrazi Spawn creature token. 
		It has "Sacrifice this creature: Add Colorless."
	"""

	@staticmethod
	def play(card_state, game_state, mana_to_use, target_creature_id, Game):
		game_state = Creature.play(card_state, game_state, mana_to_use, target_creature_id, Game)
		pwp = Card.owner(card_state)
		token_state = Creature.get_tuple(
			'EldraziSpawnToken', 
			pwp, 
			Game.get_new_card_id(game_state), 
			Game.get_current_turn(game_state)
		)
		game_state = Game.increment_new_card_id(game_state)
		game_state = Game.add_card_to_hand(game_state, token_state)
		game_state = Creature.play(token_state, game_state, mana_to_use, target_creature_id, Game)
		return game_state

	def creature_types(self):
		return ['Eldrazi', 'Drone']


class EldraziSpawnToken(Creature):
	"""
		An 0/1 colorless Eldrazi Spawn creature token. 
		It has "Sacrifice this creature: Add Colorless."
	"""

	@staticmethod
	def creature_types(self):
		return ['Eldrazi', 'Token']

	@staticmethod
	def possible_ability_moves(card_state, game_state, Game):
		return [
			(
				'ability-{}'.format(Card.name(card_state)), 
				Game.get_creatures(game_state).index(card_state), 
				((), None), 
				None, 
				None,
				Game.player_with_priority(game_state),
				card_state, 
			)
		]

	@staticmethod
	def activate_ability(card_state, game_state, mana_to_use, target_creature_id, target_land_id, card_in_play, Game):
		# print "eldrazi from gs {}".format(decarded_state(game_state))
		if Creature.id(card_state) in Game.get_attackers(game_state):
			game_state = Game.remove_attacker(game_state, Creature.id(card_state))
		if Creature.id(card_state) in Game.get_blockers(game_state):
			game_state = Game.remove_blocker(game_state, Creature.id(card_state))

		block_where_attacking = None
		block_where_blocking = None

		for block in Game.get_blocks(game_state):
			if block[0] == Creature.id(card_state):
				block_where_attacking = block
			if Creature.id(card_state) in block[1]:
				block_where_blocking = block

		if block_where_attacking:
			game_state = Game.remove_block(game_state, block_where_attacking)
		if block_where_blocking:
			game_state = Game.remove_from_block(game_state, card_state, block_where_blocking)

		for c_state in Game.get_creatures(game_state):
			if Card.id(c_state) == Creature.id(card_state):
				game_state = Game.remove_creature(game_state, c_state)
				break

		pwp = Game.player_with_priority(game_state)
		acting_player = Game.get_player_states(game_state)[pwp]
		#print "adding temp mana to {}".format(Game.temp_mana(acting_player))
		game_state = Game.add_temp_mana(game_state, pwp, (1, ))
		acting_player = Game.get_player_states(game_state)[pwp]
		#print "now has temp mana to {}".format(Game.temp_mana(acting_player))
		game_state = Game.set_creature_died_this_turn(game_state, True)
		game_state = Card.on_graveyard(card_state, game_state, Game)
		for e in Creature.enchantments(card_state):
			game_state = Card.on_graveyard(e, game_state, Card)
		
		if Game.print_moves(card_state):
			print "> {} sacrificed {}." \
				.format(
					Game.player_display_name(player, pwp), 
					Card.name(card_state), 
				)
		# print "EDLDRAZU to gs {}".format(decarded_state(game_state))
		return game_state

class SilhanaLedgewalker(Creature):
	"""
		Hexproof (This creature can't be the target of spells or abilities your opponents control.)
		Silhana Ledgewalker can't be blocked except by creatures with flying.
	"""
	#TODO is tuple hexproof being
	'''
	def __init__(self, owner, card_id, tapped=False, turn_played=-1):
		super(SilhanaLedgewalker, self).__init__(owner, card_id, tapped=tapped, turn_played=turn_played)
		self.hexproof = True
	'''

	@staticmethod
	def can_be_blocked_by(card_state, creature):
		return Creature.flying(creature)

	@staticmethod
	def creature_types(self):
		return ['Elf', 'Rogue']


class VaultSkirge(Creature):
	"""
		(Phyrexian Black can be paid with either Black or 2 life.)
		Flying
		Lifelink (Damage dealt by this creature also causes you to gain that much life.)
	"""
	#TODO is tuple flying, lifelink being set
	'''
	def __init__(self, owner, card_id, tapped=False, turn_played=-1):
		super(VaultSkirge, self).__init__(owner, card_id, tapped=tapped, turn_played=turn_played)
		self.flying = True
		self.lifelink = True
	'''

	@staticmethod
	def creature_types(self):
		return ['Artifact', 'Imp']


class CreatureEnchantment(Card):
	"""A fantasy enchantment card instance."""

	#TODO is tuple card_type = "enchantment" being set
	'''
	def __init__(self, owner, card_id, tapped=False, turn_played=-1):
		super(CreatureEnchantment, self).__init__(owner, card_id, tapped=False, turn_played=turn_played)
		self.card_type = "enchantment"
	'''

	@staticmethod
	def attack_bonus(card_state):
		return attack_bonus_map[Card.name(card_state)]

	@staticmethod
	def defense_bonus(card_state):
		return defense_bonus_map[Card.name(card_state)]

	@staticmethod
	def play(card_state, game_state, mana_to_use, target_creature_id, Game):
		"""Summon the enchantment for the player_with_priority."""
		pwp = Game.player_with_priority(game_state)
		summoner = Game.get_player_states(game_state)[pwp]
		game_state = Game.remove_card_from_hand(game_state, pwp, card_state)
		card_state = Card.set_turn_played(card_state, Game.get_current_turn(game_state))
		
		# should prolly need this
		#game_state = Game.add_permanent(game_state, land_state)

		target_creature_state = Game.creature_with_id(game_state, target_creature_id)
		if target_creature_state: # if it didn't die
			target_creature_state = Creature.add_enchantment(target_creature_state, state)
			new_creatures = []
			for creature_state in Game.get_creatures(game_state):
				if Card.id(creature_state) == Card.id(target_creature_state):
					new_creatures.append(target_creature_state)
				else:
					new_creatures.append(creature_state)
			game_state = Game.set_creatures(game_state, new_creatures)
		if Game.print_moves(game_state):
			print "> {} played a {} on {}." \
				.format(
					Game.player_display_name(summoner, pwp), 
					Card.name(card_state),
					Card.name(target_creature_state)
				)
		return game_state


	@staticmethod
	def possible_moves(card_state, game_state, Game):
		"""Returns [] if the player doesn't have enough mana, other returns the action to play the enchantment."""
		available_mana = Game.available_mana(game_state)
		has_green = False
		total_mana = 0
		pwp = Game.player_with_priority(game_state)
		card_index = Game.get_hand(game_state, pwp).index(card_state)
		possible_moves = []
		for color, count in available_mana.iteritems():
			total_mana += count
			if type(color) != int and 'G' in color:
				has_green = True
		if has_green and total_mana >= Card.mana_cost(card_state):
			for c_state in Game.get_creatures(game_state):
				if Creature.hexproof(c_state) and Card.owner(c_state) != pwp:
					continue
				if Creature.targettable(c_state) and Creature.temp_targettable(c_state):
					possible_moves.append(
						('card-rancor', 
						card_index, 
						(('G', ), None), 
						Card.id(c_state),
						None,
						pwp))
		return possible_moves


class Rancor(CreatureEnchantment):
	"""
		Enchanted creature gets +2/+0 and has trample.
		When Rancor is put into a graveyard from the battlefield, 
		return Rancor to its owner's hand.
	"""
	pass

class ElephantGuide(CreatureEnchantment):
	"""
		Enchanted creature gets +3/+3.
		When enchanted creature dies, create a 3/3 green Elephant creature token.
	"""
	pass


class ElephantToken(Creature):
	"""
		An 3/3 green Elephant Spawn creature token. 
	"""

	@staticmethod
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
			'NestInvader':(('G', ), 1),
			'SilhanaLedgewalker':(('G', ), 1),
			'VaultSkirge': (('B', ), 1),
			'VinesOfVastwood': (('G', ), None),
			'HungerOfTheHowlpack': (('G', ), None),
			'NettleSentinel': (('G', ), None),
			'QuirionRanger': (('G', ), None),
			'BurningTreeEmissary': (('RG', 'RG', ), None),
			'SkarrganPitSkulk': (('G', ), None),
			'Rancor': (('G', ), None),
			'EldraziSpawnToken': ((), 0),
			'ElephantGuide': (('G', ), 2),	
			'ElephantToken': ((), 0),	
			'Forest': ((), None),	
			'Mountain': ((), None),	
		}


name_to_card_type = {
			'NestInvader': 'creature',
			'SilhanaLedgewalker': 'creature',
			'VaultSkirge': 'creature',
			'VinesOfVastwood': 'instant',
			'HungerOfTheHowlpack': 'instant',
			'NettleSentinel': 'creature',
			'QuirionRanger': 'creature',
			'BurningTreeEmissary': 'creature',
			'SkarrganPitSkulk': 'creature',
			'Rancor': 'enchantment',
			'EldraziSpawnToken': 'creature',
			'ElephantGuide': 'enchantment',	
			'ElephantToken': 'creature',	
			'Forest': 'land',	
			'Mountain': 'land',	
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


def decarded_state(state_clone):
	mutable_player = list(state_clone[4][0])
	mutable_player[1] = ()
	mutable_player[4] = ()

	mutable_players = list(state_clone[4])
	mutable_players[0] = tuple(mutable_player)

	mutable_player = list(state_clone[4][1])
	mutable_player[1] = ()
	mutable_player[4] = ()

	mutable_players[1] = tuple(mutable_player)

	mutable_state = list(state_clone)
	mutable_state[4] = tuple(mutable_players)
	mutable_state[14] = True
	return tuple(mutable_state)


