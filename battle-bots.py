#!/usr/bin/env python

"""Play AI bots against each other in a CCG-like."""


import argparse
from src.bot import Bot
from src.human import Human
from src.monte_carlo_search_tree import MonteCarloSearchTreeBot
from src.game import Game


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
	game = Game()
	for pid in args.players:
		bot = eval("{}".format(bots_types[pid]))(hit_points=args.starting_hit_points)
		game.players.append(bot)
	game.print_moves = True
	game.play_out()


if __name__ == "__main__":
	main()