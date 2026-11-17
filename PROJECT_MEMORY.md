# Project direction

User instruction, November 17, 2026:

- **The canonical home for everything in this project is `https://thegreatgallery.art`.** The Burrow Owls website is being retired. New features, branding, navigation, documentation, and public links should target The Great Gallery.
- `/music` is a landing page with three equally prominent sibling sections: concerts at `/music/concerts`, music history at `/music/history`, and practice at `/music/practice`. Keep this hierarchy clear in navigation. Composers and individual works belong under history; performance search supports concerts.
- The Seattle concert calendar belongs at `/music/concerts`, and performance search at `/music/search`, on the same gallery domain.
- The calendar is **Seattle-area only**. Label calendar navigation “Seattle concerts” and keep its regional scope explicit. The separate performance search covers worldwide listings.
- Verify public routes using the gallery Host header. Localhost behaves differently because `galleryhost.py` rewrites gallery-domain URLs.
- Preserve the practice songbook, playback, and downloadable score URLs when adding music features. The practice room is now `/music/practice`; library JSON and score downloads keep `/music/library.json` and `/music/sources/...`.
- The account experience is **Create your gallery**: one account saves paintings, photographs, music history pieces, and practice songs. Make signup and login prominent throughout all three sections; `/my-gallery` is the private combined collection. Existing opt-in Art Lovers profiles share paintings only.
