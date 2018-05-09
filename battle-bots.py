#!/usr/bin/env python

"""Play AI bots against each other in a CCG-like."""


import argparse
from src.bot import Bot
from src.human import Human
from src.monte_carlo_search_tree import MonteCarloSearchTreeBot
from src.game import Game

from src.statcache import StatCache

def create_parser():
	"""Create the argparse parser."""
	parser = argparse.ArgumentParser()
	parser.add_argument(
		"--players",
		default=[1, 2],
		nargs=2,
		type=int,
		help="list of 2 players - defaults 1 2 - 0: plays randomly, 1: mcst, 2: Human"
	)
	parser.add_argument(
		"--starting_hit_points",
		default=20,
		type=int,
		help="the amount of hp each player starts with"
	)
	return parser


def main():
	"""Play two bots and print the results."""
	args = create_parser().parse_args()
	bots_types = [
		'Bot',
		'MonteCarloSearchTreeBot',
		'Human'
	]
	bot_names = {
		'Bot': 'random',
		'MonteCarloSearchTreeBot': 'mcst',
		'Human': 'You'
	}

	game_state = Game.new_game_state()
	game_state = Game.set_print_moves(game_state, True)

	statcache = StatCache()
	statcache.past_states.append(game_state)

	for pid in args.players:
		bot = eval("{}".format(bots_types[pid]))()
		statcache.bots.append(bot)

		player_state = Game.new_player_state_object(hit_points=args.starting_hit_points, bot_type=bot_names[bots_types[pid]])		
		game_state = Game.add_player(game_state, player_state)

	Game.play_out(game_state, statcache)


if __name__ == "__main__":
	main()