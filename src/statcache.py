class StatCache(object):
	def __init__(self):
		self.bot_to_stats = {}
		self.past_states = []

	def bot_stats(self, bot_id):
		if bot_id not in self.bot_to_stats:
			self.bot_to_stats[bot_id] = BotStats()
		return self.bot_to_stats[bot_id]


class BotStats(object):
	def __init__(self):
		# statistics about previously simulated game states
		self.wins = {}
		self.plays = {}
		self.legal_moves_cache = {}
