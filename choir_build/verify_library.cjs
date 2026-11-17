/* Validate generated singing notes against the independent melody references. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const ABCJS = require('../static/choir/vendor/abcjs-6.7.2.min.js');
const root = path.resolve(__dirname, '..');
const songs = JSON.parse(fs.readFileSync(path.join(root,'data/choir/library.json')));
const references = JSON.parse(fs.readFileSync(path.join(__dirname,'folk_melodies.json')));
assert.equal(new Set(songs.map(song=>song.id)).size, songs.length);
for (const song of songs) {
  assert(fs.existsSync(path.join(root,'data/choir/sources',song.source)), song.id);
  const tune = ABCJS.parseOnly(song.abc)[0];
  const sequence = tune.setUpAudio({qpm:song.tempo,chordsOff:true});
  const tracks = sequence.tracks.map(track=>track.filter(note=>note.cmd==='note'));
  assert.equal(tracks.length,4,song.id);
  assert(tracks.every(notes=>notes.length>0),song.id);
  assert.equal((tune.warnings || []).length,0,`${song.id}: ${tune.warnings}`);
  const reference = references.find(reference=>reference.title===song.title);
  if (!reference) continue;
  if (reference.pickup_units) {
    let pickup = 0;
    for (const element of tune.lines[0].staff[0].voices[0]) {
      if (element.el_type === 'bar') break;
      if (element.el_type === 'note') pickup += element.duration * 96;
    }
    assert.equal(pickup,reference.pickup_units,`${song.id}: preserve the opening pickup measure`);
  }
  assert.equal(tracks[0].length,reference.notes.length,song.id);
  tracks[0].forEach((note,i)=>{
    const expected = reference.notes[i];
    assert.equal(note.pitch,expected.pitch,`${song.id} note ${i}: pitch changed`);
    assert(Math.abs(note.start*96-expected.start)<1,`${song.id} note ${i}: rhythm changed`);
    assert(Math.abs(note.duration*96-expected.duration)<1,`${song.id} note ${i}: duration changed`);
  });
  tracks.forEach(notes=>{
    const end = Math.max(...notes.map(note=>note.start+note.duration));
    assert(end*96<=reference.duration+1,song.id);
  });
}
console.log(`PASS: ${songs.length} four-part scores, source files, and ${references.length} faithful melody/rhythm transcriptions.`);
