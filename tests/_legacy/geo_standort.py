"""
geo_standort.py — Standortermittlung für Windlast-Rechner
Spittelmeister GmbH

Funktionen:
  - Adresse → Koordinaten (Nominatim/OpenStreetMap)
  - Koordinaten → Höhe ü. NN (open-elevation.com)
  - Koordinaten / Landkreis → Windzone (DIN EN 1991-1-4/NA.A)
  - Koordinaten / Landkreis → Geländekategorie (Heuristik)
"""

import re
import time
import requests
from dataclasses import dataclass
from typing import Optional, Tuple

# ─────────────────────────────────────────────────────────────────────────────
# WINDZONE-LOOKUP
# Quelle: DIN EN 1991-1-4/NA:2010-12, Anhang NA.A
# Schlüssel: Normierter Kreisname (lowercase, ohne Umlaute, ohne Sonderzeichen)
# Wert: Windzone (1, 2, 3, 4) oder "2*" für erhöhte Zone 2
# ─────────────────────────────────────────────────────────────────────────────

def _norm(s: str) -> str:
    """Normalisiert Kreis-/Stadtnamen für Lookup."""
    s = s.lower()
    s = s.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    s = re.sub(r"(landkreis|kreis|stadt|lk\.|sk\.|,.*)", "", s)
    s = re.sub(r"[^a-z0-9 ]", "", s)
    return s.strip()


