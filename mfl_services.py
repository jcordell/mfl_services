from bs4 import BeautifulSoup
import requests
import re
import json
import time
from tqdm import tqdm
from IdConverterMFL import id_converter
import csv
import os

class mfl_service:

    def __init__(self, update_player_converter=False):
        # initialize id converter
        self.id_to_player_converter = id_converter(update=update_player_converter)
        self.num_trades_collected = 0


    def get_dynasty_league_ids(self):
        # be nice to MFL servers
        time.sleep(2)

        page = requests.get("http://www03.myfantasyleague.com/2017/index?YEAR=2017&SEARCH=dynasty&submit=Go")

        # check that page downloaded correctly
        if str(page.status_code)[0] != str(2):
            print("Error downloading page.")

        soup = BeautifulSoup(page.content, 'html.parser')
        league_id_list = []
        for league in soup.find_all('a', href=True):
            league_string = re.escape(str(league))
            if 'Dynasty' in league_string:
                id = league_string.split("/")[5].split("\\")[0]
                league_id_list.append(id)
        return league_id_list


    def make_trade_side_list(self, trade, side, convert_to_player=True):
        # can get errors and pass string when should be dict
        if isinstance(trade, str):
            #print('Lost another one')
            return
            #trade = json.loads(trade)

        # get players involed in trade as list
        side1_players = trade[side].split(",")

        # remove empty strings
        side1_players = filter(None, side1_players)

        # convert id to players
        if convert_to_player:
            side1_players = self.id_to_player_converter.convert_trade(side1_players)
        return side1_players


    def get_league_trades(self, league_id, year, csv_writer=None):
        '''
        Finds all trades in league.  Should return real name of playesr?
        
        :param league_id: league id to gather trade data from
        :return: list of all trades in league
        '''
        trade_url = "http://www55.myfantasyleague.com/" + str(year) + "/export?TYPE=transactions&L=" \
                    + str(league_id) + "&TRANS_TYPE=TRADE&JSON=1"
        try:
            page = requests.get(trade_url)
            page.raise_for_status()

            # load json as dictionary
            trades_dict = json.loads(page.text)
        except:
            print('Error downloading:', league_id)
            return

        #trades_dict = load_obj('trade_dict') # for easy testing
        trade_data = []

        # make sure transaction exists
        if 'transactions' in trades_dict and 'transaction' in trades_dict['transactions']:
            for trade in trades_dict['transactions']['transaction']:
                # get players in trade, split into list, convert to real name
                side1_players = self.make_trade_side_list(trade, 'franchise1_gave_up')
                side2_players = self.make_trade_side_list(trade, 'franchise2_gave_up')

                # make sure neither side is empty
                if side1_players is None or side2_players is None:
                    continue

                # weird stuff if pick can't be converted
                if None in side1_players or None in side2_players:
                    continue

                timestamp = int(trade['timestamp'])
                single_trade = [side1_players, side2_players, timestamp, league_id]

                trade_data.append(single_trade)

                if csv_writer is not None:
                    csv_writer.writerow(single_trade)
        self.num_trades_collected += len(trade_data)
        print(len(trade_data), ", Total:", self.num_trades_collected)
        return trade_data


    def get_multiple_leagues_trades(self, league_list, save_path, year=2017, disable_progess_bar=False):
        all_trades = []
        with open(save_path, "w") as csv_file:
            writer = csv.writer(csv_file, delimiter=',')
            writer.writerow(["player1", "player2", "time", "league_id"])
            for league in tqdm(league_list, disable=disable_progess_bar):
                all_trades.append(self.get_league_trades(league, year, writer))
        return all_trades


    def get_scoring_rules(league_id):
        # load league rules as json
        league_scoring_url = "http://www59.myfantasyleague.com/2017/export?TYPE=rules&L=" + league_id + "&W=&JSON=1"
        scoring_rules = requests.get(league_scoring_url)
        scoring_rules_json = json.loads(scoring_rules.content.decode('utf-8'))

        rules = {}
        # get ppr scoring
        rules['ppr'] = scoring_rules_json['rules']['positionRules'][1]['rule'][14]['points']['$t']
        print(rules['ppr'])


    def get_starter_rules(self, league_id):
        league_rules_url = "http://www59.myfantasyleague.com/2017/export?TYPE=league&L=" + league_id + "&W=&JSON=1"
        league_rules = requests.get(league_rules_url)

        #soup_rules = BeautifulSoup(league_rules.content, 'html.parser')
        rules_dict = json.loads(league_rules.text)

        league__single_rules = {}
        num_qbs = rules_dict['league']['starters']['position'][0]['limit']
        league__single_rules['num_qbs'] = num_qbs
        return league__single_rules


    def get_leagues_rules(self, SAVE_PATH, league_ids, update_all=False, disable_progress_bar=False):

        # if rules json doesn't exist or updating all league rules
        if not os.path.exists(SAVE_PATH) or update_all:
            league_rules = {}
        else:
            league_rules = json.load(open(SAVE_PATH))

        for league_id in tqdm(league_ids, disable=disable_progress_bar):

            # if already have rules, don't redownload
            if league_id in league_rules:
                continue
            league_rules[league_id] = {}

            try:
                # get number of starters
                starter_rules = self.get_starter_rules(league_id)
                if starter_rules is not None:
                    league_rules[league_id]['starters'] = starter_rules
            except:
                print("Error downloading league:", league_id)

        # save league rules to json
        with open(SAVE_PATH, 'w') as fp:
            json.dump(league_rules, fp)
        return league_rules
