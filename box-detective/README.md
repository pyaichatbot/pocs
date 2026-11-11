# Box Detective 📦🔍

A phone web app that guesses what is inside a sealed box — an Amazon parcel, a mystery box, a wrapped Christmas gift — without opening it.

It is a plain web page (PWA), so it runs in Safari on an iPhone with **no App Store, no Apple developer account, no install**. "Add to Home Screen" makes it look and launch like an app.

## The honest physics

A phone cannot see through cardboard. There is no X-ray, the LiDAR and camera stop at the surface, and radar/ultrasound chips are not exposed to apps. So the app does what a person does when they pick up a present — but with sensors and a scoring model:

| Clue | How the phone gets it | What it tells you |
|---|---|---|
| **Look** | Camera photos + tick-boxes for markings | Battery warning → electronics, "fragile" → glass, retailer/brand printing, soft mailer → clothes |
| **Density** | Size (preset or L×W×H) and weight (scale or "heft") | The strongest single clue: books ≈ 700 g/L, clothes ≈ 120 g/L, a tiny item in a big Amazon box < 40 g/L |
| **Shake** | Microphone: counts impact sounds and measures their pitch | Silent, soft thud, hard clunk, many-piece rattle (LEGO, puzzle), jingle, slosh |
| **Tilt** | Motion sensor, phone lying on the box: tilt angle + jolts when contents hit the wall | Whether things slide around inside, and how freely |
| **Knock** | Microphone: ring-down time and pitch of a knuckle knock | Hollow, packed solid, or soft |
| **Context** | You tell it: occasion, recipient, hints | Shifts the odds (a child at Christmas vs. an adult's online order) |

All clues feed a small naive-Bayes-style model over 16 content categories, which returns a ranked list with percentages and the reasons for and against each guess. This all runs on the phone, offline.

**Optional AI second opinion:** with your own Anthropic API key, the app sends the photos and clues to Claude, which can read label text, logos, box codes and customs descriptions and give specific guesses ("probably over-ear headphones"). Without a key everything else still works.

Every sensor reading is a heuristic, so each test shows what it detected and lets you correct it with one tap. Every step can be skipped.

## Use it on your iPhone

Camera, microphone and motion sensors only work on **HTTPS** pages, so the folder has to be served from somewhere. Easiest options:

1. **GitHub Pages** — repo *Settings → Pages → Deploy from a branch*, pick the branch that contains this folder, root `/`. Then open `https://<user>.github.io/pocs/box-detective/` in Safari. (Free Pages needs a public repo.)
2. **Any static host** — drag this folder onto Netlify Drop, Cloudflare Pages, Vercel, etc.
3. **Local test over Wi-Fi** — `npx serve` plus an HTTPS tunnel such as `cloudflared tunnel --url http://localhost:3000`.

Then in Safari: **Share → Add to Home Screen**. Allow microphone and motion access when asked.

For the AI guess: tap ⚙︎ and paste an Anthropic API key. It is stored only in that browser's local storage; use a key with a low spend limit.

## Files

- `index.html` — the whole app (UI, sensor capture, signal analysis, inference model, AI call). No build step, no dependencies.
- `manifest.webmanifest`, `sw.js`, `icon*.png|svg` — home-screen install and offline support.

## Limits

- Guesses are categories and probabilities, not certainties. Heavy padding hides sound and movement.
- Rough size/weight presets are much weaker than a tape measure and a kitchen scale.
- Sound thresholds were tuned on synthetic signals, not a large set of real boxes — use the correction chips.
- Photos of shipping labels contain addresses. They stay on the phone unless you press the AI button, which sends them to the Anthropic API.