# Windzone-Tabelle nach NA.A — Auswahl der wichtigsten Kreise/Städte
# Vollständige Liste: DIN EN 1991-1-4/NA:2010-12 Tabelle NA.A.1
WINDZONE_BY_KREIS: dict[str, int | str] = {

    # ── WINDZONE 1 ──────────────────────────────────────────────────────────
    # Bayern
    "ansbach":            1, "aschaffenburg":      1, "augsburg":          1,
    "bad kissingen":      1, "bamberg":             1, "bayreuth":          1,
    "berchtesgadener land": 1, "cham":              1, "coburg":            1,
    "dachau":             1, "deggendorf":          1, "dillingen":         1,
    "dingolfing landau":  1, "donau ries":          1, "ebersberg":         1,
    "eichstaett":         1, "erding":              1, "erlangen":          1,
    "erlangen hoechstadt":1, "forchheim":           1, "freising":          1,
    "freyung grafenau":   1, "fuerstenfeldbruck":   1, "fuerth":            1,
    "garmisch partenkirchen": 1, "gunzenhausen":    1, "hasberg":           1,
    "hof":                1, "ingolstadt":          1, "kaufbeuren":        1,
    "kelheim":            1, "kempten":             1, "kronach":           1,
    "kulmbach":           1, "landsberg am lech":   1, "landshut":          1,
    "lichtenfels":        1, "lindau":              1, "main spessart":     1,
    "miesbach":           1, "miltenberg":          1, "muehldorf":         1,
    "muenchen":           1, "neuburg schrobenhausen": 1, "neumarkt":        1,
    "neustadt aisch":     1, "neustadt waldnaab":   1, "nuernberg":         1,
    "nuernberger land":   1, "oberallgaeu":         1, "ostallgaeu":        1,
    "passau":             1, "pfaffenhofen":        1, "regen":             1,
    "regensburg":         1, "rhoen grabfeld":      1, "rosenheim":         1,
    "roth":               1, "rottal inn":          1, "schwabach":         1,
    "schweinfurt":        1, "starnberg":           1, "straubing":         1,
    "tirschenreuth":      1, "traunstein":          1, "unterallgaeu":      1,
    "weilheim schongau":  1, "weissenburg gunzenhausen": 1, "wuerzburg":     1,
    "wunsiedel":          1,

    # Baden-Württemberg
    "alb donau":          1, "biberach":            1, "bodenseekreis":     1,
    "breisgau hochschwarzwald": 1, "calw":           1, "emmendingen":      1,
    "enzkreis":           1, "esslingen":           1, "freiburg im breisgau": 1,
    "freudenstadt":       1, "goeppingen":          1, "heidelberg":        1,
    "heidenheim":         1, "heilbronn":           1, "hohenlohekreis":    1,
    "karlsruhe":          1, "konstanz":            1, "loerrach":          1,
    "ludwigsburg":        1, "main tauber kreis":   1, "mannheim":          1,
    "neckar odenwald kreis": 1, "ortenaukreis":      1, "ostalbkreis":       1,
    "pforzheim":          1, "rastatt":             1, "ravensburg":        1,
    "rems murr kreis":    1, "reutlingen":          1, "rhein neckar kreis": 1,
    "rottweil":           1, "schwarzwald baar kreis": 1, "sigmaringen":     1,
    "stuettgart":         1, "tuebingen":           1, "tuttlingen":        1,
    "ulm":                1, "waldshut":            1, "zollernalbkreis":   1,

    # Thüringen
    "altenburg":          1, "eichsfeld":           1, "erfurt":            1,
    "gotha":              1, "greiz":               1, "hildburghausen":    1,
    "ilmkreis":           1, "jena":                1, "kyffhaeuserkreis":  1,
    "nordhausen":         1, "saale holzland kreis": 1, "saale orla kreis": 1,
    "saalfeld rudolstadt": 1, "schmalkalden meiningen": 1, "soemmerda":     1,
    "sonneberg":          1, "suhl":                1, "unstrut hainich":   1,
    "wartburgkreis":      1, "weimar":              1, "weimarer land":     1,
    "eisenach":           1, "gera":                1, "weida":             1,

    # Sachsen
    "bautzen":            1, "chemnitz":            1, "erzgebirgskreis":   1,
    "goerlitz":           1, "leipzig":             1, "mittelsachsen":     1,
    "nordsachsen":        1, "saechsische schweiz": 1, "vogtlandkreis":     1,
    "zwickau":            1, "dresden":             1,

    # Sachsen-Anhalt (Süden)
    "burgenlandkreis":    1, "halle":               1, "mansfeld suedharz": 1,
    "saalekreis":         1,

    # Rheinland-Pfalz (Süden)
    "bernkastel wittlich": 1, "birkenfeld":         1, "cochem zell":       1,
    "daun":               1, "kusel":               1, "pirmasens":         1,
    "suedliche weinstrasse": 1, "trier":             1, "trier saarburg":    1,
    "zweibruecken":       1,

    # Saarland
    "merzig wadern":      1, "neunkirchen":         1, "saarbruecken":      1,
    "saarlouis":          1, "saarpfalz kreis":     1, "st wendel":         1,
    "voelklingen":        1,

    # ── WINDZONE 2 ──────────────────────────────────────────────────────────
    # NRW
    "aachen":             2, "bielefeld":           2, "bochum":            2,
    "bonn":               2, "borken":              2, "bottrop":           2,
    "coesfeld":           2, "dortmund":            2, "duesseldorf":       2,
    "duisburg":           2, "ennepe ruhr kreis":   2, "erftstadt":         2,
    "essen":              2, "euskirchen":           2, "gelsenkirchen":     2,
    "guetersloh":         2, "hagen":               2, "hamm":              2,
    "heinsberg":          2, "herford":             2, "herne":             2,
    "hochsauerlandkreis": 2, "hoxter":              2, "kleve":             2,
    "koeln":              2, "krefeld":             2, "leverkusen":        2,
    "lippe":              2, "maerkischer kreis":   2, "minden luebbecke":  2,
    "moenchengladbach":   2, "muelheim":            2, "muenster":          2,
    "oberbergischer kreis": 2, "oberhausen":        2, "olpe":              2,
    "paderborn":          2, "recklinghausen":      2, "remscheid":         2,
    "rhein erft kreis":   2, "rhein sieg kreis":    2, "rheinisch bergischer kreis": 2,
    "siegen wittgenstein": 2, "soest":              2, "solingen":          2,
    "steinfurt":          2, "unna":                2, "viersen":           2,
    "warendorf":          2, "wesel":               2, "wuppertal":         2,

    # Hessen
    "bergstrasse":        2, "darmstadt":           2, "darmstadt dieburg": 2,
    "frankfurt am main":  2, "fulda":               2, "giessen":           2,
    "gross gerau":        2, "hersfeld rotenburg":  2, "hochsauerlandkreis": 2,
    "hochtaunuskreis":    2, "kassel":              2, "lahn dill kreis":   2,
    "limburg weilburg":   2, "main kinzig kreis":   2, "main taunus kreis": 2,
    "marburg biedenkopf": 2, "odenwaldkreis":       2, "offenbach":         2,
    "rheingau taunus kreis": 2, "schwalm eder kreis": 2, "vogelsbergkreis": 2,
    "waldeck frankenberg": 2, "werra meissner kreis": 2, "wetteraukreis":   2,
    "wiesbaden":          2,

    # Niedersachsen (Inland)
    "celle":              2, "cuxhaven":            2, "gifhorn":           2,
    "goslar":             2, "goettingen":          2, "hameln pyrmont":    2,
    "hannover":           2, "helmstedt":           2, "hildesheim":        2,
    "holzminden":         2, "leer":                2, "lueneburg":         2,
    "nienburg":           2, "northeim":            2, "oldenburg":         2,
    "osnabrueck":         2, "osterholz":           2, "peine":             2,
    "rotenburg wuemme":   2, "schaumburg":          2, "soltau fallingbostel": 2,
    "uelzen":             2, "verden":              2, "wolfenbuettel":     2,
    "wolfsburg":          2,

    # Brandenburg / Berlin
    "berlin":             2, "barnim":              2, "dahme spreewald":   2,
    "elbe elster":        2, "havelland":           2, "maerkisch oderland": 2,
    "oberhavel":          2, "oberspreewald lausitz": 2, "oder spree":      2,
    "ostprignitz ruppin": 2, "potsdam":             2, "potsdam mittelmark": 2,
    "prignitz":           2, "spree neisse":        2, "teltow flaeming":   2,
    "uckermark":          2,

    # Sachsen-Anhalt (Norden/Mitte)
    "altmarkkreis salzwedel": 2, "anhalt bitterfeld": 2, "boerde":         2,
    "dessau":             2, "jerichower land":     2, "magdeburg":         2,
    "salzlandkreis":      2, "stasfurt":            2, "stendal":           2,
    "wittenberg":         2,

    # Rheinland-Pfalz (Norden/Mitte)
    "ahrweiler":          2, "altenkirchen":        2, "alzey worms":       2,
    "bad duerkheim":      2, "bad kreuznach":       2, "donnersbergkreis":  2,
    "eifelkreis bitburg pruem": 2, "germersheim":   2, "kaiserslautern":    2,
    "koblenz":            2, "ludwigshafen":        2, "mainz":             2,
    "mainz bingen":       2, "mayen koblenz":       2, "neustadt weinstrasse": 2,
    "rhein hunsrueck kreis": 2, "rhein lahn kreis": 2, "rhein pfalz kreis": 2,
    "speyer":             2, "vulkaneifel":         2, "westerwaldkreis":   2,
    "worms":              2,

    # Mecklenburg-Vorpommern (Inland)
    "ludwigslust parchim": 2, "mecklenburgische seenplatte": 2,
    "rostock":            2, "schwerin":            2,

    # ── WINDZONE 3 ──────────────────────────────────────────────────────────
    # Küstennahe Gebiete
    "dithmarschen":       3, "flensburg":           3, "herzogtum lauenburg": 3,
    "kiel":               3, "luebeck":             3, "nordfriesland":     3,
    "ostholstein":        3, "pinneberg":           3, "ploen":             3,
    "rendsburg eckernfoerde": 3, "schleswig flensburg": 3, "segeberg":       3,
    "steinburg":          3, "stormarn":            3,
    "emden":              3, "leer":                3, "aurich":            3,
    "friesland":          3, "wittmund":            3,
    "bremerhaven":        3, "bremen":              3, "hamburg":           3,
    "vorpommern greifswald": 3, "vorpommern ruegen": 3,
    "rostock land":       3,

    # ── WINDZONE 4 ──────────────────────────────────────────────────────────
    # Nordseeinseln + exponierte Küste
    "nordfriesland inseln": 4,
    "sylt":               4,
    "foehr":              4,
    "amrum":              4,
    "helgoland":          4,
    "borkum":             4,
    "juist":              4,
    "norderney":          4,
    "baltrum":            4,
    "langeoog":           4,
    "spiekeroog":         4,
    "wangerooge":         4,
}

