
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field


class Player():
    def __init__(self, name = "", code = "") -> None:
        self.name = name
        self.code = code
        self.info = {}

    def add_info(self, key):
        if str(key) not in self.info:
            self.info[str(key)] = PlayerInfo()

    def get_info(self, key):
        self.add_info(str(key))
        return self.info[str(key)]

    def to_dict(self, key):
        return {
            "name": self.name,
            "code": self.code,
            **self.get_info(key).__dict__,
        }

@dataclass
class PlayerInfo():
    total:int = 0
    points:int = 0
    pt_total:int = 0
    phase2:int = 0
    cut:int = 0
    wins:int = 0
    best_finish:int = 99999
    g_wins:int = 0
    g_losses:int = 0
    events:dict = field(default_factory=dict)
    mons:dict = field(default_factory=dict)
    rivals:dict = field(default_factory=dict)


class PlayerStats():
    def __init__(self, config:dict, prod:bool = False, name_updates:dict = {}) -> None:
        self.all_players = {}
        self.config = config
        self.name_updates = name_updates


    def process_event(self, event:dict, year:int):
        event_code = event['event']['code']
        event_year_code = f"{year}-{event['event']['code']}"

        for player in event['standings'].values():
            pcode = player['code']
            pname = player['name']

            merge_into = self.get_name_merge(pcode)
            if merge_into:
                pcode = merge_into['code']
                pname = merge_into['name']

            if pcode not in self.all_players:
                self.all_players[pcode] = Player(
                    name=pname,
                    code=pcode,
                )

            # player all-time
            self.all_players[pcode].get_info('all').total += 1
            if player['place'] < self.all_players[pcode].get_info('all').best_finish:
                self.all_players[pcode].get_info('all').best_finish = player['place']

            self.all_players[pcode].get_info('all').points += 1 if player['points'] > 0 else 0
            self.all_players[pcode].get_info('all').pt_total += player['points']
            self.all_players[pcode].get_info('all').phase2 += 1 if player['p2'] else 0
            self.all_players[pcode].get_info('all').cut += 1 if player['cut'] else 0
            self.all_players[pcode].get_info('all').wins += 1 if player['place'] == 1 else 0

            self.all_players[pcode].get_info('all').g_wins += player['record']['w']
            self.all_players[pcode].get_info('all').g_losses += player['record']['l']

            codes = []
            for mon in player['team']:
                mon_code = mon['code']
                codes.append(mon_code)

                # pokemon all-time
                if mon_code not in self.all_players[pcode].get_info('all').mons:
                    self.all_players[pcode].get_info('all').mons[mon_code] = {
                        "name": mon['name'],
                        "code": mon_code,
                        "altcode": mon['altcode'],
                        "dex": mon['dex'],
                        "total": 0
                    }

                self.all_players[pcode].get_info('all').mons[mon_code]['total'] += 1

            for opp in player['rounds']:
                opp_code = opp['opp']

                if not len(opp_code):
                    continue

                change_opp = self.get_name_merge(opp_code)
                if change_opp:
                    opp_code = change_opp['code']

                if opp['opp'] not in self.all_players[pcode].get_info('all').rivals:
                    self.all_players[pcode].get_info('all').rivals[opp_code] = {
                        "code": opp_code,
                        "name": "",
                        "wins": 0,
                        "losses": 0,
                        "faced": 0,
                    }

                self.all_players[pcode].get_info('all').rivals[opp_code]['faced'] += 1

                if opp['res'] == 'W':
                    self.all_players[pcode].get_info('all').rivals[opp_code]['wins'] += 1
                elif opp['res'] == 'L':
                    self.all_players[pcode].get_info('all').rivals[opp_code]['losses'] += 1

            player_event_stage = 0
            if player['cut']:
                player_event_stage = 3
            elif player['p2']:
                player_event_stage = 2
            elif player['points'] > 0:
                player_event_stage = 1

            # player all events
            self.all_players[pcode].get_info('all').events[event_year_code] = {
                'code': event_code,
                'name': event['event']['name'],
                'year': year,
                'format': event['event']['format'],
                'players': event['event']['playerCount'],
                'result': player['place'],
                'points': player['points'],
                'w': player['record']['w'],
                'l': player['record']['l'],
                'team': codes,
                'stage': player_event_stage,
            }

    def get_name_merge(self, name):
        merge_into = None
        if name in self.name_updates['merge']:
            merge_into = self.name_updates['merge'][name]

        return merge_into


    def dump_all(self):
        for code, p_data in self.all_players.items():
            p_dir = f"{self.config['output_dir']}/player/{code[0]}/{code[0:2]}/{code[0:3]}/{code}"
            os.makedirs(p_dir, exist_ok=True)

            for period in p_data.info.keys():
                p_dict = p_data.to_dict(period)
                p_dict['events'] = list(p_dict['events'].values())
                p_dict['events'].reverse()

                fav_mons = sorted(
                    p_dict['mons'].values(),
                    key=lambda m: -m['total']
                )

                p_dict['mons'] = fav_mons[:5]

                rivals = sorted(
                    p_dict['rivals'].values(),
                    key=lambda p: -p['faced']
                )

                rivals = [ r for r in rivals if r['faced'] > 1 ]

                for rival in rivals:
                    rival['name'] = self.all_players[rival['code']].name

                p_dict['rivals'] = rivals[:5]

                with open(f"{p_dir}/{period}.json", 'w') as file:
                    file.write(json.dumps(p_dict, indent=2))


    """
    top players are (via criteria I totally made up):
    * players who have won 1 or more events and top cut at least two events
    * players who have reached day two on 60% of events (15+ events)
    * players who have reached day two on 80% of events (5+ events)
    * players who have top cut 25% of their events (5+ events)
    * players who have earned points at 90% and made day 2 at 50% of their events (10+ events)
    * players who have finished top 8 two or more times and cut at least one event
    """
    def is_top_player(self, p_dict):

        if p_dict['wins'] > 0 and p_dict['cut'] > 1:
            return True

        if p_dict['total'] >= 15 and p_dict['phase2'] / p_dict['total'] >= .6:
            return True

        if p_dict['total'] >= 5 and p_dict['phase2'] / p_dict['total'] >= .8:
            return True

        if p_dict['total'] >= 5 and p_dict['cut'] / p_dict['total'] >= .3:
            return True

        if p_dict['total'] >= 10 and p_dict['phase2'] / p_dict['total'] >= .5 and p_dict['points'] / p_dict['total'] >= .9:
            return True

        top_eight = 0
        for event in p_dict['events'].values():
            if event['result'] <= 8 and event['result'] != 0:
                top_eight += 1

        if top_eight >= 2 and p_dict['cut'] > 0:
            return True

        return False


    """
    attempt to score players (based on the above criteria)
    """
    def player_rank_points(self, p_dict):
        ...


    """
    this dumps only "top" players to prevent using it to be mean
    """
    def dump_index(self, key):
        index_data = []
        for code, p_data in self.all_players.items():
            p_dict = p_data.to_dict(key)
                
            if not self.is_top_player(p_dict):
                continue

            fav_mons = sorted(
                p_dict['mons'].values(),
                key=lambda m: -m['total']
            )

            if len(fav_mons) < 1:
                print(f"no fav mons for {p_dict['code']}?")
                continue

            p_dict['mon'] = fav_mons[0]['code']

            rivals = sorted(
                p_dict['rivals'].values(),
                key=lambda p: -p['faced']
            )

            rivals = [ r for r in rivals if r['faced'] > 1 ]

            for rival in rivals:
                rival['name'] = self.all_players[rival['code']].name

            p_dict['rivals'] = rivals[:5]

            index_data.append(p_dict)
            del index_data[len(index_data) - 1]['events']
            del index_data[len(index_data) - 1]['mons']

        # sort by total
        index_data = sorted(
            index_data,
            key=lambda p: -p['total']
        )

        p_dir = f"{self.config['output_dir']}/player"
        os.makedirs(p_dir, exist_ok=True)
        with open(f"{p_dir}/{key}.json", 'w') as file:
            file.write(json.dumps(index_data, indent=2))


    """
    dump the search json, which will be used by the javascript... it's big (~16800 lines)
    in the future I might make this more efficient to search via a tree or something
    like that, but I don't think there will be too many performance issues with it
    """
    def dump_full_search(self):
        search_data = []
        for code, p_data in self.all_players.items():
            events = list(p_data.get_info('all').events.values())
            recent = events[len(events) - 1]

            search_data.append({
                "name": p_data.name,
                "code": p_data.code,
                "total": p_data.get_info('all').total,
                "recent": f"{recent['name']} ({recent['year']})",
                "top": self.is_top_player(p_data.to_dict('all')),
            })

        search_data = sorted(
            search_data,
            key=lambda s: s['code']
        )

        p_dir = f"{self.config['output_dir']}/player"
        os.makedirs(p_dir, exist_ok=True)
        with open(f"{p_dir}/search.json", 'w') as file:
            file.write(json.dumps(search_data, indent=2))

