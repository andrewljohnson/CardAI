"""MonteCarloBot plays out N iterations, trying out random move sequences affter legal moves."""

from bot import Bot
from game import Game


class MonteCarloBot(Bot):
	def play_move(self, game, iterations=100):
		"""Plays the move in game that wins the most over the test iterations."""
		scores = []
		move_index = 0
		top_score_index = 0
		top_score = 0
		legal_plays = game.legal_plays(game.states)

		if len(legal_plays) != 1:
			for move in legal_plays:
				score = self.calc_win_rate(game, move_index, iterations=iterations)
				if score > top_score:
					top_score = score
					top_score_index = move_index
				scores.append(score)
				move_index += 1

		move = legal_plays[top_score_index]
		game.next_state(None, move, game=game)
		
	def calc_win_rate(self, game, move_index, iterations):
		""" Returns a percentage times the move won. """
		wins = 0
		losses = 0

		for x in range(0, iterations):
			clone_game = game.game_for_state(game.state_repr())
			current_player = clone_game.players[clone_game.player_with_priority]
			move = clone_game.legal_plays(clone_game.states)[move_index]
			clone_game.do_move(move)
			winner = clone_game.play_out()
			if winner == current_player:
				wins += 1
			elif winner != None:
				losses += 1

		if wins + losses == 0:
			return 0
		
		return wins * 1.0 / (wins+losses)
