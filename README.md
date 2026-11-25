# FreeCat · 全球猫咪乐园

**A world for cat lovers.** A free, local-first web app for people who live with cats, are considering adoption, or simply love cats from afar. Start with a virtual cat you can pet; explore, identify visual traits, collect, learn responsible care, and play.

## What's included (v0.2.1)

- Pet: original procedural Canvas 2D cat and fur, eight coats, size, optional synthesized purr, keyboard and pointer interaction, themes, daily local companionship time.
- Atlas: 19 named breeds plus domestic cats of unknown pedigree; bilingual descriptions, search, coat filter, original illustrative art and favorites. This is a starter atlas, not a complete global breed registry.
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

No backend, tracking code, or external assets are necessary for normal use. External reference/brand links are voluntary navigation. A host may keep its own access logs. Photos are read on-device; journal photos are compressed to JPEG before storage. Local storage is best-effort and may be cleared by the browser; exported JSON contains personal cat records and should be kept safely. The budget planner is an estimate, not a market price database. Never use appearance matching to assert pedigree. Do not use this app for urgent or individualized animal medical decisions.

## Contribute

Priority: actual mobile and desktop tests; WebGL/WASM fur performance; accessibility and translation review; veterinarian-reviewed education; local photo classification with labeled, licensed evaluation data; real breed photos only with clear licenses; import/export and optional backup; additional original mini-games. Contributions should prioritize animal welfare, privacy and user experience over engagement tricks. Do not introduce paid loot boxes or unnecessary account gates.

## License

MIT for original software in this release. External linked references retain their own rights. No third-party reference-site code or images are included. The initial virtual cat is inspired by the general concept of petting a cat online, not a source-code clone.

By AI 酋长 Andy · 星觉科技 — https://metaver.vip/

## Validation

Run `python -m pip install playwright`, then `python -m playwright install chromium` and `python tests/smoke.py` (or set `CHROMIUM_PATH` to a system Chromium). The script uses in-memory HTML and does not prove storage persistence or hosting behavior. See [iteration log](docs/iterations/2026-11-25-01.md).

## Photo Lab (experimental)

[Open the photo renderer](experiments/photo-pet.html) from the same static web server. The original AI-generated ginger tabby (`experiments/ginger.webp`, 326,594 bytes) is bundled locally and is loaded automatically by the existing renderer; no photo upload or external API is required. The classic homepage remains the default. This experiment implements breathing and directional image displacement, not individual fur physics. Run `python tests/photo_lab.py` with Playwright/Chromium to exercise the renderer using the bundled sample. See [asset provenance and validation](docs/iterations/2026-11-25-09.md).
