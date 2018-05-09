def decarded_state(state_clone):
	mutable_player = list(state_clone[4][0])
	mutable_player[1] = ()
	mutable_player[4] = ()

	mutable_players = list(state_clone[4])
	mutable_players[0] = tuple(mutable_player)

	mutable_player = list(state_clone[4][1])
	mutable_player[1] = ()
	mutable_player[4] = ()

	mutable_players[1] = tuple(mutable_player)

	mutable_state = list(state_clone)
	mutable_state[4] = tuple(mutable_players)
	mutable_state[14] = True
	return tuple(mutable_state)


