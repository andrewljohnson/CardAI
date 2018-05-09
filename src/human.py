"""MonteCarloBot plays out N iterations, trying out random move sequences affter legal moves."""

from bot import Bot
from card import Card
from game import Game
from utils import decarded_state


class Human(Bot):
	def play_move(self, game_state, statcache):
		"""Plays the move in game that wins the most over the test iterations."""
		legal_plays = Game.legal_plays(game_state)
		pwp = Game.player_with_priority(game_state)
		sorted_plays = []

		for p in legal_plays:
			if p[0] == "resolve_combat" :
				sorted_plays.append(p)

		for card_type in ["land", "creature", "enchantment"]:
			for p in legal_plays:
				card_index = p[1]
				if p[0].startswith("card"):
					card = Game.get_hand(game_state, pwp)[card_index]
					if Card.card_type(card) == card_type:
						sorted_plays.append(p)

		attacks = []
		for p in legal_plays:
			if p[0] == "announce_attackers":
				attacks.append(p)
		attacks.sort(key=lambda t: len(t[1]), reverse=True)
		for p in attacks:
			sorted_plays.append(p)

		for p in legal_plays:
			card_index = p[1]
			if p[0].startswith("card"):
				card = Game.get_hand(game_state, pwp)[card_index]
				if Card.card_type(card) not in ["creature", "land", "enchantment"]:
					sorted_plays.append(p)

		for p in legal_plays:
			if p not in sorted_plays and p[0] != "pass_the_turn" :
				sorted_plays.append(p)

		for p in legal_plays:
			if p[0] == "pass_the_turn":
				sorted_plays.append(p)

		if len(sorted_plays) > 1:
			for counter, play in enumerate(sorted_plays):
				if counter == len(sorted_plays) - 1 and play[0] == "pass_the_turn": 
					print "  return: {}".format(Game.move_display_string(game_state, play))
				else:
					print "  {}: {}".format(counter + 1, Game.move_display_string(game_state, play))

			print "  p: Print your hand and the game board."
			
			answered = False
			while not answered:
				choice = raw_input("Type the number of the action you want to play: ")
				if choice == 'p' or choice == 'P':
					Game.print_board(game_state, show_opponent_hand=False);
					return self.play_move(game_state, statcache)
				elif (not choice) and sorted_plays[-1][0] == "pass_the_turn":
					choice = len(sorted_plays)				
					answered = True
				elif choice in [str(x) for x in range(0,len(sorted_plays)+1)]:					
					choice = int(choice)	
					if choice >= 1 and choice < len(sorted_plays) + 1:
						answered = True
				else:
					return self.play_move(game_state, statcache)					
		else:
			choice = 1

		game_state = Game.apply_move(game_state, sorted_plays[choice - 1])
		statcache.past_states.append(game_state)
		return sorted_plays[choice - 1], game_state


	@staticmethod
	def print_board(player_state, game_state, show_hand=True):
		if len(Game.get_creatures(game_state)):
			Card.print_hand(Game.get_creatures(game_state), owner=Game.get_player_states(game_state).index(player_state))
		if len(Game.get_lands(game_state)):
			Card.print_hand(Game.get_lands(game_state), owner=Game.get_player_states(game_state).index(player_state))
		Card.print_hand(Bot.hand(player_state), show_hand=show_hand)
		print "\n                         {} life - {} - Mana Pool: {}".format(Bot.hit_points(player_state), Bot.display_name(0), Bot.temp_mana(player_state))
