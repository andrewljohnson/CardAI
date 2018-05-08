"""Game encapsulates the rules and state of a fantasy card game, and interface with bots."""

import collections
import itertools
import json
import pickle

from card import Card, Creature, Land
from card import Forest, QuirionRanger, NestInvader, BurningTreeEmissary, SkarrganPitSkulk, \
	SilhanaLedgewalker, VaultSkirge, VinesOfVastwood, Rancor, ElephantGuide, HungerOfTheHowlpack, \
	NettleSentinel
from constants import *
from random import choice, shuffle
from statcache import StatCache


class Game():
	"""A fantasy card game instance."""

	def __init__(self):
		"""Set the list of players, and set the current_player to the first player."""
		pass
		
	# whether to print each move, typically False during simulation, but true for a real game
	@staticmethod
	def print_moves(game_state):
		return game_state[14]

	@staticmethod
	def set_print_moves(game_state, print_moves):
		mutable = list(game_state)
		mutable[14] = print_moves
		return tuple(mutable)

	@staticmethod
	def add_player(game_state, player_state):
		mutable = list(game_state)
		mutable_players = list(mutable[4])
		mutable_players.append(player_state)
		mutable[4] = tuple(mutable_players)
		return tuple(mutable)
	
	@staticmethod
	def new_player_state_object(hit_points=0):
		return (
			hit_points, 
			(), #hand
			(), #temp_mana
			"random", #TODO name from subclasses
			-1, # deck
		)

	@staticmethod
	def print_board(game_state, show_opponent_hand=True):
		'''	
		20 life - mcst - Mana: []
		[HAND]
		[LANDS]
		[CREATURES]
		____________

		[CREATURES]
		[LANDS]
		[HAND]
		20 life - YOU - Mana: []
		'''
		top_player = 1
		bottom_player = 0
		
		if Game.is_human_playing(game_state):
			top_player = 0
			bottom_player = 1
		print "".join(["~" for x in range(0,SCREEN_WIDTH)])
		Game.print_bot_board(Game.get_player_states(game_state)[top_player], game_state, show_hand=(not Game.is_human_playing(game_state)))
		
		middle_bar_width = SCREEN_WIDTH/3
		spaces = "".join([" " for x in range(0,(SCREEN_WIDTH-middle_bar_width)/2)])
		bars = "".join(["_" for x in range(0,middle_bar_width)])
		print ""
		print "{}{}".format(spaces, bars)
		print ""
		Game.print_bot_board(Game.get_player_states(game_state)[bottom_player], game_state)
		print "".join(["~" for x in range(0,SCREEN_WIDTH)])
		print ""


	@staticmethod
	def player_display_name(player_state, current_player):
		return "Player {} ({})".format(current_player + 1, Game.get_bot_type(player_state))

	@staticmethod 
	def hit_points(game_state):
		return game_state[0]

	@staticmethod 
	def temp_mana(player_state):
		return player_state[2]

	@staticmethod
	def print_bot_board(player_state, game_state, show_hand=True):
		'''	
		20 life - mcst - Mana: []
		[HAND]
		[LANDS]
		[CREATURES]

		OR

		[CREATURES]
		[LANDS]
		[HAND]
		20 life - YOU - Mana: []

		'''
		ps1 = Game.get_player_states(game_state)[1] 
		player_number = Game.get_player_states(game_state).index(player_state)
		if ps1 == player_state:
			player_str = "{} life - {} - Mana Pool: {}".format(
				Game.hit_points(player_state), 
				Game.player_display_name(player_state, 1), 
				Game.temp_mana(player_state)
			)
			spaces = "".join([" " for x in range(0,(SCREEN_WIDTH-len(player_str))/2)])
			print "{}{}\n".format(spaces, player_str)
			Card.print_hand(Game.get_hand(game_state, player_number), show_hand=show_hand)
			if len(Game.get_lands(game_state)):
				Card.print_hand(Game.get_lands(game_state), owner=player_number)
			if len(Game.get_creatures(game_state)):
				Card.print_hand(Game.get_creatures(game_state), owner=player_number)
		else:
			if len(Game.get_creatures(game_state)):
				Card.print_hand(Game.get_creatures(game_state), owner=player_number)
			if len(Game.get_lands(game_state)):
				Card.print_hand(Game.get_lands(game_state), owner=player_number)
			Card.print_hand(Game.get_hand(game_state, player_number), show_hand=show_hand)
			player_str = "{} life - {} - Mana Pool: {}".format(
				Game.hit_points(player_state), 
				Game.player_display_name(player_state, 0), 
				Game.temp_mana(player_state))
			spaces = "".join([" " for x in range(0,(SCREEN_WIDTH-len(player_str))/2)])
			print "\n{}{}".format(spaces, player_str)


	@staticmethod
	def new_game_state():
		return (0, #current_turn
				0, #player_with_priority
				0, #new_card_id
				'setup', #phase
				(), #player_states
				(), #creatures
				(), #lands
				(), #attackers
				(), #blockers
				(), #blocks
				(0, 0), #damage_to_players
				(), #stack
				False, #creature_died_this_turn
				None, #current_spell_move,
				False #print_moves
		)

	@staticmethod
	def clear_damage_to_players(game_state):
		mutable = list(game_state)
		mutable[10] = (0, 0,)
		return tuple(game_state)

	@staticmethod
	def get_damage_to_players(game_state):
		return game_state[10]

	@staticmethod
	def increment_damage_to_player(game_state, player_index, damage_to_player):
		dtp_list = list (game_state[10])
		dtp_list[player_index] += damage_to_player
		mutable = list(game_state)
		mutable[10] = tuple(dtp_list)
		return tuple(mutable)

	@staticmethod
	def get_creature_died_this_turn(game_state):
		return game_state[12]

	@staticmethod
	def set_creature_died_this_turn(game_state, creature_died_this_turn):
		mutable = list(game_state)
		mutable[12] = creature_died_this_turn
		return tuple(mutable)

	@staticmethod
	def get_stack(game_state):
		return game_state[11]

	@staticmethod
	def set_stack(game_state, stack):
		mutable = list(game_state)
		mutable[11] = stack
		return tuple(mutable)

	@staticmethod
	def get_new_card_id(game_state):
		return game_state[2]

	@staticmethod
	def increment_new_card_id(game_state):
		mutable = list(game_state)
		mutable[2] += 1
		return tuple(mutable)

	@staticmethod
	def get_current_spell_move(game_state):
		return game_state[13]

	@staticmethod
	def set_current_spell_move(game_state, current_spell_move):
		mutable = list(game_state)
		mutable[13] = current_spell_move
		return tuple(mutable)

	@staticmethod
	def set_blocks(game_state, blocks):
		mutable = list(game_state)
		mutable[9] = tuple(blocks)
		return tuple(mutable)

	@staticmethod
	def add_block(game_state, block):
		mutable = list(game_state)
		mutable_blocks = list(game_state[9])
		mutable_blocks.append(block)
		mutable[9] = tuple(mutable_blocks)
		return tuple(mutable)

	@staticmethod
	def set_blockers(game_state, blockers):
		mutable = list(game_state)
		mutable[8] = tuple(blockers)
		return tuple(mutable)

	@staticmethod
	def add_blocker(game_state, blocker):
		mutable = list(game_state)
		mutable_blockers = list(game_state[8])
		mutable_blockers.append(blocker)
		mutable[8] = tuple(mutable_blockers)
		return tuple(mutable)

	@staticmethod
	def add_attacker(game_state, attacker):
		mutable = list(game_state)
		mutable_attackers = list(game_state[7])
		mutable_attackers.append(attacker)
		mutable[7] = tuple(mutable_attackers)
		return tuple(mutable)

	@staticmethod
	def set_attackers(game_state, attackers):
		mutable = list(game_state)
		mutable[7] = tuple(attackers)
		return tuple(mutable)

	@staticmethod
	def get_attackers(game_state):
		return game_state[7]

	@staticmethod
	def get_blockers(game_state):
		return game_state[8]

	@staticmethod
	def get_blocks(game_state):
		return game_state[9]

	@staticmethod
	def get_lands(game_state):
		return game_state[6]

	@staticmethod
	def set_land(game_state, new_land_state, land_index):
		lands = list(game_state[6])
		lands[land_index] = new_land_state
		mutable = list(game_state)
		mutable[6] = tuple(lands)
		return tuple(mutable)
		
	@staticmethod
	def get_creatures(game_state):
		return game_state[5]
		
	@staticmethod
	def add_creature(creature_state, game_state):
		mutable_creatures = list(game_state[5])
		mutable_creatures.append(creature_state)
		mutable = list(game_state)
		mutable[5] = tuple(mutable_creatures)
		return tuple(mutable)

	@staticmethod
	def get_player_states(game_state):
		return game_state[4]
		
	@staticmethod
	def set_player_state(state, new_player_state, player_index):
		players = list(state[4])
		players[player_index] = new_player_state
		mutable = list(state)
		mutable[4] = tuple(players)
		return tuple(mutable)

	@staticmethod
	def get_phase(state):
		return state[3]

	@staticmethod
	def set_phase(state, phase):
		mutable = list(state)
		mutable[3] = phase
		return tuple(mutable)

	@staticmethod
	def player_with_priority(state):
		return state[1]

	@staticmethod
	def play_out(game_state, statcache):
		"""Play out a game between two bots."""
		while not Game.game_is_over(game_state):
			bot = statcache.bots[Game.player_with_priority(game_state)]
			old_game_state = game_state
			print "GS BEFORE {}".format(decarded_state(game_state))
			move, game_state = bot.play_move(game_state, statcache)
			print "MOVE {}, GS AFTER {} (equals before: {}".format(move, decarded_state(game_state), old_game_state==game_state)

		winner, winning_hp, losing_hp = Game.winning_player(game_state)
		if Game.print_moves(game_state):
			if Game.game_is_drawn(game_state):
				print "Game Over - Draw"
			else:
				print "Game Over - {} wins! Final hit points are {} to {}." \
					.format(Game.player_display_name(winner, Game.get_player_states(game_state).index(winner)),
							winning_hp, 
							losing_hp)
		return winner

	@staticmethod
	def winner(state):
		"""
			Return -1 if the state_history is drawn, 0 if the game is ongoing, 
		
			else the player_number of the winner.
		"""

		if Game.game_is_drawn(state):
			return -2

		if len(Game.dead_players(state)) == 0:
			return -1

		winning_player, _, _ = Game.winning_player(state)

		return Game.get_player_states(state).index(winning_player)

	@staticmethod
	def winning_player(state):
		"""
			Return the winning player, hp of winning player, and hp of losing player. 

			Returns None, None, None on draws.
		"""
		if Game.game_is_drawn(state):
			return None, None, None
		losing_hp = None
		winning_hp = None
		winner = None
		for p in Game.get_player_states(state):
			if Game.hit_points(p) <= 0:
				losing_hp = Game.hit_points(p)
			else:
				winning_hp = Game.hit_points(p)
				winner = p

		return winner, winning_hp, losing_hp

	@staticmethod
	def game_is_drawn(state):
		"""Return True if all players has <= 0 hit points."""
		return len(Game.dead_players(state)) == len(Game.get_player_states(state))

	@staticmethod
	def game_is_over(state):
		"""Return True if either player has <= 0 hit points."""
		return len(Game.dead_players(state)) > 0

	@staticmethod
	def dead_players(state):
		"""Return a list of players that have hit points <= 0."""
		dead_players = []
		for p in Game.get_player_states(state):
			if Game.hit_points(p) <= 0:
				dead_players.append(p)
		return dead_players

	@staticmethod
	def acting_player(state):
		"""Return the player_number of the player due to make move in state."""
		return state[1]

	@staticmethod
	def apply_move(state, move):
		"""Return a new state after applying the move to state."""
		mana_to_use = move[2]
		if move[0] == 'play_next_on_stack':		
			state = Game.play_next_on_stack(state)
		elif move[0].startswith('card-cast'):
			# after this choose how to cast the chosen spell
			state = Game.play_move(state, move)
		elif move[0].startswith('card') or move[0].startswith('ability'):
			state = Game.tap_lands_for_mana(state, mana_to_use)
			state = Game.play_move(state, move)
		elif move[0].startswith('land_ability'):
			state = Game.tap_lands_for_mana(state, mana_to_use)
			state = Game.play_land_ability_move(state, move)
		else:
			if move[0] == 'initial_draw':
				state = Game.initial_draw(state, move[1])
			elif move[0] == 'draw_card':
				state = Game.draw_card(state, move[1])
			elif move[0] == 'finish_blocking':
				state = Game.finish_blocking(state, move[1])
			elif move[0] == 'declare_attack':
				state = Game.declare_attack(state, move[1])
			elif move[0] == 'resolve_combat':
				state = Game.resolve_combat(state, move[1])
			elif move[0] == 'no_attack':
				state = Game.resolve_combat(state, move[1])
			elif move[0] == 'pass_the_turn':
				state = Game.pass_the_turn(state, move[1])
			elif move[0] == 'pass_priority_as_defender':
				state = Game.pass_priority_as_defender(state, move[1])
			elif move[0] == 'pass_priority_as_attacker':
				state = Game.pass_priority_as_attacker(state, move[1])
			elif move[0] == 'announce_attackers':
				state = Game.announce_attackers(state, move[1])
			elif move[0] == 'assign_blockers':
				state = Game.assign_blockers(state, move[1])

		return state

	@staticmethod 
	def increment_hit_points(game_state, player_index, increment):

		mutable_player = list(game_state[4][player_index])
		mutable_player[0] += increment

		mutable_player_list = list(game_state[4])
		mutable_player_list[player_index] = tuple(mutable_player)

		mutable_game_state = list(game_state)
		mutable_game_state[4] = tuple(mutable_player_list)

		return tuple(mutable_game_state)

	@staticmethod 
	def add_temp_mana(state, player_index, mana_to_add):
		mutable_temp_mana = list(state[4][player_index][2])
		for m in mana_to_add:
			mutable_temp_mana.append(m)

		mutable_player = list(state[4][player_index])
		mutable_player[2] = tuple(mutable_temp_mana)

		mutable_player_list = list(state[4])
		mutable_player_list[player_index] = tuple(mutable_player)

		mutable_state = list(state)
		mutable_state[4] = tuple(mutable_player_list)
		
		return tuple(mutable_state)

	@staticmethod 
	def remove_temp_mana(state, player_index, index_to_remove):
		mutable_temp_mana = list(state[4][player_index][2])
		# print "removing from {}".format(mutable_temp_mana)
		del mutable_temp_mana[index_to_remove]

		mutable_player = list(state[4][player_index])
		mutable_player[2] = tuple(mutable_temp_mana)

		mutable_player_list = list(state[4])
		mutable_player_list[player_index] = tuple(mutable_player)

		mutable_state = list(state)
		mutable_state[4] = tuple(mutable_player_list)
		
		return tuple(mutable_state)

	@staticmethod 
	def clear_temp_mana(state, player_index):
		mutable_player = list(state[4][player_index])
		mutable_player[2] = ()

		mutable_player_list = list(state[4])
		mutable_player_list[player_index] = tuple(mutable_player)

		mutable_state = list(state)
		mutable_state[4] = tuple(mutable_player_list)

		return tuple(mutable_state)

	@staticmethod
	def set_land_tapped(game_state, land_state, tapped):
		land_index = game_state[6].index(land_state)
		tapped_state = Card.set_tapped(land_state, tapped)

		mutable_lands = list(game_state[6])
		mutable_lands[land_index] = tapped_state
		
		mutable_state = list(game_state)
		mutable_state[6] = tuple(mutable_lands)

		return tuple(mutable_state)

	@staticmethod
	def add_to_stack(state, move):
		stack = list(Game.get_stack(state))
		if Game.print_moves(state):
			print "STACK STARTED {}, adding move {}".format(stack, move)
		stack.append(move)
		if Game.print_moves(state):
			print "ADD TO STACK, now {}".format(stack)
		return Game.set_stack(state, tuple(stack))

	@staticmethod
	def set_priority(state, player_index):
		mutable = list(state)
		mutable[1] = player_index
		return tuple(mutable)

	@staticmethod
	def remove_card_from_hand(game_state, player_index, card_state):
		pwp = Card.owner(card_state)
		mutable_hand = list(game_state[4][pwp][1])
		mutable_hand.remove(card_state)

		mutable_player = list(game_state[4][pwp])
		mutable_player[1] = tuple(mutable_hand)

		mutable_player_list = list(game_state[4])
		mutable_player_list[pwp] =  tuple(mutable_player)

		mutable_game_state = list(game_state)
		mutable_game_state[4] = tuple(mutable_player_list)

		return tuple(mutable_game_state)

	@staticmethod
	def add_card_to_hand(game_state, card_state):
		pwp = Card.owner(card_state)

		mutable_hand = list(game_state[4][pwp][1])
		mutable_hand.append(card_state)

		mutable_player = list(game_state[4][pwp])
		mutable_player[1] = tuple(mutable_hand)
		tuple_player = tuple(mutable_player)

		mutable_player_list = list(game_state[4])
		mutable_player_list[pwp] = tuple_player
		tuple_player_list = tuple(mutable_player_list)

		mutable_game_state = list(game_state)
		mutable_game_state[4] = tuple_player_list
		game_state = tuple(mutable_game_state)

		return game_state

	@staticmethod
	def remove_attacker(game_state, creature_id):
		mutable_attackers = list(game_state[7])
		mutable_attackers.remove(creature_id)
		mutable_state = list(game_state)
		mutable_state[7] = tuple(mutable_attackers)
		return tuple(mutable_state)

	@staticmethod
	def remove_blocker(game_state, creature_id):
		mutable_blockers = list(game_state[8])
		mutable_blockers.remove(creature_id)
		mutable_state = list(game_state)
		mutable_state[8] = tuple(mutable_blockers)
		return tuple(mutable_state)

	@staticmethod
	def remove_block(game_state, block_tuple):
		mutable_blocks = list(game_state[9])
		mutable_blocks.remove(block_tuple)
		mutable_state = list(game_state)
		mutable_state[9] = tuple(mutable_blocks)
		return tuple(mutable_state)

	@staticmethod
	def remove_from_block(game_state, creature_to_remove, block):
		mutable_blocks = list(game_state[9])
		mutable_blocks.remove(block)

		mutable_block = list(block)
		mutable_blocker_list = list(mutable_block[1])
		mutable_blocker_list.remove(Card.id(creature_to_remove))
		mutable_block[1] = mutable_blocker_list

		mutable_blocks.append(tuple(mutable_block))
		
		mutable_state = list(game_state)
		mutable_state[9] = tuple(mutable_blocks)
		return tuple(mutable_state)

	@staticmethod
	def add_land(game_state, land_state):
		lands = list(game_state[6])
		lands.append(land_state)
		mutable_state = list(game_state)
		mutable_state[6] = tuple(lands)
		return tuple(mutable_state)

	@staticmethod
	def set_creature_with_id(game_state, target_creature_state, target_creature_id):
		index = 0
		for c in game_state[5]:
			if Card.id(c) == target_creature_id:
				break
			index += 1
		mutable_creatures = list(game_state[5])
		mutable_creatures[index] = target_creature_state
		mutable_state = list(game_state)
		mutable_state[5] = tuple(mutable_creatures)
		return tuple(mutable_state)

	@staticmethod
	def remove_creature(game_state, card_state):
		mutable_creatures = list(game_state[5])
		mutable_creatures.remove(card_state)
		mutable_game_state = list(game_state)
		mutable_game_state[5] = tuple(mutable_creatures)
		return tuple(mutable_game_state)

	@staticmethod
	def remove_land(game_state, card_state):
		mutable_lands = list(game_state[6])
		mutable_lands.remove(card_state)
		mutable_game_state = list(game_state)
		mutable_game_state[6] = tuple(mutable_lands)
		return tuple(mutable_game_state)

	@staticmethod
	def set_creatures(game_state, new_creatures):
		mutable_state = list(game_state)
		mutable_state[5] = tuple(new_creatures)
		return tuple(mutable_state)

	@staticmethod
	def set_lands(game_state, new_lands):
		mutable_state = list(game_state)
		mutable_state[6] = tuple(new_lands)
		return tuple(mutable_state)

	@staticmethod
	def tap_lands_for_mana(state, mana_to_tap):
		"""Tap land_to_tap lands to pay for a spell or effect."""
		colored = []
		life = []
		colorless = 0
		pwp = Game.player_with_priority(state)

		caster_state = Game.get_player_states(state)[pwp]
		for mana in mana_to_tap[0]:
			if mana.startswith("L"):
				state = Game.increment_hit_points(state, pwp, -1 * int(mana[1:]))
				if Game.print_moves(state):
					print "> {} lost {} life from casting a Phyrexian, now at {}." \
						.format(
							Game.player_display_name(caster_state, Game.player_with_priority(state)), 
							int(mana[1:]),
							Game.hit_points(caster_state)
						)
			else:
				colored.append(mana)

		if mana_to_tap[1] != None:
			colorless = mana_to_tap[1]

		while len(colored) > 0:
			mana = colored[0]
			temp_index_to_remove = 0
			found_temp = False
			for temp_mana in Game.temp_mana(caster_state):
				if type(temp_mana) == str and temp_mana in mana:
					colored.pop(0)
					found_temp = True
					break
				temp_index_to_remove += 1
			if found_temp:
				state = Game.remove_temp_mana(state, pwp, temp_index_to_remove)
				continue

			caster_state = Game.get_player_states(state)[pwp]

			used_land = False
			for land_state in Game.get_lands(state):
				if Card.owner(land_state) == pwp and not Card.tapped(land_state):
					used_land = False
					for c in mana:
						if c in Land.mana_provided(land_state):
							colored.pop(0)
							used_land = True
							state = Game.set_land_tapped(state, land_state, True)
							break
					if used_land:
						break


		while colorless > 0:
			temp_index_to_remove = 0
			found_temp = False
			# use up colorless temp
			for temp_mana in Game.temp_mana(caster_state):
				if type(temp_mana) == int:
					colorless -= temp_mana
					found_temp = True
					break
				temp_index_to_remove += 1
			if found_temp:
				state = Game.remove_temp_mana(state, pwp, temp_index_to_remove)
				continue

			caster_state = Game.get_player_states(state)[pwp]

			# use up colored temp
			temp_index_to_remove = 0
			for temp_mana in Game.temp_mana(caster_state):
				if type(temp_mana) == str:
					colorless -= 1
					found_temp = True
					break
				temp_index_to_remove += 1
			if found_temp:
				state = Game.remove_temp_mana(state, pwp, temp_index_to_remove)
				continue

			for land_state in Game.get_lands(state):
				if Card.owner(land_state) == pwp and not Card.tapped(land_state):
					state = Game.set_land_tapped(state, land_state, True)
					colorless -= 1

		return state

	@staticmethod
	def available_mana(state):
		"""
			Returns a map of color to amount of mana from player_with_priority's untapped lands
			and mana pool.
		"""
		mana = collections.Counter()
		pwp = Game.player_with_priority(state)
		for land_state in Game.get_lands(state):
			if Card.owner(land_state) == pwp and not Card.tapped(land_state):
				mana.update(Land.mana_provided(land_state))

		mana_dict = dict(mana)

		player_state = Game.get_player_states(state)[pwp] 
		for mana_symbol in Game.temp_mana(player_state):
			if mana_symbol in mana:
				mana_dict[mana_symbol] += 1
			else:
				mana_dict[mana_symbol] = 1				
		return mana_dict

	@staticmethod
	def play_move(game_state, move):
		"""Play a card based on the move tuple."""
		pwp = Game.player_with_priority(game_state)
		if move[0].startswith('card-cast'):
			return Game.set_current_spell_move(game_state, move)
		elif move[0].startswith('card'):
			game_state = Game.set_current_spell_move(game_state, None)
			# lands don't go on stack
			card_index = move[1]
			card_state = Game.get_hand(game_state, pwp)[card_index]
			if card_state[5] == 'land':				
				return Game.play_card_move_from_stack(game_state, move)

		if Game.print_moves(game_state):
			print "PLAYZ_MOVE {}".format(move)
		game_state = Game.add_to_stack(game_state, move)
		if pwp == Game.current_turn_player(game_state):
			game_state = Game.set_priority(game_state, Game.not_current_turn_player(game_state))
		else:
			game_state = Game.set_priority(game_state, Game.current_turn_player(game_state))
		return game_state

	@staticmethod
	def play_next_on_stack(state):
		stack_list = list(Game.get_stack(state))
		if Game.print_moves(state):
			print "play_next_on_stack from stack {}".format(stack_list)
		move = stack_list.pop()
		state = Game.set_stack(state, tuple(stack_list))
		if move[0].startswith('card'):
			state = Game.play_card_move_from_stack(state, move)
		elif move[0].startswith('ability'):
			Game.play_ability_move_from_stack(state, move)
		return state

	@staticmethod
	def play_card_move_from_stack(game_state, move):
		player_number = Game.player_with_priority(game_state)
		target_creature = move[3]
		mana_to_use = move[2]
		card_index = move[1]
		card_state = Game.get_hand(game_state, player_number)[card_index]
		game_state = Card.play(card_state, game_state, mana_to_use, target_creature, Game)
		for creature_state in Game.get_creatures(game_state):
			game_state = Creature.react_to_spell(game_state, creature_state, card_state, Game)
		for land_state in Game.get_lands(game_state):
			game_state = Land.react_to_spell(game_state, land_state, card_state, Game)
		return game_state

	@staticmethod
	def get_hand(game_state, player_number):
		return Game.get_player_states(game_state)[player_number][1]

	@staticmethod
	def play_ability_move_from_stack(game_state, move):
		"""Play an activated based on the move tuple."""
		player_number = Game.player_with_priority(game_state)
		active_player = Game.get_player_states(game_state)[player_number]
		if Game.print_moves(game_state):
			print "\n{}:\n temp mana {} and lands count {} before".format(move[0], Game.temp_mana(active_player), len(Game.get_lands(game_state)))
		target_creature_id = move[3]
		target_land_id = move[4]
		mana_to_use = move[2]
		card_index = move[1]
		card_state = Game.creature_with_id(game_state, move[6][2])
		card_in_play = Game.creature_with_id(game_state, target_creature_id)
		game_state = Card.activate_ability(card_state, game_state, mana_to_use, target_creature_id, target_land_id, card_in_play, Game)
		#TODO should this be diff function than in play_card_move?
		for creature_state in Game.get_creatures(game_state):
			game_state = Creature.react_to_spell(game_state, creature_state, card_state, Game)
		for land_state in Game.get_lands(game_state):
			game_state = Land.react_to_spell(game_state, land_state, card_state, Game)
		active_player = Game.get_player_states(game_state)[player_number]
		if Game.print_moves(game_state):
			print "temp mana {} and lands count {} after\n".format(Game.temp_mana(active_player), len(Game.get_lands(game_state)))
		return game_state

	@staticmethod
	def play_land_ability_move(state, move):
		"""Play an activated based on the move tuple."""
		player_number = Game.player_with_priority(state)
		target_creature_id = move[3]
		target_land_id = move[4]
		mana_to_use = move[2]
		card_index = move[1]
		card_state = Game.get_lands(state)[card_index]
		state = Land.activate_ability(card_state, state, Game)
		for creature_state in Game.get_creatures(state):
			#TODO react to land tapping
			pass
		for land_state in Game.get_lands(state):
			#TODO react to land tapping
			pass
		return state

	@staticmethod
	def opponent(state, player):
		"""Return the player that isn't the given player."""
		for p in Game.get_player_states(state):
			if p != player:
				return p

	@staticmethod
	def legal_plays(game_state):
		"""Return a list of all legal moves given the last state."""
		
		spell_on_stack = Game.get_current_spell_move(game_state)
		stack = Game.get_stack(game_state)
		pwp = Game.player_with_priority(game_state)
		current_player = Game.current_turn_player(game_state)
		phase = Game.get_phase(game_state)
		if spell_on_stack:
			return Game.card_actions(game_state, move=spell_on_stack)
		elif len(stack) > 0 and stack[-1][5] == pwp:		
			return [('play_next_on_stack', pwp, 0),]		
		elif len(stack) > 0 and stack[-1][5] != pwp and pwp == current_player:		
			return[('pass_priority_as_attacker', pwp, 0)]
		elif phase == "setup":
			return [('initial_draw', pwp, 0)]	
		elif phase == "draw":
			return [('draw_card', pwp, 0)]	
		elif phase == "attack_step" and pwp == current_player:
			possible_moves = set()
			possible_moves.add(('no_attack', pwp, 0))
			return list(Game.add_attack_actions(game_state, possible_moves))
		elif phase == "declare_blockers":
			return Game.all_legal_blocks(game_state)
		elif pwp != current_player:
			possible_moves = Game.add_instant_creature_abilities(game_state, set())
			possible_moves = Game.add_land_abilities(game_state, possible_moves)
			possible_moves.add(('pass_priority_as_defender', pwp, 0))
			return list(possible_moves)
		
		possible_moves = Game.add_cast_actions(game_state, set())
		possible_moves = Game.add_instant_creature_abilities(game_state, possible_moves)
		possible_moves = Game.add_land_abilities(game_state, possible_moves)
		if phase == "precombat" and len(Game.add_attack_actions(game_state, set())) > 0:
			possible_moves.add(('declare_attack', pwp, 0))			
		elif phase == "combat_resolution":
			possible_moves.add(('resolve_combat', pwp, 0),)
			return list(possible_moves)

		possible_moves.add(('pass_the_turn', pwp, 0))
			
		return list(possible_moves)

	@staticmethod
	def played_land(game_state):
		"""Returns True if the player_with_priority has played a land this turn."""
		pwp = Game.player_with_priority(game_state)
		curr_turn = Game.get_current_turn(game_state)
		for land_state in Game.get_lands(game_state):
			if Card.owner(land_state) == pwp and Card.turn_played(land_state) == curr_turn:
				return True

		for card_state in Game.get_hand(game_state, pwp):
			if Card.turn_played(card_state) == curr_turn and Card.card_type(card_state) == 'land':
				return True
		return False

	@staticmethod
	def add_cast_actions(game_state, possible_moves):
		"""Return a list of possible cast actions based on the player_with_priority's hand."""
		card_types_added = []
		pwp = Game.player_with_priority(game_state)
		hand = Game.get_hand(game_state, pwp) 
		for card_state in hand:
			if Card.name(card_state) not in card_types_added:
				if Game.get_phase(game_state) in ['attack_step', 'combat_resolution']:
					if Card.card_type(card_state) != 'instant':
						continue
				cast_moves = Card.cast_moves(card_state, game_state, hand.index(card_state), Game)
				if len(cast_moves) > 0:
					actions = Game.card_actions(game_state, move=cast_moves[0])
					if len(actions) == 1:
						possible_moves.add(actions[0])				
					else:
						[possible_moves.add(m) for m in Card.cast_moves(card_state, game_state, hand.index(card_state), Game)]
					card_types_added.append(Card.name(card_state))
		return possible_moves


	@staticmethod
	def card_actions(game_state, move=None):
		"""Return a list of possible actions based on the player_with_priority's hand."""
		possible_moves = set()
		card_index = move[1]
		pwp = Game.player_with_priority(game_state)
		hand = Game.get_hand(game_state, pwp) 
		card_state = hand[card_index]
		[possible_moves.add(m) for m in Card.possible_moves(card_state, game_state, Game)]
		return list(possible_moves)

	@staticmethod
	def add_instant_creature_abilities(game_state, possible_moves):
		"""Return a list of possible actions based on the player_with_priority's hand."""
		for creature_state in Game.get_creatures(game_state):
			if Card.owner(creature_state) == Game.player_with_priority(game_state):
				if Game.get_phase(game_state) in ['attack_step', 'combat_resolution']:
					if Creature.activated_ability_type(creature_state) != 'instant':
						continue
				[possible_moves.add(m) for m in Creature.possible_ability_moves(creature_state, game_state, Game)]
		return possible_moves

	@staticmethod
	def add_land_abilities(game_state, possible_moves):
		"""Return a list of possible actions based on the player_with_priority's lands."""
		land_types_added = set()
		for land_state in Game.get_lands(game_state):
			if Card.name(land_state) not in land_types_added:
				if Card.owner(land_state) == Game.player_with_priority(game_state):
					[possible_moves.add(m) for m in Land.possible_ability_moves(land_state, game_state, Game)]
					land_types_added.add(Card.name(land_state))
		return possible_moves

	@staticmethod
	def add_attack_actions(game_state, possible_moves):
		"""Return a list of possible actions based on the player_with_priority's creatures."""
		available_attackers = []
		for creature_state in Game.get_creatures(game_state):
			if Card.owner(creature_state) == Game.player_with_priority(game_state) and Creature.can_attack(creature_state, game_state, Game):
				available_attackers.append(Card.id(creature_state))
		
		if len(available_attackers) > 0 and len(Game.get_attackers(game_state)) == 0:
			for L in range(0, len(available_attackers)+1):
				for subset in itertools.combinations(available_attackers, L):
					if len(subset) > 0:
						possible_moves.add(('announce_attackers', subset, 0))
		return possible_moves

	@staticmethod
	def initial_draw(game_state, moving_player):
		"""Add some cards to each player's hand."""
	 	if Game.print_moves(game_state):
		 	print "initial_draw in phase {}".format(Game.get_phase(game_state))
	 	for i in range(0,7):
	 		game_state = Game.draw_card(game_state, moving_player);
	 	if Game.print_moves(game_state):
		 	print "did initial_draw"
		pwp = Game.player_with_priority(game_state)
		if pwp == Game.current_turn_player(game_state):
			game_state = Game.set_priority(game_state, Game.not_current_turn_player(game_state))
		else:	
			game_state = Game.set_priority(game_state, Game.current_turn_player(game_state))
			game_state = Game.set_phase(game_state, 'draw')
	 	if Game.print_moves(game_state):
			print "gs after initial draw is {}".format(decarded_state(game_state))
		return game_state

	@staticmethod
	def is_human_playing(game_state):
		for player_state in Game.get_player_states(game_state):
			if Game.get_bot_type(player_state) == "Human":
				return True
		return False

	@staticmethod
	def get_bot_type(player_state):
		return player_state[3]

	@staticmethod
	def increment_current_turn(state):
		mutable = list(state)
		mutable[0] += 1
		return tuple(mutable)

	@staticmethod
	def get_current_turn(state):
		return state[0]

	@staticmethod
	def current_turn_player(state):
		"""The index in players for the player whose turn it is. """
		return state[0] % 2

	@staticmethod
	def not_current_turn_player(state):
		"""The index in players for the player whose turn it isn't. """
		return int(state[0] + 1) % 2

	@staticmethod
	def draw_card(game_state, moving_player):
		"""Add a card to moving_player's hand."""
		new_card_class = None
		p_states = Game.get_player_states(game_state)
		current_player = p_states[moving_player]
		deck, current_player = Game.deck(current_player)
		game_state = Game.set_player_state(game_state, current_player, moving_player)

		new_card_class, game_state = Game.draw_card_for_player(game_state, moving_player, deck)
		nci = Game.get_new_card_id(game_state)
		curr_turn = Game.get_current_turn(game_state)
		if new_card_class in [
				'SilhanaLedgewalker', 
				'NettleSentinel',
				'QuirionRanger',
				'NestInvader',
				'SkarrganPitSkulk',
				'VaultSkirge',
				'ElephantToken',
				'BurningTreeEmissary',
				'EldraziSpawnToken',
			]:
			new_card_state = Creature.get_tuple(new_card_class, moving_player, nci, curr_turn, False, False, False)
		elif new_card_class in [
				'VaultSkirge',
			]:
			new_card_state = Creature.get_tuple(new_card_class, moving_player, nci, curr_turn, True, False, True)
		else:
			new_card_state = Card.get_tuple(new_card_class, moving_player, nci, curr_turn)

		game_state = Game.add_card_to_hand(game_state, new_card_state)
		game_state = Game.increment_new_card_id(game_state)

		if Game.get_phase(game_state) == "draw":
			if Game.print_moves(game_state) and not Game.is_human_playing(game_state):
				Game.print_board(game_state);
			elif current_player.__class__.__name__ == "Human":
				Game.print_board(game_state);
			if Game.print_moves(game_state):
				print "# TURN {} ################################################".format(Game.get_current_turn(game_state) + 1)
			game_state = Game.clear_temp_mana(game_state, 0)
			game_state = Game.clear_temp_mana(game_state, 1)
		
		if Game.print_moves(game_state) and Game.get_phase(game_state) != 'setup':			
			if Game.is_human_playing(game_state) and current_player.__class__.__name__ != "Human":
				print "> {} drew a card in phase {}." \
					.format(Game.player_display_name(current_player, moving_player), Game.get_phase(game_state))	 		
			else:
				print "> {} drew {} in phase {}." \
					.format(Game.player_display_name(current_player, moving_player),
							Card.display_name(new_card_state), Game.get_phase(game_state))	 		

		if Game.get_phase(game_state) == "draw":
			game_state = Game.set_phase(game_state, "precombat")

		return game_state

	@staticmethod
	def draw_card_for_player(game_state, moving_player, deck):
		mutable_deck = list(deck)
		card = mutable_deck.pop()
		mutable_player = list(game_state[4][moving_player])
		mutable_player[4] = tuple(mutable_deck)
		tuple_player = tuple(mutable_player)

		mutable_player_list = list(game_state[4])
		mutable_player_list[moving_player] = tuple_player
		tuple_player_list = tuple(mutable_player_list)

		mutable_game_state = list(game_state)
		mutable_game_state[4] = tuple_player_list
		game_state = tuple(mutable_game_state)

		return card, game_state

	@staticmethod
	def deck(bot_state):
		mutable = bot_state
		if bot_state[4] == -1:
			with open('src/stompy.json') as json_data:
			    d = json.load(json_data)
			    mutable = list (bot_state)
			    mutable[4] = d['cards']
			    shuffle(mutable[4])
			    mutable[4] = tuple(mutable[4])
		return mutable[4], mutable
		

	@staticmethod
	def announce_attackers(game_state, attackers):
		"""Set attackers, shift priority to the defending player, and update the phase."""
		game_state = Game.clear_temp_mana(game_state, 0)
		game_state = Game.clear_temp_mana(game_state, 1)
		game_state = Game.set_attackers(game_state, attackers)
				
		for creature_state in Game.get_creatures(game_state):
			if Card.id(creature_state) in attackers:
				creature_state = Card.set_tapped(creature_state, True)
				game_state = Game.set_creature_with_id(game_state, creature_state,  Card.id(creature_state))

		if Game.print_moves(game_state):
			pwp = Game.player_with_priority(game_state)
			current_player = Game.get_player_states(game_state)[pwp]
			print "> {} declared attackers {}.".format(Game.player_display_name(current_player, pwp),
				", ".join([Card.display_name(Game.creature_with_id(game_state, cid)) for cid in attackers]))
		game_state = Game.set_priority(game_state, Game.not_current_turn_player(game_state))
		game_state = Game.set_phase(game_state, "declare_blockers")
		return game_state

	@staticmethod
	def assign_blockers(game_state, block_tuple):
		"""Set blockers according to block_tiple that maps an attacker to multiple bloickers."""
		if Game.print_moves(game_state):
			print "blockers before {}".format(Game.get_blockers(game_state))
		game_state = Game.add_block(game_state, block_tuple)
		for blocker in block_tuple[1]:
			game_state = Game.add_blocker(game_state, blocker)

		if Game.print_moves(game_state):
			pwp = Game.player_with_priority(game_state)
			current_player = Game.get_player_states(game_state)[pwp]
			print "> {} blocked {} with {}." \
				.format(Game.player_display_name(current_player, pwp), 
					Card.display_name(Game.creature_with_id(game_state, block_tuple[0])), 
					", ".join([Card.display_name(Game.creature_with_id(game_state, cid)) for cid in block_tuple[1]])
				)
		if Game.print_moves(game_state):
			print "blockers after {}".format(Game.get_blockers(game_state))
		return game_state

	@staticmethod
	def finish_blocking(game_state, player_number):
		"""Shift priority to the defending player and update the phase."""
		if Game.print_moves(game_state):
			pwp = Game.player_with_priority(game_state)
			current_player = Game.get_player_states(game_state)[pwp]
			print "> {} finished blocking." \
				.format(Game.player_display_name(current_player, pwp))
		game_state = Game.set_phase(game_state, 'combat_resolution')
		game_state = Game.set_priority(game_state, Game.current_turn_player(game_state))		
		return game_state

	@staticmethod
	def declare_attack(game_state, player_number):
		"""Shift priority to the defending player and update the phase."""
		if Game.print_moves(game_state):
			pwp = Game.player_with_priority(game_state)
			current_player = Game.get_player_states(game_state)[pwp]
			print "> {} announced attack." \
				.format(Game.player_display_name(current_player, pwp))
		game_state = Game.set_phase(game_state, 'attack_step')
		game_state = Game.set_priority(game_state, Game.not_current_turn_player(game_state))
		return game_state

	@staticmethod
	def resolve_combat(game_state, player_number):
		"""Deal damage, remove any dead creatures, check for winners, and go to postcombat phase.""" 
		game_state = Game.clear_temp_mana(game_state, 0)
		game_state = Game.clear_temp_mana(game_state, 1)
		game_state = Game.set_phase(game_state, 'postcombat')
		total_attack = 0
		current_player = Game.get_player_states(game_state)[player_number]
		opponent = Game.opponent(game_state, current_player)
		opponent_index = Game.get_player_states(game_state).index(opponent)
		dead_creatures = []

		for creature_id in Game.get_attackers(game_state):
			is_blocked = False 
			attacker_state = Game.creature_with_id(game_state, creature_id)
			attacker_strength_to_apportion = Creature.total_damage(attacker_state)

			for block in Game.get_blocks(game_state):
				if block[0] == creature_id:
					# is blocked, continue
					damage_to_attacker = 0
					creature = None
					is_blocked = True
					for blocker_id in block[1]:
						blocker_state = Game.creature_with_id(game_state, blocker_id)
						if blocker_state:  #it might have died
							damage_to_attacker += Creature.total_damage(blocker_state)
							if attacker_strength_to_apportion >= Creature.total_hit_points(blocker_state):
								dead_creatures.append(blocker_id)
							attacker_strength_to_apportion -= Creature.total_hit_points(blocker_state)

					if damage_to_attacker >= Creature.total_hit_points(attacker_state):
						dead_creatures.append(Card.id(attacker_state))

					if attacker_strength_to_apportion > 0 and Creature.has_trample(attacker_state):
						
						game_state = Game.increment_hit_points(
							game_state, 
							opponent_index, 
							-attacker_strength_to_apportion)
						game_state = Creature.did_deal_damage(attacker_state, game_state)
						total_attack += Creature.total_damage(attacker_state)

					continue


			if not is_blocked:
				game_state = Game.increment_hit_points(
					game_state, 
					opponent_index, 
					-Creature.total_damage(attacker_state))
				game_state = Creature.did_deal_damage(attacker_state, game_state)
				total_attack += Creature.total_damage(attacker_state)

		game_state = Game.increment_damage_to_player(game_state, opponent_index, total_attack)

		if Game.print_moves(game_state):
			dead_names = ", ".join([Card.display_name(Game.creature_with_id(game_state, d)) for d in dead_creatures])
			if len(dead_creatures) == 0:
				dead_names = "nothing"
			pwp = Game.player_with_priority(game_state)
			#if len(Game.get_attackers(game_state)) == 0:
			#	print "No attack, savage feint dude!"
			if total_attack > 0:
				print "> {} attacked for {} (killed: {})." \
					.format(Game.player_display_name(current_player, pwp),
							total_attack,
							dead_names)
			else:
				print "> {} attacked, (killed: {})" \
					.format(Game.player_display_name(current_player, pwp), 
							dead_names)

		if len(dead_creatures) > 0:
			game_state = Game.set_creature_died_this_turn(game_state, True)

		game_state = Game.set_attackers(game_state, ())
		game_state = Game.set_blockers(game_state, ())
		game_state = Game.set_blocks(game_state, ())
		for dcid in dead_creatures:
			dc_state = Game.creature_with_id(game_state, dcid)
			game_state = Card.on_graveyard(dc_state, game_state, Game)
			for e in Creature.enchantments(dc_state):
				game_state = Card.on_graveyard(e, game_state, Game)

		new_creatures = []
		for creature_state in Game.get_creatures(game_state):
			if Card.id(creature_state) not in dead_creatures:
				new_creatures.append(creature_state)
		game_state = Game.set_creatures(game_state, new_creatures)
		if Game.print_moves(game_state) and not Game.is_human_playing(game_state):
			Game.print_board(game_state);

		return game_state

	@staticmethod
	def adjust_players_for_end_turn(game_state, player):
		# set temp mana to none
		game_state = Game.clear_temp_mana(game_state, 0)
		game_state = Game.clear_temp_mana(game_state, 1)
		return game_state

	@staticmethod
	def creature_with_id(game_state, creature_id):
		"""Return the creature in creatures with id equal to creature_id."""
		for creature_state in Game.get_creatures(game_state):
			if Card.id(creature_state) == creature_id:
				return creature_state

	@staticmethod
	def pass_priority_as_attacker(game_state, moving_player):
		return Game.set_priority(game_state, Game.not_current_turn_player(game_state))

	@staticmethod
	def pass_priority_as_defender(game_state, moving_player):
		return Game.set_priority(game_state, Game.current_turn_player(game_state))

	@staticmethod
	def pass_the_turn(game_state, moving_player):
		"""Pass to the next player."""
		game_state = Game.increment_current_turn(game_state)

		player = Game.get_player_states(game_state)[Game.current_turn_player(game_state)]
		game_state = Game.set_priority(game_state, Game.current_turn_player(game_state))
		game_state = Game.adjust_players_for_end_turn(game_state, player)

		new_creatures = []
		for creature_state in Game.get_creatures(game_state):
			new_creatures.append(Creature.adjust_for_end_turn(creature_state))
		game_state = Game.set_creatures(game_state, new_creatures)

		new_lands = []
		for land_state in Game.get_lands(game_state):
			new_lands.append(Card.adjust_for_end_turn(land_state))
		game_state = Game.set_lands(game_state, new_lands)

		for idx, card_list in enumerate([Game.get_creatures(game_state), Game.get_lands(game_state)]):
			new_card_list = []
			for card_state in card_list:
				if Card.owner(card_state) == Game.player_with_priority(game_state):
					new_card_state = Card.adjust_for_untap_phase(card_state)
					new_card_list.append(new_card_state)
				else:
					new_card_list.append(card_state)				
			if idx == 0:
				game_state = Game.set_creatures(game_state, new_card_list)
			else:
				game_state = Game.set_lands(game_state, new_card_list)

		game_state = Game.clear_damage_to_players(game_state)
		game_state = Game.set_creature_died_this_turn(game_state, False)
		game_state = Game.set_phase(game_state, "draw")

		return game_state

	@staticmethod
	def all_legal_blocks(game_state):
		"""
		Returns a list of possible_moves that include finishing_blocking, 
		plus all possible ways to assign blockers to the current attackers.
		"""
		pwp = Game.player_with_priority(game_state)
		possible_moves = [('finish_blocking', pwp, 0)]

		blockers = []
		for c_state in Game.get_creatures(game_state):
			if Card.owner(c_state) == pwp:
				if Card.id(c_state) not in Game.get_blockers(game_state):
					blockers.append(Card.id(c_state))
		if len(blockers) == 0:
			return possible_moves
		
		blocker_combos = []
		for i in xrange(1,len(blockers)+1):
			blocker_combos += itertools.combinations(blockers, i)

		possible_blocks = itertools.product(Game.get_attackers(game_state), blocker_combos)
		for block in possible_blocks:
			if Game.block_is_legal(game_state, block):
				possible_moves.append(('assign_blockers', block, 0))

		return possible_moves

	@staticmethod
	def block_is_legal(game_state, block):
		attacker_state = Game.creature_with_id(game_state, block[0])
		blockers = [Game.creature_with_id(game_state, x) for x in block[1]]

		for blocker_state in blockers:
			if not Creature.can_be_blocked_by(attacker_state, blocker_state):
				return False
		return True

	@staticmethod
	def opponent_was_dealt_damage(game_state):
		return game_state[10][Game.not_current_turn_player(game_state)] > 0

	@staticmethod
	def move_display_string(game_state, move):
		"""Move is a tuple. Prints a display for humans."""

		move_type = move[0] 
		mana_to_use = move[2]
		pwp = Game.player_with_priority(game_state)

		if move_type == 'play_next_on_stack':		
			return "Playing Top Move on Stack: {}".format(Game.get_stack(game_state)[-1])
		elif move_type.startswith('card'):
			card_index = move[1]
			card_state = Game.get_hand(game_state, pwp)[card_index]
			if Card.card_type(card_state) == "creature":
				action_word = "Summon"
			elif Card.card_type(card_state) == "land":
				action_word = "Play"
			else:
				action_word = "Cast"

			target_creature_id = move[3]
			target_state = Game.creature_with_id(game_state, target_creature_id)
			pronoun = "your"
			if target_state and Card.owner(target_state) != pwp:
				pronoun = "their"
			target_string =  "{} {}".format(action_word, Card.display_name(card_state))
			if target_state:
				target_string += " on {} {}".format(pronoun, Card.display_name(target_state))
			if mana_to_use:
				return "({}) {}".format(Card.casting_cost_string(card_state, move=move), target_string)
			else:
				return target_string
		elif move[0].startswith('ability'):
			target_creature_id = move[3]
			target_state = Game.creature_with_id(game_state, target_creature_id)
			pronoun = "your"
			if target_state and Card.owner(target_state) != pwp:
				pronoun = "their"

			card_state = move[6]
			card_in_play = Game.creature_with_id(game_state, target_creature_id)

			action_string = None
			if not card_in_play:
				action_string = "{} {}".format(Card.action_word(card_state), Card.display_name(card_state))
			elif card.id == card_in_play.id:
				action_string = "{} {} with itself".format(Card.action_word(card_state), Card.display_name(card_state))
			else:
				action_string = "{} {} {} with {}".format(Card.action_word(card_state), pronoun, Card.display_name(card_in_play), Card.display_name(card_state))

			target_land_id = move[4]
			land_to_return = None
			tapped_string = None
			for land_state in Game.get_lands(game_state):
				if Card.id(land_state) == target_land_id:
					land_to_return = land
					if Card.tapped(land_state):
						tapped_string = "tapped"
					else:
						tapped_string = "untapped"
					break
			land_string = None
			if land_to_return:
				action_string += ", returning {} {}".format(tapped_string, Card.display_name(land))

			return action_string
		elif move_type.startswith('land_ability'):
			card_index = move[1]
			card_state = Game.get_lands(game_state)[card_index]
			return "Tap {}".format(Card.display_name(card_state))
		else:
			if move_type == 'finish_blocking':
				return "Finish Blocking"
			elif move_type == 'declare_attack':
				return "Declare Attack"
			elif move_type == 'resolve_combat':
				return "Resolve Combat"
			elif move_type == 'no_attack':
				return "No Attackers"
			elif move_type == 'pass_the_turn':
				return "Pass the Turn"
			elif move_type == 'pass_priority_as_defender' or move_type == 'pass_priority_as_attacker':
				return "Pass Priority"
			elif move_type == 'announce_attackers':
				attackers = move[1]
				attacker_names = []
				for creature_id in attackers:
					attacker_state = Game.get_creature_with_id(game_state, creature_id)
					attacker_names.append(Card.display_name(attacker_state))
				return "Attack with {}".format(", ".join(attacker_names))
			elif move_type == 'assign_blockers':
				attacker = move[1][0]
				blockers = move[1][1]
				blocker_names = []
				for creature_id in blockers:
					blocker_state = Game.get_creature_with_id(game_state, creature_id)
					blocker_names.append(Card.display_name(blocker_state))
				return "Block {} with {}".format(Card.display_name(Game.get_creature_with_id(game_state, attacker)), ", ".join(blocker_names))


				return "Assign Blockers {}".format(move)


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

