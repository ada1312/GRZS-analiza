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

Za zagon testov:

```bash
python3 -m unittest discover -s tests
```
