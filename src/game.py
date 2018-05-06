"""Game encapsulates the rules and state of a fantasy card game, and interface with bots."""

import collections
import itertools
from bot import Bot
from card import Card, Creature, Land
from card import Forest, QuirionRanger, NestInvader, BurningTreeEmissary, SkarrganPitSkulk, \
	SilhanaLedgewalker, VaultSkirge, VinesOfVastwood, Rancor, ElephantGuide, HungerOfTheHowlpack, \
	NettleSentinel
from constants import *
import pickle
from random import choice
from statcache import StatCache

class Game():
	"""A fantasy card game instance."""

	def __init__(self):
		"""Set the list of players, and set the current_player to the first player."""

		# the current turn, switches after each player takes their full turn
		self.current_turn = 0

		# the index of the player in self.players who currently has priority
		self.player_with_priority = 0

		# gets incremented everytime a card is played, used as the id for each new card
		self.new_card_id = 0

		# can be setup, draw, precombat, declare_attackers, declare_blockers, 
		# combat_resolution, or postcombat
		self.phase = "setup"

		# a list of Bot subclass players
		self.players = []

		# a list of Creature objects in play
		self.creatures = []

		# a list of Land objects in play
		self.lands = []

		# a list of ids for declared attackers
		self.attackers = []

		# a list of ids for declared blockers
		self.blockers = []

		# a list of dicts keying a single attacking creature id to a list of blocking creature ids
		self.blocks = []

		self.damage_to_players = [0, 0]

		self.stack = []
		self.stack = []

		self.creature_died_this_turn = False

		self.current_spell_move = None

		# a list of previous states the game has been in
		self.states = [self.state_repr()]

		# whether to print each move, typically False during simulation, but true for a real game
		self.print_moves = False 

		self.hide_bot_hand = True

	def print_board(self, show_opponent_hand=True):
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
		
		if self.is_human_playing():
			top_player = 0
			bottom_player = 1
		print "".join(["~" for x in range(0,SCREEN_WIDTH)])
		self.get_players()[top_player].print_board(self, show_hand=(not self.is_human_playing()))
		
		middle_bar_width = SCREEN_WIDTH/3
		spaces = "".join([" " for x in range(0,(SCREEN_WIDTH-middle_bar_width)/2)])
		bars = "".join(["_" for x in range(0,middle_bar_width)])
		print ""
		print "{}{}".format(spaces, bars)
		print ""
		self.get_players()[bottom_player].print_board(self)
		print "".join(["~" for x in range(0,SCREEN_WIDTH)])
		print ""

	def state_repr(self):
		"""A hashable representation of the game state."""
		#return pickle.dumps(self)
		players = [p.state_repr() for p in self.get_players()]
		creatures = self.creatures 
		lands = self.lands 
		return (self.current_turn, 
				self.player_with_priority, 
				self.new_card_id, 
				self.phase, 
				tuple(players),
				tuple(creatures),
				tuple(lands),
				tuple(self.attackers),
				tuple(self.blockers),
				tuple(self.blocks),
				tuple(self.damage_to_players),
				tuple(self.stack),
				self.creature_died_this_turn,
				self.current_spell_move
		)

	def game_for_state(self, state):
		"""Return a Game for a state tuple."""
		#game = pickle.loads(state)
		#game.print_moves = False
		#return game
		clone_game = Game()
		clone_game.current_turn = state[0]
		clone_game.player_with_priority = state[1]
		clone_game.new_card_id = state[2]
		clone_game.phase = state[3]

		for player_tuple in state[4]:
			player = Bot(hit_points=player_tuple[0], temp_mana=player_tuple[2])
			for card_tuple in player_tuple[1]:
				player.hand.append(card_tuple)
			clone_game.players.append(player)

		for creature_tuple in state[5]:
				clone_game.creatures.append(creature_tuple)
	
		for land_tuple in state[6]:
			clone_game.lands.append(land_tuple)

		clone_game.attackers = list(state[7])
		clone_game.blockers = list(state[8])
		clone_game.blocks = list(state[9])
		clone_game.damage_to_players = list(state[10])
		clone_game.stack = list(state[11])
		clone_game.creature_died_this_turn = state[12]
		clone_game.current_spell_move = state[13]

		return clone_game

	def get_lands(self):
		return self.lands
		

	def get_creatures(self):
		return self.creatures
		
	def get_players(self):
		return self.players
		
	"""
		Bot protocol methods after this. These are: 

			play_out, winner, acting_player, next_state, legal_plays.
	"""

	def play_out(self):
		"""Play out a game between two bots."""
		statcache = StatCache()
		while not self.game_is_over():
			player = self.get_players()[self.player_with_priority]
			move = player.play_move(self, statcache)

		winner, winning_hp, losing_hp = self.winning_player()
		if self.print_moves:
			if self.game_is_drawn():
				print "Game Over - Draw"
			else:
				print "Game Over - {} wins! Final hit points are {} to {}." \
					.format(winner.display_name(self.get_players().index(winner)),
							winning_hp, 
							losing_hp)
		return winner

	def winner(self, state_history):
		"""
			Return -1 if the state_history is drawn, 0 if the game is ongoing, 
		
			else the player_number of the winner.
		"""
		current_state = state_history[-1]
		clone_game = self.game_for_state(current_state)

		if clone_game.game_is_drawn():
			return -2

		if len(clone_game.dead_players()) == 0:
			return -1

		winning_player, _, _ = clone_game.winning_player()

		return clone_game.players.index(winning_player)

	def winning_player(self):
		"""
			Return the winning player, hp of winning player, and hp of losing player. 

			Returns None, None, None on draws.
		"""
		if self.game_is_drawn():
			return None, None, None
		losing_hp = None
		winning_hp = None
		winner = None
		for p in self.get_players():
			if p.hit_points <= 0:
				losing_hp = p.hit_points
			else:
				winning_hp = p.hit_points
				winner = p

		return winner, winning_hp, losing_hp

	def game_is_drawn(self):
		"""Return True if all players has <= 0 hit points."""
		return len(self.dead_players()) == len(self.get_players())

	def game_is_over(self):
		"""Return True if either player has <= 0 hit points."""
		return len(self.dead_players()) > 0

	def dead_players(self):
		"""Return a list of players that have hit points <= 0."""
		dead_players = []
		for p in self.get_players():
			if p.hit_points <= 0:
				dead_players.append(p)
		
		return dead_players

	def acting_player(self, state):
		"""Return the player_number of the player due to make move in state."""
		return state[1]

	def next_state(self, state, move, game=None):
		"""Return a new state after applying the move to state."""
		if game:
			clone_game = game
		else:
			clone_game = self.game_for_state(state)
		mana_to_use = move[2]
		if move[0] == 'play_next_on_stack':		
			clone_game.play_next_on_stack()
		elif move[0].startswith('card-cast'):
			# after this choose how to cast the chosen spell
			clone_game.play_move(move)
		elif move[0].startswith('card') or move[0].startswith('ability'):
			clone_game.tap_lands_for_mana(mana_to_use)
			clone_game.play_move(move)
		elif move[0].startswith('land_ability'):
			clone_game.tap_lands_for_mana(mana_to_use)
			clone_game.play_land_ability_move(move)
		else:
			# too slow: eval("self.{}".format(move[0]))(move[1])
			if move[0] == 'initial_draw':
				clone_game.initial_draw(move[1])
			elif move[0] == 'draw_card':
				clone_game.draw_card(move[1])
			elif move[0] == 'finish_blocking':
				clone_game.finish_blocking(move[1])
			elif move[0] == 'declare_attack':
				clone_game.declare_attack(move[1])
			elif move[0] == 'resolve_combat':
				clone_game.resolve_combat(move[1])
			elif move[0] == 'no_attack':
				clone_game.resolve_combat(move[1])
			elif move[0] == 'pass_the_turn':
				clone_game.pass_the_turn(move[1])
			elif move[0] == 'pass_priority_as_defender':
				clone_game.pass_priority_as_defender(move[1])
			elif move[0] == 'pass_priority_as_attacker':
				clone_game.pass_priority_as_attacker(move[1])
			elif move[0] == 'announce_attackers':
				clone_game.announce_attackers(list(move[1]))
			elif move[0] == 'assign_blockers':
				clone_game.assign_blockers(move[1])

		state_rep = clone_game.state_repr()
		clone_game.states.append(state_rep)
		return state_rep

	def tap_lands_for_mana(self, mana_to_tap):
		"""Tap land_to_tap lands to pay for a spell or effect."""
		colored = []
		life = []
		colorless = 0

		caster = self.get_players()[self.player_with_priority]
		for mana in mana_to_tap:
			if isinstance(mana, int):
				colorless = mana
			elif mana.startswith("L"):
				caster.hit_points -= int(mana[1:])
				if self.print_moves:
					print "> {} lost {} life from casting a Phyrexian, now at {}." \
						.format(
							caster.display_name(self.player_with_priority), 
							int(mana[1:]),
							caster.hit_points
						)
			else:
				colored.append(mana)

		while len(colored) > 0:
			mana = colored[0]
			temp_index_to_remove = 0
			found_temp = False
			for temp_mana in caster.temp_mana:
				if type(temp_mana) == str and temp_mana in mana:
					colored.pop(0)
					found_temp = True
					break
				temp_index_to_remove += 1
			if found_temp:
				del caster.temp_mana[temp_index_to_remove]
				continue

			used_land = False
			for land_state in self.get_lands():
				if Card.owner(land_state) == self.player_with_priority and not Card.tapped(land_state):
					used_land = False
					for c in mana:
						if c in Land.mana_provided(land_state):
							colored.pop(0)
							used_land = True
							break
					if used_land:
						break
			if used_land:
				new_lands = []
				for lstate in self.get_lands():
					if lstate == land_state:
						land_state = Card.set_tapped(land_state, True)
						new_lands.append(land_state)
					else:
						new_lands.append(lstate)
				self.lands = new_lands

		while colorless > 0:
			temp_index_to_remove = 0
			found_temp = False
			for temp_mana in caster.temp_mana:
				if type(temp_mana) == int:
					colorless -= temp_mana
					found_temp = True
					break
				temp_index_to_remove += 1
			if found_temp:
				del caster.temp_mana[temp_index_to_remove]
				continue

			temp_index_to_remove = 0
			for temp_mana in caster.temp_mana:
				if type(temp_mana) == str:
					colorless -= 1
					found_temp = True
					break
				temp_index_to_remove += 1
			if found_temp:
				del caster.temp_mana[temp_index_to_remove]
				continue

			new_lands = []
			for land_state in self.get_lands():
				if Card.owner(land_state) == self.player_with_priority and not Card.tapped(land_state):
					tapped_state = Card.set_tapped(land_state, True)
					colorless -= 1
					new_lands.append(tapped_state)
				else:
					new_lands.append(land_state)
			self.lands = new_lands

	def available_mana(self):
		"""
			Returns a map of color to amount of mana from player_with_priority's untapped lands
			and mana pool.
		"""
		mana = collections.Counter()
		for land_state in self.get_lands():
			if Card.owner(land_state) == self.player_with_priority and not Card.tapped(land_state):
				mana.update(Land.mana_provided(land_state))

		mana_dict = dict(mana)

		for mana_symbol in self.get_players()[self.player_with_priority].temp_mana:
			if mana_symbol in mana:
				mana_dict[mana_symbol] += 1
			else:
				mana_dict[mana_symbol] = 1				
		return mana_dict

	def play_move(self, move):
		"""Play a card based on the move tuple."""
		if move[0].startswith('card-cast'):
			self.current_spell_move = move
			return
		elif move[0].startswith('card'):
			self.current_spell_move = None
			# lands don't go on stack
			card_index = move[1]
			state = self.get_players()[self.player_with_priority].get_hand()[card_index]
			if state[5] == 'land':
				self.play_card_move_from_stack(move)
				return

		self.stack.append(move)
		if self.player_with_priority == self.current_turn_player():
			self.player_with_priority = self.not_current_turn_player()
		else:
			self.player_with_priority = self.current_turn_player()

	def play_next_on_stack(self):
		move = self.stack.pop()
		if move[0].startswith('card'):
			self.play_card_move_from_stack(move)
		elif move[0].startswith('ability'):
			self.play_ability_move_from_stack(move)

	def play_card_move_from_stack(self, move):
		player_number = self.player_with_priority
		target_creature = move[3]
		mana_to_use = move[2]
		card_index = move[1]
		card_state = self.get_players()[player_number].get_hand()[card_index]
		Card.play(card_state, self, mana_to_use, target_creature)
		new_creatures = []
		for creature_state in self.get_creatures():
			new_creatures.append(Card.react_to_spell(creature_state, card_state))
		self.creatures = new_creatures
		new_lands = []
		for land_state in self.get_lands():
			new_lands.append(Card.react_to_spell(land_state, card_state))
		self.lands = new_lands

	def play_ability_move_from_stack(self, move):
		"""Play an activated based on the move tuple."""
		player_number = self.player_with_priority
		target_creature_id = move[3]
		target_land_id = move[4]
		mana_to_use = move[2]
		card_index = move[1]
		card_state = self.creature_with_id(move[6][2])
		card_in_play = self.creature_with_id(target_creature_id)
		Card.activate_ability(card_state, self, mana_to_use, target_creature_id, target_land_id, card_in_play)
		#TODO should this be diff function than in play_card_move?
		new_creatures = []
		for creature_state in self.get_creatures():
			new_creatures.append(Card.react_to_spell(creature_state, card_state))
		self.creatures = new_creatures
		new_lands = []
		for land_state in self.get_lands():
			new_lands.append(Card.react_to_spell(land_state, card_state))
		self.lands = new_lands

	def play_land_ability_move(self, move):
		"""Play an activated based on the move tuple."""
		player_number = self.player_with_priority
		target_creature_id = move[3]
		target_land_id = move[4]
		mana_to_use = move[2]
		card_index = move[1]
		card_state = self.get_lands()[card_index]
		Land.activate_ability(card_state, self)
		for creature_state in self.get_creatures():
			#TODO react to land tapping
			pass
		for land_state in self.get_lands():
			#TODO react to land tapping
			pass

	def opponent(self, player):
		"""Return the player that isn't the given player."""
		for p in self.get_players():
			if p != player:
				return p

	def legal_plays(self, state_history, cached_game=None):
		"""
			Return a list of all legal moves given the state_history. 
		
			We only use the most recent state in state_history for now.
		"""
		
		if cached_game:
			game = cached_game
		else:
			game_state = state_history[-1]
			game = self.game_for_state(game_state)
		if game.current_spell_move:
			return game.card_actions(game, move=game.current_spell_move)
		elif len(game.stack) > 0 and game.stack[-1][5] == game.player_with_priority:		
			return [('play_next_on_stack', game.player_with_priority, 0),]		
		elif len(game.stack) > 0 and game.stack[-1][5] != game.player_with_priority and game.player_with_priority == game.current_turn_player():		
			return[('pass_priority_as_attacker', game.player_with_priority, 0)]
		elif game.phase == "setup":
			return [('initial_draw', game.player_with_priority, 0),]	
		elif game.phase == "draw":
			return [('draw_card', game.player_with_priority, 0),]	
		elif game.phase == "attack_step" and game.player_with_priority == game.current_turn_player():
			possible_moves = set()
			possible_moves.add(('no_attack', game.player_with_priority, 0))
			return list(game.add_attack_actions(game, possible_moves))
		elif game.phase == "declare_blockers":
			return game.all_legal_blocks()
		elif game.player_with_priority != game.current_turn_player():
			possible_moves = game.add_instant_creature_abilities(game, set())
			possible_moves = game.add_land_abilities(game, possible_moves)
			possible_moves.add(('pass_priority_as_defender', game.player_with_priority, 0))
			return list(possible_moves)
		possible_moves = game.add_cast_actions(game, set())
		possible_moves = game.add_instant_creature_abilities(game, possible_moves)
		possible_moves = game.add_land_abilities(game, possible_moves)
		if game.phase == "precombat" and len(game.add_attack_actions(game, set())) > 0:
			possible_moves.add(('declare_attack', game.player_with_priority, 0))			
		elif game.phase == "combat_resolution":
			possible_moves.add(('resolve_combat', game.player_with_priority, 0),)
			return list(possible_moves)

		
		possible_moves.add(('pass_the_turn', game.player_with_priority, 0))
			
		return list(possible_moves)

	def played_land(self):
		"""Returns True if the player_with_priority has played a land this turn."""
		for land_state in self.get_lands():
			if Card.owner(land_state) == self.player_with_priority and Card.turn_played(land_state) == self.current_turn:
				return True
		return False

	def add_cast_actions(self, game, possible_moves):
		"""Return a list of possible cast actions based on the player_with_priority's hand."""
		card_types_added = []
		hand = game.get_players()[game.player_with_priority].get_hand()
		for card_state in hand:
			if Card.name(card_state) not in card_types_added:
				if game.phase in ['attack_step', 'combat_resolution']:
					if Card.card_type(card_state) != 'instant':
						continue
				cast_moves = Card.cast_moves(card_state, game, hand.index(card_state))
				if len(cast_moves) > 0:
					actions = game.card_actions(game, move=cast_moves[0])
					if len(actions) == 1:
						possible_moves.add(actions[0])				
					else:
						[possible_moves.add(m) for m in Card.cast_moves(card_state, game, hand.index(card_state))]
					card_types_added.append(Card.name(card_state))
		return possible_moves


	def card_actions(self, game, move=None):
		"""Return a list of possible actions based on the player_with_priority's hand."""
		possible_moves = set()
		card_index = move[1]
		card_state = game.get_players()[game.player_with_priority].get_hand()[card_index]
		[possible_moves.add(m) for m in Card.possible_moves(card_state, game)]
		return list(possible_moves)

	def add_instant_creature_abilities(self, game, possible_moves):
		"""Return a list of possible actions based on the player_with_priority's hand."""
		for creature_state in game.get_creatures():
			if Card.owner(creature_state) == game.player_with_priority:
				if game.phase in ['attack_step', 'combat_resolution']:
					if Creature.activated_ability_type(creature_state) != 'instant':
						continue
				[possible_moves.add(m) for m in Creature.possible_ability_moves(creature_state, game)]
		return possible_moves

	def add_land_abilities(self, game, possible_moves):
		"""Return a list of possible actions based on the player_with_priority's lands."""
		land_types_added = set()
		for land_state in game.get_lands():
			if Card.name(land_state) not in land_types_added:
				if Card.owner(land_state) == game.player_with_priority:
					[possible_moves.add(m) for m in Land.possible_ability_moves(land_state, game)]
					land_types_added.add(Card.name(land_state))
		return possible_moves

	def add_attack_actions(self, game, possible_moves):
		"""Return a list of possible actions based on the player_with_priority's creatures."""
		available_attackers = []
		for creature_state in game.get_creatures():
			if Card.owner(creature_state) == game.player_with_priority and Creature.can_attack(creature_state, game):
				available_attackers.append(Card.id(creature_state))
		
		if len(available_attackers) > 0 and len(game.attackers) == 0:
			for L in range(0, len(available_attackers)+1):
				for subset in itertools.combinations(available_attackers, L):
					if len(subset) > 0:
						possible_moves.add(('announce_attackers', subset, 0))

		return possible_moves

	def initial_draw(self, moving_player):
		"""Add some cards to each player's hand."""
	 	for i in range(0,7):
	 		self.draw_card(moving_player);
		if self.player_with_priority == self.current_turn_player():
			self.player_with_priority = self.not_current_turn_player()
		else:	
			self.player_with_priority = self.current_turn_player()
			self.phase = 'draw'

	def is_human_playing(self):
		for p in self.get_players():
			if p.__class__.__name__ == "Human":
				return True
		return False

	def current_turn_player(self):
		"""The index in self.players for the player whose turn it is. """
		return self.current_turn % 2

	def not_current_turn_player(self):
		"""The index in self.players for the player whose turn it isn't. """
		return (self.current_turn + 1) % 2

	def draw_card(self, moving_player, card=None):
		"""Add a card to moving_player's hand."""
		new_card_class = None
		current_player = self.get_players()[moving_player]
		if card:
			new_card_class = card
		else:
			new_card_class = eval(current_player.deck().pop())
		
		new_card = new_card_class(
			moving_player, 
			self.new_card_id
		)
		new_card_state = new_card.state_repr()
		current_player.get_hand().append(new_card_state)
		self.new_card_id += 1

		if self.phase == "draw":
			if self.print_moves and not self.is_human_playing():
				self.print_board();
			elif current_player.__class__.__name__ == "Human":
				self.print_board();
			if self.print_moves:
				print "# TURN {} ################################################".format(self.current_turn + 1)
			for p in self.get_players():
				p.temp_mana = []
			self.phase = "precombat"
		
		if self.print_moves and self.phase != 'setup':			
			if self.is_human_playing() and current_player.__class__.__name__ != "Human" and self.hide_bot_hand:
				print "> {} drew a card." \
					.format(current_player.display_name(moving_player))	 		
			else:
				print "> {} drew {}." \
					.format(current_player.display_name(moving_player),
							Card.display_name(new_card_state))	 		

	def announce_attackers(self, attackers):
		"""Set attackers, shift priority to the defending player, and update the phase."""
		for p in self.get_players():
			p.temp_mana = []
		self.attackers = attackers
				
		new_creatures = []
		for creature_state in self.get_creatures():
			if Card.id(creature_state) in self.attackers:
				tapped_state = Card.set_tapped(creature_state, True)
				new_creatures.append(tapped_state)
			else:
				new_creatures.append(creature_state)
		self.creatures = new_creatures

		if self.print_moves:
			current_player = self.get_players()[self.player_with_priority]
			print "> {} declared attackers {}.".format(current_player.display_name(self.player_with_priority),
				", ".join([Card.display_name(self.creature_with_id(cid)) for cid in self.attackers]))
		self.player_with_priority = self.not_current_turn_player()
		self.phase = "declare_blockers"

	def assign_blockers(self, block_tuple):
		"""Set blockers according to block_tiple that maps an attacker to multiple bloickers."""
		self.blocks.append(block_tuple)
		for blocker in block_tuple[1]:
			self.blockers.append(blocker)

		if self.print_moves:
			current_player = self.get_players()[self.player_with_priority]
			print "> {} blocked {} with {}." \
				.format(current_player.display_name(self.player_with_priority), 
					Card.display_name(self.creature_with_id(block_tuple[0])), 
					", ".join([Card.display_name(self.creature_with_id(cid)) for cid in block_tuple[1]])
				)

	def finish_blocking(self, player_number):
		"""Shift priority to the defending player and update the phase."""
		if self.print_moves:
			current_player = self.get_players()[self.player_with_priority]
			print "> {} finished blocking." \
				.format(current_player.display_name(self.player_with_priority))

		self.phase = 'combat_resolution'
		self.player_with_priority = self.current_turn_player()

	def declare_attack(self, player_number):
		"""Shift priority to the defending player and update the phase."""
		if self.print_moves:
			current_player = self.get_players()[self.player_with_priority]
			print "> {} announced attack." \
				.format(current_player.display_name(self.player_with_priority))

		self.player_with_priority = self.not_current_turn_player()

		self.phase = 'attack_step'

	def resolve_combat(self, player_number):
		"""Deal damage, remove any dead creatures, check for winners, and go to postcombat phase.""" 
		for p in self.get_players():
			p.temp_mana = []
		self.phase = 'postcombat'
		total_attack = 0
		current_player = self.get_players()[player_number]
		opponent = self.opponent(current_player)
		dead_creatures = []

		for creature_id in self.attackers:
			is_blocked = False 
			attacker_state = self.creature_with_id(creature_id)
			attacker_strength_to_apportion = Creature.total_damage(attacker_state)

			for block in self.blocks:
				if block[0] == creature_id:
					# is blocked, continue
					damage_to_attacker = 0
					creature = None
					is_blocked = True
					for blocker_id in block[1]:
						blocker_state = self.creature_with_id(blocker_id)
						if blocker_state:  #it might have died
							damage_to_attacker += Creature.total_damage(blocker_state)
							if attacker_strength_to_apportion >= Creature.total_hit_points(blocker_state):
								dead_creatures.append(blocker_id)
							attacker_strength_to_apportion -= Creature.total_hit_points(blocker_state)

					if damage_to_attacker >= Creature.total_hit_points(attacker_state):
						dead_creatures.append(Card.id(attacker_state))

					if attacker_strength_to_apportion > 0 and Creature.has_trample(attacker_state):
						opponent.hit_points -= attacker_strength_to_apportion
						Creature.did_deal_damage(attacker_state, self)
						total_attack += Creature.total_damage(attacker_state)

					continue


			if not is_blocked:
				opponent.hit_points -= Creature.total_damage(attacker_state)
				Creature.did_deal_damage(attacker_state, self)
				total_attack += Creature.total_damage(attacker_state)

		self.damage_to_players[self.players.index(opponent)] += total_attack
		if self.print_moves:
			dead_names = ", ".join([Card.display_name(self.creature_with_id(d)) for d in dead_creatures])
			if len(dead_creatures) == 0:
				dead_names = "nothing"
			if len(self.attackers) == 0:
				print "No attack, savage feint dude!"
			elif total_attack > 0:
				print "> {} attacked for {} (killed: {})." \
					.format(current_player.display_name(self.player_with_priority),
							total_attack,
							dead_names)
			else:
				print "> {} attacked, (killed: {})" \
					.format(current_player.display_name(self.player_with_priority), 
							dead_names)

		if len(dead_creatures) > 0:
			self.creature_died_this_turn = True

		self.attackers = []
		self.blockers = []
		self.blocks = []

		for dcid in dead_creatures:
			dc_state = self.creature_with_id(dcid)
			Card.on_graveyard(dc_state, self)
			for e in Creature.enchantments(dc_state):
				Card.on_graveyard(e, self)

		new_creatures = []		
		for creature_state in self.get_creatures():
			if Card.id(creature_state) not in dead_creatures:
				new_creatures.append(creature_state)
		self.creatures = new_creatures
		if self.print_moves and not self.is_human_playing():
			self.print_board();


	def creature_with_id(self, creature_id):
		"""Return the creature in self.creatures with id equal to creature_id."""
		for creature_state in self.get_creatures():
			if Card.id(creature_state) == creature_id:
				return creature_state

	def pass_priority_as_attacker(self, moving_player):
		self.player_with_priority = self.not_current_turn_player()

	def pass_priority_as_defender(self, moving_player):
		self.player_with_priority = self.current_turn_player()

	def pass_the_turn(self, moving_player):
		"""Pass to the next player."""
		self.current_turn += 1
		player = self.get_players()[self.current_turn_player()]

		self.player_with_priority = self.current_turn_player()

		for player in self.get_players():
			player.adjust_for_end_turn()

		new_creatures = []
		for creature_state in self.get_creatures():
			new_creatures.append(Creature.adjust_for_end_turn(creature_state))
		self.creatures = new_creatures

		new_lands = []
		for land_state in self.get_lands():
			new_lands.append(Card.adjust_for_end_turn(land_state))
		self.lands = new_lands

		for idx, card_list in enumerate([self.get_creatures(), self.get_lands()]):
			new_card_list = []
			for card_state in card_list:
				if Card.owner(card_state) == self.player_with_priority:
					new_card_state = Card.adjust_for_untap_phase(card_state)
					new_card_list.append(new_card_state)
				else:
					new_card_list.append(card_state)				
			if idx == 0:
				self.creatures = new_card_list 	
			else:
				self.lands = new_card_list 					

		self.damage_to_players = [0, 0]
		self.creature_died_this_turn = False
		self.phase = "draw"

	def all_legal_blocks(self):
		"""
		Returns a list of possible_moves that include finishing_blocking, 
		plus all possible ways to assign blockers to the current attackers.
		"""
		possible_moves = [('finish_blocking', self.player_with_priority, 0)]

		blockers = []
		for c_state in self.get_creatures():
			if Card.owner(c_state)== self.player_with_priority:
				if Card.id(c_state) not in self.blockers:
					blockers.append(Card.id(c_state))
		if len(blockers) == 0:
			return possible_moves
		
		blocker_combos = []
		for i in xrange(1,len(blockers)+1):
			blocker_combos += itertools.combinations(blockers, i)

		possible_blocks = itertools.product(self.attackers, blocker_combos)
		for block in possible_blocks:
			if self.block_is_legal(block):
				possible_moves.append(('assign_blockers', block, 0))

		return possible_moves

	def block_is_legal(self, block):
		attacker_state = self.creature_with_id(block[0])
		blockers = [self.creature_with_id(x) for x in block[1]]

		for blocker_state in blockers:
			if not Creature.can_be_blocked_by(attacker_state, blocker_state):
				return False
		return True

	def opponent_was_dealt_damage(self):
		return self.damage_to_players[self.not_current_turn_player()] > 0


	def move_display_string(self, move):
		"""Move is a tuple. Prints a display for humans."""

		move_type = move[0] 
		mana_to_use = move[2]

		if move_type == 'play_next_on_stack':		
			return "Playing Top Move on Stack: {}".format(self.stack[-1])
		elif move_type.startswith('card'):
			card_index = move[1]
			card_state = self.get_players()[self.player_with_priority].get_hand()[card_index]
			if Card.card_type(card_state) == "creature":
				action_word = "Summon"
			elif Card.card_type(card_state) == "land":
				action_word = "Play"
			else:
				action_word = "Cast"

			target_creature_id = move[3]
			target_state = self.creature_with_id(target_creature_id)
			pronoun = "your"
			if target_state and Card.owner(target_state) != self.player_with_priority:
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
			target_state = self.creature_with_id(target_creature_id)
			pronoun = "your"
			if target_state and Card.owner(target_state) != self.player_with_priority:
				pronoun = "their"

			card_state = move[6]
			card_in_play = self.creature_with_id(target_creature_id)

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
			for land_state in self.get_lands():
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
			card_state = self.get_lands()[card_index]
			return "Tap {}".format(Card.display_name(card_state))
		else:
			# too slow: eval("self.{}".format(move[0]))(move[1])
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
					attacker_state = self.creature_with_id(creature_id)
					attacker_names.append(Card.display_name(attacker_state))
				return "Attack with {}".format(", ".join(attacker_names))
			elif move_type == 'assign_blockers':
				attacker = move[1][0]
				blockers = move[1][1]
				blocker_names = []
				for creature_id in blockers:
					blocker_state = self.creature_with_id(creature_id)
					blocker_names.append(Card.display_name(blocker_state))
				return "Block {} with {}".format(Card.display_name(self.creature_with_id(attacker)), ", ".join(blocker_names))


				return "Assign Blockers {}".format(move)
