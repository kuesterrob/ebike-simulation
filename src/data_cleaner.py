from itertools import groupby

# Ortsteile, die die API uneinheitlich statt der Gemeinde liefert.
ALIASES = {
    "Endach": "Kufstein",
    "Unterlangkampfen": "Langkampfen",
    "Mariatal": "Kramsach",
}

class Cleaner():

    def clean_places(places:list, values=None, min_size:int=15, aliases:dict=ALIASES) -> list:
        """Entfernt kurze Ortssprünge; min_size in Einheiten von values bzw. Punkten."""
        p = [aliases.get(v, v) for v in places]
        size = lambda r: values[r[2] - 1] - values[r[1]] if values is not None else r[2] - r[1]
        while True:
            runs, i = [], 0
            for n, g in groupby(p):
                runs.append((n, i, i := i + len(list(g))))
            k = min(runs, key=size)
            if len(runs) < 2 or size(k) >= min_size:
                return p
            i = runs.index(k)
            nb = max((runs[j] for j in (i - 1, i + 1) if 0 <= j < len(runs)), key=size)
            p[k[1]:k[2]] = [nb[0]] * (k[2] - k[1])