# Fallback: Windzone nach Bundesland (Mittelwert / häufigster Wert)
WINDZONE_BY_BUNDESLAND: dict[str, int] = {
    "Bayern":                    1,
    "Baden-Württemberg":         1,
    "Thüringen":                 1,
    "Sachsen":                   1,
    "Saarland":                  1,
    "Rheinland-Pfalz":           2,
    "Hessen":                    2,
    "Nordrhein-Westfalen":       2,
    "Brandenburg":               2,
    "Berlin":                    2,
    "Sachsen-Anhalt":            2,
    "Niedersachsen":             2,
    "Mecklenburg-Vorpommern":    2,
    "Hamburg":                   3,
    "Bremen":                    3,
    "Schleswig-Holstein":        3,
}


# ─────────────────────────────────────────────────────────────────────────────
# DATENKLASSE ERGEBNIS
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class StandortErgebnis:
    adresse_eingabe: str
    adresse_gefunden: str
    lat: float
    lon: float
    hoehe_uNN: float
    hoehe_quelle: str
    windzone: int | str
    windzone_quelle: str
    bundesland: str
    county: str
    gelaende: str   # "binnen" oder "kueste"
    gelaende_begruendung: str


# ─────────────────────────────────────────────────────────────────────────────
# GEOCODING
# ─────────────────────────────────────────────────────────────────────────────

