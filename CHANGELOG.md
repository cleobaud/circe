# Changelog

## 0.6.0 · Nov 27, 2026 · signed, self-updating
This version brings everything fixed since 0.5.0 (0.5.1 to 0.5.3 were never published).
- **CIRCÉ updates itself.** At startup it installs the new version on its own and tells you which one is running; it takes over at the next launch of Claude Code. Automatic updates only come from the official CDOW marketplace (this repository); any other source is announced and nothing installs by itself. `python scripts/maj.py proposer` or `jamais` gives you back control.
- **Every version is signed by CDOW.** The package carries a signed record of its files; at startup CIRCÉ says in one line if a file of the software was changed, and how to restore the original (`claude plugin update circe@circe-cdow`). It never blocks: it is your computer. Line-ending conversions by Git do not count as changes.
- **CIRCÉ tells you where it stands.** `python scripts/etat.py`: installed version, licence state, server reachable or not, the skills counted in the product, and what keeps working without the server.
- **26 skills**: new `visuel` (posts, stories, posters, banners) and `schema-video` (a video series: a fixed format, new content each episode).
- **Video checks are tooled** (`scripts/video.py`): frame, frames per second, duration, sound, black frames, a 12-image contact sheet, a registry that refuses a shot already shown, and a font check before rendering.
- **Images are measured, not guessed** (`scripts/regarder.py`): size, luminance, dominant colours, transparency and the largest plain area where text can sit.
- Reflexes that now catch the common cases: a brief read from a file, image requests that were missed, the end-of-task words used by CIRCÉ itself; a plan is proposed once real work is under way.
- The licensed method can no longer leave the work in progress: it is refused in files written to the project and in exports to your automations.
- 249 automated tests.

## 0.5.0 · Nov 25, 2026 · nothing imposed
- **CIRCÉ imposes nothing at install.**
  - By default it refuses only 3 catastrophic moves: formatting a disk, wiping a drive root, wiping your home folder.
  - Claude explains this in the first session, then reminds you briefly.
- **Every other protection is proposed, never applied by default.** This covers recursive deletion, `git push`, rewriting git history, production deploys, publishing a package, a script downloaded then run, databases and secret files.
  - You turn on what you want with "configure CIRCÉ".
  - Turning a protection off always asks for your consent.
- New reflex: CIRCÉ proposes a protection once, when a move it would have covered happens. The log of proposals never contains the command.
- Fix (found in review): a reflex no longer answers twice to the same event when two Python interpreters renew an expired token at the same time.

## 0.4.0 · Nov 24, 2026
- **Signed tools, with your key.** The plugin does not contain their code: it requests the tool from the server with your key, then checks its fingerprint and CDOW's signature.
- New `integrations` path, the library. It covers what Claude Code can already do, then the tools we actually use for each need (animation, site, video, 3D, image), each with its official source, licence, installation, check and Quai verdict.
- New `system` path: set up a working base like ours (memory and rituals, notes vault, phone, scheduled tasks, second opinion), one checked step at a time, with costs stated upfront.
- New `illustration`, `design` and `security` paths.
- Method served in version 1.4.

## 0.3.0 · Nov 24, 2026
- New `step back` skill: Claude stops, rereads everything done since the last checkpoint, re-runs the proofs, fixes, then moves on. A reflex reminds it every 10 prompts and before going live.
- New `identity` path (logo and visual identity) and `motion` path (animation as a language, filmed preview, measured 60 fps).
- Your permissions are respected: CIRCÉ reads the ones you already granted in Claude Code and never asks again for something already allowed.
- New `quality` skill and side-by-side tool: before each "here it is", the result is put next to the references and judged with fresh eyes.
- 78 automated tests, clean Windows, and a "new user" test on a fresh Claude Code.

## 0.2.0 · Nov 24, 2026
- The method works in loops: one big loop from request to delivery, and small loops (example, preview, check, fix) inside each step.
- Method served up to date by the CIRCÉ server, only to active subscribers.
- New skills: `examples`, `configure` (inventory of your setup, never reading a secret) and `output` (send a validated deliverable to n8n, Make, Zapier or your tool).
- Memory: an automatic log of each request and the files touched, handed back at session start.
- 54 automated tests.

## 0.1.0 · Nov 24, 2026 · preview
- Guard before each action, no "done" without proof, and a log that never stores command arguments.
- Method: 12 skills. Memory: project relay at session start, copy before compaction.
- Licence key checked at most once every 24 h, 7 days of offline grace, 3 computers per key.
- 33 automated tests.
