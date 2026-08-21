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

### Publish flow

```bash
git add blog index.html styles.css
git commit -m "devlog: YYYY-MM-DD"
git push origin master
```

Then report the live URL: `https://pkia.github.io/blog/posts/YYYY-MM-DD.html`.
If the push fails, leave the working tree clean (reset uncommitted blog files)
and report the failure instead of leaving a mess.
