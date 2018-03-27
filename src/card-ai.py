import random


class Game():
	"""A fantasy card game instance."""

	def __init__(self, players):
		"""Set the list of players, and set the current_player to the first player."""
		self.current_player = 0
		self.players = players
		self.print_moves = False 

	def play_out(self):
		"""Play out a game until one or more players is at zero hit points."""
		while not self.game_is_over():
			player = self.players[self.current_player]
			if self.print_moves:
				print "{} {}'s turn.".format(player.__class__.__name__, self.current_player)
			player.play_move(self)
			self.end_turn()

	def end_turn(self):
		"""Check if the game is over. If not, pass to the next player."""
		if self.game_is_over():
			self.end_game()

		self.current_player = 1 if self.current_player == 0 else 0

	def end_game(self):
		"""Print the winner of the game."""
		if self.game_is_drawn():
			print "Game Over - Draw"

		losing_hp = None
		winning_hp = None
		winner = None
		for p in self.players:
			if p.hit_points <= 0:
				losing_hp = p.hit_points
			else:
				winning_hp = p.hit_points
				winner = p

		print "Game Over - {} {} wins! Final hit points are {} to {}.".format(winner.__class__.__name__, players.index(winner), winning_hp, losing_hp)

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
			print ">>>>{} {} got hit for {} damage!".format(player.__class__.__name__, players.index(player), damage)

	def do_nothing(self, player):
		"""Do nothing for a turn."""
		if self.print_moves:
			print ">>>>{} {} did nothing.".format(player.__class__.__name__, players.index(player))

class Bot():
	"""The base Bot class."""

	def __init__(self, starting_hit_points=0):
		self.hit_points = starting_hit_points

	def play_move(self, game):
		game.do_nothing(self)


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
		possible_moves = [
							{'method': game.strike_player, 'arg': game.players[0]},
							{'method': game.strike_player, 'arg': game.players[1]},
							{'method': game.do_nothing, 'arg': self},
						  ]

		move_index = random.randint(0,2)
		move = possible_moves[move_index]
		if 'arg' in move:
			move['method'](move['arg'])
		else:
			move['method']()


if __name__ == "__main__":
	starting_hit_points = 2

	for x in range(0, 10000):
		players = [
			RandomBot(starting_hit_points=starting_hit_points),
	    	StrikeBot(starting_hit_points=starting_hit_points),
		]
		game = Game(players)
		game.play_out()
