/* The notation, MIDI export, sound and cursor all come from the same ABC score.
 * Playback uses a short Web Audio scheduling window and the audio clock for
 * progress. No remote soundfonts, microphone access or audio uploads.
 */
(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const names = ['Soprano', 'Alto', 'Tenor', 'Bass'];
  let songs = [], song, tune, sequence, events = [], tracks = [], duration = 0;
  let context, master, gains = [], sounding = new Set(), playing = false;
  let position = 0, anchorPosition = 0, anchorTime = 0, speed = .8, cursor, eventIndex = -1;
  let nextNotes = [], midiURL, frame, playRequest = 0;
  const enabled = [true, true, true, true];
  const status = message => { $('playback-status').textContent = message; };
  const clock = seconds => `${Math.floor(seconds / 60)}:${String(Math.floor(seconds % 60)).padStart(2, '0')}`;
  const now = () => playing ? Math.max(0, Math.min(duration, anchorPosition + (context.currentTime - anchorTime) * speed)) : position;

  function releaseSound() {
    for (const node of sounding) {
      try { node.stop(); } catch (_) { /* It may already have ended. */ }
    }
    sounding.clear();
  }

  function prepareAudio() {
    if (context) return;
    const Audio = window.AudioContext || window.webkitAudioContext;
    if (!Audio) throw new Error('This browser does not support audio playback. Try a current Chrome, Safari, Edge or Firefox.');
    context = new Audio();
    master = context.createGain();
    master.gain.value = .55;
    master.connect(context.destination);
    gains = names.map((_, i) => {
      const gain = context.createGain();
      gain.gain.value = enabled[i] ? 1 : 0;
      gain.connect(master);
      return gain;
    });
    context.addEventListener('statechange', () => {
      if (playing && context.state !== 'running') {
        pause();
        status('Playback paused. Tap Play to continue.');
      }
    });
  }

  function sound(pitch, start, length, voice, volume) {
    // A soft fundamental with a small upper harmonic gives a clear singing
    // guide without needing a large or externally hosted sample library.
    const envelope = context.createGain();
    const level = Math.min(.15, .1 * (volume || 90) / 100);
    envelope.gain.setValueAtTime(0, start);
    envelope.gain.linearRampToValueAtTime(level, start + Math.min(.015, length / 4));
    envelope.gain.setValueAtTime(level * .75, start + Math.max(.016, length - .035));
    envelope.gain.linearRampToValueAtTime(0, start + length);
    envelope.connect(gains[voice]);
    const oscillator = context.createOscillator();
    oscillator.type = 'triangle';
    oscillator.frequency.value = 440 * Math.pow(2, (pitch - 69) / 12);
    oscillator.connect(envelope);
    oscillator.start(start);
    oscillator.stop(start + length + .005);
    sounding.add(oscillator);
    oscillator.onended = () => { sounding.delete(oscillator); oscillator.disconnect(); envelope.disconnect(); };
  }

  function resetScheduler() {
    nextNotes = tracks.map(notes => {
      const i = notes.findIndex(n => n.start + n.duration > position + .001);
      return i === -1 ? notes.length : i;
    });
    anchorPosition = position;
    anchorTime = context.currentTime + .025;
  }

  function schedule(current) {
    const horizon = current + .14 * speed;
    tracks.forEach((notes, voice) => {
      while (nextNotes[voice] < notes.length && notes[nextNotes[voice]].start <= horizon) {
        const note = notes[nextNotes[voice]++];
        const start = Math.max(context.currentTime + .003, anchorTime + (Math.max(note.start, anchorPosition) - anchorPosition) / speed);
        const length = (note.start + note.duration - Math.max(note.start, anchorPosition)) / speed;
        if (length > .015) sound(note.pitch, start, Math.max(.025, length * .94), voice, note.volume);
      }
    });
  }

  function updateVoices() {
    document.querySelectorAll('.voice-toggle').forEach((button, i) => {
      button.setAttribute('aria-pressed', String(enabled[i]));
      button.querySelector('.voice-state').textContent = enabled[i] ? 'Sound on' : 'Muted';
      if (gains[i]) gains[i].gain.setTargetAtTime(enabled[i] ? 1 : 0, context.currentTime, .01);
      document.querySelectorAll(`#score .abcjs-v${i}`).forEach(el => el.classList.toggle('muted-voice', !enabled[i]));
    });
    if (!enabled.some(Boolean)) status('All voices are muted. Turn one on when you’re ready to listen.');
    else status(`Listening to ${names.filter((_, i) => enabled[i]).join(', ')}.`);
  }

  function showProgress(force = false) {
    const current = now();
    $('seek').value = duration ? Math.round(current / duration * 1000) : 0;
    $('time').textContent = `${clock(current / speed)} / ${clock(duration / speed)}`;
    const ms = current * 1000;
    // The library is short; binary search keeps cursor updates cheap at 60 fps.
    let lo = 0, hi = events.length - 1, index = -1;
    while (lo <= hi) {
      const mid = (lo + hi) >> 1;
      if (events[mid].milliseconds <= ms + 1) { index = mid; lo = mid + 1; }
      else hi = mid - 1;
    }
    const ev = events[index];
    if (!ev || !cursor) { if (cursor) cursor.style.display = 'none'; return; }
    cursor.style.display = '';
    if (index !== eventIndex || force) {
      $('score').querySelectorAll('.note-playing').forEach(el => el.classList.remove('note-playing'));
      (ev.elements || []).flat().filter(Boolean).forEach(el => el.classList.add('note-playing'));
      cursor.setAttribute('y', ev.top - 8);
      cursor.setAttribute('height', ev.height + 16);
      const pane = $('score-scroll'), svg = cursor.ownerSVGElement;
      const scale = svg.getBoundingClientRect().width / svg.viewBox.baseVal.width;
      const y = ev.top * scale;
      if (playing && $('follow').checked) {
        if (y < pane.scrollTop + 20 || y + ev.height * scale > pane.scrollTop + pane.clientHeight - 20) pane.scrollTop = Math.max(0, y - 35);
      }
      eventIndex = index;
    }
    const next = events[index + 1];
    let x = ev.left - 3;
    if (next && next.line === ev.line && next.left > ev.left) {
      const fraction = Math.max(0, Math.min(1, (ms - ev.milliseconds) / (next.milliseconds - ev.milliseconds)));
      x += fraction * (next.left - ev.left);
    }
    cursor.setAttribute('x', x);
    const pane = $('score-scroll');
    if (playing && $('follow').checked && pane.scrollWidth > pane.clientWidth) {
      const svg = cursor.ownerSVGElement;
      const scale = svg.getBoundingClientRect().width / svg.viewBox.baseVal.width;
      const left = x * scale + 14;
      if (left < pane.scrollLeft + 15 || left > pane.scrollLeft + pane.clientWidth - 35) pane.scrollLeft = Math.max(0, left - 50);
    }
  }

  function tick() {
    if (!playing) return;
    position = now();
    schedule(position);
    showProgress();
    if (position >= duration) {
      if ($('loop').checked) {
        releaseSound(); position = 0; resetScheduler();
      } else {
        pause();
        status('Nicely practiced. Restart, or try singing with the other voices.');
        return;
      }
    }
    frame = requestAnimationFrame(tick);
  }

  async function play() {
    if (!song) return;
    const request = ++playRequest;
    $('play').disabled = true;
    try {
      prepareAudio();
      await context.resume();
      if (request !== playRequest) return;
      if (position >= duration - .01) position = 0;
      playing = true;
      resetScheduler();
      $('play').textContent = 'Ⅱ Pause';
      $('play').setAttribute('aria-label', 'Pause playback');
      updateVoices();
      tick();
    } catch (error) {
      status(error.message || 'Audio could not start. Tap Play to try again.');
    } finally {
      $('play').disabled = false;
    }
  }

  function pause() {
    ++playRequest;
    position = now(); playing = false;
    cancelAnimationFrame(frame);
    releaseSound();
    $('play').textContent = '▶ Play';
    $('play').setAttribute('aria-label', 'Play music');
    showProgress();
  }

  function seek(fraction) {
    const wasPlaying = playing;
    pause();
    position = fraction * duration;
    showProgress(true);
    if (wasPlaying) play();
  }

  function filterSongs() {
    const normalize = value => value.toLocaleLowerCase().normalize('NFD').replace(/[\u0300-\u036f\u0591-\u05bd\u05bf-\u05c7]/g, '').replace(/[’‘']/g, '');
    const term = normalize($('song-search').value.trim());
    const category = $('category').value;
    let count = 0;
    document.querySelectorAll('.song-option').forEach(button => {
      const item = songs.find(s => s.id === button.dataset.song);
      const searchable = normalize([item.title, item.native_title, item.origin, item.category, ...(item.aliases || [])].filter(Boolean).join(' '));
      const show = searchable.includes(term) && (category === 'all' || item.category === category);
      button.hidden = !show;
      if (show) count++;
    });
    $('song-count').textContent = count ? `${count} song${count === 1 ? '' : 's'} to sing` : 'No songs found. Try another search.';
    document.querySelectorAll('[data-collection]').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.collection === category)));
    $('song-list').scrollTop = 0;
  }

  function selectSong(id) {
    pause(); position = 0; eventIndex = -1;
    song = songs.find(s => s.id === id) || songs[0];
    $('practice-error')?.remove();
    $('song-title').textContent = song.title;
    $('song-native-title').textContent = song.native_title || '';
    $('song-native-title').hidden = !song.native_title;
    $('song-category').textContent = song.category.toUpperCase();
    $('song-subtitle').textContent = [song.origin, song.note].filter(Boolean).join(' · ');
    $('song-credit').textContent = song.credit;
    $('song-license').textContent = song.license;
    $('source-link').href = song.source_url;
    $('download-source').href = window.CHOIR_SOURCE_URL.replace('SCORE_FILE', encodeURIComponent(song.source));
    $('score-note').textContent = 'Soprano · Alto · Tenor · Bass. Scroll to read the full score.';
    document.querySelectorAll('.song-option').forEach(button => button.setAttribute('aria-current', String(button.dataset.song === song.id)));
    const width = Math.max(640, $('score-scroll').clientWidth) - 28;
    tune = ABCJS.renderAbc('score', song.abc, {
      add_classes:true, staffwidth:width - 30, responsive:'resize',
      paddingtop:15, paddingbottom:20, paddingleft:12, paddingright:12,
      format:{titlefont:'Georgia 18', vocalfont:'Georgia 11', gchordfont:'Georgia 11', partsfont:'Georgia 11'},
      wrap:{minSpacing:1.7, maxSpacing:2.7, preferredMeasuresPerLine:4},
    })[0];
    sequence = tune.setUpAudio({qpm:song.tempo, chordsOff:true});
    const secondsPerWhole = 240 / sequence.tempo;
    tracks = sequence.tracks.map(track => track.filter(n => n.cmd === 'note').map(n => ({
      pitch:n.pitch, start:n.start * secondsPerWhole, duration:n.duration * secondsPerWhole, volume:n.volume,
    })).sort((a,b) => a.start - b.start));
    if (tracks.length !== 4 || tracks.some(t => !t.length)) throw new Error('This score could not be prepared as four voice parts.');
    events = tune.setTiming().filter(e => e.type === 'event');
    duration = sequence.totalDuration * secondsPerWhole;
    const svg = $('score').querySelector('svg');
    cursor = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
    cursor.classList.add('playhead'); cursor.setAttribute('width', '12');
    svg.appendChild(cursor);
    $('score-scroll').scrollTop = 0;
    $('score-scroll').scrollLeft = 0;
    $('bpm').textContent = `${Math.round(song.tempo * speed)} bpm`;
    if (midiURL) URL.revokeObjectURL(midiURL);
    const midi = ABCJS.synth.getMidiFile(tune, {midiOutputType:'binary'});
    midiURL = URL.createObjectURL(new Blob([midi], {type:'audio/midi'}));
    $('download-midi').href = midiURL;
    $('download-midi').download = `${song.id}.mid`;
    $('download-midi').title = 'Download all four parts at the original tempo';
    $('play').disabled = $('restart').disabled = $('seek').disabled = false;
    document.querySelector('.practice').setAttribute('aria-busy', 'false');
    updateVoices(); showProgress(true);
    const url = new URL(location.href); url.searchParams.set('song', song.id);
    history.replaceState(null, '', url);
    // A small read-only snapshot is useful for browser regression checks.
    window.choirState = () => ({song:song.id, playing, position:now(), duration, speed, enabled:[...enabled], tracks:tracks.map(t => t.length), audioState:context?.state});
  }

  $('play').addEventListener('click', () => playing ? pause() : play());
  $('restart').addEventListener('click', () => { seek(0); status('Back to the beginning.'); });
  $('seek').addEventListener('input', e => seek(Number(e.target.value) / 1000));
  $('speed').addEventListener('input', e => {
    const resume = playing; pause(); speed = Number(e.target.value) / 100;
    $('speed-value').textContent = `${e.target.value}%`;
    if (song) $('bpm').textContent = `${Math.round(song.tempo * speed)} bpm`;
    showProgress(); if (resume) play();
  });
  document.querySelectorAll('.voice-toggle').forEach((button, i) => button.addEventListener('click', () => { enabled[i] = !enabled[i]; updateVoices(); }));
  document.querySelectorAll('.solo').forEach((button, i) => button.addEventListener('click', () => { enabled.fill(false); enabled[i] = true; updateVoices(); }));
  $('learn-part').addEventListener('click', () => { enabled.fill(false); enabled[Number($('my-part').value)] = true; updateVoices(); });
  $('backing').addEventListener('click', () => { enabled.fill(true); enabled[Number($('my-part').value)] = false; updateVoices(); });
  $('all-voices').addEventListener('click', () => { enabled.fill(true); updateVoices(); });
  $('print').addEventListener('click', () => {
    if (!song) return;
    pause();
    let paper = $('print-score');
    if (!paper) { paper = document.createElement('div'); paper.id = 'print-score'; document.body.appendChild(paper); }
    paper.style.cssText = 'display:block;position:absolute;left:-10000px;width:720px;';
    // A separate SVG per system lets browsers paginate between systems.
    ABCJS.renderAbc(paper, song.abc, {staffwidth:680, oneSvgPerLine:true, wrap:{preferredMeasuresPerLine:4,minSpacing:1.6,maxSpacing:2.7}});
    const credit = document.createElement('p'); credit.textContent = `${song.credit} ${song.license}`; paper.appendChild(credit);
    window.print();
  });
  $('song-search').addEventListener('input', filterSongs);
  $('category').addEventListener('change', filterSongs);
  document.querySelectorAll('[data-collection]').forEach(button => button.addEventListener('click', () => {
    $('category').value = $('category').value === button.dataset.collection ? 'all' : button.dataset.collection;
    $('song-search').value = '';
    filterSongs();
  }));
  $('song-list').addEventListener('click', event => {
    const button = event.target.closest('[data-song]');
    if (!button || !songs.length) return;
    try { selectSong(button.dataset.song); } catch (error) { fail(error); }
  });
  document.addEventListener('visibilitychange', () => {
    // Never let background-tab throttling desynchronize the sound and score.
    if (document.hidden && playing) { pause(); status('Paused while you were away. Tap Play to continue.'); }
  });
  window.addEventListener('pagehide', () => { pause(); if (midiURL) URL.revokeObjectURL(midiURL); });
  function fail(error) {
    pause();
    $('play').disabled = $('restart').disabled = $('seek').disabled = true;
    document.querySelector('.practice').setAttribute('aria-busy', 'false');
    status(error.message || 'The songbook could not load. Refresh the page to try again.');
    $('playback-status').classList.add('error');
  }
  fetch(window.CHOIR_LIBRARY_URL).then(response => {
    if (!response.ok) throw new Error('The songbook could not load. Refresh the page to try again.');
    return response.json();
  }).then(data => {
    songs = data;
    if (!window.ABCJS) throw new Error('Music notation could not load. Refresh the page to try again.');
    selectSong(new URLSearchParams(location.search).get('song') || 'hava-nagila');
  }).catch(fail);
})();
