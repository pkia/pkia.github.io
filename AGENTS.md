# personal-website — agent instructions

Source for **https://pkia.github.io** (GitHub Pages user site). Static
HTML/CSS/JS, no build step. The deploy branch is `master` — pushing to
`origin master` deploys automatically.
**Never force-push. Never rewrite history. Never delete existing posts.**

## Devlog job (runs daily at 07:00 via hermes cron)

Write today's devlog post and publish it, then refresh the homepage content to
match the current state of things (see "Portfolio refresh" below), then refresh
my GitHub profile README (see "Profile README refresh" below). The blog is
at `blog/`; each post is a standalone HTML page styled by the site's existing
`styles.css`.

### File conventions

- Post path: `blog/posts/YYYY-MM-DD.html` using today's **local** date.
  If that file already exists, do nothing further and report that the post
  already exists.
- Index update: prepend a new `<article class="post-card reveal">` directly
  below the `<!-- ... -->` marker line inside `<div id="post-list">` in
  `blog/index.html` — newest post always first.
- Feed + sitemap update: prepend a matching `<item>` to `feed.xml` (title,
  link, guid, pubDate at 07:00 +0100, description = the post card's summary)
  and add the post URL to `sitemap.xml`.
- Copy the overall page structure (head, nav, footer, `post-header`,
  `post-body`) from the newest existing post in `blog/posts/`. Link assets
  absolutely: `/styles.css`, `/script.js`, `/favicon.svg`; nav links use
  `/#about`, `/#projects`, `/#journey`, `/blog/`, `/#contact`.
- Reuse existing CSS classes (`post-*`, `section-label`, `chips`, …). Only add
  to `styles.css` if genuinely necessary.

### Post structure and content rules

Sections, in order:

1. **Intro** — one short paragraph setting the scene for the day.
2. `Shipped` — work completed since the previous post.
3. `On the radar` — future project ideas / what's coming next. Make them
   concrete and buildable: a 09:00 "radar implementer" job
   (github.com/pkia/radar) picks one of these per day and builds it, so phrase
   each as an actionable next step rather than a vague wish.
4. `Interesting reads` — 2–3 external links.

Content rules:

- `Shipped` must be evidence-backed. Determine the date of the newest existing
  post (filename), then discover the repos to cover with
  `for d in /home/ev/*/; do git -C "$d" remote get-url origin 2>/dev/null | grep -q pkia && echo "$d"; done`
  (owned repos only — new repos created by the radar implementer show up here
  automatically) and run `git -C <repo> log --since=<YYYY-MM-DD> --oneline`
  in each. Summarise real commits in first person; link repos as
  `https://github.com/pkia/<repo>`.
- Quiet day with no commits? Say so in one line and lean on `On the radar`
  and `Interesting reads`. Never invent work.
- `Interesting reads`: pick 2–3 current items matching my interests — AI / dev
  tooling, Raspberry Pi, SDR / maritime / AIS, self-hosting. First grep
  `blog/posts/` and **never repeat a link already used**. If web search is
  unavailable this run, omit the section gracefully.
- Tone: first-person engineer's devlog — concise, concrete, a little dry
  humour is fine, no marketing voice, no emoji spam.
- **Never publish network addresses** — no LAN IPs, no Tailscale/tailnet IPs,
  no hostnames that resolve to the home network (say "LAN" or "tailnet"
  instead of the address). Applies to posts, homepage and profile README.

### Portfolio refresh (also part of the daily job)

After writing the post, bring the homepage content up to date with what the
git history and the radar board (https://github.com/pkia/radar/IDEAS.md) say
is current. Rules:

- **Projects section** (`#projects`): add a `.project-card` for any owned
  repo that has shipped real substance (README, tests, working code) and is
  not already listed. Copy the exact markup pattern of an existing card
  (`.project-top`, badge, year, `chips-sm`, GitHub link). Keep the grid at
  about eight cards — flagship first, then recent home-lab work (radar, cs2,
  ais_analysis, hub, pi-cicd) before older highlights; past eight, fold the
  least significant into the "Also:" `.more-link` line instead. Badges must
  stay honest: "In progress" until the work is committed and green.
- **"Currently" panel** (`#currently`, in `#about`): a terminal-styled panel
  showing `systemctl status currently` output. Update the systemd-style lines
  to match what is actually being worked on right now (recent commits + the
  radar board's In progress / Proposed items). Shape per line:
  `● <unit>  active (running|waiting)  <one-line description>` — keep two or
  three work units plus the final `location.service … active (permanent)`
  the city line. Unit names are lowercase-hyphenated slugs (e.g.
  `radar-agent.service`; use `.timer` + `active (waiting)` for recurring
  background work). Leave the command line, closing prompt line and window
  chrome untouched; if you change the command text, update the `--term-ch`
  style hint on `.term-type` to its character count.
- **Journey timeline** (`#journey`): only for genuinely notable milestones
  (a new flagship project going live, awards, role changes) — add an entry
  or refresh the "Now" entry. Do not add an entry per day.
- **Stats bar**: update counts only when clearly stale (e.g. number of
  projects/repos).
- **Design and structure changes are allowed** — hero, experience, contact,
  new sections, restyling, restructuring — when there is a genuine reason
  (outdated copy, a better way to present something, new content that needs a
  home). The owner has explicitly OK'd this: CI/CD and git history are the
  safety net, and anything that breaks can be reverted.
- Quality bar for any change: stay in the site's design language (the CSS
  variables and class system in `styles.css`), keep the HTML valid and the
  page fast (no frameworks, no build step), and only ship changes that make
  the site better — never churn for the sake of change.

### Profile README refresh (also part of the daily job)

Keep my GitHub profile README (repo `pkia/pkia`, file `README.md`, default
branch `master`) in sync with the projects I'm actually working on. It is
**not** part of this repo — do not clone it into `/home/ev` (that would
pollute the devlog repo discovery); edit it through the GitHub contents API
with the authenticated `gh` CLI:

```bash
gh api repos/pkia/pkia/readme --jq '.sha'                  # sha needed for the update
gh api repos/pkia/pkia/readme --jq '.content' | base64 -d  # current README.md
# write the new README to a temp file, then commit it in one API call:
gh api -X PUT repos/pkia/pkia/contents/README.md \
    -f message='readme: <what changed>' -f sha=<sha> \
    -f content="$(base64 -w0 /tmp/readme-new.md)"
```

Rules:

- **Featured work**: same bar as the homepage projects grid — owned repos
  that shipped real substance (README, tests, working code). Add newly
  shipped repos (including ones created by the radar implementer), keep the
  list at four to five bullets, retire or fold the least significant older
  ones into a short "More on GitHub" line. Never invent or oversell work.
- **"Right now" interest line**: refresh from the same sources as the
  homepage "Currently" panel (recent commits + the radar board at
  https://github.com/pkia/radar/IDEAS.md).
- **Toolbox**: update only when genuinely stale.
- Keep the intro bio and contact links untouched unless genuinely outdated;
  keep the markdown valid and the concise engineer voice; no emoji spam.
- **No profile-views counter**: deliberately removed in Aug 2026 — the hosted
  counter services are either dead (komarev.com) or unprofessionally styled
  (getloli anime characters), and a vanity view count adds nothing to the
  profile. Do not re-add any visitor counter badge.
- Only push a commit when something actually changed — never churn for the
  sake of change. If the API update fails, report the failure and continue
  with the rest of the job.

### Publish flow

```bash
git add blog index.html styles.css script.js feed.xml sitemap.xml
git commit -m "devlog: YYYY-MM-DD"        # + a separate "content: ..." commit if portfolio content changed
git push origin master
```

Then report the live URL: `https://pkia.github.io/blog/posts/YYYY-MM-DD.html`.
If the push fails, leave the working tree clean (reset uncommitted blog files)
and report the failure instead of leaving a mess.
