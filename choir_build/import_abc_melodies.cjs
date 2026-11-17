/* One-time melody import. Only pitches, rhythms and first-verse syllables enter
 * the reviewed dataset. No source accompaniment or engraving is copied.
 * node choir_build/import_abc_melodies.cjs <manifest.json> <source-directory>
 */
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const ABCJS = require('../static/choir/vendor/abcjs-6.7.2.min.js');
const manifest = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const results = [];
for (const item of manifest.filter(item => item.format === 'abc')) {
  const bytes = fs.readFileSync(path.join(process.argv[3], item.file));
  let text = new TextDecoder('windows-1252').decode(bytes);
  for (const [before, after] of item.corrections || []) text = text.replace(before, after);
  if (item.end_before) text = text.split(item.end_before)[0];
  if (item.inline_voices) text = text.split('\n').map(line => {
    if (/^V:/.test(line) && !/\b(program|Program|bass|treble)\b/.test(line)) return line.replace(/^V:(\w+)\s+/, '[V:$1] ');
    return line;
  }).join('\n');
  // Modern tempo markings, grace notes and expressive decorations are not part
  // of these deliberately simple melodic practice transcriptions.
  text = text.replace(/^Q:.*\r?\n/gm, '').replace(/^%%continueall.*\r?\n/gm, '')
    .replace(/\[Q:[^\]]*\]/g, '').replace(/\{[^}]*\}/g, '');
  const tune = ABCJS.parseOnly(text)[item.tune_index || 0];
  const seq = tune.setUpAudio({qpm:120, chordsOff:true});
  const voice = item.voice || 0;
  const syllables = new Map();
  for (const line of tune.lines) for (const staff of line.staff || []) for (const part of staff.voices || []) {
    for (const el of part) if (el.lyric?.[item.lyric_verse || 0]) {
      const lyric = el.lyric[item.lyric_verse || 0];
      // Preserve original-language syllables, not uncredited English translations.
      syllables.set(el.startChar, (lyric.syllable || '*') + (lyric.divider === '-' ? '-' : ''));
    }
  }
  if (!seq.tracks[voice]) throw new Error(`No melodic voice: ${item.title}`);
  const notes = seq.tracks[voice].filter(n => n.cmd === 'note').map(n => ({
    start:Math.round(n.start*96), duration:Math.round(n.duration*96), pitch:n.pitch + (item.transpose || 0),
    lyric:item.lyrics === false ? '*' : (syllables.get(n.startChar) || '*'),
  }));
  results.push({...item, duration:Math.round(seq.totalDuration*96), notes,
    reference_sha256:crypto.createHash('sha256').update(bytes).digest('hex')});
}
fs.writeFileSync(path.join(process.argv[3], 'abc-melodies.json'), JSON.stringify(results,null,2)+'\n');
console.log(`Imported ${results.length} single-line melodies.`);
