"""Implements MCST, based on https://jeffbradberry.com/posts/2015/09/intro-to-monte-carlo-tree-search/"""

import datetime
from bot import Bot
from math import log, sqrt
from random import choice
from copy import deepcopy
import itertools, sys
import pickle 

class MonteCarloSearchTreeBot(Bot):
	def __init__(self, hit_points=0, max_moves=300, simulation_time=2, C=1.4):
		"""
			Adjust simulation_time and max_moves to taste.

			For C, sqrt(2) would be the theoretically correct choice, 

			but higher if we want more exploration and less focus on good moves.
		"""
		super(MonteCarloSearchTreeBot, self).__init__(hit_points=hit_points)

		# the amount of time to call run_simulation as much as possible 		
		self.calculation_time = datetime.timedelta(seconds=simulation_time)
		self.simulation_time = simulation_time

		# the max_moves for any simulation
		self.max_moves = max_moves
		
		# Larger C encourages more exploration of the possibilities, 
		# smaller causes the AI to prefer concentrating on known good moves
		self.C = C

		# enable to log simulation results
		self.show_simulation_results = True

	def play_move(self, game, statcache):
		"""Play a move in game."""
		move = self.get_play(game, statcache)
		state, game = game.next_state(None, move, game=game)
		statcache.past_states.append(state)
		return move

	def get_play(self, root_game, statcache):
		"""
			Return the best play,

			after simulating possible plays and updating plays and wins stats.
		"""
		state = statcache.past_states[-1]

		legal = root_game.legal_plays(state)

		# Bail out early if there is no real choice to be made.
		if not legal:
			return []
		if len(legal) == 1:
			return legal[0]

		games = 0
		begin = datetime.datetime.utcnow()
		spinner = itertools.cycle(['-', '/', '|', '\\'])
		sys.stdout.write("Thinking ")
		while datetime.datetime.utcnow() - begin < self.calculation_time:
			self.run_simulation(root_game, statcache)
			sys.stdout.write(spinner.next())
			sys.stdout.flush()
			sys.stdout.write('\b')
			games += 1

		print "SIMULATED {} playouts/s".format(games*1.0/self.simulation_time)


		CURSOR_UP_ONE = '\x1b[1A'
		ERASE_LINE = '\x1b[2K'
		print ERASE_LINE + CURSOR_UP_ONE
		
		moves_states = []
		for p in legal:
			game_state, _ = root_game.next_state(state, p)
			moves_states.append((p, game_state))

		player = root_game.acting_player(state)

		# Pick the move with the highest percentage of wins.
		percent_wins, move = max(
			(statcache.bot_stats(root_game.player_with_priority).wins.get((player, S), 0) * 1.0 /
			 statcache.bot_stats(root_game.player_with_priority).plays.get((player, S), 1),
			 p)
			for p, S in moves_states
		)

		if self.show_simulation_results:
			# Display the stats for each possible play.
			for x in sorted(
				((100 * statcache.bot_stats(root_game.player_with_priority).wins.get((player, S), 0) * 1.0 /
					statcache.bot_stats(root_game.player_with_priority).plays.get((player, S), 1),
					statcache.bot_stats(root_game.player_with_priority).wins.get((player, S), 0),
					statcache.bot_stats(root_game.player_with_priority).plays.get((player, S), 0), p)
				 for p, S in moves_states),
				reverse=True
			):
				print "{3}: {0:.2f}% ({1} / {2})".format(*x)
			'''
			'''
		return move

	# 

	def run_simulation(self, root_game, statcache):
		# A bit of an optimization here, so we have a local
		# variable lookup instead of an attribute access each loop.
		plays, wins, legal_moves_cache = \
			statcache.bot_stats(root_game.player_with_priority).plays, \
			statcache.bot_stats(root_game.player_with_priority).wins,  \
			statcache.bot_stats(root_game.player_with_priority).legal_moves_cache

		visited_states = set()
		state = statcache.past_states[-1]
		player = root_game.acting_player(state)

		expand = True
		for t in xrange(1, self.max_moves + 1):

			if state not in legal_moves_cache:
				legal_moves_cache[state] = root_game.legal_plays(state)		
			legal = legal_moves_cache[state]			

			moves_states = []
			play_randomly = True
			
			ended_game_for_move = {}
			for p in legal:
				if (p[1], state) in plays:
					game_state, ended_game_for_move[p] = root_game.next_state(state, p)
					moves_states.append((p, game_state, ended_game_for_move[p]))
				else:
					play_randomly = True
					break

			if play_randomly:
				move = choice(legal)
				state, ended_game_for_move[move] = root_game.next_state(state, move)
				pass
			elif all(plays.get((player, S)) for p, S in moves_states):
				# If we have stats on all of the legal moves here, use them.
				log_total = log(
					sum(plays[(player, S)] for p, S in moves_states))
				value, move, state, ended_game = max(
					((wins[(player, S)] / plays[(player, S)]) +
					 self.C * sqrt(log_total / plays[(player, S)]), p, S)
					for p, S, ended_game in moves_states
				)
			else:
				# Otherwise, just make an arbitrary decision.
				move, state, ended_game = choice(moves_states)

			# `player` here and below refers to the player
			# who moved into that particular state.
			if expand and (player, state) not in plays:
				expand = False
				plays[(player, state)] = 0
				wins[(player, state)] = 0

			visited_states.add((player, state))
			player = root_game.acting_player(state)

			winner = ended_game_for_move[move].winner()
			if winner >= 0:
				break

		for player, state in visited_states:
			if (player, state) not in plays:
				continue
			plays[(player, state)] += 1
			if player == winner:
				wins[(player, state)] += 1

	def bot_type(self):
		return "mcst"
