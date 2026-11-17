# Project direction

User instruction, November 17, 2026:

- **The canonical home for everything in this project is `https://thegreatgallery.art`.** The Burrow Owls website is being retired. New features, branding, navigation, documentation, and public links should target The Great Gallery.
- `/music` is the existing music practice room. Link music history prominently from that page; the history timeline is `/music/history`, with composer and piece pages beneath it.
- The Seattle concert calendar belongs at `/music/concerts`, and performance search at `/music/search`, on the same gallery domain.
- The calendar is **Seattle-area only**. Label calendar navigation “Seattle concerts” and keep its regional scope explicit. The separate performance search covers worldwide listings.
- Verify public routes using the gallery Host header. Localhost behaves differently because `galleryhost.py` rewrites gallery-domain URLs.
- Preserve the existing practice room, songbook, playback, and downloadable score URLs when adding music features.
