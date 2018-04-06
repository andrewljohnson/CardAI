import datetime
from math import log, sqrt

from random import choice


class Game():
	"""A fantasy card game instance."""

	def __init__(self, players):
		"""Set the list of players, and set the current_player to the first player."""
		self.current_player_number = 1
		self.players = players
		self.print_moves = False 
		self.print_wins = False 
		self.current_turn = 0


	def state_repr(self):
		return (self.current_player_number, self.current_turn, self.players[0].hit_points, self.players[0].mana, self.players[1].hit_points, self.players[1].mana)


	def play_out(self):
		"""Play out a game until one or more players is at zero hit points."""

		while not self.game_is_over():
			player = self.players[self.current_player_number - 1]
			player.play_move(self)
			if player != self.players[0]:
				self.players[0].update(game.state_repr())
			#print game.state_repr()


		winner, winning_hp, losing_hp = self.winning_player()
		if self.print_wins:
			if not winner:
				print "Game Over - Draw"
			else:
				print "Game Over - {} {} wins! Final hit points are {} to {}.".format(winner.__class__.__name__, self.players.index(winner), winning_hp, losing_hp)

		return winner, winning_hp, losing_hp

	def end_turn(self):
		"""Pass to the next player."""
		self.current_player_number = 2 if self.current_player_number == 1 else 1
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

	def blast_player(self, player_numbers):
		blaster = self.players[player_numbers[0]-1]
		blastee = self.players[player_numbers[1]-1]
		"""Remove hit points from player."""
		blastee.hit_points -= blaster.mana
		if self.print_moves:
			print "Turn {} - {} {} got hit for {} damage!".format(self.current_turn, blastee.__class__.__name__, self.players.index(blastee), blaster.mana)

	def add_mana(self, player_number):
		"""Add 1 to the mana player can use each turn."""
		player = self.players[player_number-1]
		player.mana += 1
		if self.print_moves:
			print "Turn {} - {} {} added a mana, how has {} mana.".format(self.current_turn, player.__class__.__name__, player_number, player.mana)

	def possible_moves(self, past_states):
		game_state = past_states[-1]
		moving_player = game_state[0]
		opponent = 2 if moving_player == 1 else 1
		return [
			{'method': 'add_mana', 'arg': moving_player},
			{'method': 'blast_player', 'arg': [moving_player, opponent]},
		]

	def do_move(self, move):
		eval("self.{}".format(move['method']))(move['arg'])
		self.end_turn()

	def current_player(self, state):
			return state[0]

	def next_state(self, state, play):
		players = [Bot(starting_hit_points=state[2], starting_mana=state[3]), 
							Bot(starting_hit_points=state[4], starting_mana=state[5])]
		clone_game = Game(players)
		clone_game.print_moves = False
		clone_game.print_wins = False
		clone_game.current_player_number = state[0]
		clone_game.current_turn = state[1]
		eval("clone_game.{}".format(play['method']))(play['arg'])
		clone_game.end_turn()
		return clone_game.state_repr()

	def legal_plays(self, state_history):
		return self.possible_moves(state_history)

	def winner(self, state_history):
		current_state = state_history[-1]
		players = [Bot(starting_hit_points=current_state[2], starting_mana=current_state[3]), 
							Bot(starting_hit_points=current_state[4], starting_mana=current_state[5])]
		clone_game = Game(players)
		clone_game.current_player_number = current_state[0]
		clone_game.current_turn = current_state[1]
		clone_game.print_moves = False
		clone_game.print_wins = False

		if clone_game.game_is_drawn():
			return -1

		if len(clone_game.dead_players()) == 0:
			return 0

		winning_player, _, _ = clone_game.winning_player()

		return clone_game.players.index(winning_player)+1


class Bot():
	"""The base Bot class."""

	def __init__(self, starting_hit_points=0, starting_mana=0):
		self.hit_points = starting_hit_points
		self.mana = starting_mana

class RandomBot(Bot):
	"""RandomBot plays a random legal move on its turn, then ends the turn,."""

	def play_move(self, game):
		"""Play a random move in game. Possible moves are strike self, strike opponent, or do nothing."""

		move = choice(game.possible_moves([game.state_repr()]))
		game.do_move(move)
		

