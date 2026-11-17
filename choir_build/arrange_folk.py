"""New SATB practice settings from reviewed, public-domain melody event data.

The saved melody data contains pitches/rhythms, not source accompaniments or
engraving. Harmonies are newly generated educational settings, released as CC0.
Times use 96 integer units per whole note. Repeats are written out for practice.
"""
import itertools
from bisect import bisect_right
from collections import defaultdict
from fractions import Fraction

NATURAL = {'C': 0, 'D': 2, 'E': 4, 'F': 5, 'G': 7, 'A': 9, 'B': 11}
SIGNATURES = {'C': 0, 'G': 1, 'D': 2, 'A': 3, 'E': 4, 'B': 5,
              'F': -1, 'Bb': -2, 'Eb': -3, 'Ab': -4,
              'Am': 0, 'Em': 1, 'Bm': 2, 'F#m': 3, 'C#m': 4,
              'Dm': -1, 'Gm': -2, 'Cm': -3, 'Fm': -4}


def spelling(pitch, key, state):
    """Spell with a real key signature; explicitly cancel bar accidentals."""
    fifths = SIGNATURES[key]
    defaults = {n: 0 for n in NATURAL}
    for name in ('FCGDAEB' if fifths > 0 else 'BEADGCF')[:abs(fifths)]:
        defaults[name] = 1 if fifths > 0 else -1
    options = [(n, a) for n, pc in NATURAL.items() for a in (-1, 0, 1)
               if (pc + a) % 12 == pitch % 12]
    # Use key spellings first, then common flat/sharp spellings for alterations.
    preferred = {1: ('C', 1), 3: ('E', -1), 6: ('F', 1),
                 8: ('A', -1) if fifths < 0 else ('G', 1), 10: ('B', -1)}
    name, accidental = min(options, key=lambda p: (
        0 if p[1] == defaults[p[0]] else 1,
        0 if p == preferred.get(pitch % 12) else abs(p[1]) + 1))
    octave = (pitch - NATURAL[name] - accidental - 60) // 12
    identity = (name, octave)
    old = state.get(identity, defaults[name])
    prefix = '' if old == accidental else {-1: '_', 0: '=', 1: '^'}[accidental]
    state[identity] = accidental
    return prefix + (name.lower() + "'" * (octave - 1) if octave >= 1 else name + ',' * -octave)


def duration_suffix(units):
    duration = Fraction(units, 12)  # L:1/8
    if duration == 1:
        return ''
    if duration.denominator == 1:
        return str(duration.numerator)
    return f'{duration.numerator}/{duration.denominator}'


def notated_lengths(units):
    """Split long tied values into printable dotted notes; retain triplets."""
    standard = [192, 144, 96, 72, 48, 36, 24, 18, 12, 9, 6, 3]
    triplets = [128, 64, 32, 16, 8, 4, 2, 1]
    result = []
    while units:
        choices = standard if units % 3 == 0 else triplets
        part = next(n for n in choices if n <= units)
        result.append((part, part % 3 != 0))
        units -= part
    return result


def render_tokens(tokens):
    result, i = [], 0
    while i < len(tokens):
        token, triplet_units = tokens[i]
        if triplet_units and i + 2 < len(tokens) and all(t[1] == triplet_units for t in tokens[i:i+3]):
            result.append('(3' + ' '.join(t[0] for t in tokens[i:i+3]))
            i += 3
        else:
            result.append(('(3:2:1' if triplet_units else '') + token)
            i += 1
    return ' '.join(result)


def chord_family(key):
    root = key[:-1] if key.endswith('m') else key
    tonic = (NATURAL[root[0]] + (1 if '#' in root else -1 if 'b' in root else 0)) % 12
    degrees = [(0, (0, 3, 7)), (5, (0, 3, 7)), (7, (0, 4, 7)),
               (3, (0, 4, 7)), (8, (0, 4, 7)), (10, (0, 4, 7))] if key.endswith('m') else [
               (0, (0, 4, 7)), (5, (0, 4, 7)), (7, (0, 4, 7)),
               (9, (0, 3, 7)), (2, (0, 3, 7)), (4, (0, 3, 7))]
    return [tuple((tonic + degree + interval) % 12 for interval in intervals)
            for degree, intervals in degrees]


