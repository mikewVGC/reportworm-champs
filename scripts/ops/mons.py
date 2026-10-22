
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field

from lib.formes import (
    get_mon_alt_from_code,
    get_mega_form,
    is_mega_form,
    get_mega_from_stone,
)
from lib.util import get_regulation_code

class Mon():
    def __init__(self, name = "", code = "", dex = 0) -> None:
        self.name = name
        self.code = code
        self.dex = dex
        self.info = {}

    def add_info(self, key):
        if str(key) not in self.info:
            self.info[str(key)] = MonInfo()

    def get_info(self, key):
        self.add_info(str(key))
        return self.info[str(key)]

    def to_dict(self, key):
        return {
            "name": self.name,
            "code": self.code,
            "dex": self.dex,
            **self.get_info(key).__dict__,
        }


@dataclass
class MonInfo():
    total:int = 0
    points:int = 0
    phase2:int = 0
    cut:int = 0
    wins:int = 0
    events:dict = field(default_factory=dict)
    players:dict = field(default_factory=dict)
    items:dict = field(default_factory=dict)
    teras:dict = field(default_factory=dict)


class MonStats():
    def __init__(self, config, prod:bool = False) -> None:
        self.all_mons = {}
        self.config = config

        self.seasons = []
        self.formats = []

        self.indent = 0 if prod else 2


    def get_categories(self):
        return self.categories


    def process_event(self, event:dict, year:int):
        event_code = event['event']['code']
        event_format = event['event']['format']

        if year not in self.seasons:
            self.seasons.append(year)

        if event_format not in self.formats:
            self.formats.append(event_format)

        for player in event['standings'].values():
            team = player['team']
            pcode = player['code']

            for mon in team:
                mon_code = mon['code']

                mega_form = get_mega_form(mon_code, mon)
                if len(mega_form):
                    mon_code = mega_form

                # general setup + overall total
                if mon_code not in self.all_mons:
                    dex = mon['dex']
                    if len(mega_form):
                        dex = get_mon_alt_from_code(mon_code)

                    self.all_mons[mon_code] = Mon(
                        code=mon_code,
                        name=mon['altname'] if len(mega_form) else mon['name'],
                        dex=dex,
                    )

                if pcode not in self.all_mons[mon_code].get_info('all').players:
                    self.all_mons[mon_code].get_info('all').players[pcode] = {
                        "code": pcode,
                        "name": player['name'],
                        "count": 0,
                    }

                self.all_mons[mon_code].get_info('all').players[pcode]['count'] += 1

                if player['place'] == 1 and event_code != "worlds-day-1":
                    self.all_mons[mon_code].get_info('all').wins += 1
                    self.all_mons[mon_code].get_info(year).wins += 1

                # store more granular data about each event
                event_key = f"{year}-{event_code}"
                if event_key not in self.all_mons[mon_code].get_info('all').events:
                    self.all_mons[mon_code].get_info('all').events[event_key] = {
                        "code": event_code,
                        "name": event['event']['name'],
                        "year": year,
                        "order": len(self.all_mons[mon_code].get_info('all').events.values()),
                        "format": event_format,
                        "total": 0,
                        "points": 0,
                        "phase2": 0,
                        "cut": 0,
                        "best_finish": 9999,
                    }

                if player['place'] < self.all_mons[mon_code].get_info('all').events[event_key]['best_finish']:
                    self.all_mons[mon_code].get_info('all').events[event_key]['best_finish'] = player['place']


    def process_usage(self, usage:dict, event_info:dict, year:int):
        event_key = f"{year}-{event_info['code']}"
        ruleset = get_regulation_code(event_info['format'])
        for base_mon in usage:
            forms = [ base_mon, *base_mon['forms'] ]

            if len(forms) > 1:
                for mon in forms:
                    # adjust the counts for the base form
                    if is_mega_form(mon['code']):
                        forms[0]['counts']['total'] -= mon['counts']['total']
                        forms[0]['counts']['points'] -= mon['counts']['points']
                        forms[0]['counts']['phase2'] -= mon['counts']['phase2']
                        forms[0]['counts']['cut'] -= mon['counts']['cut']

            for mon in forms:
                mon_code = mon['code']
                is_mega = is_mega_form(mon_code)

                if mon_code not in self.all_mons:
                    # mon doesn't exist at all
                    print(f"Unable to find '{mon_code}' in usage, skipping")
                    continue

                if event_key not in self.all_mons[mon_code].get_info('all').events:
                    # mon doesn't exist specifically on this event
                    print(f"'{mon_code}' not in event '{event_key}', skipping")
                    continue

                # event specific stats
                self.all_mons[mon_code].get_info('all').events[event_key]['total'] = mon['counts']['total']
                self.all_mons[mon_code].get_info('all').events[event_key]['totpct'] = mon['counts']['total'] / event_info['playerCount']
                self.all_mons[mon_code].get_info('all').events[event_key]['points'] = mon['counts']['points']
                self.all_mons[mon_code].get_info('all').events[event_key]['ptspct'] = mon['counts']['points'] / event_info['points']
                self.all_mons[mon_code].get_info('all').events[event_key]['phase2'] = mon['counts']['phase2']
                if event_info['phase2Count']:
                    self.all_mons[mon_code].get_info('all').events[event_key]['p2pct'] = mon['counts']['phase2'] / event_info['phase2Count']
                self.all_mons[mon_code].get_info('all').events[event_key]['cut'] = mon['counts']['cut']
                if event_info['cutCount']:
                    self.all_mons[mon_code].get_info('all').events[event_key]['cutpct'] = mon['counts']['cut'] / event_info['cutCount']

                # alltime stats
                self.all_mons[mon_code].get_info('all').total += mon['counts']['total']
                self.all_mons[mon_code].get_info('all').points += mon['counts']['points']
                self.all_mons[mon_code].get_info('all').phase2 += mon['counts']['phase2']
                self.all_mons[mon_code].get_info('all').cut += mon['counts']['cut']

                # item stats
                if 'items' not in mon:
                    mon['items'] = []

                for item in mon['items']:
                    icode = item['code']
                    is_mega_item = get_mega_from_stone(icode)
                    m_item_code = mon_code
                    if is_mega_item or mon_code == is_mega_item:
                        m_item_code = is_mega_item

                    if icode not in self.all_mons[m_item_code].get_info('all').items:
                        self.all_mons[m_item_code].get_info('all').items[icode] = {
                            "name": item['name'],
                            "code": icode,
                            "count": 0,
                        }

                    self.all_mons[m_item_code].get_info('all').items[icode]['count'] += item['count']['total']

                # tera stats
                if 'teras' in mon:
                    for tera in mon['teras']:
                        tera_type = tera['name']
                        if tera_type not in self.all_mons[mon_code].get_info('all').teras:
                            self.all_mons[mon_code].get_info('all').teras[tera_type] = {
                                "name": tera_type,
                                "count": 0,
                            }

                        self.all_mons[mon_code].get_info('all').teras[tera_type]['count'] += tera['count']['total']

                # season stats
                self.all_mons[mon_code].get_info(year).total += mon['counts']['total']
                self.all_mons[mon_code].get_info(year).points += mon['counts']['points']
                self.all_mons[mon_code].get_info(year).phase2 += mon['counts']['phase2']
                self.all_mons[mon_code].get_info(year).cut += mon['counts']['cut']

                # ruleset / format stats
                self.all_mons[mon_code].get_info(ruleset).total += mon['counts']['total']
                self.all_mons[mon_code].get_info(ruleset).points += mon['counts']['points']
                self.all_mons[mon_code].get_info(ruleset).phase2 += mon['counts']['phase2']
                self.all_mons[mon_code].get_info(ruleset).cut += mon['counts']['cut']


    def dump_all(self):
        for code, mon_data in self.all_mons.items():
            mon_dir = f"{self.config['output_dir']}/mon/{code[0]}/{code}"
            os.makedirs(mon_dir, exist_ok=True)

            mon_dict = mon_data.to_dict('all')
            mon_dict['events'] = list(mon_dict['events'].values())

            soldiers = sorted(
                mon_dict['players'].values(),
                key=lambda p: -p['count']
            )

            del mon_dict['players']

            mon_dict['soldiers'] = soldiers[:12]

            mon_dict['items'] = sorted(
                mon_dict['items'].values(),
                key=lambda p: -p['count']
            )

            mon_dict['items'] = mon_dict['items'][:4]

            mon_dict['teras'] = sorted(
                mon_dict['teras'].values(),
                key=lambda p: -p['count']
            )

            mon_dict['teras'] = mon_dict['teras'][:4]

            with open(f"{mon_dir}/all.json", 'w') as file:
                file.write(json.dumps(mon_dict, indent=self.indent))


    def dump_index(self, key):
        index_data = []
        for code, mon_data in self.all_mons.items():
            mon_dict = mon_data.to_dict(key)
            if mon_dict['total'] == 0:
                continue

            index_data.append(mon_dict)
            del index_data[len(index_data) - 1]['events']

        # sort by total
        index_data = sorted(
            index_data,
            key=lambda mon: -mon['total']
        )

        mon_dir = f"{self.config['output_dir']}/mon"
        with open(f"{mon_dir}/{key}.json", 'w') as file:
            file.write(json.dumps(index_data, indent=self.indent))


    def dump_info(self):
        data_dir = f"{self.config['common_data_dir']}"
        with open(f"{data_dir}/info.json", 'w') as file:
            file.write(
                # this needs to be dumped without any formatting
                json.dumps({ "seasons": self.seasons, "formats": self.formats }, separators=(',', ':'))
            )
