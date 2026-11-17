"""One-time import of public-domain single-line melody references (not audio).

Use: .venv/bin/python choir_build/import_midi_melodies.py manifest.json source-dir
Only written pitches and rhythms are retained; MIDI sound, dynamics, tempo,
articulation and accompaniment are discarded. Output is reviewed melody data.
"""
import hashlib
import json
import struct
import sys
from pathlib import Path


def read_melody(data):
    assert data[:4] == b'MThd'
    header_len = int.from_bytes(data[4:8], 'big')
    _, count, ticks_per_quarter = struct.unpack('>HHH', data[8:14])
    assert not ticks_per_quarter & 0x8000
    offset = 8 + header_len
    tracks = []
    for _ in range(count):
        assert data[offset:offset+4] == b'MTrk'
        length = int.from_bytes(data[offset+4:offset+8], 'big')
        track = data[offset+8:offset+8+length]
        offset += 8 + length
        pos, tick, running = 0, 0, None
        active, notes = {}, []
        def varlen():
            nonlocal pos
            value = 0
            while True:
                byte = track[pos]
                pos += 1
                value = (value << 7) | (byte & 127)
                if byte < 128:
                    return value
        while pos < len(track):
            tick += varlen()
            status = track[pos]
            if status >= 128:
                pos += 1
                if status < 240:
                    running = status
            else:
                status = running
            if status == 255:
                pos += 1  # meta event type
                length = varlen()
                pos += length
            elif status in (240, 247):
                length = varlen()
                pos += length
            else:
                assert status is not None
                kind, channel = status >> 4, status & 15
                a = track[pos]
                b = track[pos+1] if kind not in (12, 13) else 0
                pos += 1 if kind in (12, 13) else 2
                identity = (channel, a)
                if kind == 9 and b:
                    active[identity] = tick
                elif kind == 8 or (kind == 9 and b == 0):
                    start = active.pop(identity)
                    notes.append(dict(start=round(start / ticks_per_quarter * 24),
                                      duration=round((tick-start) / ticks_per_quarter * 24), pitch=a))
        if notes:
            tracks.append(sorted(notes, key=lambda n: n['start']))
    return tracks


if __name__ == '__main__':
    manifest = json.loads(Path(sys.argv[1]).read_text())
    source = Path(sys.argv[2])
    results = json.loads((source / 'abc-melodies.json').read_text())
    for item in manifest:
        if item['format'] != 'midi':
            continue
        data = (source / item['file']).read_bytes()
        tracks = read_melody(data)
        assert len(tracks) == 1 or 'melody_track' in item, f"Choose a reviewed melody track: {item['title']}"
        notes = tracks[item.get('melody_track', 0)]
        if 'lyric_tokens' in item:
            assert len(item['lyric_tokens']) == len(notes), f"Lyric alignment: {item['title']}"
            for note, lyric in zip(notes, item['lyric_tokens']):
                note['lyric'] = lyric
        for note in notes:
            note['pitch'] += item.get('transpose', 0)
        # MIDI notation exports sometimes shorten sounding notes. Retain the
        # notated rhythm by snapping lengths to a 1/32-note grid.
        for i, note in enumerate(notes):
            note['start'] = round(note['start'] / 3) * 3
            note['duration'] = max(3, round(note['duration'] / 3) * 3)
            if i + 1 < len(notes):
                note['duration'] = min(note['duration'], round(notes[i+1]['start'] / 3)*3 - note['start'])
            assert note['duration'] > 0
        results.append(dict(item, notes=notes, duration=max(n['start'] + n['duration'] for n in notes),
                            reference_sha256=hashlib.sha256(data).hexdigest()))
    output = Path(__file__).with_name('folk_melodies.json')
    output.write_text(json.dumps(results, ensure_ascii=False, indent=2)+'\n')
    print(f'Saved {len(results)} reviewed melody inputs to {output}.')
