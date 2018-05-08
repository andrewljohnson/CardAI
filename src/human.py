"""MonteCarloBot plays out N iterations, trying out random move sequences affter legal moves."""

from bot import Bot
from card import Card
from game import Game


class Human(Bot):
	def play_move(self, game):
		"""Plays the move in game that wins the most over the test iterations."""
		legal_plays = game.legal_plays(game.states)
		sorted_plays = []

		for p in legal_plays:
			if p[0] == "resolve_combat" :
				sorted_plays.append(p)

		for card_type in ["land", "creature", "enchantment"]:
			for p in legal_plays:
				card_index = p[1]
				if p[0].startswith("card"):
					card = game.get_player_states()[game.player_with_priority].hand[card_index]
					if card.card_type == card_type:
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
				card = game.get_player_states()[game.player_with_priority].hand[card_index]
				if card.card_type not in ["creature", "land", "enchantment"]:
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
					print "  return: {}".format(game.move_display_string(play))
				else:
					print "  {}: {}".format(counter + 1, game.move_display_string(play))

			print "  p: Print your hand and the game board."
			
			answered = False
			while not answered:
				choice = raw_input("Type the number of the action you want to play: ")
				if choice == 'p' or choice == 'P':
					game.print_board(show_opponent_hand=False);
					self.play_move(game)
					return
				elif (not choice) and sorted_plays[-1][0] == "pass_the_turn":
					choice = len(sorted_plays)				
					answered = True
				elif choice in [str(x) for x in range(0,len(sorted_plays)+1)]:					
					choice = int(choice)	
					if choice >= 1 and choice < len(sorted_plays) + 1:
						answered = True
				else:
					self.play_move(game)
					return					
		else:
			choice = 1

		game.next_state(None, sorted_plays[choice - 1], game=game)

	# TODO FIX for tuples
	#def display_name(self, current_player):
	#		return "You"

	# TODO FIX FOR SUBCLASS NOT WORKING FOR TUPLES
	@staticmethod
	def print_board(player_state, game, show_hand=True):
		if len(game.creatures):
			Card.print_hand(game.creatures, owner=game.get_player_states().index(player_state))
		if len(game.lands):
			Card.print_hand(game.lands, owner=game.get_player_states().index(player_state))
		Card.print_hand(Bot.hand(player_state), show_hand=show_hand)
		print "\n                         {} life - {} - Mana Pool: {}".format(Bot.hit_points(player_state), Bot.display_name(0), Bot.temp_mana(player_state))
