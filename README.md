# GRZS-analiza

Zbiranje javno objavljene statistike intervencij Gorske reševalne zveze
Slovenije (GRZS) za nadaljnjo analizo po letih.

## Podatki

Vir je [statistika nesreč GRZS](https://www.grzs.si/resevanje/statistika-nesrec/).
Stran trenutno ponuja podatke od leta 2006 naprej v petih agregiranih
tabelah, razčlenjenih po reševalnih enotah. To niso podatki o posameznih
nesrečah. GRZS navaja, da so zajete le intervencije, ki so administrativno
zaključene oziroma imajo oddana popolna poročila; podatki za tekoče leto so
zato lahko nepopolni.

Za prenos trenutno objavljenih let zaženite iz korenske mape repozitorija:

```bash
python3 scripts/fetch_stats.py
```

Skripta shrani izvirni odgovor za vsako leto v `data/raw/<leto>.json` in
posodobi `data/accidents.csv`. CSV je v dolgi obliki s stolpci `year`, `section`, `unit`, `metric` in
`value`; vsaka vrstica predstavlja eno metriko za eno reševalno enoto v
določenem letu. Za osvežitev novejših let uporabite na primer:

```bash
python3 scripts/fetch_stats.py --start-year 2020
```

Že shranjeni podatki za leta pred izbranim začetnim letom se ponovno uporabijo
iz `data/raw/`; leta od začetnega naprej se prenesejo znova.
V normaliziranem CSV je izvorno starostno polje `otroci18do55Let`
preimenovano v `osebe18do55Let`; vrednosti in surovi odgovori ostanejo
nespremenjeni. Zvezek sprejme tudi staro ime v starejših kopijah CSV.

## Analize

Zvezek [notebooks/grzs_analiza.ipynb](notebooks/grzs_analiza.ipynb) v
slovenščini in angleščini prikazuje trende intervencij, dejavnosti, vrste akcij,
poškodbe oziroma izide, starostne kategorije in primerjavo enot. Namenjen je
vsem, ki želijo raziskovati podatke. Analize uporabljajo lokalni
`data/accidents.csv`; posameznih nesreč ne prikazujejo.
Zadnje leto je lahko nepopolno, primerjava enot pa ni lestvica tveganja ali
uspešnosti. Pred uporabo preverite metodologijo in stanje podatkov pri GRZS.

Za pripravo okolja in zagon zvezka:

```bash
python3 -m pip install -r requirements-notebook.txt
jupyter lab notebooks/grzs_analiza.ipynb
```

Po osvežitvi podatkov z `scripts/fetch_stats.py` znova zaženite vse celice.

Grafi uporabljajo enoten slog, neposredne oznake vrednosti in ločene
trendne prikaze z neodvisnimi lestvicami. Oranžno ozadje označuje zadnje,
morebiti nepopolno leto. Starost je združena v tri širše skupine
(pod 10 + 10–18, 18–55, 55–70 + nad 70), neznana starost pa ostane ločena.
Točne razmejitve pri 18 in 55 letih sledijo izvornim kategorijam; iz
agregiranih podatkov jih ni mogoče spremeniti. Deleži vključujejo neznano
starost in niso deleži intervencij ali stopnje tveganja.
Legende, primerjave in trendne plošče so razvrščene od največje do najmanjše
vrednosti v primerjalnem letu; šest dejavnosti je še vedno izbranih po vsoti
vseh let. Barve starostnih skupin ostajajo enake v obeh prikazih.
Vrste reševalnih akcij primerjamo na skupni lestvici, polje `resevalcev`
pa je prikazano v ločenem stolpčnem grafu z lastno lestvico, ker ne šteje
intervencij in bi z večjimi vrednostmi zakrilo druge kategorije.

Zvezek izračuna tudi dolgoročno letno rast (CAGR) zaključenih intervencij:
`(končna / začetna vrednost) ** (1 / število let) - 1`.
Zadnje, lahko nepopolno leto je izključeno. Prikazana enakomerna rast
povezuje končni točki; ni regresija, napoved ali mera tveganja.
CAGR je občutljiv na izbiro obdobja in ne prikazuje vmesnih nihanj.

### Izbor grafov za poročilo

Za predstavitev začnite s povzetkom in dvema časovnima vrstama smrtnih
izidov v razdelku 9, nato uporabite trend intervencij, urejen starostni
prerez in po potrebi graf vrst akcij. Podrobni trendi dejavnosti, enote in
CAGR so podporno gradivo. Izogibajte se tortnim grafom prekrivajočih
kategorij, dvojnim osem in interpretaciji enot kot lestvice tveganja.

Polji `smrtGorska` in `smrtDrugo` ostajata ločeni; definicij ne razširjamo
in ju brez potrditve pri viru ne seštevamo. Povzetek vsebuje vrednosti
primerjalnega leta, absolutne spremembe glede na predhodno leto in mediane.
Zadnje leto je izključeno iz teh primerjav in korelacij.

Raziskovalna priloga primerja vsako smrtno polje z zaključenimi
intervencijami s Pearsonovim r, posebej za letna števila in absolutne
spremembe med zaporednimi leti. Vedno navede število parov in občutljivost
brez leta 2007, ki v tej kopiji vsebuje le 8 zaključenih intervencij.
To ni dokaz napake; glavna analiza leto ohrani. Spremembe ne premostijo
manjkajočih ali izločenih let. Manjkajoče metrike niso nadomeščene z ničlo.
Korelacije niso dokaz vzročnosti, učinkovitosti reševanja ali tveganja
smrti po starosti oziroma dejavnosti. Za to manjkajo povezave med
posameznimi dogodki, podatki o izpostavljenosti in potrjena primerljivost
poročanja. Spremembe zmanjšajo vpliv trenda, ne odpravijo pa vseh motenj.

Za zagon testov:

```bash
python3 -m unittest discover -s tests
```
