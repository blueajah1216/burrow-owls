The 35 `openhymnal-*.abc` files are selected from the Open Hymnal archive,
https://github.com/mzealey/openhymnal (retrieved 16 November 2026).
Each selected file explicitly identifies its music/setting as public domain.
Original comments, credits, historical source citations, and rights statements
are retained. The archive's legacy Latin-1 text has been converted to UTF-8.
`../provenance.json` records the source paths, repository tree and SHA-256 hashes.

The original other 15 ABC files are new, simple block-chord educational harmonizations
of public-domain melodies, prepared for The Great Gallery. The new harmonies
are dedicated under CC0 1.0: https://creativecommons.org/publicdomain/zero/1.0/.
They are labeled as new practice settings, not attributed to historical arrangers.
Jingle Bells and Oh! Susanna use their choruses. My Country, 'Tis of Thee and God
Save the King share a melody. Traditional rounds are harmonized here, not played
as canons. These new arrangements are deliberately simple; teacher review is
useful before using them as performance editions.

The browser-ready catalog separates SATB onto four staves, retains one verse
of lyrics where present, omits print-only introduction marks, translates old
ABC Plus dotted ties to ties and fermata abbreviations to abcjs syntax, and uses
a single explicit quarter-note tempo for consistent playback and highlighting.
Rebuild with `.venv/bin/python choir_build/build_library.py`.

The expansion adds 40 new practice arrangements: 18 Jewish songs (Hebrew,
Yiddish, and a Sephardic Ladino lullaby) and 22 world folk songs. Melody references
are credited in each downloadable ABC and in `choir_build/folk_manifest.json`.
Their reviewed pitch/rhythm data and reference hashes are preserved in
`choir_build/folk_melodies.json`. Source engravings, recordings, and accompaniment
parts are not redistributed. The new harmonies are CC0; source editions are not
claimed as CC0. Some melodies are transposed for singing. Repeats are written
out, optional graces omitted, and compound durations written as tied notes or
triplets. Documented reference corrections include Tumbalalaika's key/bar typo,
Zum Gali's missing note length, and omission of a later Santa Lucia coda.

These are simplified Western SATB educational harmonizations of the identified
melody versions, not traditional-performance transcriptions. Hatikvah is in the
Jewish collection; Shalom Aleichem uses Israel Goldfarb's 1918 setting and the
Dreidel Song uses Samuel E. Goldfarb's 1927 melody (public domain in the U.S.).

Two further anthem settings bring the library to 92 songs: O Canada, with the
current English words published by the Government of Canada, and the first verse
of The Star-Spangled Banner. The former uses Lavallée's public-domain melody and
the latter Smith's melody with Key's words. Their new SATB harmonies are CC0;
the U.S. anthem's melody is transposed to B-flat major for singing. Official
Canadian text/copyright information and a Library of Congress historical source
are included in their score credits.