def _reverse_postcode(lat: float, lon: float, headers: dict, timeout: int = 6) -> str:
    """Reverse geocoding → PLZ via Nominatim.
    Nominatim Policy: max 1 req/sec → sleep vor dem Call.
    """
    try:
        time.sleep(1.1)  # Nominatim rate limit: 1 req/sec
        url = "https://nominatim.openstreetmap.org/reverse"
        params = {"lat": lat, "lon": lon, "format": "json", "addressdetails": 1, "zoom": 18}
        resp = requests.get(url, params=params, headers=headers, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        return data.get("address", {}).get("postcode", "")
    except Exception:
        return ""


def geocode_adresse(adresse: str, timeout: int = 8) -> dict:
    """
    Adresse → Koordinaten + Admin-Info via Nominatim (OpenStreetMap).
    Gibt dict mit lat, lon, display_name, county, state zurück.
    """
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q": adresse,
        "format": "json",
        "limit": 1,
        "addressdetails": 1,
        "countrycodes": "de",
    }
    headers = {"User-Agent": "SpittelmeisterWindlast/1.0 (statik@spittelmeister.de)"}
    resp = requests.get(url, params=params, headers=headers, timeout=timeout)
    resp.raise_for_status()
    data = resp.json()
    if not data:
        raise ValueError(f"Adresse nicht gefunden: {adresse}")
    r = data[0]
    addr = r.get("address", {})
    county = (
        addr.get("county") or
        addr.get("city") or
        addr.get("town") or
        addr.get("municipality") or ""
    )
    state = addr.get("state", "")
    # PLZ aus allen möglichen Feldern extrahieren
    postcode = (
        addr.get("postcode") or
        addr.get("postal_code") or
        ""
    )

    # Fallback: reverse geocode — NUR wenn PLZ nicht gefunden (+ rate-limit-konform)
    if not postcode:
        postcode = _reverse_postcode(float(r["lat"]), float(r["lon"]), headers, timeout)
    else:
        # Auch bei bekannter PLZ kurz warten (Nominatim Policy)
        time.sleep(0.5)

    return {
        "lat":          float(r["lat"]),
        "lon":          float(r["lon"]),
        "display_name": r.get("display_name", ""),
        "county":       county,
        "state":        state,
        "postcode":     postcode,
    }


# ─────────────────────────────────────────────────────────────────────────────
# HÖHE Ü. NN
# ─────────────────────────────────────────────────────────────────────────────

def get_hoehe_uNN(lat: float, lon: float, timeout: int = 8) -> Tuple[float, str]:
    """
    Koordinaten → Höhe ü. NN in Metern.
    Primär: open-elevation.com (SRTM)
    Fallback: opentopodata.org
    """
    # Primär: open-elevation
    try:
        url = "https://api.open-elevation.com/api/v1/lookup"
        resp = requests.post(
            url,
            json={"locations": [{"latitude": lat, "longitude": lon}]},
            timeout=timeout
        )
        resp.raise_for_status()
        h = resp.json()["results"][0]["elevation"]
        return float(h), "open-elevation.com (SRTM)"
    except Exception:
        pass

    # Fallback: opentopodata
    try:
        url = f"https://api.opentopodata.org/v1/srtm30m?locations={lat},{lon}"
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        h = resp.json()["results"][0]["elevation"]
        return float(h), "opentopodata.org (SRTM30m)"
    except Exception:
        pass

    return None, "nicht verfügbar"


