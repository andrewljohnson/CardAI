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
		help="a list of 3 player types - types are 0 for plays randomly, 1 for monte carlo, 2 for mcst, defaults to mcst vs. plays randomly"
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

	while not game.game_is_over():
		player = game.players[game.player_with_priority]
		player.play_move(game)

	winner, winning_hp, losing_hp = game.winning_player()
	if game.game_is_drawn():
		print "Game Over - Draw"
	else:
		print "Game Over - {} {} wins! Final hit points are {} to {}.".format(winner.__class__.__name__, game.players.index(winner), winning_hp, losing_hp)



if __name__ == "__main__":
	main()