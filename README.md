# pkia.dev — personal portfolio

Source for my personal website, served via GitHub Pages at
**<https://pkia.github.io>**.

Single-page portfolio: hero, stats, about, projects, experience, journey
timeline and contact. Vanilla HTML/CSS/JS — no framework, no build step.

## Structure

```
index.html            content and sections
blog/index.html       devlog — post list (newest first)
blog/posts/*.html     one devlog post per day (YYYY-MM-DD.html)
styles.css            design system (navy maritime theme, radar accent)
script.js             reveals, counters, rotating greeting, copy-email
favicon.svg           radar mark
og.png                social share card (1200×630)
apple-touch-icon.png  home-screen icon
feed.xml              RSS feed for the devlog
sitemap.xml · robots.txt   search engine plumbing
404.html              themed "signal lost" page
AGENTS.md             conventions for the automated devlog writer
```

## Editing

All copy lives directly in `index.html` in clearly-commented sections.
Push to `master` and GitHub Pages deploys automatically.

## Devlog automation

A hermes cron job on the Pi runs every morning at 07:00, gathers the previous
day's commits across the home-lab repos, writes `blog/posts/YYYY-MM-DD.html`,
prepends its card to `blog/index.html`, refreshes the homepage content
(project cards, "Currently" panel, milestones) and pushes to `master`.
Conventions for that job live in `AGENTS.md`.
