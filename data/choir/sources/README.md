The 35 `openhymnal-*.abc` files are selected from the Open Hymnal archive,
https://github.com/mzealey/openhymnal (retrieved 16 November 2026).
Each selected file explicitly identifies its music/setting as public domain.
Original comments, credits, historical source citations, and rights statements
are retained. The archive's legacy Latin-1 text has been converted to UTF-8.
`../provenance.json` records the source paths, repository tree and SHA-256 hashes.

The other 15 ABC files are new, simple block-chord educational harmonizations
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
