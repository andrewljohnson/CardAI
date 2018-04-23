"""Game encapsulates the rules and state of a fantasy card game, and interface with bots."""

import collections
import itertools
from bot import Bot
from card import Bear, Creature, Fireball
from card import Forest, Mountain
from random import choice


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

		# a list of previous states the game has been in
		self.states = [self.state_repr()]

		# whether to print each move, typically False during simulation, but true for a real game
		self.print_moves = False 

	def state_repr(self):
		"""A hashable representation of the game state."""
		return (self.current_turn, 
				self.player_with_priority, 
				self.new_card_id, 
				self.phase, 
				tuple([p.state_repr() for p in self.players]),
				tuple([c.state_repr() for c in self.creatures]),
				tuple([l.state_repr() for l in self.lands]),
				tuple(self.attackers),
				tuple(self.blockers),
				tuple(self.blocks),
		)

	def game_for_state(self, state):
		"""Return a Game for a state tuple."""
		clone_game = Game()
		clone_game.current_turn = state[0]
		clone_game.player_with_priority = state[1]
		clone_game.new_card_id = state[2]
		clone_game.phase = state[3]

		for player_tuple in state[4]:
			cards = []
			for card_tuple in player_tuple[1]:
				cards.append(eval("{}".format(card_tuple[0]))(card_tuple[2], card_id=card_tuple[1]))
			clone_game.add_player(
				Bot(
					hit_points=player_tuple[0], 
					hand=cards
				)
			)

		for creature_tuple in state[5]:
			c = Creature(
				creature_tuple[1], 
				creature_tuple[4], 
				strength=creature_tuple[2], 
				hit_points=creature_tuple[3], 
				creature_id=creature_tuple[0]
			)
			clone_game.creatures.append(c)

		for land_tuple in state[6]:
			classname = land_tuple[0]
			land = eval("{}".format(classname))(
				land_tuple[2], 
				card_id=land_tuple[1],
				turn_played=land_tuple[3],
				is_tapped=land_tuple[4],
			)
			clone_game.lands.append(land)

		clone_game.attackers = list(state[7])
		clone_game.blockers = list(state[8])
		clone_game.blocks = list(state[9])

		return clone_game

	def add_player(self, player):
		"""Add a player to the game and set its game."""
		self.players.append(player)
		player.game = self


	"""
		Bot protocol methods after this. These are: 

			play_out, winner, acting_player, next_state, legal_plays.
	"""

	def play_out(self):
		"""Play out a game between two bots."""
		while not self.game_is_over():
			player = self.players[self.player_with_priority]
			player.play_move(self)

		winner, winning_hp, losing_hp = self.winning_player()
		if self.print_moves:
			if self.game_is_drawn():
				print "Game Over - Draw"
			else:
				print "Game Over - {} {} wins! Final hit points are {} to {}." \
					.format(winner.__class__.__name__, 
							self.players.index(winner), 
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
		"""Return the player_number of the player due to make move in state."""
		return state[1]

	def next_state(self, state, move):
		"""Return a new state after applying the move to state."""
		clone_game = self.game_for_state(state)
		return clone_game.do_move(move)

	def do_move(self, move):
		"""Do the move and increment the turn."""
		player = self.players[self.player_with_priority]
		mana_to_use = move[2]
		if move[0].startswith('card'):
			self.play_card_move(move)
		else:
			eval("self.{}".format(move[0]))(move[1])
		self.tap_lands_for_mana(mana_to_use)
		state_rep = self.state_repr()
		self.states.append(state_rep)
		return state_rep

	def tap_lands_for_mana(self, lands_to_tap):
		"""Tap land_to_tap lands to pay for a spell or effect."""
		tapped = lands_to_tap
		for land in self.lands:
			if tapped == 0:
				break
			if land.owner == self.player_with_priority and not land.is_tapped:
				land.is_tapped = True
				tapped -= 1

	def available_mana(self):
		"""Returns a map of color to amount of mana from player_with_priority's untapped lands."""
		mana = collections.Counter()
		for land in self.lands:
			if land.owner == self.player_with_priority and not land.is_tapped:
				mana.update(land.mana_provided())
		return dict(mana)

	def play_card_move(self, move):
		"""Play a card baed on the move tuple."""
		player_number = self.player_with_priority
		target_creature = move[3]
		mana_to_use = move[2]
		card_index = move[1]
		method_name = move[0]
		card = self.players[player_number].hand[card_index]
		card.play(self, mana_to_use, target_creature)

	def opponent(self, player):
		"""Return the player that isn't the given player."""
		for p in self.players:
			if p != player:
				return p

	def legal_plays(self, state_history):
		"""
			Return a list of all legal moves given the state_history. 
		
			We only use the most recent state in state_history for now.
		"""
		
		game_state = state_history[-1]
		game = self.game_for_state(game_state)

		if game.phase == "setup":
			return [('initial_draw', game.player_with_priority, 0),]			
		elif game.phase == "draw":
			return [('draw_card', game.player_with_priority, 0),]			
		elif game.phase == "declare_blockers":
			return game.all_legal_blocks()
		elif game.phase == "combat_resolution":
			return [('resolve_combat', game.player_with_priority, 0),]

		possible_moves = [('pass_the_turn', game.player_with_priority, 0)]
		possible_moves = game.add_card_actions(game, possible_moves)
		if game.phase == "precombat":
			possible_moves = game.add_attack_actions(game, possible_moves)
		return possible_moves

	def played_land(self):
		"""Returns True if the player_with_priority has played a land this turn."""
		for land in self.lands:
			if land.owner == self.player_with_priority and land.turn_played == self.current_turn:
				return True
		return False

	def add_card_actions(self, game, possible_moves):
		"""Return a list of possible actions based on the player_with_priority's hand."""
		card_types_added = []
		for card in game.players[game.player_with_priority].hand:
			if card.__class__ not in card_types_added:
				possible_moves += card.possible_moves(game)
				card_types_added.append(card.__class__)
		return possible_moves

	def add_attack_actions(self, game, possible_moves):
		"""Return a list of possible actions based on the player_with_priority's creatures."""
		available_attackers = []
		for creature in game.creatures:
			if creature.owner == game.player_with_priority and creature.can_attack(game):
				available_attackers.append(creature.id)
		
		if len(available_attackers) > 0 and len(game.attackers) == 0:
			for L in range(0, len(available_attackers)+1):
				for subset in itertools.combinations(available_attackers, L):
					if len(subset) > 0:
						possible_moves.append(('announce_attackers', subset, 0))

		return possible_moves

	def initial_draw(self, moving_player):
		"""Add some cards to each player's hand."""
	 	for i in range(0,7):
	 		self.draw_card(moving_player);
		if self.print_moves:
			current_player = self.players[moving_player]
			hand_strings = [type(c).__name__ for c in current_player.hand]
			print "> {} {} DREW HER HAND: {} ({} cards)." \
				.format(current_player.__class__.__name__, 
						self.players.index(current_player), 
						hand_strings, 
						len(current_player.hand))	 		
		if self.player_with_priority == self.current_turn_player():
			self.player_with_priority = self.not_current_turn_player()
		else:	
			self.player_with_priority = self.current_turn_player()
			self.phase = 'draw'
			if self.print_moves:
				print "End of initial draw SETUP"

	def current_turn_player(self):
		"""The index in self.players for the player whose turn it is. """
		return self.current_turn % 2

	def not_current_turn_player(self):
		"""The index in self.players for the player whose turn it isn't. """
		return (self.current_turn + 1) % 2

	def draw_card(self, moving_player):
		"""Add a card to moving_player's hand."""
		new_card = choice(self.available_cards(moving_player))
		current_player = self.players[moving_player]
		current_player.hand.append(new_card)
		self.new_card_id += 1

		if self.phase == "draw":
			self.phase = "precombat"

		if self.print_moves and self.phase != 'setup':
			print "> {} {} DREW {}." \
				.format(current_player.__class__.__name__, 
						self.players.index(current_player), 
						type(new_card).__name__)	 		

	def available_cards(self, moving_player):
		"""All possible cards in the game."""
		return [
			Forest(moving_player, card_id=self.new_card_id),
			Mountain(moving_player, card_id=self.new_card_id),
			Fireball(moving_player, card_id=self.new_card_id),
			Bear(moving_player, card_id=self.new_card_id),
		]

	def announce_attackers(self, attackers):
		"""Set attackers, shift priority to the defending player, and update the phase."""
		self.attackers = attackers
		if self.print_moves:
			current_player = self.players[self.player_with_priority]
			print "> {} {} ANNOUNCED ATTACK." \
				.format(current_player.__class__.__name__, 
						self.players.index(current_player))
		self.player_with_priority = self.not_current_turn_player()
		self.phase = "declare_blockers"

	def assign_blockers(self, block_tuple):
		"""Set blockers according to block_tiple that maps an attacker to multiple bloickers."""
		self.blocks.append(block_tuple)
		for blocker in block_tuple[1]:
			self.blockers.append(blocker)

		if self.print_moves:
			current_player = self.players[self.player_with_priority]
			print "> {} {} BLOCKED {} with {}." \
				.format(current_player.__class__.__name__, 
					self.players.index(current_player), 
					block_tuple[0], 
					block_tuple[1])

	def finish_blocking(self, player_number):
		"""Shift priority to the defending player and update the phase."""
		if self.print_moves:
			current_player = self.players[self.player_with_priority]
			print "> {} {} FINISHED BLOCKING." \
				.format(current_player.__class__.__name__, 
						self.players.index(current_player))

		self.phase = 'combat_resolution'
		self.player_with_priority = self.current_turn_player()

	def resolve_combat(self, player_number):
		"""Deal damage, remove any dead creatures, check for winners, and go to postcombat phase.""" 
		self.phase = 'postcombat'
		total_attack = 0
		current_player = self.players[player_number]
		opponent = self.opponent(current_player)
		dead_creatures = []

		for creature_id in self.attackers:
			attacker = None
			is_blocked = False 
			attacker = self.creature_with_id(creature_id)
			attacker_strength_to_apportion = attacker.strength

			for block in self.blocks:
				if block[0] == creature_id:
					# is blocked, continue
					damage_to_attacker = 0
					creature = None
					is_blocked = True
					for blocker_id in block[1]:
						blocker = self.creature_with_id(blocker_id)
						damage_to_attacker += blocker.strength
						if attacker_strength_to_apportion >= blocker.hit_points:
							dead_creatures.append(blocker_id)
						attacker_strength_to_apportion -= blocker.hit_points

					if damage_to_attacker >= attacker.hit_points:
						dead_creatures.append(id)
					continue


			if not is_blocked:
				opponent.hit_points -= attacker.strength
				total_attack += attacker.strength

		if self.print_moves:
			if total_attack > 0:
				print "> {} {} ATTACKED for {}, {} killed." \
					.format(current_player.__class__.__name__,
							self.players.index(current_player),
							total_attack,
							dead_creatures)
			else:
				print "> {} {} ATTACKED, {} killed." \
					.format(current_player.__class__.__name__, 
							self.players.index(current_player), 
							dead_creatures)

		self.attackers = []
		self.blockers = []
		self.blocks = []

		new_creatures = []		
		for creature in self.creatures:
			if creature.id not in dead_creatures:
				new_creatures.append(creature)
		self.creatures = new_creatures

	def creature_with_id(self, creature_id):
		"""Return the creature in self.creatures with id equal to creature_id."""
		for creature in self.creatures:
			if creature.id == creature_id:
				return creature

	def pass_the_turn(self, moving_player):
		"""Pass to the next player."""
		self.current_turn += 1
		player = self.players[self.current_turn_player()]
		for land in self.lands:
			if land.owner == self.player_with_priority:
				land.is_tapped = False

		self.player_with_priority = self.current_turn_player()
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
				if c.id not in self.blockers:
					blockers.append(c.id)
		if len(blockers) == 0:
			return possible_moves
		
		blocker_combos = []
		for i in xrange(1,len(blockers)+1):
			blocker_combos += itertools.combinations(blockers, i)

		possible_blocks = itertools.product(self.attackers, blocker_combos)
		for block in possible_blocks:
			possible_moves.append(('assign_blockers', block, 0))

		return possible_moves
