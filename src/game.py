"""Game encapsulates the rules and state of a game."""

import itertools
from bot import Bot
from card import AnyManaLand, Bear, Creature, Fireball
from rando import RandomBot
from random import choice


class Game():
	"""A fantasy card game instance."""

	def __init__(self, players):
		"""Set the list of players, and set the current_player to the first player."""

		# a list of two Bot subclass players
		self.players = players

		# whether to print each move, typically False during simulation, but true for a real game
		self.print_moves = False 

		# the current turn, switches after each player takes their full turn
		self.current_turn = 0

		self.creatures = []

		self.ready_creatures = []

		self.attackers = []

		self.blockers = []

		self.blocks = []

		self.player_with_priority = 0

		self.played_land = False

		self.attacked = False

		# gets incremented everytime a card is played, used as the id for each new card
		self.new_card_id = 0

		# can be setup, draw, precombat, attack, or postcombat
		self.phase = "setup"

		for p in players:
			p.board = self
			p.states = [self.state_repr()]

	def state_repr(self):
		"""A hashable representation of the game state."""
		return (self.current_turn, 
				self.played_land, 
				self.player_with_priority, 
				self.attacked, 
				self.new_card_id, 
				self.phase, 
				(
					(self.players[0].hit_points, self.players[0].mana, self.players[0].current_mana, self.tuple_for_hand(self.players[0].hand)), 
					(self.players[1].hit_points, self.players[1].mana, self.players[1].current_mana, self.tuple_for_hand(self.players[1].hand)),
				), 
				tuple([c.state_repr() for c in self.creatures]),
				tuple(self.ready_creatures),
				tuple(self.attackers),
				tuple(self.blockers),
				tuple(self.blocks),
		)

	def game_for_state(self, state):
		players = [
			RandomBot(starting_hit_points=state[6][0][0], starting_mana=state[6][0][1], current_mana=state[6][0][2], hand=self.cards_for_hand_state_repr(state[6][0][3])), 
			RandomBot(starting_hit_points=state[6][1][0], starting_mana=state[6][1][1], current_mana=state[6][1][2], hand=self.cards_for_hand_state_repr(state[6][1][3])), 
		]
		clone_game = Game(players)
		clone_game.current_turn = state[0]
		clone_game.played_land = state[1]
		clone_game.player_with_priority = state[2]
		clone_game.attacked = state[3]
		clone_game.new_card_id = state[4]
		clone_game.phase = state[5]

		for creature_tuple in state[7]:
			c = Creature(creature_tuple[1], strength=creature_tuple[2], hit_points=creature_tuple[3], guid=creature_tuple[0])
			clone_game.creatures.append(c)

		clone_game.ready_creatures = list(state[8])
		clone_game.attackers = list(state[9])
		clone_game.blockers = list(state[10])
		clone_game.blocks = list(state[11])

		return clone_game

	def print_state(self, state):
		"""A human readable way to print the game state."""
		clone_game = self.game_for_state(state)
		print "TURN: {}, Current Player: {}, Priority: {}, played_land: {}".format(
			clone_game.current_turn, clone_game.current_turn_player(), clone_game.player_with_priority,
			clone_game.played_land)
		print "PLAYER 1: {} hp {}/{} mana, PLAYER 2: {} hp {}/{} mana".format(clone_game.players[0].hit_points, clone_game.players[0].current_mana, clone_game.players[0].mana,
			clone_game.players[1].hit_points, clone_game.players[1].current_mana, clone_game.players[1].mana)
		print "creatures: {}, ready_creatures: {}, attackers: {}, blockers: {}".format(tuple([c.state_repr() for c in clone_game.creatures]), tuple([c for c in clone_game.ready_creatures]), tuple([c for c in clone_game.attackers]),
			tuple([c for c in clone_game.blockers]))

	def tuple_for_hand(self, hand):
		cards = []
		for card in hand:
			cards.append(card.state_repr())
		return tuple(cards)

	def cards_for_hand_state_repr(self, hand_tuple):
		cards = []
		for card_state_repr in hand_tuple:
			cards.append(self.card_for_state_repr(card_state_repr))
		return cards

	def card_for_state_repr(self, card_tuple):
		return eval("{}".format(card_tuple[0]))(card_tuple[2], guid=card_tuple[1])

	def current_turn_player(self):
		return self.current_turn % 2

	def not_current_turn_player(self):
		return (self.current_turn + 1) % 2


	"""Card protocol methods after this. These are: do_move."""

	def do_move(self, move):
		"""Do the move and increment the turn."""
		player = self.players[self.player_with_priority]
		if move[0].startswith('card'):
			player_number = self.player_with_priority
			target_creature = move[3]
			mana_to_use = move[2]
			card_index = move[1]
			method_name = move[0]
			card = self.players[player_number].hand[card_index]
			player.current_mana -= mana_to_use
			card.play(self, mana_to_use, target_creature)
		else:
			player.current_mana -= move[2]
			eval("self.{}".format(move[0]))(move[1])
		state_rep = self.state_repr()
		player.states.append(state_rep)
		self.opponent(player).states.append(state_rep)

	def opponent(self, player):
		"""Return the player that isn't the given player."""
		for p in self.players:
			if p != player:
				return p

	"""MCST protocol methods after this. These are: winner, acting_player, next_state, and legal_plays."""

	def winner(self, state_history):
		"""Returns -1 if the state_history is drawn, 0 if the game is ongoing, else the player_number of the winner."""
		current_state = state_history[-1]
		clone_game = self.game_for_state(current_state)

		if clone_game.game_is_drawn():
			return -2

		if len(clone_game.dead_players()) == 0:
			return -1

		winning_player, _, _ = clone_game.winning_player()

		return clone_game.players.index(winning_player)

	def winning_player(self):
		"""Returns the winning player, hp of winning player, and hp of losing player. Returns None, None, None on draws."""
		if self.game_is_drawn():
			return None, None, None
		losing_hp = None
		winning_hp = None
		winner = None
		for p in self.players:
			if p.hit_points <= 0:
				losing_hp = p.hit_points
			else:
				winning_hp = p.hit_points
				winner = p

		return winner, winning_hp, losing_hp

	def game_is_drawn(self):
		"""Return True if all players has <= 0 hit points."""
		return len(self.dead_players()) == len(self.players)

	def game_is_over(self):
		"""Return True if either player has <= 0 hit points."""
		return len(self.dead_players()) > 0

	def dead_players(self):
		"""Return a list of players that have hit points <= 0."""
		dead_players = []
		for p in self.players:
			if p.hit_points <= 0:
				dead_players.append(p)
		
		return dead_players

	def acting_player(self, state):
		"""The player_number of the player due to make move in state."""
		return state[2]

	def next_state(self, state, move):
		"""Returns a new state after applying the move to state."""
		clone_game = self.game_for_state(state)
		if move[0].startswith('card'):
			player_number = clone_game.player_with_priority
			target_creature = move[3]
			mana_to_use = move[2]
			card_index = move[1]
			method_name = move[0]
			card = clone_game.players[player_number].hand[card_index]
			card.play(clone_game, mana_to_use, target_creature)
		else:
			player = clone_game.players[clone_game.player_with_priority]
			player.current_mana -= move[2]
			eval("clone_game.{}".format(move[0]))(move[1])
		return clone_game.state_repr()

	def legal_plays(self, state_history, available_mana):
		"""Returns a list of all legal moves given the state_history. We only use the most recent state in state_history for now."""
		game_state = state_history[-1]
		game = self.game_for_state(game_state)

		if game.phase == "setup":
			return [('initial_draw', game.player_with_priority, 0),]			
		elif game.phase == "draw":
			return [('draw_card', game.player_with_priority, 0),]			
		elif game.phase == "combat_resolution":
			return [('resolve_combat', game.player_with_priority, 0),]
		elif game.player_with_priority != game.current_turn_player():
			return game.all_legal_blocks()

		possible_moves = [('pass_the_turn', game.player_with_priority, 0)]
		possible_moves = game.add_card_actions(game, possible_moves)
		possible_moves = game.add_attack_actions(game, possible_moves)
		return possible_moves

	def add_card_actions(self, game, possible_moves):
		card_types_added = []
		for card in game.players[game.player_with_priority].hand:
			if card.__class__ not in card_types_added:
				possible_moves += card.possible_moves(game)
				card_types_added.append(card.__class__)
		return possible_moves

	def add_attack_actions(self, game, possible_moves):
		available_attackers = []
		for guid in game.ready_creatures:
			creature = game.creature_with_guid(guid)
			if creature.owner == game.player_with_priority:
				available_attackers.append(guid)
		
		if len(available_attackers) > 0 and len(game.attackers) == 0 and not game.attacked:
			for L in range(0, len(available_attackers)+1):
				for subset in itertools.combinations(available_attackers, L):
					if len(subset) > 0:
						possible_moves.append(('announce_attackers', subset, 0))

		return possible_moves

	def initial_draw(self, moving_player):
		# print self.state_repr()
	 	for i in range(0,3):
	 		self.draw_card(moving_player);
		if self.print_moves:
			current_player = self.players[moving_player]
			print "> {} {} DREW HER HAND ({} cards).".format(current_player.__class__.__name__, self.players.index(current_player), len(current_player.hand))	 		
		if self.player_with_priority == self.current_turn_player():
			self.player_with_priority = self.not_current_turn_player()
		else:	
			self.player_with_priority = self.current_turn_player()
			self.phase = 'draw'
			if self.print_moves:
				print "End of initial draw SETUP"

	def available_cards(self, moving_player):
		return [
			AnyManaLand(moving_player, guid=self.new_card_id),
			Fireball(moving_player, guid=self.new_card_id),
			Bear(moving_player, guid=self.new_card_id),
		]

	def draw_card(self, moving_player):
		new_card = choice(self.available_cards(moving_player))
		current_player = self.players[moving_player]
		current_player.hand.append(new_card)
		self.new_card_id += 1

		if self.phase == "draw":
			self.phase = "precombat"

		if self.print_moves:
			print "> {} {} DREW {}.".format(current_player.__class__.__name__, self.players.index(current_player), new_card.__class__)	 		

	def announce_attackers(self, attackers):
		self.attackers = attackers
		if self.print_moves:
			current_player = self.players[self.player_with_priority]
			print "> {} {} ANNOUNCED ATTACK.".format(current_player.__class__.__name__, self.players.index(current_player))
		self.player_with_priority = self.not_current_turn_player()
		self.attacked = True

	def assign_blockers(self, block_tuple):
		self.blocks.append(block_tuple)
		for blocker in block_tuple[1]:
			self.blockers.append(blocker)

		if self.print_moves:
			current_player = self.players[self.player_with_priority]
			print "> {} {} BLOCKED {} with {}.".format(current_player.__class__.__name__, self.players.index(current_player), block_tuple[0], block_tuple[1])

	def finish_blocking(self, player_number):
		if self.print_moves:
			current_player = self.players[self.player_with_priority]
			print "> {} {} FINISHED BLOCKING.".format(current_player.__class__.__name__, self.players.index(current_player))

		self.phase = 'combat_resolution'
		self.player_with_priority = self.current_turn_player()

	def resolve_combat(self, player_number):
		self.phase = 'post_combat'
		total_attack = 0
		current_player = self.players[player_number]
		opponent = self.opponent(current_player)
		dead_creatures = []

		for guid in self.attackers:
			attacker = None
			is_blocked = False 
			attacker = self.creature_with_guid(guid)
			attacker_strength_to_apportion = attacker.strength

			for block in self.blocks:
				if block[0] == guid:
					# is blocked, continue
					damage_to_attacker = 0
					creature = None
					is_blocked = True
					for blocker_guid in block[1]:
						blocker = self.creature_with_guid(blocker_guid)
						damage_to_attacker += blocker.strength
						if attacker_strength_to_apportion >= blocker.hit_points:
							dead_creatures.append(blocker_guid)
						attacker_strength_to_apportion -= blocker.hit_points

					if damage_to_attacker >= attacker.hit_points:
						dead_creatures.append(guid)
					continue


			if not is_blocked:
				opponent.hit_points -= attacker.strength
				total_attack += attacker.strength

		if self.print_moves:
			if total_attack > 0:
				print "> {} {} ATTACKED for {}, {} killed.".format(current_player.__class__.__name__, self.players.index(current_player), total_attack, dead_creatures)
			else:
				print "> {} {} ATTACKED, {} killed.".format(current_player.__class__.__name__, self.players.index(current_player), dead_creatures)

		self.attackers = []
		self.blockers = []
		self.blocks = []

		new_creatures = []		
		for creature in self.creatures:
			if creature.guid in dead_creatures:
				if creature.guid in self.ready_creatures:
					self.ready_creatures.remove(creature.guid)
			else:
				new_creatures.append(creature)
		self.creatures = new_creatures

	def creature_with_guid(self, guid):
		for creature in self.creatures:
			if creature.guid == guid:
				return creature

	def pass_the_turn(self, moving_player):
		"""Pass to the next player."""
		self.current_turn += 1
		player = self.players[self.current_turn_player()]
		player.current_mana = player.mana
		self.played_land = False
		self.player_with_priority = self.current_turn_player()
		self.attacked = False

		self.ready_creatures = [c.guid for c in self.creatures]
		self.phase = "draw"

		if self.print_moves:
			print "End of Turn {}".format(self.current_turn)

	def all_legal_blocks(self):
		"""
		Returns a list of possible_moves that include finishing_blocking, 
		plus all possible ways to assign blockers to the current attackers.
		"""
		possible_moves = [('finish_blocking', self.player_with_priority, 0)]

		blockers = []
		for c in self.creatures:
			if c.owner == self.player_with_priority:
				if c.guid not in self.blockers:
					blockers.append(c.guid)
		if len(blockers) == 0:
			return possible_moves
		
		blocker_combos = []
		for i in xrange(1,len(blockers)+1):
			blocker_combos += itertools.combinations(blockers, i)

		possible_blocks = itertools.product(self.attackers, blocker_combos)
		for block in possible_blocks:
			possible_moves.append(('assign_blockers', block, 0))

		return possible_moves