# ─────────────────────────────────────────────────────────────────────────────
# WINDZONE-LOOKUP
# ─────────────────────────────────────────────────────────────────────────────


# ─────────────────────────────────────────────────────────────────────────────
# WINDZONE-LOOKUP NACH PLZ
# Quelle: DIN EN 1991-1-4/NA:2010-12, Anhang NA.A (Tabelle nach Gemeinde)
# Fokus: WZ 3 und WZ 4 (Küstengebiete), wo Kreislevel ungenau ist.
# WZ 1/2 Inland: Kreis-Fallback ausreichend.
# ─────────────────────────────────────────────────────────────────────────────

# ── WINDZONE 4: Nordseeinseln ────────────────────────────────────────────────
WINDZONE_BY_PLZ: dict[str, int] = {
    # Sylt
    "25980": 4, "25992": 4, "25996": 4, "25997": 4, "25999": 4,
    # Föhr
    "25938": 4,
    # Amrum
    "25946": 4,
    # Helgoland
    "27498": 4,
    # Borkum
    "26757": 4,
    # Juist
    "26571": 4,
    # Norderney
    "26548": 4,
    # Baltrum
    "26579": 4,
    # Langeoog
    "26465": 4,
    # Spiekeroog
    "26474": 4,
    # Wangerooge
    "26486": 4,
    # Pellworm
    "25849": 4,
    # Nordstrand
    "25845": 4,
    # Hallig-Inseln
    "25859": 4, "25863": 4, "25869": 4, "25871": 4, "25872": 4,
    # Fehmarn
    "23769": 3,

    # ── WZ 4: Exponierte Küstenbereiche ──────────────────────────────────────
    # Cuxhaven Küste + Elbe-Mündung (PLZ 276xx und 275xx Küste)
    "27472": 4, "27474": 4, "27476": 4, "27478": 4,  # Cuxhaven Stadt
    "27619": 4, "27624": 4, "27628": 4,               # Cuxhaven Küstenorte (Bramel etc.)
    "27616": 4, "27612": 4,                            # Cuxhaven Küste

    # ── WZ 3: Küste Schleswig-Holstein (Nordsee) ─────────────────────────────
    "25335": 3, "25336": 3, "25337": 3,  # Elmshorn Umgebung
    "25348": 3, "25349": 3,              # Stör-Mündung
    "25355": 3, "25358": 3, "25361": 3,  # Wilster / Itzehoe Marsh
    "25364": 3, "25365": 3, "25368": 3, "25370": 3,
    "25371": 3, "25373": 3, "25376": 3, "25377": 3,
    "25379": 3, "25381": 3, "25382": 3, "25384": 3,
    "25386": 3, "25387": 3, "25388": 3, "25389": 3,
    # Dithmarschen Küste
    "25693": 3, "25694": 3, "25693": 3, "25704": 3, "25709": 3,
    "25710": 3, "25712": 3, "25715": 3, "25718": 3, "25719": 3,
    "25721": 3, "25724": 3, "25725": 3, "25727": 3, "25729": 3,
    "25761": 3, "25764": 3, "25767": 3, "25770": 3, "25774": 3,
    "25776": 3, "25779": 3, "25782": 3, "25785": 3, "25786": 3,
    "25788": 3, "25791": 3, "25792": 3, "25794": 3, "25795": 3,
    "25797": 3, "25799": 3, "25801": 3, "25813": 3, "25821": 3,
    "25826": 3, "25832": 3, "25836": 3, "25840": 3, "25842": 3,
    "25843": 3, "25845": 3, "25850": 3, "25851": 3, "25852": 3,
    "25853": 3, "25855": 3, "25856": 3, "25858": 3, "25860": 3,
    "25862": 3, "25864": 3, "25866": 3, "25867": 3, "25868": 3,
    "25870": 3, "25873": 3, "25874": 3, "25876": 3, "25878": 3,
    "25879": 3, "25881": 3, "25882": 3, "25884": 3, "25885": 3,
    "25887": 3, "25889": 3, "25890": 3, "25891": 3, "25893": 3,
    "25894": 3, "25895": 3, "25897": 3, "25899": 3,
    # Flensburg + Schleswig
    "24937": 3, "24939": 3, "24941": 3, "24943": 3, "24944": 3,
    "24837": 3, "24848": 3, "24850": 3, "24852": 3, "24853": 3,
    "24855": 3, "24857": 3, "24860": 3, "24861": 3, "24863": 3,
    "24864": 3, "24866": 3, "24867": 3, "24869": 3, "24870": 3,
    "24872": 3, "24873": 3, "24875": 3, "24876": 3, "24878": 3,
    "24879": 3, "24881": 3, "24882": 3, "24884": 3, "24885": 3,
    "24887": 3, "24888": 3, "24890": 3, "24891": 3, "24893": 3,
    "24894": 3, "24896": 3, "24897": 3, "24899": 3,
    # Kiel + Ostsee SH
    "24103": 3, "24105": 3, "24106": 3, "24107": 3, "24109": 3,
    "24111": 3, "24113": 3, "24114": 3, "24116": 3, "24118": 3,
    "24119": 3, "24143": 3, "24145": 3, "24146": 3, "24147": 3,
    "24148": 3, "24149": 3, "24159": 3,
    # Lübeck
    "23552": 3, "23554": 3, "23556": 3, "23558": 3, "23560": 3,
    "23562": 3, "23564": 3, "23566": 3, "23568": 3, "23569": 3,
    "23570": 3,
    # Ostholstein Küste
    "23701": 3, "23714": 3, "23715": 3, "23717": 3, "23719": 3,
    "23730": 3, "23738": 3, "23743": 3, "23744": 3, "23746": 3,
    "23747": 3, "23749": 3, "23758": 3, "23769": 3,

    # ── WZ 3: Hamburg ─────────────────────────────────────────────────────────
    "20095": 3, "20097": 3, "20099": 3, "20144": 3, "20146": 3,
    "20148": 3, "20149": 3, "20251": 3, "20253": 3, "20255": 3,
    "20257": 3, "20259": 3, "20354": 3, "20355": 3, "20357": 3,
    "20359": 3, "20457": 3, "20459": 3, "20535": 3, "20537": 3,
    "20539": 3,

    # ── WZ 3: Bremen / Bremerhaven ────────────────────────────────────────────
    "27568": 3, "27570": 3, "27572": 3, "27574": 3, "27576": 3,
    "27578": 3, "27580": 3, "27582": 3, "27583": 3,  # Bremerhaven
    "28195": 3, "28197": 3, "28199": 3, "28201": 3, "28203": 3,
    "28205": 3, "28207": 3, "28209": 3, "28211": 3, "28213": 3,
    "28215": 3, "28217": 3, "28219": 3, "28237": 3, "28239": 3,
    "28259": 3, "28277": 3, "28279": 3, "28307": 3, "28309": 3,
    "28325": 3, "28327": 3, "28329": 3, "28355": 3, "28357": 3,
    "28359": 3, "28717": 3, "28719": 3, "28721": 3, "28723": 3,
    "28725": 3, "28755": 3, "28757": 3, "28759": 3, "28777": 3,
    "28779": 3, "28790": 3, "28816": 3,

    # ── WZ 3: Niedersachsen Küste (Ostfriesland, Cuxhaven Inland) ─────────────
    # Emden
    "26721": 3, "26723": 3, "26725": 3,
    # Aurich
    "26603": 3, "26605": 3, "26607": 3,
    # Norden
    "26506": 3, "26524": 3, "26529": 3, "26532": 3, "26534": 3,
    "26535": 3, "26548": 3, "26553": 3, "26556": 3, "26559": 3,
    "26571": 3, "26579": 3,
    # Leer
    "26789": 3, "26802": 3, "26810": 3, "26817": 3, "26826": 3,
    "26831": 3, "26835": 3, "26836": 3, "26842": 3, "26844": 3,
    "26845": 3, "26847": 3, "26849": 3,
    # Wilhelmshaven
    "26382": 3, "26384": 3, "26386": 3, "26388": 3, "26389": 3,
    # Friesland
    "26316": 3, "26340": 3, "26345": 3, "26349": 3, "26409": 3,
    "26419": 3, "26427": 3, "26434": 3, "26441": 3, "26446": 3,
    "26452": 3, "26465": 3, "26474": 3, "26486": 3,
    # Wittmund
    "26409": 3, "26452": 3, "26487": 3, "26489": 3,
    # Cuxhaven Inland (WZ 2 → 3 Übergang)
    "21502": 3, "21514": 3, "21516": 3,  # Lauenburg Elbe-Küste
    "27299": 3, "27318": 3, "27321": 3, "27324": 3, "27327": 3,
    "27330": 3, "27333": 3, "27336": 3, "27339": 3, "27404": 3,
    "27412": 3, "27419": 3, "27422": 3, "27432": 3, "27442": 3,
    "27446": 3, "27449": 3,
    # Stade
    "21680": 3, "21682": 3, "21683": 3, "21684": 3, "21685": 3,
    "21698": 3, "21702": 3, "21706": 3, "21709": 3, "21710": 3,
    "21712": 3, "21714": 3, "21717": 3, "21720": 3, "21723": 3,
    "21726": 3, "21727": 3, "21730": 3, "21732": 3, "21734": 3,
    "21737": 3, "21739": 3, "21745": 3, "21755": 3, "21762": 3,
    "21769": 3, "21770": 3, "21772": 3, "21775": 3, "21776": 3,
    "21781": 3, "21782": 3, "21785": 3, "21787": 3, "21789": 3,

    # ── WZ 3: Mecklenburg-Vorpommern Küste ────────────────────────────────────
    # Rostock
    "18055": 3, "18057": 3, "18059": 3, "18069": 3, "18106": 3,
    "18107": 3, "18109": 3, "18119": 3, "18147": 3, "18181": 3,
    "18182": 3, "18184": 3, "18190": 3, "18196": 3,
    # Rügen
    "18528": 3, "18546": 3, "18551": 3, "18556": 3, "18565": 3,
    "18569": 3, "18573": 3, "18574": 3, "18581": 3, "18586": 3,
    "18587": 3, "18609": 3,
    # Stralsund + Vorpommern-Rügen
    "18435": 3, "18437": 3, "18439": 3, "18442": 3, "18445": 3,
    "18461": 3, "18465": 3, "18469": 3, "18461": 3,
    # Greifswald + Vorpommern-Greifswald
    "17489": 3, "17491": 3, "17493": 3, "17495": 3, "17498": 3,
    "17449": 3, "17454": 3, "17459": 3,
    # Usedom
    "17406": 3, "17419": 3, "17424": 3, "17429": 3, "17440": 3,
    "17449": 3,
    # Wismar + Nordwestmecklenburg Küste
    "23966": 3, "23968": 3, "23970": 3, "23972": 3, "23974": 3,
    "23992": 3, "23996": 3, "23999": 3,
}

