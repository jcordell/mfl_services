import requests
import json
from Object_Manipulations import load_obj, save_obj

class id_converter:
    def __init__(self, update=False):
        if update:
            self.converter = {}
            self.update_id_to_player_dict()
        self.converter = load_obj('mfl_id_to_player')

    def update_id_to_player_dict(self):
        page = requests.get("http://www63.myfantasyleague.com/2017/export?TYPE=players&L=11083&W=&JSON=1")
        players_json = json.loads(page.text)
        for player in players_json['players']['player']:
            self.converter[player['id']] = player['name']
        save_obj(self.converter, 'mfl_id_to_player')


    def convert_current_dp(self, pick):
        pick_round = str(int(pick[1]) + 1)
        pick_pos = int(pick[2]) + 1
        # format pick position
        if pick_pos < 10:
            pick_pos = "0" + str(pick_pos)
        else:
            pick_pos = str(pick_pos)
        return str(pick_round + "." + pick_pos)

    def convert_future_dp(self, pick):
        year = pick[2]
        pick_round = pick[3]
        return str(year + " Round " + pick_round)

    def convert_pick(self, pick):
        pick = pick.split("_")
        # check if pick is current year or future pick
        if pick[0] == "DP":
            draft_pick = self.convert_current_dp(pick)
        elif pick[0] == "FP":
            draft_pick = self.convert_future_dp(pick)
        else:
            #print("Couldn't convert: ", pick)
            return None
        return draft_pick

    def convert(self, player_id):
        if player_id in self.converter:
            return self.converter[player_id]
        else:
            return self.convert_pick(player_id)

    def convert_trade(self, player_list):
        return [self.convert(player) for player in player_list]
