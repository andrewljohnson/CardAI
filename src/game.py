"""Game encapsulates the rules and state of a game."""

from bot import Bot


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

		self.attackers = []

		self.blockers = []

		self.is_my_turn = True

		self.played_land = False

		self.assigned_blockers = False

		self.attacked = False

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
						self.is_my_turn, 
						self.assigned_blockers, 
						tuple([c.state_repr() for c in self.creatures]),
						tuple([c.state_repr() for c in self.attackers]),
						tuple([c.state_repr() for c in self.blockers]))

	def play_out(self):
		"""Play out a game until one or more players is at zero hit points."""

		while not self.game_is_over():
			player = self.players[self.current_player_number - 1]
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
			print "{} {} passes the turn.".format(player.__class__.__name__, self.players.index(player))
		self.end_turn()


	def end_turn(self):
		"""Pass to the next player."""
		
		self.current_player_number = 2 if self.current_player_number == 1 else 1
		player = self.players[self.current_player_number - 1]
		player.current_mana = player.mana
		self.played_land = False
		self.is_my_turn = True
		self.assigned_blockers = False
		self.attacked = False

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

	def fireball(self, player_numbers):
		"""Decrement hit_points equal to blaster's mana from blastee."""
		blaster = self.players[player_numbers[0]-1]
		blastee = self.players[player_numbers[1]-1]
		"""Remove hit points from player."""
		blastee.hit_points -= blaster.current_mana * 2 - 1
		if self.print_moves:
			print "> {} {} FIREBALLED for {} damage!".format(blaster.__class__.__name__,  self.players.index(blaster), blaster.current_mana)

	def bolt(self, player_number):
		"""Decrement some damage from player_number."""
		player = self.players[player_number-1]
		damage = 2
		player.hit_points -= damage
		opponent = self.opponent(player)
		if self.print_moves:
			print "> {} {} BOLTED for {} damage!".format(opponent.__class__.__name__, self.players.index(opponent), damage)

	def play_tapped_land(self, player_number):
		"""Increment a mana from player_number."""
		player = self.players[player_number-1]
		player.mana += 1
		self.played_land = True
		if self.print_moves:
			print "> {} {} played a TAPPED LAND!".format(player.__class__.__name__, self.players.index(player))

	def do_nothing(self, player_number):
		player = self.players[player_number-1]
		if self.print_moves:
			print "> {} {} does nothing.".format(player.__class__.__name__, self.players.index(player))

	def summon_bear(self, player_number):
		"""Summon a creature that attacks every turn and has haste, for player_number."""
		c = Creature(player_number, strength=2, hit_points=2)
		self.creatures.append(c)
		player = self.players[player_number-1]
		if self.print_moves:
			print "> {} {} SUMMONED a {}/{} NEST ROBBER.".format(player.__class__.__name__, self.players.index(player), c.strength, c.hit_points)

	def summon_bull(self, player_number):
		"""Summon a creature that attacks every turn and has haste, for player_number."""
		c = Creature(player_number, strength=3, hit_points=3)
		self.creatures.append(c)
		player = self.players[player_number-1]
		if self.print_moves:
			print "> {} {} SUMMONED a {}/{} BRAZEN SCOURGE.".format(player.__class__.__name__, self.players.index(player), c.strength, c.hit_points)

	def edict(self, player_number):
		"""Remove a creature from player_number, FIFO for now."""
		new_creatures = []
		killed = False
		for c in self.creatures:
			if not killed and c.owner == player_number:
				killed = True
			else:
				new_creatures.append(c)
		if self.print_moves:
			opponent = self.players[player_number-1]
			current_player = self.opponent(opponent)
			print "> {} {} EDICTED.".format(current_player.__class__.__name__, self.players.index(current_player))
		self.creatures = new_creatures

	def wrath(self, player_number):
		"""Remove aall creature for player_number."""
		if self.print_moves:
			opponent = self.players[player_number-1]
			current_player = self.opponent(opponent)
			print "> {} {} WRATHED, {} creatures died.".format(current_player.__class__.__name__, self.players.index(current_player), len(self.creatures))
		self.creatures = []

	def announce_attackers(self, player_number):
		attackers = []
		current_player = self.players[player_number-1]
		opponent = self.opponent(current_player)
		for creature in self.creatures:
			if creature.owner == player_number:
				attackers.append(creature)
				"print found an attacker"

		self.attackers = attackers
		self.current_player_number = 2 if self.current_player_number == 1 else 1
		self.is_my_turn = False

	def assign_blockers(self, player_number):
		self.assigned_blockers = True
		self.blockers = []
		self.current_player_number = 2 if self.current_player_number == 1 else 1
		self.is_my_turn = True

	def resolve_combat(self, player_number):
		self.assigned_blockers = False
		total_attack = 0
		current_player = self.players[player_number-1]
		opponent = self.opponent(current_player)
		for creature in self.attackers:
			opponent.hit_points -= creature.strength
			total_attack += creature.strength

		if self.print_moves:
			if total_attack > 0:
				print "> {} {} ATTACKED for {}.".format(current_player.__class__.__name__, self.players.index(current_player), total_attack)

		self.attackers = []
		self.blockers = []
		self.attacked = True

	def do_move(self, move):
		"""Do the move and increment the turn."""
		eval("self.{}".format(move[0]))(move[1])
		player = self.players[self.current_player_number -1]
		player.current_mana -= move[2]

		player.states.append(self.state_repr())
		self.opponent(player).states.append(self.state_repr())

	def current_player(self, state):
		"""The player_number of the player due to make move in state."""
		return state[0]

	def next_state(self, state, play):
		"""Returns a new state after applying the play to state."""
		players = [
			Bot(starting_hit_points=state[2], starting_mana=state[3], current_mana=state[4]), 
			Bot(starting_hit_points=state[5], starting_mana=state[6], current_mana=state[7])
		]
		current_player = self.players[state[0] - 1]
		clone_game = Game(players)
		players[0].states = self.players[0].states
		players[1].states = self.players[1].states
		clone_game.current_player_number = state[0]
		clone_game.current_turn = state[1]
		clone_game.played_land = state[8]
		clone_game.is_my_turn = state[9]
		clone_game.assigned_blockers = state[10]

		for creature_tuple in state[11]:
			c = Creature(creature_tuple[0], strength=creature_tuple[1], hit_points=creature_tuple[2])
			clone_game.creatures.append(c)

		for creature_tuple in state[12]:
			c = Creature(creature_tuple[0], strength=creature_tuple[1], hit_points=creature_tuple[2])
			clone_game.attackers.append(c)

		for creature_tuple in state[13]:
			c = Creature(creature_tuple[0], strength=creature_tuple[1], hit_points=creature_tuple[2])
			clone_game.blockers.append(c)

		eval("clone_game.{}".format(play[0]))(play[1])

		if play[0] == "announce_attackers":
			clone_game.assign_blockers(0)
			clone_game.resolve_combat(state[0])

		'''


		#if play[0] == "assign_blockers":
		#	clone_game.resolve_combat(state[0])
		'''

		return clone_game.state_repr()


	def legal_plays(self, state_history, available_mana):
		"""Returns a list of all legal moves given the state_history. We only use the most recent state in state_history for now."""
		game_state = state_history[-1]
		moving_player = game_state[0]
		opponent = 2 if moving_player == 1 else 1

		if not self.is_my_turn:
			return [('assign_blockers', moving_player, 0),]

		if self.assigned_blockers:
			return [('resolve_combat', moving_player, 0),]

		possible_moves = [('pass_the_turn', moving_player, 0)]

		if not self.played_land:
			possible_moves.append(('play_tapped_land', moving_player, available_mana))

		#if available_mana > 0:
		#	possible_moves.append(('fireball', [moving_player, opponent], available_mana))

		has_attackers = False
		for c in self.creatures:
			if c.owner == moving_player:
				has_attackers = True
				break
		if has_attackers and len(self.attackers) == 0 and not self.attacked:
			possible_moves.append(('announce_attackers', moving_player, 0))

		methods = [('summon_bear', moving_player, 2), 
	               #('summon_bull', moving_player, 3), 
	               #('edict', opponent, 1), 
	               #('wrath', opponent, 2), 
	               #('bolt', opponent, 2),
		]
		for method in methods:
			if method[2] <= available_mana:
				possible_moves.append(method+tuple())

		return possible_moves


	def winner(self, state_history):
		"""Returns -1 if the state_history is drawn, 0 if the game is ongoing, else the player_number of the winner."""
		current_state = state_history[-1]

		players = [Bot(starting_hit_points=current_state[2], starting_mana=current_state[3], current_mana=current_state[4]), 
				  Bot(starting_hit_points=current_state[5], starting_mana=current_state[6], current_mana=current_state[7])]
		current_player = self.players[self.current_player_number - 1]
		clone_game = Game(players)
		players[0].states = current_player.states
		players[1].states = self.opponent(current_player).states
		clone_game.current_player_number = current_state[0]
		clone_game.current_turn = current_state[1]

		# might need to add creatures here later?

		if clone_game.game_is_drawn():
			return -1

		if len(clone_game.dead_players()) == 0:
			return 0

		winning_player, _, _ = clone_game.winning_player()

		return clone_game.players.index(winning_player)+1


class Creature():
	"""A fantasy creature card instance."""

	def __init__(self, owner, strength=0, hit_points=0):
		
		# the player_number of the owner
		self.owner = owner

		# how much hit points this removes when it attacks
		self.strength = strength 

		# how many hit_points this takes to kill it
		self.hit_points = hit_points

	def state_repr(self):
		return (self.owner, 
			 	self.strength, 
				self.hit_points
		)

