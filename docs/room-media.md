# Homepage media provenance

MIT applies to FreeCat's original software only. Third-party photographs and audio recordings retain their individual licenses listed below. Real photographs and AI-generated virtual cats are always labeled separately; AI-generated images are never presented as real photography.

## Real full-body room photographs

1. **Milo (Curled tabby on sofa — default homepage cat)** · `assets/cats/milo-tabby.webp`
   - Source: [File:Cat-sleeping-curled-up.jpg](https://commons.wikimedia.org/wiki/File:Cat-sleeping-curled-up.jpg) on Wikimedia Commons
   - Photographer: **Sonkiki** (own work, uploaded 2021-04-14)
   - License & resolution: The author's file page wikitext explicitly declares `{{self|cc-zero}}` ([CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/)). Structured Data on Commons (`SchlurcherBot` automated statement) also lists [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). FreeCat conservatively complies with **CC BY-SA 4.0** (full photographer attribution, source link, license link, statement of modifications, and separation from the MIT software license), which satisfies both licenses.
   - Original: 3024×4032 JPEG, 3,648,391 bytes, SHA-1 `5aaae8ddd38e7f9443df7ad725e3e75a905ee3a1`.
   - Derivative: EXIF-oriented, cropped to `[0, 756, 3024, 3780]` (1:1 composition framing the curled cat on the sofa and ochre pillow without empty top wall), downscaled to 1024×1024 WebP (quality 76, metadata stripped), 225,008 bytes, SHA-256 `6df824046b3214167969e11218acd00dd9fb4e42aa1599700adf5732f30e2878`. Also used in the refreshed 1200×630 `assets/social-card.jpg` (retaining CC BY-SA 4.0 attribution for the photo portion) and 96×96 swatch thumbnail `assets/cats/thumb-milo-tabby.webp`.

2. **Linen (Tabby dozing on cream blanket)** · `assets/cats/linen-tabby.webp`
   - Source: [File:Cat dozing off on a blanket (Unsplash).jpg](https://commons.wikimedia.org/wiki/File:Cat_dozing_off_on_a_blanket_(Unsplash).jpg) on Wikimedia Commons
   - Photographer: **Erik-Jan Leusink** (`@ejleusink`, Unsplash 2017-04-30, Wayback-verified pre-license-change CC0)
   - License: [CC0 1.0 Universal](https://creativecommons.org/publicdomain/zero/1.0/)
   - Original: 4272×2848 JPEG, 3,604,142 bytes, SHA-1 `2bc0873b3f5542582583e1a7e8e7391dc49fcae7`.
   - Derivative: Full-frame downscale (no crop) to 1200×800 WebP (quality 88, metadata stripped), 89,050 bytes, SHA-256 `213c2d3ef5d0941b6e4507fb20b7d1d2631f415e91643821e9f0b38e0a4d3215`, plus 96×96 thumbnail `assets/cats/thumb-linen-tabby.webp`.

3. **Siam (Overhead curled Siamese on botanical linen)** · `assets/cats/siamese-curl.webp`
   - Source: [File:Sleeping Siamese cat.jpg](https://commons.wikimedia.org/wiki/File:Sleeping_Siamese_cat.jpg) on Wikimedia Commons
   - Photographer: **Gzzz** (own work, 2024-10-27)
   - License: [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)
   - Original: 3024×4032 JPEG, 7,058,558 bytes, SHA-1 `18bd2891c39a681bab7435023c641922322ea992`.
   - Derivative: EXIF-oriented, gently cropped to `[0, 220, 3024, 3760]`, downscaled to 923×1080 WebP (quality 76, metadata stripped), 208,112 bytes, SHA-256 `0816b7399a26b52a00acc13b4f0a19163d4669cab5d24182638516dd4826c634`, plus 96×96 thumbnail `assets/cats/thumb-siamese-curl.webp`.

## Real cat purr audio

- **Ariadne's purr**: [Cat Purring.ogg](https://commons.wikimedia.org/wiki/File:Cat_Purring.ogg), **Sgerbic**, [CC BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/).
  - Bundled as `assets/ariadne-purr.mp3`: 105,837 bytes, 13.133708 s, mono, 24 kHz, 64 kbps MP3.
  - Changes: transcode, mono downmix, resample and remove metadata; CC BY-SA 3.0 applies to the recording and derivative, not the MIT software.
  - Original Ogg SHA-1 `a1d96f0fdeed9c89c2a10ce1f7068f90d1a40573`; MP3 SHA-256 `81a70e312dc1166cb22b8558202729cbefdcee5dfd6895badf4c80d13c440ae4`.
  - Requested only after a deliberate user gesture, level-checked, and crossfaded over the labeled local synthesized fallback.

## Optional AI-generated virtual cats & archived sample

- `experiments/sleepy-tabby.webp` & `experiments/ginger.webp`: Optional transparent-edge AI-generated virtual studio cats, explicitly labeled **AI-generated virtual cat / AI 生成虚拟猫咪** in the UI.
- `experiments/chelsea.webp`: Real photograph by Stefan van der Walt ([scikit-image](https://scikit-image.org/docs/0.25.x/api/skimage.data.html#skimage.data.chelsea), CC0, 375×300 close-up), retained in `experiments/` for provenance/legacy test compatibility and superseded on the homepage by full-body high-resolution photography.