# PLZ-Präfix-Lookup (3-stellig) für schnellen Bereichs-Check
# Nur WZ 3 und 4 Küstenbereiche — Rest fällt auf Kreis zurück
WINDZONE_BY_PLZ_PREFIX: dict[str, int] = {
    # Schleswig-Holstein Nordseeküste
    "258": 3, "259": 3, "256": 3, "257": 3,
    "249": 3, "248": 3,
    # Kiel
    "241": 3,
    # Lübeck
    "235": 3,
    # Hamburg gesamt
    "200": 3, "201": 3, "202": 3, "203": 3, "204": 3,
    "205": 3, "206": 3, "207": 3, "208": 3, "209": 3,
    "210": 3, "211": 3, "212": 3, "213": 3, "214": 3,
    "215": 3, "216": 3, "217": 3, "218": 3, "219": 3,
    "220": 3, "221": 3, "222": 3,
    # Bremerhaven
    "275": 3,
    # Bremen
    "281": 3, "282": 3, "283": 3, "284": 3, "285": 3, "287": 3,
    # Ostfriesland / Nordseeküste NDS
    "264": 3, "265": 3, "267": 3, "263": 3, "261": 3,
    # Cuxhaven Küste
    "274": 3, "276": 3,
    # Stade / Elbe
    "216": 3, "217": 3,
    # Rügen / Vorpommern
    "185": 3, "184": 3, "183": 3,
    "174": 3, "175": 3,
    # Wismar / NW-Mecklenburg
    "239": 3,
    # Nordseeinseln
    "259": 4, "269": 4, "274": 4,
}

