"""Build the offline choir songbook: .venv/bin/python choir_build/build_library.py.

Original Open Hymnal ABC files live in data/choir/sources, with notices intact.
New, simple practice harmonizations of public-domain melodies are CC0.
No network, runtime conversion tools, or soundfont service is needed by the app.
"""
import itertools
import json
import re
from pathlib import Path

from arrange_folk import arrange

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "choir"
SOURCES = DATA / "sources"
VOICES = [('S1V1', 'Soprano', 'S', 'treble'), ('S1V2', 'Alto', 'A', 'treble'),
          ('S2V1', 'Tenor', 'T', 'bass'), ('S2V2', 'Bass', 'B', 'bass')]


def slug(title):
    return re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')


def normalize(text, title, tempo):
    """Separate the four existing voices into four staves; retain first verse."""
    header = ['X:1', f'T:{title}', '%%score S1V1 | S1V2 | S2V1 | S2V2']
    for key in ['M', 'L']:
        header.append(next(l.split('%')[0].strip() for l in text.splitlines() if l.startswith(key + ':')))
    header += [f'Q:1/4={tempo}']
    header += [f'V:{v} name="{name}" snm="{short}" clef={clef}' for v, name, short, clef in VOICES]
    header.append(next(l.split('%')[0].strip() for l in text.splitlines() if l.startswith('K:')))
    body, verse_seen = [], False
    for line in text.splitlines():
        if line.startswith('[V:'):
            line = re.sub(r'\[Q:[^\]]+\]', '', line)
            line = re.sub(r'!(sintro|eintro)!', '', line)
            line = line.replace('!()!', '').replace('!ferm!', '!fermata!')
            # ABC Plus dotted ties/slurs and breath marks have no abcjs
            # equivalent. Preserve the actual tie, pitches and durations.
            line = line.replace('.-', '-').replace('.(', '(')
            line = re.sub(r"(?<=[ (])'(?=[A-Ga-g])", '', line)
            body.append(line)
            verse_seen = False
        elif line.startswith('w:') and not verse_seen:
            body.append(re.sub(r'^w:\s*1\.~?', 'w: ', line))
            verse_seen = True
    return '\n'.join(header + body) + '\n'