class BasicMonteCarloBot(Bot):
	"""BasicMonteCarloBot plays out N iterations randomly, trying out all possible moves, choosing the move that wins the most."""

	def play_move(self, game, iterations=1000):
		"""Plays the move in game that wins the most over the test iterations."""
		scores = []
		move_index = 0
		top_score_index = 0
		top_score = 0

		for move in game.possible_moves([game]):
			score = self.calc_win_rate(game, move_index, iterations=iterations)
			if score > top_score:
				top_score = score
				top_score_index = move_index
			scores.append(score)
			move_index += 1

		# print "move scores: {} ({} won)".format(scores, top_score_index)
		move = game.possible_moves([game])[top_score_index]
		game.do_move(move)
		
	def calc_win_rate(self, game, move_index, iterations):
		""" Returns a percentage times the move won. """
		
		wins = 0
		losses = 0

		for x in range(0, iterations):

			current_player = game.players[game.current_player_number-1]
			players = [
				RandomBot(starting_hit_points=current_player.hit_points, starting_mana=current_player.mana),
				RandomBot(starting_hit_points=game.opponent(current_player).hit_points, starting_mana=game.opponent(current_player).mana),
			]

			clone_game = Game(players)
 			clone_game.print_wins = False
 			clone_game.print_moves = False
			clone_game.current_player_number = game.current_player_number

			move = clone_game.possible_moves([clone_game])[move_index]
			clone_game.do_move(move)
			winner, _, _ = clone_game.play_out()
			if winner == players[game.current_player_number-1]:
				wins += 1
			elif winner != None:
				losses += 1

		if wins + losses == 0:
			return 0
		
		return wins * 1.0 / (wins+losses)

class MonteCarloSearchTreeBot(BasicMonteCarloBot):
		"""Based on https://jeffbradberry.com/posts/2015/09/intro-to-monte-carlo-tree-search/"""


		def __init__(self, **kwargs):
				self.states = []

				self.mana = kwargs.get('mana', 0)
				self.hit_points = kwargs.get('starting_hit_points', 10)

				seconds = kwargs.get('time', .1)
				self.calculation_time = datetime.timedelta(seconds=seconds)

				self.max_moves = kwargs.get('max_moves', 100)
				
				self.C = kwargs.get('C', 3.5)

				self.wins = {}
				self.plays = {}

		def update(self, state):
				self.states.append(state)

		def play_move(self, game):
				move = self.get_play()
				self.update(game.next_state(game.state_repr(), move))
				game.do_move(move)

		def get_play(self):
				self.max_depth = 0
				state = self.states[-1]
				player = self.board.current_player(state)
				legal = self.board.legal_plays(self.states[:])

				# Bail out early if there is no real choice to be made.
				if not legal:
						return
				if len(legal) == 1:
						return legal[0]

				games = 0
				begin = datetime.datetime.utcnow()
				while datetime.datetime.utcnow() - begin < self.calculation_time:
						self.run_simulation()
						games += 1

				moves_states = [(p, self.board.next_state(state, p)) for p in legal]

				# Display the number of calls of `run_simulation` and the
				# time elapsed.
				# print games, datetime.datetime.utcnow() - begin
				# Pick the move with the highest percentage of wins.
				percent_wins, move = max(
						(self.wins.get((player, S), 0) * 1.0 /
						 self.plays.get((player, S), 1),
						 p)
						for p, S in moves_states
				)

				# Display the stats for each possible play.
				for x in sorted(
						((100 * self.wins.get((player, S), 0) * 1.0 /
							self.plays.get((player, S), 1),
							self.wins.get((player, S), 0),
							self.plays.get((player, S), 0), p['method'])
						 for p, S in moves_states),
						reverse=True
				):
						print "{3}: {0:.2f}% ({1} / {2})".format(*x)

				print "Maximum depth searched:", self.max_depth

				return move

		def run_simulation(self):
				# A bit of an optimization here, so we have a local
				# variable lookup instead of an attribute access each loop.
				plays, wins = self.plays, self.wins

				visited_states = set()
				states_copy = self.states[:]
				state = states_copy[-1]
				player = self.board.current_player(state)

				expand = True
				for t in xrange(1, self.max_moves + 1):
						legal = self.board.legal_plays(states_copy)
						moves_states = [(p, self.board.next_state(state, p)) for p in legal]

						if all(plays.get((player, S)) for p, S in moves_states):
								# If we have stats on all of the legal moves here, use them.
								log_total = log(
										sum(plays[(player, S)] for p, S in moves_states))
								value, move, state = max(
										((wins[(player, S)] / plays[(player, S)]) +
										 self.C * sqrt(log_total / plays[(player, S)]), p, S)
										for p, S in moves_states
								)
						else:
								# Otherwise, just make an arbitrary decision.
								move, state = choice(moves_states)

						states_copy.append(state)

						# `player` here and below refers to the player
						# who moved into that particular state.
						if expand and (player, state) not in plays:
								expand = False
								plays[(player, state)] = 0
								wins[(player, state)] = 0
								if t > self.max_depth:
										self.max_depth = t

						visited_states.add((player, state))

						player = self.board.current_player(state)
						winner = self.board.winner(states_copy)
						if winner > 0:
								break

				for player, state in visited_states:
						if (player, state) not in plays:
								continue
						plays[(player, state)] += 1
						if player == winner:
								wins[(player, state)] += 1

if __name__ == "__main__":

	starting_hit_points = 10

	mcst = MonteCarloSearchTreeBot(starting_hit_points=starting_hit_points)
	players = [
		mcst,
		RandomBot(starting_hit_points=starting_hit_points),
	]
	game = Game(players)
	mcst.board = game
	mcst.states = [game.state_repr()]
	game.print_moves = False
	game.print_wins = True
	game.play_out()