def get_windzone(county: str, state: str, postcode: str = "") -> Tuple[int | str, str]:
    """
    PLZ (primär) / Kreis / Bundesland → Windzone nach DIN EN 1991-1-4/NA.A
    PLZ-Lookup hat Priorität — wichtig für Küstenkreise mit gemischten WZ.
    """
    # 0. PLZ-Lookup (höchste Priorität)
    if postcode and postcode in WINDZONE_BY_PLZ:
        wz = WINDZONE_BY_PLZ[postcode]
        return wz, f"PLZ {postcode} → Tabelle NA.A"

    # PLZ-Präfix (erste 3 Stellen)
    if postcode and len(postcode) >= 3:
        prefix = postcode[:3]
        if prefix in WINDZONE_BY_PLZ_PREFIX:
            wz = WINDZONE_BY_PLZ_PREFIX[prefix]
            return wz, f"PLZ-Bereich {prefix}xx → Tabelle NA.A"

    # 1. Suche in Kreis-Tabelle
    key = _norm(county)
    if key in WINDZONE_BY_KREIS:
        return WINDZONE_BY_KREIS[key], f"Kreis '{county}' → Tabelle NA.A"

    # Teilstring-Suche (z.B. "Landkreis Würzburg" → "wuerzburg")
    for k, v in WINDZONE_BY_KREIS.items():
        if k in key or key in k:
            return v, f"Kreis '{county}' (Teilübereinstimmung '{k}') → Tabelle NA.A"

    # 2. Fallback Bundesland
    if state in WINDZONE_BY_BUNDESLAND:
        wz = WINDZONE_BY_BUNDESLAND[state]
        return wz, f"Bundesland '{state}' (Standardwert, Kreis nicht in Tabelle)"

    return 2, "Standardwert WZ 2 (Kreis/Bundesland nicht gefunden)"