# These are newly written practice arrangements, not historical SATB editions.
# Each bar has its own chord; the upper melody retains its familiar rhythm.
# Jingle Bells and Oh! Susanna deliberately use their recognizable choruses.
TUNES = [
 ('Jingle Bells', 'Christmas carols', '4/4', 112, 'Chorus',
  'E E E2|E E E2|E G C3/2 D/|E4|F F F F|F E E E/ E/|E D D E|D2 G2|E E E2|E E E2|E G C3/2 D/|E4|F F F F|F E E E/ E/|G G F D|C4',
  'C C C C F C G G C C C C F C G C'),
 ('Deck the Halls', 'Christmas carols', '4/4', 104, 'Traditional Welsh melody',
  'G3/2 F/ E D|C D E C|D/ E/ F/ D/ E3/2 D/|C B, C2|G3/2 F/ E D|C D E C|D/ E/ F/ D/ E3/2 D/|C B, C2|D3/2 E/ F D|E3/2 F/ G D|E/ F/ G/ A/ B c|B A G2|G3/2 F/ E D|C D E C|A/ A/ A/ A/ G3/2 F/|E D C2',
  'C C G C C C G C G C C G C C F C'),
 ('We Wish You a Merry Christmas', 'Christmas carols', '3/4', 108, 'Traditional English melody',
  'G,|C C/ D/ C/ B,/|A, A, A,|D D/ E/ D/ C/|B, G, G,|E E/ F/ E/ D/|C A, G,/ G,/|A, D B,|C2 G,|C C C|B,2 B,|C B, A,|G,2 D|E D/ D/ C/ C/|G G, G,/ G,/|A, D B,|C2',
  'C C F D G C F G C C G F C C C G C'),
 ('Good King Wenceslas', 'Christmas carols', '4/4', 104, 'Traditional melody: Tempus adest floridum',
  'C C C D|C C G,2|A, G, A, B,|C2 C2|C C C D|C C G,2|A, G, A, B,|C2 C2|G G F E|D D C2|A, G, A, B,|C2 C2|G, G, A, B,|C C D2|G F E D|C2 F2|C4',
  'C C F C C C F C C G F C C C G F C'),
 ('Auld Lang Syne', 'Folk & familiar', '4/4', 88, 'Traditional Scottish melody · verse and refrain',
  'G,|C3/2 C/ C E|D3/2 C/ D E|C3/2 C/ E G|A3 A|G3/2 E/ E C|D3/2 C/ D E|C3/2 A,/ A, G,|C3 A|G3/2 E/ E C|D3/2 C/ D A|G3/2 E/ E G|A3 c|G3/2 E/ E C|D3/2 C/ D E|C3/2 A,/ A, G,|C3',
  'C C G C F C G F C C G C F C G F C'),
 ('Twinkle, Twinkle, Little Star', 'Folk & familiar', '4/4', 88, 'Traditional French melody',
  'C C G G|A A G2|F F E E|D D C2|G G F F|E E D2|G G F F|E E D2|C C G G|A A G2|F F E E|D D C2',
  'C F F G C C G C C F F C'),
 ('Frère Jacques', 'Folk & familiar', '4/4', 96, 'Traditional French round · harmonized practice version',
  'C D E C|C D E C|E F G2|E F G2|G/ A/ G/ F/ E C|G/ A/ G/ F/ E C|C G, C2|C G, C2',
  'C C C C C C G C'),
 ('Row, Row, Row Your Boat', 'Folk & familiar', '6/8', 120, 'Traditional round · harmonized practice version',
  'C3 C3|C2 D E3|E2 D E2 F|G6|c c c G G G|E E E C C C|G2 F E2 D|C6',
  'C C C C C C G C'),
 ('Mary Had a Little Lamb', 'Folk & familiar', '4/4', 96, 'Traditional melody',
  'E D C D|E E E2|D D D2|E G G2|E D C D|E E E E|D D E D|C4',
  'C C G C C C G C'),
 ('London Bridge', 'Folk & familiar', '4/4', 96, 'Traditional English melody',
  'G3/2 A/ G F|E F G2|D E F2|E F G2|G3/2 A/ G F|E F G2|D2 G2|E C3',
  'C C G C C C G C'),
 ('When the Saints Go Marching In', 'Folk & familiar', '4/4', 104, 'Traditional spiritual melody',
  'C E F|G4|z C E F|G4|z C E F|G2 E2|C2 E2|D4|z E E D|C2 C E|G G F2|F4|E2 F2|G2 E2|C2 D2|C4',
  'C C C C C C C G G C C F F C G C'),
 ('Oh! Susanna', 'Folk & familiar', '4/4', 112, 'Stephen Foster, 1848 · chorus only',
  'F2 F2|A A2 A|G G E C|D4|C/ D/ E G G3/2 A/|G E C3/2 D/ E/ E/|D C D E|C4',
  'F F C G C C G C'),
 ('Happy Birthday to You', 'Folk & familiar', '3/4', 96, 'Hill melody · simple practice setting',
  'G,/ G,/|A, G, C|B,2 G,/ G,/|A, G, D|C2 G,/ G,/|G E C|B, A, F/ F/|E C D|C2',
  'C F G G C C F G C'),
 ('God Save the King', 'Anthems', '3/4', 84, 'British anthem · traditional melody',
  'C C D|B,3/2 C/ D|E E F|E3/2 D/ C|D C B,|C3|G G G|G3/2 F/ E|F F F|F3/2 E/ D|E F/ E/ D/ C/|E3/2 F/ G|A F D|C3',
  'C G C C G C C C F G C C F C'),
 ('My Country, ’Tis of Thee', 'Anthems', '3/4', 88, 'America · traditional melody shared with God Save the King',
  'C C D|B,3/2 C/ D|E E F|E3/2 D/ C|D C B,|C3|G G G|G3/2 F/ E|F F F|F3/2 E/ D|E F/ E/ D/ C/|E3/2 F/ G|A F D|C3',
  'C G C C G C C C F G C C F C'),
]

PITCHES = {'C':0, 'D':2, 'E':4, 'F':5, 'G':7, 'A':9, 'B':11}
CHORDS = {'C':(0,4,7), 'F':(5,9,0), 'G':(7,11,2), 'D':(2,6,9)}


