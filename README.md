# FreeCat · 全球猫咪乐园

**A world for cat lovers.** A free, local-first web app for people who live with cats, are considering adoption, or simply love cats from afar. Start with a virtual cat you can pet; explore, identify visual traits, collect, learn responsible care, and play.

## What's included (v0.2.1)

- Pet: original procedural Canvas 2D cat and fur, eight coats, size, optional synthesized purr, keyboard and pointer interaction, themes, daily local companionship time.
- Atlas: 19 named breeds plus domestic cats of unknown pedigree; bilingual descriptions, search, coat filter, credited photographic references where available and favorites. This is a starter atlas, not a complete global breed registry.
- Identify: manual coat/pattern/face/ear trait matcher with optional local photo preview. It is NOT an AI image classifier, veterinary diagnosis, or pedigree test.
- Journal: local favorite breeds and up to 50 real cat profiles, optional compressed photos, notes, removal confirmation, JSON export. No device sync or import yet.
- Care: twelve educational topics, seven-item adoption readiness checklist, editable cost planner and emergency guidance. Reference links are included. Not a substitute for veterinary advice; content has not been independently reviewed by a veterinarian.
- Play: eight-question knowledge quiz, best-score record and random breed discovery.
- English / 简体中文, responsive layout, static hosting, no account or API key, no analytics; this standalone baseline has no service worker yet.

## Run and deploy

Open `index.html` directly, or use a local server:

```sh
python3 -m http.server 8000
```

Open http://localhost:8000. Storage and audio behavior can vary by browser, especially from `file://`. Audio begins only after a user gesture. Installability and offline caching are pending restoration.

### GitHub Pages
1. Use the public repository `AIPMAndy/FreeCat`.
2. Commit the contents of this folder at the root, including `.nojekyll`.
3. Settings → Pages → Deploy from a branch → main → /(root) → Save. Wait for the actual site URL and verify the deployed page.

### Cloudflare Pages
1. Cloudflare Dashboard → Workers & Pages → Create → Pages. Connect the repository, or direct-upload the static site files.
2. No framework, no build step; output directory `.`. If required, use `exit 0` as the build command.
3. Cloudflare assigns an available `*.pages.dev` domain. Confirm the actual URL before sharing.

## Privacy & welfare

No backend or tracking code is required. The pet room, trait matching, journal and care remain local-first. Opening the atlas loads public reference photographs from Wikimedia image servers on demand, with lazy loading and no referrer. Wikimedia receives normal image-request network metadata; local photos and journal entries are not transmitted. External reference/brand links are voluntary navigation. A host may keep its own access logs. Photos are read on-device; journal photos are compressed to JPEG before storage. Local storage is best-effort and may be cleared by the browser; exported JSON contains personal cat records and should be kept safely. The budget planner is an estimate, not a market price database. Never use appearance matching to assert pedigree. Do not use this app for urgent or individualized animal medical decisions.

## Contribute

Priority: actual mobile and desktop tests; WebGL/WASM fur performance; accessibility and translation review; veterinarian-reviewed education; local photo classification with labeled, licensed evaluation data; real breed photos only with clear licenses; import/export and optional backup; additional original mini-games. Contributions should prioritize animal welfare, privacy and user experience over engagement tricks. Do not introduce paid loot boxes or unnecessary account gates.

## License

MIT for original software in this release. External linked references retain their own rights. No third-party reference-site code or images are included. The initial virtual cat is inspired by the general concept of petting a cat online, not a source-code clone.

By AI 酋长 Andy · 星觉科技 — https://metaver.vip/

## Validation

Run `python -m pip install playwright`, then `python -m playwright install chromium` and `python tests/smoke.py` (or set `CHROMIUM_PATH` to a system Chromium). The script uses in-memory HTML and does not prove storage persistence or hosting behavior. See [iteration log](docs/iterations/2026-11-25-01.md).

## Photo Lab (experimental)

[Open the photo renderer](experiments/photo-pet.html) from the same static web server. The original AI-generated ginger tabby (`experiments/ginger.webp`, 326,594 bytes) is bundled locally and is loaded automatically by the existing renderer; no photo upload or external API is required. The classic homepage remains the default. This experiment implements breathing and directional image displacement, not individual fur physics. Run `python tests/photo_lab.py` with Playwright/Chromium to exercise the renderer using the bundled sample. See [asset provenance and validation](docs/iterations/2026-11-25-09.md).

## FreeCat Room · redesigned photo experience

[Enter the immersive cat room](room.html). The classic homepage now has a prominent link to this separately accessible, bilingual photo experience. It reuses the original ginger WebP and the tested round-10 Canvas interaction engine, with optional synthesized purr, day/night mode, a local-photo option and direct links to all five other modules. No additional runtime dependencies or external API. The classic experience remains the default until real served-origin and mobile-device verification can be completed.

