"""
Offline tool: turn the Seattle Symphony season brochure PDF into data/seattle_symphony_season.json
(title, dates, performers, program). The Benaroya scraper merges that file in to fill in programs
that the website's detail pages didn't give us.

    pip install pypdf          # only needed for this tool, not by the web app
    python music_brochure.py "/path/to/Seattle Symphony 2026-2027 Season Brochure.pdf" [--year 2026]

Brochure layout (per concert):  "OCTOBER 22 OR 24" / title / "Name role" lines / "Seattle Symphony" /
"COMPOSER Work" lines / prose blurb.  Dates carry no year or time: the year comes from the season
(Sep-Dec = start year, Jan-Aug = next year); times come from the website feed.
"""

import json
import os
import re
import sys

MONTHS = ["JANUARY", "FEBRUARY", "MARCH", "APRIL", "MAY", "JUNE", "JULY", "AUGUST",
          "SEPTEMBER", "OCTOBER", "NOVEMBER", "DECEMBER"]
MON = "|".join(MONTHS)
HEADER = re.compile(rf"^((?:{MON})\s+\d{{1,2}}(?:\s*(?:,|OR|AND|&|–|-)\s*(?:(?:{MON})\s+)?\d{{1,2}})*)\s*$")
ROLE = re.compile(r"\s(?:conductor|piano|violin|viola|cello|bass|soprano|mezzo-soprano|mezzo|alto|tenor|baritone|bass-baritone|"
                  r"flute|saxophone|clarinet|oboe|bassoon|trumpet|horn|harp|guitar|organ|percussion|vocals|narrator|"
                  r"host|banjo|theremin|electronics|commentator)s?\s*$", re.I)
ORCH = re.compile(r"^(Seattle Symphony|Seattle Symphony Chorale|Seattle Symphony Chamber Players|Seattle Symphony and Chorale)", re.I)
def split_composer(line):
    """'R. STRAUSS Also sprach Zarathustra' -> ('R. STRAUSS', 'Also sprach Zarathustra').
    Composer = leading all-caps tokens (plus 'R.'-style initials); work = the rest."""
    toks, i = line.split(), 0
    while i < len(toks):
        t = toks[i]
        core = re.sub(r"[^A-Za-zÀ-ÿŁŚł]", "", t)
        if (core and core.isupper() and len(core) > 1) or re.match(r"^[A-Z]\.$", t) or t.startswith("-"):
            i += 1
        else:
            break
    if i == 0 or i >= len(toks) or not any(len(re.sub(r"[^A-Za-zÀ-ÿ]", "", t)) > 2 for t in toks[:i]):
        return None
    rest = " ".join(toks[i:])
    rest = re.sub(r"^\(arr\.[^)]*\)\s*", "", rest)
    return " ".join(toks[:i]), rest


# "Eric Schweikert timpani", "Mei Gui Zhang soprano": 2-4 capitalised words + optional lowercase role
NAME_ROLE = re.compile(r"^[A-ZÀ-Ý][\w'’.\-]*(?: [A-ZÀ-Ý][\w'’.\-]*){1,3}(?: [a-z\-]{3,20})?\s*$")


def is_performer(l):
    """'Xian Zhang conductor' yes; 'Tchaikovsky’s First Piano' (wrapped title) no."""
    return bool(ORCH.match(l) or (ROLE.search(" " + l) and not re.search(r"['’]s\b", l)))


def _titlecase_name(s):
    s = re.sub(r"\s*-\s*", "-", s.strip())
    return " ".join(("-".join(p.capitalize() for p in w.split("-")) if len(w) > 2 else w) for w in s.split())


def _dates(header, season_year):
    out, cur_month = [], None
    for tok in re.findall(rf"(?:{MON})|\d{{1,2}}", header):
        if tok in MONTHS:
            cur_month = MONTHS.index(tok) + 1
        else:
            y = season_year if cur_month >= 9 else season_year + 1
            out.append(f"{y}-{cur_month:02d}-{int(tok):02d}")
    return out


def parse(text, season_year):
    concerts = []
    for page in re.split(r"=====PAGE \d+=====", text):
        lines = [l.rstrip() for l in page.split("\n")]
        i = 0
        while i < len(lines):
            m = HEADER.match(lines[i].strip())
            if not m:
                i += 1
                continue
            dates = _dates(m.group(1), season_year)
            i += 1
            title, performers, program, state = [], [], [], "title"
            while i < len(lines) and not HEADER.match(lines[i].strip()):
                raw, l = lines[i], lines[i].strip()
                i += 1
                if not l:
                    continue
                if state == "title":
                    if is_performer(l):
                        state = "perf"
                    elif l.isupper():
                        continue  # banner such as "NATURE IN MUSIC FESTIVAL"
                    else:
                        title.append(l)
                        continue
                if state == "perf":
                    if is_performer(l) or (NAME_ROLE.match(l) and not split_composer(l)):
                        performers.append(re.sub(r"(?<= )([A-Z]) (?=[a-z]{6})", r"\1", re.sub(r"\s{2,}", " ", l)))
                        continue  # (orchestra/chorale lines can come in a run; program starts after them)
                    state = "prog"
                if state == "prog":
                    cm = split_composer(l)
                    cont = raw[:1] in (" ", "\t") or l[0] in "(abcdefghijklmnopqrstuvwxyz"
                    if cm and not cont:
                        program.append({"composer": _titlecase_name(cm[0]), "work": cm[1].strip()})
                    elif cont and program and len(l) < 80:
                        program[-1]["work"] += " " + l
                    else:
                        break  # blurb prose starts
            if title and (program or performers):
                concerts.append({
                    "title": " ".join(title),
                    "dates": dates,
                    "performers": performers,
                    "program": program,
                })
    merged = {}
    for c in concerts:
        k = re.sub(r"[^a-z0-9]", "", c["title"].lower())
        m = merged.setdefault(k, c)
        if m is not c:
            m["dates"] = sorted(set(m["dates"]) | set(c["dates"]))
            if len(c["program"]) > len(m["program"]):
                m["program"], m["performers"] = c["program"], c["performers"]
    return sorted(merged.values(), key=lambda c: c["dates"][0])


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    year = int(sys.argv[sys.argv.index("--year") + 1]) if "--year" in sys.argv else 2026
    args = [a for a in args if not a.isdigit()]
    from pypdf import PdfReader
    reader = PdfReader(args[0])
    text = "".join(f"\n=====PAGE {i + 1}=====\n{p.extract_text() or ''}" for i, p in enumerate(reader.pages))
    concerts = parse(text, year)
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "seattle_symphony_season.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(concerts, f, ensure_ascii=False, indent=1)
    print(f"{len(concerts)} concerts -> {out}")


if __name__ == "__main__":
    main()
