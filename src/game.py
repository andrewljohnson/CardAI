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

		for p in players:
			p.board = self
			p.states = [self.state_repr()]

	def state_repr(self):
		"""A hashable representation of the game state."""

		return (self.current_player_number, 
						self.current_turn, 
						self.players[0].hit_points, 
						self.players[0].mana, 
						self.players[1].hit_points, 
						self.players[1].mana,
						tuple([c.state_repr() for c in self.creatures]))

	def play_out(self):
		"""Play out a game until one or more players is at zero hit points."""

		while not self.game_is_over():
			player = self.players[self.current_player_number - 1]
			player.play_move(self)
			self.opponent(player).states.append(self.state_repr())

		return self.winning_player()

	def end_turn(self):
		"""Pass to the next player."""
		
		total_attack = 0
		current_player = self.players[self.current_player_number-1]
		opponent = self.opponent(current_player)
		for creature in self.creatures:
			if creature.owner == self.current_player_number:
				opponent.hit_points -= creature.strength
				total_attack += creature.strength

		if self.print_moves:
			if total_attack > 0:
				print "> {} {} ATTACKED for {}.".format(current_player.__class__.__name__, self.players.index(current_player), total_attack)

		self.current_player_number = 2 if self.current_player_number == 1 else 1

		if self.current_player_number == 1:
			self.current_turn += 1
			self.players[0].mana += 1
			self.players[1].mana += 1
		
		#self.players[0].states.append(self.state_repr())
		#self.players[1].states.append(self.state_repr())

		if self.print_moves:
			if self.game_is_over():
				winner, winning_hp, losing_hp = self.winning_player()
				if self.game_is_drawn():
					print "Game Over - Draw"
				else:
					print "Game Over - {} {} wins! Final hit points are {} to {}.".format(winner.__class__.__name__, self.players.index(winner), winning_hp, losing_hp)

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
		"""Return true if all players has <= 0 hit points."""
		return len(self.dead_players()) == len(self.players)

	def game_is_over(self):
		"""Return true if either player has <= 0 hit points."""
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

	def blast_player(self, player_numbers):
		"""Decrement hit_points equal to blaster's mana from blastee."""
		blaster = self.players[player_numbers[0]-1]
		blastee = self.players[player_numbers[1]-1]
		"""Remove hit points from player."""
		blastee.hit_points -= blaster.mana * 2 - 1
		if self.print_moves:
			print "> {} {} BLASTED for {} damage!".format(blaster.__class__.__name__,  self.players.index(blaster), blaster.mana)

	def bolt(self, player_number):
		"""Decrement some damage from player_number."""
		player = self.players[player_number-1]
		damage = 2
		player.hit_points -= damage
		opponent = self.opponent(player)
		if self.print_moves:
			print "> {} {} BOLTED for {} damage!".format(opponent.__class__.__name__, self.players.index(opponent), damage)

	def buff_mana(self, player_number):
		"""Increment a mana from player_number."""
		player = self.players[player_number-1]
		player.mana += 1
		if self.print_moves:
			print "> {} {} buffed mana!".format(player.__class__.__name__, self.players.index(player))

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
			print "> {} {} SUMMONED a {}/{} BEAR.".format(player.__class__.__name__, self.players.index(player), c.strength, c.hit_points)

	def summon_bull(self, player_number):
		"""Summon a creature that attacks every turn and has haste, for player_number."""
		c = Creature(player_number, strength=3, hit_points=3)
		self.creatures.append(c)
		player = self.players[player_number-1]
		if self.print_moves:
			print "> {} {} SUMMONED a {}/{} BULL.".format(player.__class__.__name__, self.players.index(player), c.strength, c.hit_points)

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

	def do_move(self, move):
		"""Do the move and increment the turn."""
		if self.current_player_number == 1 and self.print_moves:
			print "Turn {}".format(self.current_turn)
		eval("self.{}".format(move[0]))(move[1])
		self.end_turn()

	def current_player(self, state):
		"""The player_number of the player due to make move in state."""
		return state[0]

	def next_state(self, state, play):
		"""Returns a new state after applying the play to state."""
		players = [
			Bot(starting_hit_points=state[2], starting_mana=state[3]), 
			Bot(starting_hit_points=state[4], starting_mana=state[5])
		]
		clone_game = Game(players)
		clone_game.current_player_number = state[0]
		clone_game.current_turn = state[1]
		
		for creature_tuple in state[6]:
			c = Creature(creature_tuple[0], strength=creature_tuple[1], hit_points=creature_tuple[2])
			clone_game.creatures.append(c)

		eval("clone_game.{}".format(play[0]))(play[1])
		clone_game.end_turn()

		return clone_game.state_repr()


	def legal_plays(self, state_history, available_mana):
		"""Returns a list of all legal moves given the state_history. We only use the most recent state in state_history for now."""
		game_state = state_history[-1]
		moving_player = game_state[0]
		opponent = 2 if moving_player == 1 else 1

		possible_moves = [('buff_mana', moving_player, available_mana),]

		methods = [('summon_bear', moving_player, 2), 
	               ('summon_bull', moving_player, 3), 
	               ('edict', opponent, 1), 
	               ('wrath', opponent, 2), 
	               ('blast_player', [moving_player, opponent], available_mana), 
	               ('bolt', opponent, 1),
		]
		for method in methods:
			if method[2] <= available_mana:
				possible_moves.append(method+tuple())
		
		return possible_moves


	def winner(self, state_history):
		"""Returns -1 if the state_history is drawn, 0 if the game is ongoing, else the player_number of the winner."""
		current_state = state_history[-1]
		players = [Bot(starting_hit_points=current_state[2], starting_mana=current_state[3]), 
							Bot(starting_hit_points=current_state[4], starting_mana=current_state[5])]
		clone_game = Game(players)
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

