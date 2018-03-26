import random


class Player():
	def init(self):
		self.life_total = 16


class Game():

	def strike_player(self, player):
		player.life_total -= 3


	def play_random_move(self):
		possible_moves = [
							{'method': self.strike_player, 'arg': self.players[0]},
							{'method': self.strike_player, 'arg': self.players[1]},
							{'method': self.do_nothing},
						  ]

		move_index = random.randint(0,2)

		move = possible_moves[move_index]

		if 'arg' in move:
			move['method'](move['arg'])
		else:
			move['method']()

	def is_game_over(self):
		for p in players:
			if p.life_total == 0:
				return True
		return False

	def init(self):
		players = [
			Player(),
			Player(),
		]