"""MonteCarloBot plays out N iterations randomly, trying out all possible moves, choosing the move that wins the most."""

from bot import Bot
from game import Game
from rando import RandomBot


class MonteCarloBot(Bot):
	def play_move(self, game, iterations=1000):
		"""Plays the move in game that wins the most over the test iterations."""
		scores = []
		move_index = 0
		top_score_index = 0
		top_score = 0

		for move in game.legal_plays([game.state_repr()], self.mana):
			score = self.calc_win_rate(game, move_index, iterations=iterations)
			if score > top_score:
				top_score = score
				top_score_index = move_index
			scores.append(score)
			move_index += 1

		move = game.legal_plays([game.state_repr()], self.mana)[top_score_index]
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
			clone_game.current_player_number = game.current_player_number

			move = clone_game.legal_plays([clone_game.state_repr()], self.mana)[move_index]
			clone_game.do_move(move)
			winner, _, _ = clone_game.play_out()
			if winner == players[game.current_player_number-1]:
				wins += 1
			elif winner != None:
				losses += 1

		if wins + losses == 0:
			return 0
		
		return wins * 1.0 / (wins+losses)
