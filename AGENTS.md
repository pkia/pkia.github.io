# personal-website — agent instructions

Source for **https://pkia.github.io** (GitHub Pages user site). Static
HTML/CSS/JS, no build step. The deploy branch is `master` — pushing to
`origin master` deploys automatically.
**Never force-push. Never rewrite history. Never delete existing posts.**

## Devlog job (runs daily at 07:00 via hermes cron)

Write today's devlog post and publish it. The blog is at `blog/`; each post is
a standalone HTML page styled by the site's existing `styles.css`.

### File conventions

- Post path: `blog/posts/YYYY-MM-DD.html` using today's **local** date.
  If that file already exists, do nothing further and report that the post
  already exists.
- Index update: prepend a new `<article class="post-card reveal">` directly
  below the `<!-- ... -->` marker line inside `<div id="post-list">` in
  `blog/index.html` — newest post always first.
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
3. `On the radar` — future project ideas / what's coming next.
4. `Interesting reads` — 2–3 external links.

Content rules:

- `Shipped` must be evidence-backed. Determine the date of the newest existing
  post (filename), then run git log since that date, e.g.
  `git -C <repo> log --since=<YYYY-MM-DD> --oneline`, across:
  `/home/ev/personal-website`, `/home/ev/maritime-dashboard`,
  `/home/ev/project-hub`, `/home/ev/pi-cicd`, `/home/ev/ais_analysis`
  (skip repos that don't exist). Summarise real commits in first person;
  link repos as `https://github.com/pkia/<repo>`.
- Quiet day with no commits? Say so in one line and lean on `On the radar`
  and `Interesting reads`. Never invent work.
- `Interesting reads`: pick 2–3 current items matching my interests — AI / dev
  tooling, Raspberry Pi, SDR / maritime / AIS, self-hosting. First grep
  `blog/posts/` and **never repeat a link already used**. If web search is
  unavailable this run, omit the section gracefully.
- Tone: first-person engineer's devlog — concise, concrete, a little dry
  humour is fine, no marketing voice, no emoji spam.

### Publish flow

```bash
git add blog index.html styles.css
git commit -m "devlog: YYYY-MM-DD"
git push origin master
```

Then report the live URL: `https://pkia.github.io/blog/posts/YYYY-MM-DD.html`.
If the push fails, leave the working tree clean (reset uncommitted blog files)
and report the failure instead of leaving a mess.
