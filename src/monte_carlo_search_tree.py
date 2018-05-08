"""Implements MCST, based on https://jeffbradberry.com/posts/2015/09/intro-to-monte-carlo-tree-search/"""

import datetime
from bot import Bot
from math import log, sqrt
from random import choice
from copy import deepcopy
import itertools, sys
import pickle 

from game import Game

class MonteCarloSearchTreeBot(Bot):
	def __init__(self, hit_points=0, max_moves=150, simulation_time=2, C=1.4):
		"""
			Adjust simulation_time and max_moves to taste.

			For C, sqrt(2) would be the theoretically correct choice, 

			but higher if we want more exploration and less focus on good moves.
		"""
		super(MonteCarloSearchTreeBot, self).__init__()

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

	def play_move(self, game_state, statcache):
		"""Play a move in game."""
		move = self.get_play(statcache)
		# print "GOT PLAY GOT PLAY {}".format(move)
		first_moving = Game.player_with_priority(game_state) == 0
		if move[0].startswith('ability') and first_moving:
			print "starting in gs {}".format(decarded_state(game_state))
		game_state = Game.apply_move(game_state, move)
		if move[0].startswith('ability') and first_moving:
			print "moving to gs {}".format(decarded_state(game_state))
		statcache.past_states.append(game_state)
		print "mcst played, states len now {}".format(len(statcache.past_states))
		return move, game_state

	def get_play(self, statcache):
		"""
			Return the best play,

			after simulating possible plays and updating plays and wins stats.
		"""
		game_state = statcache.past_states[-1]
		pwp = Game.player_with_priority(game_state)

		legal = Game.legal_plays(game_state)
		# print "CHOOSING FROM {} for state {}".format(legal, game_state)

		# Bail out early if there is no real choice to be made.
		if not legal:
			return []
		if len(legal) == 1:
			return legal[0]
			print "just one choice: {}".format(legal[0])

		games = 0
		begin = datetime.datetime.utcnow()
		spinner = itertools.cycle(['-', '/', '|', '\\'])
		sys.stdout.write("Thinking ")
		while datetime.datetime.utcnow() - begin < self.calculation_time:
			self.run_simulation(statcache)
			sys.stdout.write(spinner.next())
			sys.stdout.flush()
			sys.stdout.write('\b')
			games += 1

		first_moving = Game.player_with_priority(game_state) == 0
		if first_moving:
			print "SIMULATED {} playouts/s ({} playouts)".format(games*1.0/self.simulation_time, games)


		CURSOR_UP_ONE = '\x1b[1A'
		ERASE_LINE = '\x1b[2K'
		if first_moving:
			print ERASE_LINE + CURSOR_UP_ONE
		
		moves_states = []
		for p in legal:
			new_state = Game.apply_move(game_state, p)
			new_state = decarded_state(new_state)
			moves_states.append((p, tuple(new_state)))

		player = Game.acting_player(game_state)

		# Pick the move with the highest percentage of wins.
		percent_wins, move = max(
			(statcache.bot_stats(pwp).wins.get((player, S), 0) * 1.0 /
			 statcache.bot_stats(pwp).plays.get((player, S), 1),
			 p)
			for p, S in moves_states
		)
		'''

		for m in moves_states:
			print m[1]

		print statcache.bot_stats(pwp).plays
		print "plays"

		for w in statcache.bot_stats(pwp).plays:
			print w[1]

		print "wins and plays lens {} {}".format(len( statcache.bot_stats(pwp).wins),
			len( statcache.bot_stats(pwp).plays))

		print "plays"
		for w in statcache.bot_stats(pwp).wins:
			print statcache.bot_stats(pwp).wins[w]
		'''


		'''
		if self.show_simulation_results:
			# Display the stats for each possible play.
			for x in sorted(
				((100 * statcache.bot_stats(pwp).wins.get((player, S), 0) * 1.0 /
					statcache.bot_stats(pwp).plays.get((player, S), 1),
					statcache.bot_stats(pwp).wins.get((player, S), 0),
					statcache.bot_stats(pwp).plays.get((player, S), 0), 
					p)
				 for p, S in moves_states),
				reverse=True
			):
				print "{3}: {0:.2f}% ({1} / {2})".format(*x)
		'''

		print "chose move {}".format(move)
		return move

	def run_simulation(self, statcache):
		# print "STARTING SIM"
		# A bit of an optimization here, so we have a local
		# variable lookup instead of an attribute access each loop.
		state = statcache.past_states[-1]
		state = Game.set_print_moves(state, False)
		pwp = Game.player_with_priority(state)
		first_moving = Game.player_with_priority(state) == 0
		plays, wins, legal_moves_cache = \
			statcache.bot_stats(pwp).plays, \
			statcache.bot_stats(pwp).wins,  \
			statcache.bot_stats(pwp).legal_moves_cache

		visited_states = set()
		player = Game.acting_player(state)

		expand = True
		for t in xrange(1, self.max_moves + 1):
			# print t
			if state not in legal_moves_cache:
				legal_moves_cache[state] = Game.legal_plays(state)		
			legal = legal_moves_cache[state]			

			moves_states = []
			play_randomly = True
			
			ended_game_for_move = {}
			for p in legal:
				if (p[1], state) in plays:
					ended_game_for_move[p] = Game.apply_move(state, p)
					moves_states.append((p, ended_game_for_move[p], ended_game_for_move[p]))
				else:
					play_randomly = True
					break

			if play_randomly:
				move = choice(legal)
				ended_game_for_move[move] = Game.apply_move(state, move)
				state = ended_game_for_move[move]
  			elif all(plays.get((player, S)) for p, S in moves_states):
				# If we have stats on all of the legal moves here, use them.
				log_total = log(
					sum(plays[(player, S)] for p, S in moves_states))
				value, move, state = max(
					((wins[(player, S)] / plays[(player, S)]) +
					 self.C * sqrt(log_total / plays[(player, S)]), p, S)
					for p, S, ended_game in moves_states
				)
			else:
				# Otherwise, just make an arbitrary decision.
				move, state, ended_game = choice(moves_states)

			# print "moving. {}".format(move)
			# `player` here and below refers to the player
			# who moved into that particular state.
			state_clone = decarded_state(state)

			if expand and (player, state_clone) not in plays:
				expand = False

				plays[(player, state_clone)] = 0
				wins[(player, state_clone)] = 0

			visited_states.add((player, state_clone))
			player = Game.acting_player(state)

			winner = Game.winner(state)
			
			if winner >= 0:
				break

		for player, state in visited_states:
			if (player, state) not in plays:
				continue
			plays[(player, state)] += 1
			if player == winner:
				wins[(player, state)] += 1

		#exit(0)


def decarded_state(state_clone):
	mutable_player = list(state_clone[4][0])
	mutable_player[1] = ()
	mutable_player[4] = ()

	mutable_players = list(state_clone[4])
	mutable_players[0] = tuple(mutable_player)

	mutable_player = list(state_clone[4][1])
	mutable_player[1] = ()
	mutable_player[4] = ()

	mutable_players[1] = tuple(mutable_player)

	mutable_state = list(state_clone)
	mutable_state[4] = tuple(mutable_players)
	mutable_state[14] = True
	return tuple(mutable_state)