def arrange(song):
    key = song['key']
    num, den = map(int, song['meter'].split('/'))
    bar_units = 96 * num // den
    end = song['duration']
    notes = song['notes']
    assert end > 0 and notes
    pickup = song.get('pickup_units', 0)
    assert 0 <= pickup < bar_units
    bar_starts = [0] + list(range(pickup or bar_units, end, bar_units))
    bar_ends = bar_starts[1:] + [end]
    # Choose our own harmony from the melody, independent of source chord labels.
    family = chord_family(key)
    chords = {}
    for bar, (start, stop) in enumerate(zip(bar_starts, bar_ends)):
        weights = defaultdict(float)
        for note in notes:
            overlap = max(0, min(stop, note['start'] + note['duration']) - max(start, note['start']))
            weights[note['pitch'] % 12] += overlap * (1.4 if note['start'] == start else 1)
        def cost(chord):
            return sum(weight for pc, weight in weights.items() if pc not in chord) + (.6 if chord != family[0] else 0)
        chords[bar] = min(family, key=cost)
    # A genuine tonic at the final cadence makes the short practice settings settle.
    chords[len(bar_starts) - 1] = family[0]
    voicings = {}
    for chord in family:
        voicings[chord] = [p for p in itertools.product(range(53, 74), range(48, 66), range(40, 59))
                           if p[2] < p[1] <= p[0] and p[0] - p[1] <= 12
                           and all(n % 12 in chord for n in p)]
    previous = (60, 55, 48)
    events = []
    cursor = 0
    for note in notes:
        assert note['start'] >= cursor, f"Overlapping melody notes: {song['title']}"
        if note['start'] > cursor:
            events.append(dict(start=cursor, duration=note['start'] - cursor, pitches=None, lyric='*'))
        soprano = note['pitch']
        chord = chords[bisect_right(bar_starts, note['start']) - 1]
        options = [p for p in voicings[chord] if p[0] <= soprano and soprano - p[0] <= 16]
        assert options, f"Melody outside vocal arrangement range: {song['title']} {soprano}"
        def cost(parts):
            missing = len(set(chord) - {p % 12 for p in (soprano, *parts)})
            motion = sum(abs(a - b) for a, b in zip(parts, previous))
            # Avoid parallel fifths and octaves where another close voicing exists.
            parallel = 0
            for i, j in ((0, 1), (0, 2), (1, 2)):
                before, after = (previous[i] - previous[j]) % 12, (parts[i] - parts[j]) % 12
                if before == after and after in (0, 7) and (parts[i] - previous[i]) * (parts[j] - previous[j]) > 0:
                    parallel += 6
            return missing * 24 + motion + parallel + (0 if parts[2] % 12 == chord[0] else 3)
        previous = min(options, key=cost)
        events.append(dict(start=note['start'], duration=note['duration'], pitches=(soprano, *previous), lyric=note.get('lyric', '*')))
        cursor = note['start'] + note['duration']
    if cursor < end:
        events.append(dict(start=cursor, duration=end - cursor, pitches=None, lyric='*'))
    bars = [[[] for _ in range(4)] for _ in bar_starts]
    lyrics = [[] for _ in bars]
    states = [[{} for _ in range(4)] for _ in bars]
    for event in events:
        start, remaining = event['start'], event['duration']
        first = True
        while remaining:
            bar = bisect_right(bar_starts, start) - 1
            length = min(remaining, bar_ends[bar] - start)
            for piece, triplet in notated_lengths(length):
                for voice in range(4):
                    token = 'z' if event['pitches'] is None else spelling(event['pitches'][voice], key, states[bar][voice])
                    token += duration_suffix(piece * 3 // 2 if triplet else piece)
                    if event['pitches'] and remaining > piece:
                        token += '-'
                    bars[bar][voice].append((token, piece if triplet else 0))
                if event['pitches']:
                    lyrics[bar].append(event['lyric'] if first else '*')
                start += piece
                remaining -= piece
                first = False
    voices = [('S1V1', 'Soprano', 'S', 'treble'), ('S1V2', 'Alto', 'A', 'treble'),
              ('S2V1', 'Tenor', 'T', 'bass'), ('S2V2', 'Bass', 'B', 'bass')]
    lines = ['X:1', f"T:{song['title']}", 'C:New practice harmony: The Great Gallery (CC0).',
             f"M:{song['meter']}", 'L:1/8', f"Q:1/4={song['tempo']}", '%%score S1V1 | S1V2 | S2V1 | S2V2']
    lines += [f'V:{v} name="{name}" snm="{short}" clef={clef}' for v, name, short, clef in voices]
    lines.append(f'K:{key}')
    has_lyrics = any(n.get('lyric', '*') != '*' for n in notes)
    for start in range(0, len(bars), 4):
        for voice, (v, *_) in enumerate(voices):
            lines.append(f'[V:{v}] ' + ' | '.join(render_tokens(bar[voice]) for bar in bars[start:start + 4]) + (' |]' if start + 4 >= len(bars) else ' |'))
            if voice == 0 and has_lyrics:
                lines.append('w: ' + ' | '.join(' '.join(row) for row in lyrics[start:start + 4]))
    return '\n'.join(lines) + '\n'
