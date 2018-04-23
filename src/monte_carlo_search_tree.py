"""Implements MCST, based on https://jeffbradberry.com/posts/2015/09/intro-to-monte-carlo-tree-search/"""

import datetime
from bot import Bot
from math import log, sqrt
from random import choice


class MonteCarloSearchTreeBot(Bot):
	def __init__(self, hit_points=0, max_moves=60, simulation_time=4, C=1.4):
		"""
			Adjust simulation_time and max_moves to taste.

			For C, sqrt(2) would be the theoretically correct choice, 

			but higher if we want more exploration and less focus on good moves.
		"""
		super(MonteCarloSearchTreeBot, self).__init__(hit_points=hit_points)

		# the amount of time to call run_simulation as much as possible 		
		self.calculation_time = datetime.timedelta(seconds=simulation_time)

		# the max_moves for any simulation
		self.max_moves = max_moves
		
		# Larger C encourages more exploration of the possibilities, 
		# smaller causes the AI to prefer concentrating on known good moves
		self.C = C

		# statistics about previously simulated game states
		self.wins = {}
		self.plays = {}

		# enable to log simulation results
		self.show_simulation_results = False

	def play_move(self, game):
		"""Play a move in game."""
		move = self.get_play()
		game.do_move(move)

	def get_play(self):
		"""
			Return the best play,

			after simulating possible plays and updating plays and wins stats.
		"""
		state = self.game.states[-1]
		legal = self.game.legal_plays(self.game.states[:])

		# Bail out early if there is no real choice to be made.
		if not legal:
			return []
		if len(legal) == 1:
			return legal[0]

		games = 0
		begin = datetime.datetime.utcnow()
		while datetime.datetime.utcnow() - begin < self.calculation_time:
			self.run_simulation()
			games += 1

		moves_states = [(p, self.game.next_state(state, p)) for p in legal]

		player = self.game.acting_player(state)

		# Pick the move with the highest percentage of wins.
		percent_wins, move = max(
			(self.wins.get((player, S), 0) * 1.0 /
			 self.plays.get((player, S), 1),
			 p)
			for p, S in moves_states
		)

		if self.show_simulation_results:
			# Display the stats for each possible play.
			for x in sorted(
				((100 * self.wins.get((player, S), 0) * 1.0 /
					self.plays.get((player, S), 1),
					self.wins.get((player, S), 0),
					self.plays.get((player, S), 0), p)
				 for p, S in moves_states),
				reverse=True
			):
				print "{3}: {0:.2f}% ({1} / {2})".format(*x)

		return move

	def run_simulation(self):
		# A bit of an optimization here, so we have a local
		# variable lookup instead of an attribute access each loop.
		plays, wins = self.plays, self.wins

		visited_states = set()
		states_copy = self.game.states[:]
		state = states_copy[-1]
		player = self.game.acting_player(state)

		expand = True
		for t in xrange(1, self.max_moves + 1):
			curr_play_num = state[1]

			legal = self.game.legal_plays(states_copy)
			moves_states = [(p, self.game.next_state(state, p)) for p in legal]
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

			visited_states.add((player, state))
			player = self.game.acting_player(state)
			winner = self.game.winner(states_copy)
			if winner >= 0:
				break

		for player, state in visited_states:
			if (player, state) not in plays:
				continue
			plays[(player, state)] += 1
			if player == winner:
				wins[(player, state)] += 1
