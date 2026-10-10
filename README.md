# Reportworm Champs (Stats for Pokemon Champions)

Reportworm... but stats. This project utilizes data from Reportworm Standings. As such it requires the full set of data from the site in order to function.

This is an updated and improved version of [reportworm-svstats](https://github.com/mikewVGC/reportworm-svstats), which covers only Scarlet & Voilet events.

## Running Locally

A `docker-compose.yaml` is included.

```
docker compose up -d
```

URL: http://localhost:88/

## Site Build

### Config

Create `config.json` in the project root with the following format (remove comments since they're not valid json):

```
{
    # these are required fields
    "manifest": "path-to-vgc-standings-data/manifest.json",
    "data_dir": "path-to-reportworm-standings/public/data",
    "output_dir": "public/data",

    # these are both optional
    "google_tag": "[optional google tag]",
    "mode": "dev"|"prod"
}
```

If the "mode" setting is set to "prod" the project will always build the production version. For the Google Analytics tag, include the characters after the `G-` in the `gtag('config', 'G-ABCDEF123');` line (so, just `ABCDEF123` in this example).

### Build

The script may throw some errors so you may need to create some directories in `public/data` manually first.

```
# build stats and site:
./scripts/porygon2.py

# build only the site (leave stats alone)
./scripts/porygon2.py --build-only
```

You can also use the `--process-only` to just build stats and leave the current build alone, but the site build should be pretty fast so there's probably no need for it. The `--prod` flag will run some production specific optimizations. You can permanently set this in the config file if you prefer.

## License

Reportworm Stats is licensed with the BSD license. See `LICENSE.md`
