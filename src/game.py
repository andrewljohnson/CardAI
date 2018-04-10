"""Game encapsulates the rules and state of a game."""

from bot import Bot
import itertools
from rando import RandomBot

class Game():
	"""A fantasy card game instance."""

	def __init__(self, players):
		"""Set the list of players, and set the current_player to the first player."""

		# a list of two Bot subclass players
		self.players = players

		# the active player, can be 1 or 2
		self.current_player_number = 1

		# whether to print each move
		self.print_moves = False 

		# the current term, switches after each player goes
		self.current_turn = 1

		# a hashable list of creatures
		self.creatures = []

		self.ready_creatures = []

		self.attackers = []

		self.blockers = []

		self.blocks = []

		self.player_with_priority = self.current_player_number

		self.played_land = False

		self.assigned_blockers = False

		self.attacked = False

		self.creature_id = 0

		for p in players:
			p.board = self
			p.states = [self.state_repr()]

	def state_repr(self):
		"""A hashable representation of the game state."""
		return (self.current_player_number, 
						self.current_turn, 
						self.players[0].hit_points, 
						self.players[0].mana, 
						self.players[0].current_mana, 
						self.players[1].hit_points, 
						self.players[1].mana,
						self.players[1].current_mana, 
						self.played_land, 
						self.player_with_priority, 
						self.assigned_blockers, 
						self.attacked, 
						self.creature_id, 
						tuple([c.state_repr() for c in self.creatures]),
						tuple(self.ready_creatures),
						tuple(self.attackers),
						tuple(self.blockers),
						tuple(self.blocks))

	def print_state(self, state):
		"""A hashable representation of the game state."""
		clone_game = self.game_for_state(state)
		print "TURN: {}, Current Player: {}, Priority: {}, played_land: {}, assigned_blockers: {}".format(
			clone_game.current_turn, clone_game.current_player_number, clone_game.player_with_priority,
			clone_game.played_land, clone_game.assigned_blockers)
		print "PLAYER 1: {} hp {}/{} mana, PLAYER 2: {} hp {}/{} mana".format(clone_game.players[0].hit_points, clone_game.players[0].current_mana, clone_game.players[0].mana,
			clone_game.players[1].hit_points, clone_game.players[1].current_mana, clone_game.players[1].mana)
		print "creatures: {}, ready_creatures: {}, attackers: {}, blockers: {}".format(tuple([c.state_repr() for c in clone_game.creatures]), tuple([c for c in clone_game.ready_creatures]), tuple([c for c in clone_game.attackers]),
			tuple([c for c in clone_game.blockers]))

	def play_out(self):
		"""Play out a game until one or more players is at zero hit points."""
		while not self.game_is_over():
			player = self.players[self.player_with_priority - 1]
			player.play_move(self)

		if self.print_moves:
			if self.game_is_over():
				winner, winning_hp, losing_hp = self.winning_player()
				if self.game_is_drawn():
					print "Game Over - Draw"
				else:
					print "Game Over - {} {} wins! Final hit points are {} to {}.".format(winner.__class__.__name__, self.players.index(winner), winning_hp, losing_hp)

		return self.winning_player()

	def pass_the_turn(self, moving_player):
		player = self.players[moving_player - 1]
		if self.print_moves:
			print "> {} {} passes the turn.".format(player.__class__.__name__, self.players.index(player))
		self.end_turn()

	def end_turn(self):
		"""Pass to the next player."""
		self.current_player_number = 2 if self.current_player_number == 1 else 1
		player = self.players[self.current_player_number - 1]
		player.current_mana = player.mana
		self.played_land = False
		self.player_with_priority = self.current_player_number
		self.assigned_blockers = False
		self.attacked = False

		self.ready_creatures = [c.guid for c in self.creatures]

		if self.print_moves:
			print "End of Turn {}".format(self.current_turn)

		self.current_turn += 1
		
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

	def opponent(self, player):
		"""Return the player that isn't the given player."""
		for p in self.players:
			if p != player:
				return p
				
		return dead_players

	def fireball(self, info):
		"""Decrement hit_points equal to blaster's mana from blastee."""
		blaster = self.players[info[0] - 1]
		current_mana = info[1]
		blastee = self.opponent(blaster)
		blastee.hit_points -= (current_mana - 1)
		if self.print_moves:
			print "> {} {} FIREBALLED for {} damage!".format(blaster.__class__.__name__, self.players.index(blaster), current_mana - 1)

	def fireball_creature(self, info):
		"""Decrement hit_points equal to blaster's mana from blastee."""
		blaster = self.players[self.player_with_priority - 1]
		creature = self.creature_with_guid(info[0])
		mana_to_use = info[1]
		if (mana_to_use - 1) >= creature.hit_points:
			if info[0] in self.attackers:
				self.attackers.remove(info[0])
			self.creatures.remove(creature)
			if creature.guid in self.ready_creatures:
				self.ready_creatures.remove(creature.guid)
		else:
			creature.hit_points -= (mana_to_use - 1)
		if self.print_moves:
			print "> {} {} FIREBALLED CREATURE {} for {} damage!".format(blaster.__class__.__name__, self.players.index(blaster), creature.guid, mana_to_use - 1)

	def shock(self, player_number):
		"""Decrement some damage from player_number."""
		player = self.players[player_number-1]
		damage = 2
		player.hit_points -= damage
		opponent = self.opponent(player)
		if self.print_moves:
			print "> {} {} SHOCKED for {} damage!".format(opponent.__class__.__name__, self.players.index(opponent), damage)

	def play_tapped_land(self, player_number):
		"""Increment a mana from player_number."""
		player = self.players[player_number-1]
		player.mana += 1
		self.played_land = True
		if self.print_moves:
			print "> {} {} played a TAPPED LAND!".format(player.__class__.__name__, self.players.index(player))

	def do_nothing(self, player_number):
		if self.print_moves:
			player = self.players[player_number-1]
			print "> {} {} does nothing.".format(player.__class__.__name__, self.players.index(player))

	def summon_bear(self, player_number):
		"""Summon a creature that attacks every turn and has haste, for player_number."""
		c = Creature(player_number, strength=4, hit_points=1, guid=self.creature_id)
		self.creature_id += 1
		self.creatures.append(c)
		if self.print_moves:
			player = self.players[player_number-1]
			print "> {} {} SUMMONED a {}/{} BEAR.".format(player.__class__.__name__, self.players.index(player), c.strength, c.hit_points)

	def summon_bull(self, player_number):
		"""Summon a creature that attacks every turn and has haste, for player_number."""
		c = Creature(player_number, strength=3, hit_points=3, guid=self.creature_id)
		self.creature_id += 1
		self.creatures.append(c)
		if self.print_moves:
			player = self.players[player_number-1]
			print "> {} {} SUMMONED a {}/{} GIANT.".format(player.__class__.__name__, self.players.index(player), c.strength, c.hit_points)

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
			opponent = self.players[player_number-1]
			current_player = self.opponent(opponent)
			print "> {} {} EDICTED.".format(current_player.__class__.__name__, self.players.index(current_player))
		self.creatures = new_creatures
		if killed_guid in self.ready_creatures:
			self.ready_creatures.remove(killed_guid)

	def wrath(self, player_number):
		"""Remove aall creature for player_number."""
		if self.print_moves:
			opponent = self.players[player_number-1]
			current_player = self.opponent(opponent)
			print "> {} {} WRATHED, {} creatures died.".format(current_player.__class__.__name__, self.players.index(current_player), len(self.creatures))
		self.creatures = []
		self.ready_creatures = []

	def announce_attackers(self, attackers):
		self.attackers = attackers
		if self.print_moves:
			current_player = self.players[self.player_with_priority-1]
			print "> {} {} ANNOUNCED ATTACK.".format(current_player.__class__.__name__, self.players.index(current_player))
		self.player_with_priority = 2 if self.current_player_number == 1 else 1
		self.attacked = True

	def assign_blockers(self, block_tuple):
		self.blocks.append(block_tuple)
		for blocker in block_tuple[1]:
			self.blockers.append(blocker)

		if self.print_moves:
			current_player = self.players[self.player_with_priority-1]
			print "> {} {} BLOCKED {} with {}.".format(current_player.__class__.__name__, self.players.index(current_player), block_tuple[0], block_tuple[1])

	def finish_blocking(self, player_number):
		if self.print_moves:
			current_player = self.players[self.player_with_priority-1]
			print "> {} {} FINISHED BLOCKING.".format(current_player.__class__.__name__, self.players.index(current_player))

		self.assigned_blockers = True
		self.player_with_priority = self.current_player_number

	def resolve_combat(self, player_number):
		self.assigned_blockers = False
		total_attack = 0
		current_player = self.players[player_number-1]
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

	def do_move(self, move):
		"""Do the move and increment the turn."""
		player = self.players[self.player_with_priority -1]
		player.current_mana -= move[2]
		eval("self.{}".format(move[0]))(move[1])
		state_rep = self.state_repr()
		player.states.append(state_rep)
		self.opponent(player).states.append(state_rep)

	def current_player(self, state):
		"""The player_number of the player due to make move in state."""
		return state[9]

	def next_state(self, state, play):
		"""Returns a new state after applying the play to state."""
		clone_game = self.game_for_state(state)
		player = clone_game.players[clone_game.player_with_priority - 1]
		player.current_mana -= play[2]
		eval("clone_game.{}".format(play[0]))(play[1])
		return clone_game.state_repr()

	def game_for_state(self, state):
		players = [
			RandomBot(starting_hit_points=state[2], starting_mana=state[3], current_mana=state[4]), 
			RandomBot(starting_hit_points=state[5], starting_mana=state[6], current_mana=state[7])
		]
		clone_game = Game(players)
		clone_game.current_player_number = state[0]
		clone_game.current_turn = state[1]
		clone_game.played_land = state[8]
		clone_game.player_with_priority = state[9]
		clone_game.assigned_blockers = state[10]
		clone_game.attacked = state[11]
		clone_game.creature_id = state[12]

		for creature_tuple in state[13]:
			c = Creature(creature_tuple[1], strength=creature_tuple[2], hit_points=creature_tuple[3], guid=creature_tuple[0])
			clone_game.creatures.append(c)

		clone_game.ready_creatures = list(state[14])
		clone_game.attackers = list(state[15])
		clone_game.blockers = list(state[16])
		clone_game.blocks = list(state[17])

		return clone_game

	def legal_plays(self, state_history, available_mana):
		"""Returns a list of all legal moves given the state_history. We only use the most recent state in state_history for now."""
		game_state = state_history[-1]
		clone_game = self.game_for_state(game_state)
		moving_player = game_state[9]
		opponent = 2 if moving_player == 1 else 1

		if clone_game.player_with_priority != clone_game.current_player_number:
			#TODO IMPLEMENT BLOCKING
			possible_moves = [('finish_blocking', moving_player, 0)]

			blockers = []
			for c in clone_game.creatures:
				if c.owner == clone_game.player_with_priority:
					if c.guid not in clone_game.blockers:
						blockers.append(c.guid)
			if len(blockers) == 0:
				return possible_moves
			
			blocker_combos = []
			for i in xrange(1,len(blockers)+1):
				blocker_combos += itertools.combinations(blockers, i)

			possible_blocks = itertools.product(clone_game.attackers, blocker_combos)
			for block in possible_blocks:
				possible_moves.append(('assign_blockers', block, 0))

			return possible_moves

		if clone_game.assigned_blockers:
			return [('resolve_combat', moving_player, 0),]

		possible_moves = [('pass_the_turn', moving_player, 0)]

		if not clone_game.played_land:
			possible_moves.append(('play_tapped_land', moving_player, 0))

		if available_mana > 1:
			possible_moves.append(('fireball', (moving_player, available_mana), available_mana))
			for c in clone_game.creatures:
				for mana in range(2, available_mana):
					possible_moves.append(('fireball_creature', (c.guid, mana), mana))
		
		available_attackers = []
		for guid in clone_game.ready_creatures:
			creature = clone_game.creature_with_guid(guid)
			if creature.owner == moving_player:
				available_attackers.append(guid)
		
		if len(available_attackers) > 0 and len(clone_game.attackers) == 0 and not clone_game.attacked:
			for L in range(0, len(available_attackers)+1):
				for subset in itertools.combinations(available_attackers, L):
					if len(subset) > 0:
						possible_moves.append(('announce_attackers', subset, 0))

		methods = [
			('summon_bear', moving_player, 2), 
			 #('summon_bull', moving_player, 2), 
			 #('edict', opponent, 1), 
			 #('wrath', opponent, 1), 
			 #('shock', opponent, 1),
		]
		for method in methods:
			if method[2] <= available_mana:
				possible_moves.append(method+tuple())

		return possible_moves

	def creature_with_guid(self, guid):
		for creature in self.creatures:
			if creature.guid == guid:
				return creature

	def winner(self, state_history):
		"""Returns -1 if the state_history is drawn, 0 if the game is ongoing, else the player_number of the winner."""
		current_state = state_history[-1]
		clone_game = self.game_for_state(current_state)

		if clone_game.game_is_drawn():
			return -1

		if len(clone_game.dead_players()) == 0:
			return 0

		winning_player, _, _ = clone_game.winning_player()

		return clone_game.players.index(winning_player)+1


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

