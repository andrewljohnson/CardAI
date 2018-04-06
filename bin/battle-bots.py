#!/usr/bin/env python

"""Play AI bots against each other in a CCG-like."""


import argparse
from src.monte_carlo import MonteCarloBot
from src.monte_carlo_search_tree import MonteCarloSearchTreeBot
from src.rando import RandomBot
from src.game import Game


def create_parser():
	"""Create the argparse parser."""
	parser = argparse.ArgumentParser()
	parser.add_argument(
		"--players",
		default=[2, 0],
		nargs=2,
		type=int,
		help="a list of two player types - types are 0 for random, 1 for monte carlo, 2 for mcst, defaults to mcst vs. random"
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
		'RandomBot',
		'MonteCarloBot',
		'MonteCarloSearchTreeBot'
	]
	game = Game([
		eval("{}".format(bots_types[args.players[0]]))(starting_hit_points=args.starting_hit_points),
		eval("{}".format(bots_types[args.players[1]]))(starting_hit_points=args.starting_hit_points)

		])
	game.print_moves = True
	game.play_out()


if __name__ == "__main__":
	main()