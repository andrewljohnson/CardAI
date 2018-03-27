import random


class Game():
	"""A single game of a CCG-like game."""

	def __init__(self, players):
		"""Set the list of players, and set the current_player to the first player."""
		self.current_player = 0
		self.players = players 

	def play_out(self):
		"""Play out a single game until one or more players is dead."""
		while not self.game_is_over():
			player = self.players[self.current_player]
			print "{} {}'s turn.".format(player.__class__.__name__, self.current_player)
			player.play_move(self)
			self.end_turn()

	def end_turn(self):
		"""Check if the game is over. If not, pass to the next player."""

		if self.game_is_over():
			self.end_game()

		self.current_player = 1 if self.current_player == 0 else 0

	def end_game(self):
		"""Prints the winner of the game."""
		if self.game_is_drawn():
			print "Game Over - Draw"

		losing_hp = None
		winning_hp = None
		for p in self.players:
			if p.hit_points <= 0:
				losing_hp = p.hit_points
			else:
				winning_hp = p.hit_points

		print "Game Over - {} {} wins! Final hit points are {} to {}.".format(p.__class__.__name__, players.index(p), winning_hp, losing_hp)

	def game_is_drawn(self):
		"""Returns true if all players has <= 0 hit points."""
		return len(self.dead_players()) == len(self.players)

	def game_is_over(self):
		"""Returns true if either player has <= 0 hit points."""
		return len(self.dead_players()) > 0

	def dead_players(self):
		"""Returns a list of players that have hit points <= 0."""
		dead_players = []
		for p in self.players:
			if p.hit_points <= 0:
				dead_players.append(p)
				
		return dead_players

	def strike_player(self, player):
		"""Remove 3 it points from player."""
		damage = 3
		player.hit_points -= damage
		print ">>>>{} {} got hit for {} damage!".format(player.__class__.__name__, players.index(player), damage)

	def do_nothing(self, player):
		"""Do nothing for a turn, as opposed to striking."""
		print ">>>>{} {} did nothing.".format(player.__class__.__name__, players.index(player))

	def play_random_move(self, player):
		"""Possible moves are strike self, strike opponent, or do nothing."""
		possible_moves = [
							{'method': self.strike_player, 'arg': self.players[0]},
							{'method': self.strike_player, 'arg': self.players[1]},
							{'method': self.do_nothing, 'arg': player},
						  ]

		move_index = random.randint(0,2)

		move = possible_moves[move_index]

		if 'arg' in move:
			move['method'](move['arg'])
		else:
			move['method']()


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


class RandomBot(Bot):
	"""RandomBot plays a random legal move on its turn, then ends the turn,."""

	def play_move(self, game):
		game.play_random_move(self)


if __name__ == "__main__":
	starting_hit_points = 15
	players = [
    	PassBot(starting_hit_points=starting_hit_points),
		RandomBot(starting_hit_points=starting_hit_points),
	]

	game = Game(players)
	game.play_out()