# ─────────────────────────────────────────────────────────────────────────────
# GELÄNDEKATEGORIE (HEURISTIK)
# ─────────────────────────────────────────────────────────────────────────────

def get_gelaende(county: str, state: str, windzone) -> Tuple[str, str]:
    """
    Einfache Heuristik: Küstengebiete → 'kueste', sonst 'binnen'.
    """
    kueste_states = {"Schleswig-Holstein", "Hamburg", "Bremen", "Mecklenburg-Vorpommern"}
    kueste_kreise_keys = {
        "nordfriesland", "dithmarschen", "pinneberg", "steinburg",
        "rendsburg eckernfoerde", "flensburg", "kiel", "luebeck",
        "ostholstein", "ploen", "herzogtum lauenburg", "stormarn",
        "aurich", "friesland", "wittmund", "emden", "bremerhaven",
        "vorpommern ruegen", "vorpommern greifswald", "rostock",
        "cuxhaven",
    }
    key = _norm(county)
    if key in kueste_kreise_keys or int(windzone) >= 3:
        return "kueste", "Küsten- oder Inselgebiet (WZ ≥ 3)"
    if state in kueste_states:
        return "kueste", f"Bundesland {state} → Küste"
    return "binnen", "Binnenland"


# ─────────────────────────────────────────────────────────────────────────────
# HAUPTFUNKTION
# ─────────────────────────────────────────────────────────────────────────────

def standort_ermitteln(adresse: str) -> StandortErgebnis:
    """
    Vollständige Standortermittlung aus Adressstring.
    Gibt StandortErgebnis zurück.
    """
    # Geocoding
    geo = geocode_adresse(adresse)
    lat, lon = geo["lat"], geo["lon"]
    county    = geo["county"]
    state     = geo["state"]

    # Höhe
    hoehe, hoehe_quelle = get_hoehe_uNN(lat, lon)

    # Windzone
    postcode = geo.get("postcode", "")
    windzone, wz_quelle = get_windzone(county, state, postcode)

    # Geländekategorie
    gelaende, gel_begruendung = get_gelaende(county, state, windzone)

    return StandortErgebnis(
        adresse_eingabe=adresse,
        adresse_gefunden=geo["display_name"],
        lat=lat,
        lon=lon,
        hoehe_uNN=hoehe,
        hoehe_quelle=hoehe_quelle,
        windzone=windzone,
        windzone_quelle=wz_quelle,
        bundesland=state,
        county=county,
        gelaende=gelaende,
        gelaende_begruendung=gel_begruendung,
    )