def midi_to_abc(m):
    accidental = ''
    if m % 12 not in PITCHES.values():
        accidental, m = '^', m - 1
    name = next(k for k, v in PITCHES.items() if v == m % 12)
    if m >= 72:
        return accidental + name.lower() + "'" * ((m - 72) // 12)
    return accidental + name + ',' * max(0, (60 - m + 11) // 12)


def harmonize(tune):
    title, category, meter, tempo, note, melody, chord_names = tune
    # 6/8 here uses eighth-note units; all other examples use quarter notes.
    unit = '1/8' if meter == '6/8' else '1/4'
    parts = [[], [], [], []]
    previous = (60, 52, 43)
    bars, chords = melody.split('|'), chord_names.split()
    assert len(bars) == len(chords), title
    for bar, chord_name in zip(bars, chords):
        chord = CHORDS[chord_name]
        out = [[], [], [], []]
        for token in bar.split():
            match = re.fullmatch(r"([A-Ga-gz])([,']*)([\d/]*)", token)
            assert match, token
            name, octave, duration = match.groups()
            if name == 'z':
                for part in out:
                    part.append(token)
                continue
            soprano = 60 + PITCHES[name.upper()] + (12 if name.islower() else 0) + 12 * (octave.count("'") - octave.count(','))
            candidates = []
            for alto, tenor, bass in itertools.product(range(48, 74), range(43, 66), range(36, 58)):
                if not (bass < tenor <= alto <= soprano and soprano - alto <= 12 and alto - tenor <= 12):
                    continue
                if any(p % 12 not in chord for p in (alto, tenor, bass)):
                    continue
                pcs = {p % 12 for p in (soprano, alto, tenor, bass)}
                missing = len(set(chord) - pcs)
                motion = sum(abs(a - b) for a, b in zip((alto, tenor, bass), previous))
                root_penalty = 0 if bass % 12 == chord[0] else 4
                # Prefer a complete chord, a root in the bass, and small steps.
                cost = missing * 25 + motion + root_penalty + abs(alto - 62) * .15
                candidates.append((cost, (alto, tenor, bass)))
            _, previous = min(candidates)
            for i, pitch in enumerate((soprano, *previous)):
                out[i].append(midi_to_abc(pitch) + duration)
        for i in range(4):
            parts[i].append(' '.join(out[i]))
    lines = ['X:1', f'T:{title}', f'C:Traditional/public-domain melody. New practice harmony: The Great Gallery, CC0.',
             f'M:{meter}', f'L:{unit}', f'Q:1/4={tempo}', '%%score S1V1 | S1V2 | S2V1 | S2V2']
    lines += [f'V:{v} name="{name}" snm="{short}" clef={clef}' for v, name, short, clef in VOICES]
    lines += ['K:C']
    for start in range(0, len(bars), 4):
        for i, (v, *_) in enumerate(VOICES):
            lines.append(f'[V:{v}] ' + ' | '.join(parts[i][start:start+4]) + (' |]' if start + 4 >= len(bars) else ' |'))
    return '\n'.join(lines) + '\n'


def build():
    songs = []
    provenance = json.loads((DATA / 'provenance.json').read_text())['scores']
    for source in sorted(SOURCES.glob('openhymnal-*.abc')):
        text = source.read_text()
        title = re.search(r'^T:\s*(.+)', text, re.M)[1].strip()
        assert re.search(r'C: copyright: public domain\.', text, re.I), source
        category = 'Christmas carols' if '%OHCATEGORY CHRISTMAS' in text else 'Hymns & spirituals'
        tempo = int(re.search(r'\[Q:1/4=(\d+)', text)[1]) if re.search(r'\[Q:1/4=(\d+)', text) else 88
        credits = ' '.join(l[3:].strip() for l in text.splitlines() if l.startswith(('C: ', 'S: ')))
        songs.append(dict(id=slug(title), title=title, category=category, tempo=tempo,
                          note='Four-part setting · first verse', credit=credits,
                          license='Public domain, as identified by the Open Hymnal Project. Original source notices are preserved in the downloadable ABC file.',
                          source=source.name, source_url=provenance[source.name]['source_url'],
                          abc=normalize(text, title, tempo)))
    for tune in TUNES:
        title, category, _, tempo, note, *_ = tune
        abc = harmonize(tune)
        filename = slug(title) + '.abc'
        (SOURCES / filename).write_text('% New practice arrangement dedicated to the public domain under CC0 1.0.\n% https://creativecommons.org/publicdomain/zero/1.0/\n' + abc)
        songs.append(dict(id=slug(title), title=title, category=category, tempo=tempo, note=note,
                          credit=note + '. Simple educational four-part harmony newly prepared for The Great Gallery. The melody is carried by soprano; accompaniment uses block chords. These are practice settings, not historical choir editions.',
                          license='Underlying melody: public domain. New practice harmony: CC0 1.0.',
                          source=filename, source_url='https://creativecommons.org/publicdomain/zero/1.0/', abc=abc))
    for melody in json.loads((Path(__file__).with_name('folk_melodies.json')).read_text()):
        abc = arrange(melody)
        filename = slug(melody['title']) + '.abc'
        rights = melody.get('rights_basis', 'Traditional melody, identified as traditional in the linked melody reference.')
        credit = (melody['reference_credit'] + ' ' + rights +
                  ' Newly prepared educational SATB harmony: The Great Gallery, CC0. '
                  'This is a simplified Western four-part practice setting, not a traditional-performance transcription or a historical choral edition. Repeats are written out; source accompaniment is not used.')
        (SOURCES / filename).write_text('% Melody reference: ' + melody['source_url'] + '\n% ' + rights +
                                      '\n% New practice harmony: CC0 1.0.\n% https://creativecommons.org/publicdomain/zero/1.0/\n' + abc)
        songs.append(dict(id=slug(melody['title']), title=melody['title'], category=melody['category'],
                          origin=melody['origin'], native_title=melody.get('native_title', ''),
                          aliases=melody.get('aliases', []), tempo=melody['tempo'],
                          note=melody.get('version', 'Traditional melody · new four-part practice setting'),
                          credit=credit, license='Underlying melody: public domain in the United States. New practice harmony: CC0 1.0.',
                          source=filename, source_url=melody['source_url'], abc=abc))
    assert len(songs) == 50 + len(json.loads((Path(__file__).with_name('folk_melodies.json')).read_text()))
    assert len({s['id'] for s in songs}) == len(songs)
    songs.sort(key=lambda s: s['title'].casefold())
    (DATA / 'library.json').write_text(json.dumps(songs, ensure_ascii=False, indent=2) + '\n')
    print(f'Built {len(songs)} four-part scores.')


if __name__ == '__main__':
    build()
