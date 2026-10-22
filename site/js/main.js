export default {
    data() {
        return {
            currentRoute: '',

            currentView: 'loading',

            showCredits: false,
            showTopPlayerCriteria: false,

            sitesNav: [],

            mons: [],
            monsLoaded: false,
            monsTimeframe: 'all',
            monsRuleset: 'all',
            monSearchStr: '',

            sorts: {
                mon: { column: 'total', dir: 1 },
                event: { column: 'order', dir: 1 },
                players: { column: 'total', dir: 1 },
            },

            monStats: {},
            monLoaded: false,
            monRegs: {},
            monSeasons: [],

            players: [],
            playersLoaded: false,

            playerSearchStr: '',
            playerSearch: [],

            topPlayerSearchStr: '',

            playerCode: '',
            player: {},
            playerLoaded: false,
            playerEventFilter: 'all',

            resultsFilter: {
                season: 'all',
                reg: 'all',
            },

            spriteCoords: {},

            seasons: [],
            rulesets: [],
        }
    },
    computed: {
        currentProps() {
            if (this.currentRoute == '') {
                return {};
            }

            let route = (this.currentRoute || '/');
            let chunks = [];

            if (route != '/') {
                chunks = route.split('/');
            } else {
                chunks = [ 'home' ];
            }

            switch (chunks[0] || '') {
                case 'home':
                    this.currentView = 'home';
                    break;
                case 'mons':
                    this.currentView = 'mons-stats';
                    break
                case 'mon':
                    this.currentView = 'mon';
                    break;
                case 'players':
                    if (chunks.length > 1 && chunks[1] == 'search') {
                        this.currentView = 'players-search';
                    } else {
                        this.currentView = 'players-list';
                    }
                    break;
                case 'player':
                    this.currentView = 'player';
                    this.playerCode = chunks[1] || '';
                    break;
                case 'events':
                    this.currentView = 'events';
                    break;

            }

            switch (this.currentView) {

                case 'home':
                    return {
                        showCredits: this.showCredits,
                    };

                case 'mons-stats':
                    return {
                        searchMons: this.searchMons,
                        monSearchStr: this.monSearchStr,
                        monsLoaded: this.monsLoaded,
                        monsTimeframe: this.monsTimeframe,
                        monsRuleset: this.monsRuleset,
                        seasons: this.seasons,
                        rulesets: this.rulesets,
                    };

                case 'mon':
                    return {
                        monStats: this.monStats,
                        monLoaded: this.monLoaded,
                        code: chunks[1],
                        monRegs: this.monRegs,
                        monSeasons: this.monSeasons,
                        resultsFilter: this.resultsFilter,
                        filteredEvents: this.filteredEvents,
                    };

                case 'players-list':
                    return {
                        searchTopPlayers: this.searchTopPlayers,
                        showTopPlayerCriteria: this.showTopPlayerCriteria,
                        topPlayerSearchStr: this.topPlayerSearchStr,
                    };

                case 'players-search':
                    return {
                        playerSearch: this.playerSearch,
                        searchPlayers: this.searchPlayers,
                        playerSearchStr: this.playerSearchStr,
                    };

                case 'player':
                    return {
                        playerCode: this.playerCode,
                        player: this.player,
                        playerEventFilter: this.playerEventFilter,
                    };

                case 'events':
                    return {
                    };
            }

            return {};
        },

        filteredEvents() {
            if (!this.monStats.events) {
                return [];
            }

            if (this.resultsFilter.season == 'all' && this.resultsFilter.reg == 'all') {
                return this.monStats.events;
            }
            
            return this.monStats.events.filter(event => {
                return (
                    (this.resultsFilter.season == 'all' || event.year == this.resultsFilter.season)
                    &&
                    (this.resultsFilter.reg == 'all' || event.format == this.resultsFilter.reg)
                );
            });
        },

        searchMons() {
            if (!this.monSearchStr.length) {
                return this.mons;
            }

            let searchStr = this.monSearchStr.toLowerCase();
            return this.mons.filter(
                mon => mon.code.includes(searchStr)
            );
        },

        searchPlayers() {
            let searchStr = this.playerSearchStr
                .toLowerCase()
                .normalize('NFD')
                .replace(/[\u0300-\u036f]/g, '');

            if (searchStr.length < 2) {
                return [];
            }

            return this.playerSearch.filter(
                pdata =>  pdata.search.includes(searchStr)
            );
        },

        searchTopPlayers() {
            if (!this.topPlayerSearchStr.length) {
                return this.players;
            }

            let searchStr = this.topPlayerSearchStr
                .toLowerCase()
                .normalize('NFD')
                .replace(/[\u0300-\u036f]/g, '');

            return this.players.filter(
                pdata => pdata.search.includes(searchStr)
            );
        },
    },

    methods: {
        init() {
            // main listener that lets us have nice looking urls
            window.addEventListener('click', (e) => {
                if (e.target && e.target.closest('a')) {
                    const anchor = e.target.closest('a');
                    if ('pass' in anchor.dataset && anchor.dataset.pass == 1) {
                        return;
                    }

                    if (e.metaKey || e.ctrlKey) {
                        return;
                    }

                    e.preventDefault();

                    const url = anchor.getAttribute('href');
                    history.pushState({ page: url }, null, url);

                    const chips = window.location.pathname.split('/');
                    this.setCurrentRoute(chips.slice(1).join('/'));
                }
            });

            // listen on back button events
            window.addEventListener('popstate', (e) => {
                if (e.state) {
                    const chips = e.state.page.split('/');
                    this.setCurrentRoute(chips.slice(1).join('/'));
                }
            });

            document.addEventListener("keydown", (e) => {
                // ctrl+F, F3, cmd+F use the built in searches
                if (e.code === 'F3' || ((e.ctrlKey || e.metaKey) && e.code === 'KeyF')) {
                    let searchElId = '';
                    if (this.currentView == 'mons-stats') {
                        searchElId = 'monNameSearch';
                    } else if (this.currentView == 'players-list') {
                        searchElId = 'topPlayerSearch';
                    } else if (this.currentView == 'players-search') {
                        searchElId = 'allPlayersSearch';
                    }

                    if (searchElId.length) {
                        document.getElementById(searchElId).focus();
                        e.preventDefault();
                    }
                }

                // clear/reset search
                if (event.key === 'Escape') {
                    if (this.currentView == 'mons-stats') {
                        this.monSearchStr = '';
                    } else if (this.currentView == 'players-list') {
                        this.topPlayerSearchStr = '';
                    } else if (this.currentView == 'players-search') {
                        this.playerSearchStr = '';
                    }
                }
            });

            // some init setup
            const chips = window.location.pathname.split('/');
            history.pushState({ page: window.location.pathname }, null, window.location.pathname);
            this.setCurrentRoute(chips.slice(1).join('/'));
        },

        setBootstrapData(data) {
            this.spriteCoords = data.spriteCoords;
            if (data?.info?.seasons) {
                this.seasons = data.info.seasons;
            }
            if (data?.info?.formats) {
                this.rulesets = data.info.formats.map(r => r.split(' ')[1]);
            }
            if (data?.sitesNav) {
                this.sitesNav = data.sitesNav;
            }
        },

        setCurrentRoute(route) {
            if (!route.length) {
                route = 'home';
            }
            this.currentRoute = route;
        },

        toggleCredits() {
            this.showCredits = !this.showCredits;
        },

        toggleTopPlayerCriteria() {
            this.showTopPlayerCriteria = !this.showTopPlayerCriteria;
        },

        getMons(timeframe) {
            // sligthly too complicated cache check
            if (this.monsLoaded) {
                if (
                    timeframe != 'all' &&
                    (timeframe == this.monsTimeframe || timeframe == this.monsRuleset)
                ) {
                    return;
                }

                if (
                    timeframe == 'all' && 
                    this.monsTimeframe == 'all' &&
                    this.monsRuleset == 'all'
                ) {
                    return;
                }
            }

            this.monsLoaded = false;

            fetch(`/api/v1/mons/${timeframe}`, {
                method: "GET",
                headers: { "Content-type": "application/json" },
            }).then(r => {
                if (!r.ok) {
                    // do something...
                }

                if (timeframe == 'all') {
                    this.monsTimeframe = 'all';
                    this.monsRuleset = 'all';
                } else if (timeframe.startsWith('reg-')) {
                    this.monsTimeframe = 'all';
                    this.monsRuleset = timeframe;
                } else {
                    this.monsTimeframe = timeframe;
                    this.monsRuleset = 'all';
                }

                this.monsLoaded = true;

                return r.json();
            }).then(d => {
                this.mons = d;

                this.mons.forEach(m => {
                    m.phase2Conversion = m.phase2 / m.total;
                    m.cutConversion = m.cut / m.phase2;
                });
            });
        },

        updateMonsTimeframe(timeframe) {
            this.monsTimeframe = timeframe;
        },

        updateMonsRuleset(ruleset) {
            this.monsRuleset = ruleset;
        },

        search(searchData) {
            const { type, search } = searchData;

            if (type == 'mons') {
                this.monSearchStr = search;
            } else if (type == 'player') {
                this.playerEventFilter = search;
            } else if (type == 'top-players') {
                this.topPlayerSearchStr = search;
            } else if (type == 'players') {
                this.playerSearchStr = search;
            }
        },

        getMon(code) {
            if (this.monStats.code == code) {
                return;
            }

            this.monLoaded = false;

            fetch(`/api/v1/mon/${code}`, {
                method: "GET",
                headers: { "Content-type": "application/json" },
            }).then(r => {
                if (!r.ok) {
                    // do something...
                }

                this.monLoaded = true;

                return r.json();
            }).then(d => {
                this.monStats = d;

                this.monStats.t = this.monStats.total
                this.monStats.total = this.monStats.total.toLocaleString();
                this.monStats.points = this.monStats.points.toLocaleString();
                this.monStats.phase2 = this.monStats.phase2.toLocaleString();
                this.monStats.cut = this.monStats.cut.toLocaleString();
                this.monStats.wins = this.monStats.wins.toLocaleString();

                this.monSeasons = [ ...new Set(this.monStats.events.map(i => i.year)) ];
                this.monRegs = [ ...new Set(this.monStats.events.map(i => i.format)) ];
            });
        },

        getPlayers() {
            if (this.playersLoaded) {
                return;
            }

            this.playersLoaded = false;

            fetch(`/api/v1/players/all`, {
                method: "GET",
                headers: { "Content-type": "application/json" },
            }).then(r => {
                if (!r.ok) {
                    // do something...
                }

                this.playersLoaded = true;

                return r.json();
            }).then(d => {
                this.players = d;

                this.players.forEach(p => {
                    p.ptsPct = p.points / p.total;
                    p.ph2Pct = p.phase2 / p.total;
                    p.cutPct = p.cut / p.total;
                    p.search = p.name
                        .toLowerCase()
                        .normalize('NFD')
                        .replace(/[\u0300-\u036f]/g, '');
                });
            });
        },

        getPlayerSearch() {
            if (Object.keys(this.playerSearch).length) {
                return;
            }

            fetch(`/api/v1/players/search`, {
                method: "GET",
                headers: { "Content-type": "application/json" },
            }).then(r => {
                if (!r.ok) {
                    // do something...
                }
                return r.json();
            }).then(d => {
                this.playerSearch = d;

                for (let i = 0; i < this.playerSearch.length; i++) {
                    this.playerSearch[i].search = this.playerSearch[i].name
                        .toLowerCase()
                        .normalize('NFD')
                        .replace(/[\u0300-\u036f]/g, '');
                }
            });
        },

        getPlayer(code) {
            if (this.player.code == code) {
                return;
            }

            this.playerLoaded = false;

            fetch(`/api/v1/player/${code}`, {
                method: "GET",
                headers: { "Content-type": "application/json" },
            }).then(r => {
                if (!r.ok) {
                    // do something...
                }

                this.playerLoaded = true;

                return r.json();
            }).then(d => {
                this.player = d;
            });
        },

        sortData(dataName, sortName, column) {
            if (column == this.sorts[sortName].column) {
                this.sorts[sortName].dir *= -1;
            } else {
                this.sorts[sortName].column = column;
                this.sorts[sortName].dir = 1;
            }

            let data = this[dataName];
            if (!data) {
                if (dataName == 'monStats.events') {
                    data = this.monStats.events;
                }
            }

            data.sort((a, b) => {
                if (a[column] < b[column]) {
                    return this.sorts[sortName].dir;
                } else if (a[column] > b[column]) {
                    return -this.sorts[sortName].dir;
                }
                return 0;
            });
        },

        getSortedClass(sortName, column) {
            if (this.sorts[sortName].column == column) {
                if (this.sorts[sortName].dir == -1) {
                    return "up";
                }
                if (this.sorts[sortName].dir == 1) {
                    return "down";
                }
            }
            return "";
        },

        updateResultFilter(filterBy, val) {
            this.resultsFilter[filterBy] = val;
        },

        // for mons / items
        getSpritePos(name) {
            let pos = this.spriteCoords[name] || [ 0, 0 ];
            return `-${pos[0]}px -${pos[1]}px`;
        },

        getPct(dec, precision) {
            if (isNaN(dec)) {
                return "-";
            }
            if (precision == undefined) {
                precision = 5;
            }
            return (dec * 100).toPrecision(dec >= 1 ? precision : dec < .1 ? precision - 2 : precision - 1).toLocaleString() + "%";
        },
    },
    components: {
        'loading': {
            template: '#loading-template',
        },
        'home': {
            template: '#home-template',
            props: [ 'showCredits' ],
            methods: {
                toggleCredits() {
                    this.$parent.toggleCredits();
                }
            }
        },
        'mons-stats': {
            template: '#mons-stats-template',
            props: [
                'currentRoute',
                'searchMons',
                'monSearchStr',
                'monsLoaded',
                'monsTimeframe',
                'monsRuleset',
                'seasons',
                'rulesets',
            ],
            emits: [
                'search',
            ],
            mounted: function() {
                let chunks = this.$parent.currentRoute.split('/');
                this.$parent.getMons(chunks[1]);
            },
            methods: {
                monsTimeframeStr() {
                    if (this.monsRuleset == 'all' && this.monsTimeframe == 'all') {
                        return "Combined Seasons";
                    }

                    if (this.monsRuleset != 'all') {
                        let lastChar = this.monsRuleset.length - 1;
                        if (this.monsRuleset[lastChar]) {
                            return `Regulation ${this.monsRuleset[lastChar].toUpperCase()} Events`;                        
                        }
                    }

                    return `${this.monsTimeframe} Season`;
                },
                searchForMons(e) {
                    this.$emit('search', { type: 'mons', search: e.target.value });
                },
                clearMonSearch() {
                    this.$emit('search', { type: 'mons', search: '' });
                },
                getSortedClass(column) {
                    return this.$parent.getSortedClass('mon', column);
                },
                getSpritePos(name) {
                    return this.$parent.getSpritePos(name);
                },
                getPct(dec, precision) {
                    return this.$parent.getPct(dec, precision);
                },
                sortStats(column) {
                    return this.$parent.sortData('mons', 'mon', column);
                },
                updateMonsFilter(e) {
                    const monsPath = `mons/${e.target.value}`;
                    history.pushState({ page: `/${monsPath}` }, null, `/${monsPath}`);
                    this.$parent.setCurrentRoute(monsPath);

                    this.$parent.getMons(e.target.value);
                },
            },
        },
        'mon': {
            template: '#mon-template',
            props: [
                'currentRoute',
                'monStats',
                'code',
                'monLoaded',
                'monRegs',
                'monSeasons',
                'resultsFilter',
                'filteredEvents',
            ],
            emits: [
                'search',
            ],
            mounted: function() {
                let chunks = this.$parent.currentRoute.split('/');
                this.$parent.getMon(chunks[1]);
            },
            methods: {
                getSortedClass(column) {
                    return this.$parent.getSortedClass('event', column);
                },
                updateSeasonFilter(e) {
                    this.$parent.updateResultFilter('reg', 'all');
                    return this.$parent.updateResultFilter('season', e.target.value);
                },
                updateRegFilter(e) {
                    this.$parent.updateResultFilter('season', 'all');
                    return this.$parent.updateResultFilter('reg', e.target.value);
                },
                sortEvents(column) {
                    return this.$parent.sortData('monStats.events', 'event', column);
                },
                getPct(dec, precision) {
                    return this.$parent.getPct(dec, precision);
                },
                getSpritePos(name) {
                    return this.$parent.getSpritePos(name);
                },
            },
        },
        'players-list': {
            template: '#players-list-template',
            props: [ 'searchTopPlayers', 'showTopPlayerCriteria', 'topPlayerSearchStr' ],
            emits: [ 'search' ],
            mounted: function() {
                this.$parent.getPlayers();
            },
            methods: {
                searchForTopPlayers(e) {
                    this.$emit('search', { type: 'top-players', search: e.target.value });
                },
                clearTopPlayerSearch() {
                    this.$emit('search', { type: 'top-players', search: '' });
                },
                toggleTopPlayerCriteria() {
                    this.$parent.toggleTopPlayerCriteria();
                },
                getPct(dec, precision) {
                    return this.$parent.getPct(dec, precision);
                },
                getSpritePos(name) {
                    return this.$parent.getSpritePos(name);
                },
                getSortedClass(column) {
                    return this.$parent.getSortedClass('players', column);
                },
                sortPlayers(column) {
                    return this.$parent.sortData('players', 'players', column);
                },
            }
        },
        'players-search': {
            template: '#players-search-template',
            props: [ 'playerSearch', 'searchPlayers', 'playerSearchStr' ],
            emits: [ 'search' ],
            mounted: function() {
                this.$parent.getPlayerSearch();
            },
            methods: {
                searchForPlayers(e) {
                    this.$emit('search', { type: 'players', search: e.target.value });
                },
                clearPlayerSearch() {
                    this.$emit('search', { type: 'players', search: '' });
                },
            }
        },
        'player': {
            template: '#player-template',
            props: [ 'player', 'playerCode', 'playerEventFilter' ],
            emits: [ 'search' ],
            mounted: function() {
                let chunks = this.$parent.currentRoute.split('/');
                this.$parent.getPlayer(chunks[1]);
                this.$emit('search', { type: 'player', search: 'all' });
            },
            watch: {
                playerCode(newCode, oldCode) {
                    this.$parent.getPlayer(newCode);
                    this.$emit('search', { type: 'player', search: 'all' });
                },
            },
            methods: {
                filterPlayerEvents(e) {
                    this.$emit('search', { type: 'player', search: e.target.value });
                },
                filterEvents(events) {
                    if (this.playerEventFilter == 'all') {
                        return events;
                    }

                    return events.filter(e => {
                        switch (this.playerEventFilter) {
                            case 'cut':
                                return e.stage >= 3;
                            case 'phase2':
                                return e.stage >= 2;
                            case 'points':
                                return e.stage >= 1;
                        }
                        return false;
                    });
                },
                getSpritePos(name) {
                    return this.$parent.getSpritePos(name);
                },
                getPct(dec, precision) {
                    return this.$parent.getPct(dec, precision);
                },
            }
        },
        'events': {
            template: '#events-template',
            props: [],
            emits: [ 'search' ],
            mounted: function() {
            },
            methods: {
            },
        },
    },
}
