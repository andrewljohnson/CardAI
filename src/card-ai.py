import random


class Game():
	"""A fantasy card game instance."""

	def __init__(self, players):
		"""Set the list of players, and set the current_player to the first player."""
		self.current_player = 0
		self.players = players
		self.print_moves = False 
		self.print_wins = True 
		self.current_turn = 0;

	def play_out(self):
		"""Play out a game until one or more players is at zero hit points."""

		while not self.game_is_over():
			player = self.players[self.current_player]
			player.play_move(self)
			self.end_turn()
		
		winner, winning_hp, losing_hp = self.winning_player()
		if self.print_wins:
			if not winner:
				print "Game Over - Draw"
			else:
				print "Game Over - {} {} wins! Final hit points are {} to {}.".format(winner.__class__.__name__, self.players.index(winner), winning_hp, losing_hp)

		return winner, winning_hp, losing_hp

	def end_turn(self):
		"""Pass to the next player."""
		self.current_player = 1 if self.current_player == 0 else 0
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

	def strike_player(self, player):
		"""Remove 1 hit point from player."""
		damage = 1
		player.hit_points -= damage
		if self.print_moves:
			print "Turn {} - {} {} got hit for {} damage!".format(self.current_turn, player.__class__.__name__, self.players.index(player), damage)

	def blast_player(self, players):
		blaster = players[0]
		blastee = players[1]
		"""Remove hit points from player."""
		blastee.hit_points -= blaster.mana
		if self.print_moves:
			print "Turn {} - {} {} got hit for {} damage!".format(self.current_turn, blastee.__class__.__name__, self.players.index(blastee), blaster.mana)

	def add_mana(self, player):
		"""Add 1 to the mana player can use each turn."""
		player.mana += 1
		if self.print_moves:
			print "Turn {} - {} {} added a mana, how has {} mana.".format(self.current_turn, player.__class__.__name__, self.players.index(player), player.mana)

	def do_nothing(self, player):
		"""Do nothing for a turn."""
		if self.print_moves:
			print "Turn {} - {} {} did nothing.".format(self.current_turn, player.__class__.__name__, self.players.index(player))

	def possible_moves(self, moving_player):
		return [
			{'method': self.add_mana, 'arg': moving_player},
			{'method': self.blast_player, 'arg': [moving_player, self.opponent(moving_player)]},
			#{'method': self.strike_player, 'arg': self.opponent(moving_player)},
			#{'method': self.strike_player, 'arg': moving_player},
			#{'method': self.do_nothing, 'arg': moving_player},
		]


class Bot():
	"""The base Bot class."""

	def __init__(self, starting_hit_points=0, starting_mana=0):
		self.hit_points = starting_hit_points
		self.mana = starting_mana

class PassBot(Bot):
	"""PassBot always does nothing, then ends the turn."""

	def play_move(self, game):
		game.do_nothing(self)


class StrikeBot(Bot):
	"""StrikeBot always Strikes, then ends the turn,."""

	def play_move(self, game):
		game.strike_player(game.opponent(self))


class RandomBot(Bot):
	"""RandomBot plays a random legal move on its turn, then ends the turn,."""

	def play_move(self, game):
		"""Play a random move in game. Possible moves are strike self, strike opponent, or do nothing."""

		move_index = random.randint(0,1)
		move = game.possible_moves(self)[move_index]
		move['method'](move['arg'])


class BasicMonteCarloBot(Bot):
	"""BasicMonteCarloBot plays out N iterations randomly, trying out all possible moves, choosing the move that wins the most."""

	def play_move(self, game, iterations=2000):
		"""Plays the move in game that wins the most over the test iterations."""
		scores = []
		move_index = 0
		top_score_index = 0
		top_score = 0

		for move in game.possible_moves(self):
			score = self.calc_win_rate(game, move_index, iterations=iterations)
			if score > top_score:
				top_score = score
				top_score_index = move_index
			scores.append(score)
			move_index += 1

		print "move scores: {} ({} won)".format(scores, top_score_index)
		move = game.possible_moves(self)[top_score_index]
		move['method'](move['arg'])

	def calc_win_rate(self, game, move_index, iterations):
		""" Returns a percentage times the move won. """
		
		wins = 0
		losses = 0

		for x in range(0, iterations):

			players = [
	    	RandomBot(starting_hit_points=game.players[game.current_player].hit_points, starting_mana=game.players[game.current_player].mana),
				RandomBot(starting_hit_points=game.opponent(game.current_player).hit_points, starting_mana=game.opponent(game.current_player).mana),
			]

			clone_game = Game(players)
 			clone_game.print_wins = False
 			clone_game.print_moves = False
			clone_game.current_player = game.current_player

			move = clone_game.possible_moves(players[game.current_player])[move_index]
			move['method'](move['arg'])
			clone_game.end_turn()
			winner, _, _ = clone_game.play_out()
			if winner == players[game.current_player]:
				wins += 1
			elif winner != None:
				losses += 1

		if wins + losses == 0:
			return 0
		
		return wins * 1.0 / (wins+losses)


if __name__ == "__main__":

	starting_hit_points = 100
	number_of_games = 1

	for x in range(0, number_of_games):
		players = [
	    BasicMonteCarloBot(starting_hit_points=starting_hit_points),
			RandomBot(starting_hit_points=starting_hit_points),
		]
		game = Game(players)
		game.play_out()
