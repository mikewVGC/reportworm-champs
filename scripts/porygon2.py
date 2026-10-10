#!.venv/bin/python

import argparse
import json

from reportworm_builder.builder import Builder
from reportworm_builder.builder_cache import BuilderCache

from ops.players import PlayerStats
from ops.mons import MonStats
from ops.events import EventStats

from lib.util import get_regulation_code

def main():
    parser = argparse.ArgumentParser(
        prog="./scripts/porygon2.py",
        description="Porygon2 for building Reportworm Stats. Building stats requires having Reportworm Standings.",
    )
    parser.add_argument('--prod', action="store_true", help="Build production version")
    parser.add_argument('--build-only', action="store_true", help="Don't process any data, only rebuild the site")
    parser.add_argument('--process-only', action="store_true", help="Don't rebuild the site, only process data")

    cl = parser.parse_args()

    prod_mode = False

    config = {}
    try:
        with open("config.json") as file:
            config = json.loads(file.read())
    except FileNotFoundError:
        print("Could not find config.json, exiting")
        return

    try:
        with open("data/common/sites-nav-source.json") as file:
            sites_nav = json.loads(file.read())
            with open("data/common/sites-nav.json", "w") as ofile:
                ofile.write(json.dumps(sites_nav, separators=(',', ':')))
    except FileNotFoundError:
        print("Couldn't open sites-nav-source.json")

    if ('mode' in config and config['mode'] == 'prod') or cl.prod:
        prod_mode = True

    if not cl.process_only:
        print("Rebuilding site... ", end="")
        builder = Builder(config, {})
        builder.build()
        print("Done!")
    else:
        print("Process-only flag set, skipping rebuild")

    if cl.build_only:
        print("Build-only flag specified, exiting!")
        return

    manifest = {}
    try:
        with open(config['manifest']) as file:
            manifest = json.loads(file.read())
    except FileNotFoundError:
        print("Could not find manifest.json, exiting")
        return

    name_updates = {}

    try:
        with open("data/common/name-updates.json") as file:
            name_updates = json.loads(file.read())
    except FileNotFoundError:
        name_updates = {
            "merge": {},
        }

    player_stats = PlayerStats(config, prod_mode, name_updates)
    mon_stats = MonStats(config, prod_mode)
    event_stats = EventStats(config, prod_mode)

    for year in manifest['seasons']:
        season = []
        try:
            with open(f"{config['data_dir']}/{year}.json") as file:
                season = json.loads(file.read())
        except FileNotFoundError:
            print(f"[manifest] Couldn't open {year}.json, skipping")
            continue

        season.reverse()

        for event_info in season:
            if event_info['game'] != "Champions":
                continue

            event = {}
            try:
                with open(f"{config['data_dir']}/{year}/{event_info['code']}.json") as file:
                    event = json.loads(file.read())
            except FileNotFoundError:
                print(f"Couldn't open {year}/{event_info['code']}.json, skipping")
                continue

            player_stats.process_event(event, year)

            mon_stats.process_event(event, year)

            event_stats.process_event(event, year)

            usage = {}
            try:
                with open(f"{config['data_dir']}/{year}/{event_info['code']}-usage.json") as file:
                    usage = json.loads(file.read())
            except FileNotFoundError:
                print(f"Couldn't open {year}/{event_info['code']}-usage.json, skipping")
                continue

            mon_stats.process_usage(usage, event['event'], year)

    mon_stats.dump_all()
    mon_stats.dump_index('all')

    player_stats.dump_all()
    player_stats.dump_index('all')
    player_stats.dump_full_search()

    for year in mon_stats.seasons:
        mon_stats.dump_index(year)

    for fmt in mon_stats.formats:
        mon_stats.dump_index(get_regulation_code(fmt))

    mon_stats.dump_info()


if __name__ == "__main__":
    main()