Regression: `CHROMIUM_PATH=/usr/bin/chromium python tests/room.py` (or use Playwright's Chromium). The test injects the bundled asset as a data URI and checks the rendered room, not network deployment.

### Portrait cat (round 12)

The immersive room now opens with the original AI-generated sleepy longhair tabby (`experiments/sleepy-tabby.webp`). The landscape ginger is also available through the room’s Another cat button and in [Photo Lab](experiments/photo-pet.html). The room's source is identical to the previously tested portrait preview except that its embedded image is a relative, same-origin WebP asset. Public deployment and device Safari tests remain unverified.

### Shared brand and two-cat room (round 13)

The room now includes an **Another cat / 换只猫** button. It switches between the two existing original AI-generated WebP cats; only the current image is loaded, and switching back from a local photo restores the portrait cat. The interactive renderer, keyboard input, optional purr and local-first design remain unchanged. The two pictures are AI-generated illustrations with photographic realism, not photographs of actual animals.

The classic app, room and Photo Lab use a shared original SVG mark, a 32×32 PNG favicon, a full-bleed 180×180 Apple touch icon, and a 1200×630 JPEG social preview. The social image references the expected GitHub Pages path. Public deployment must still be checked. The new `tests/brand_and_cats.py` and the updated `tests/room.py` and `tests/room_reentry.py` exercise the room with local assets in memory.

### Region-aware petting (round 14)

The immersive room varies local stroke radius and strength across hand-authored regions for each bundled pose; uploaded images keep the generic renderer. Scratch-buffer reuse avoids repeated dimension changes as breathing and stroke regions change. This is localized 2D image displacement, not individual fur physics or recognition. Run `python tests/region_pet.py` with both bundled assets; see [validation and limitations](docs/iterations/2026-11-25-14.md).

### Round 15: visible first cat and quieter breathing

The room now displays the original AI-generated portrait before interactive rendering is ready, keeps the face still during its localized idle torso motion, and validates bounded image masks before replacing the active cat. Run `python tests/room_firstpaint.py` with Playwright/Chromium. This is an in-memory renderer test; see [round 15 evidence](docs/iterations/2026-11-25-15.md) for scope and unverified deployment.

### Round 16: small-screen controls and interruption-safe petting

More settings now expand within the document rather than covering navigation; Escape restores the disclosure focus, and outside clicks close it. Touch-safe padding and pointer capture cleanup reduce interruption problems. Run `python tests/room_disclosure.py` with Playwright and Chromium. See [round 16 verification](docs/iterations/2026-11-25-16.md) for fixture scope and outstanding deployment checks.

### Round 17: portrait micro-gestures

The sleeping portrait now has brief independent ear and tail displacement in addition to torso breathing. These subtle 2D alpha-blended movements are limited to the hand-mapped portrait, fade during petting, and are disabled under reduced motion. Same-size canvas fitting no longer clears the frame. Run `python tests/idle_gestures.py`; see [round 17 evidence](docs/iterations/2026-11-25-17.md). Browser tests use in-memory assets; public deployment remains unverified.

### Round 18: photographic atlas, not synthetic breed pictures

Eight of twenty entries now have visually checked Wikimedia Commons photograph references with author, file source and license links. The remaining twelve explicitly have no photograph; the shared illustrative cat silhouette is removed from the atlas. Images use original aspect ratios without cropping; network failure exposes the source rather than substituting another cat. A journal record with no personal photo explicitly says so. Saved reference entries and play link to the source instead of fetching photos automatically outside the atlas. Breed descriptions are educational, not pedigree evidence. Third-party photos retain their original Creative Commons licenses; MIT applies to original software only. See [photo provenance](docs/atlas-photography.md) and [validation scope](docs/iterations/2026-11-25-18.md). Test: `CHROMIUM_PATH=/usr/bin/chromium python tests/atlas_photos.py`.

### Round 19: 19/20 atlas entries have sourced photography

Eleven additional licensed photographic references were visually reviewed and added. Bombay stays explicitly photo-pending because candidates had contradictory breed descriptions or were identified as mixes. All new images remain remotely hosted, not locally bundled. See [updated source register](docs/atlas-photography.md) and [round 19 evidence](docs/iterations/2026-11-25-19.md). No changes to the pet renderer, storage schema, or other features.

### Round 20 — real homepage photo, sound and brand

The public root without a fragment now leads to [the immersive room](room.html), with a bundled CC0 photograph of Chelsea as default. Existing index fragment routes including `#pet` and `#discover` remain intact. The two original generated cats remain optional and labeled. First intentional touch or keyboard pet starts sound unless muted; clicking the sound control auditions a purr. Browser autoplay policies prevent audio before user activation. A textured local synthetic buffer is immediately available; optional Sgerbic recording is fetched after user activation and used only on successful decode. Wikimedia receives normal audio-request metadata, not personal photos. If unavailable, labeled synth continues. Refreshed logo, PNG icons and social card are bundled. See [media provenance](docs/room-media.md) and [validation scope](docs/iterations/2026-11-25-20.md). New regression: `python tests/room_real_photo.py`. Earlier pose-specific tests need explicit legacy pose/initial mute fixtures for the intentional default and audio changes.

### Local licensed purr (PR #4)

The room uses the bundled Ariadne MP3 after user activation instead of remote Ogg. The original recording and MP3 derivative are CC BY-SA 3.0 (Sgerbic); see [media provenance](docs/room-media.md). A validated synthetic fallback is retained. The atlas's independently licensed photos and existing data remain unchanged. The served-origin regression checks exact local bytes, no pre-gesture request, actual decoded recording and first-tap/recorded audio signals in Chromium and WebKit. Physical speakers and production Pages remain separate acceptance gates.
