from mfl_services import mfl_service

# create a mfl service instance and create/update the player_id to name converter
mfl = mfl_service(update_player_converter=True)

# Set league id
league_id = 27985

# returns [[players_side1_list], [players_side2_list], time_of_trade, league_id
# players are in trade list are by name, not id
trades = mfl.get_league_trades(league_id, year=2017)

print(trades)