/* EV — personal site interactions */

(function () {
  "use strict";

  var reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ---------- Mobile nav ---------- */
  var toggle = document.getElementById("nav-toggle");
  var links = document.getElementById("nav-links");

  if (toggle && links) {
    toggle.addEventListener("click", function () {
      var open = links.classList.toggle("open");
      toggle.setAttribute("aria-expanded", String(open));
    });
    links.addEventListener("click", function (e) {
      if (e.target.tagName === "A") {
        links.classList.remove("open");
        toggle.setAttribute("aria-expanded", "false");
      }
    });
  }

  /* ---------- Nav border on scroll ---------- */
  var nav = document.getElementById("nav");
  function onScroll() {
    if (nav) nav.classList.toggle("scrolled", window.scrollY > 8);
  }
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();

  /* ---------- Reveal on scroll ---------- */
  var revealEls = document.querySelectorAll(".reveal");
  if ("IntersectionObserver" in window && !reduceMotion) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add("visible");
          io.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12, rootMargin: "0px 0px -40px 0px" });
    revealEls.forEach(function (el) { io.observe(el); });
  } else {
    revealEls.forEach(function (el) { el.classList.add("visible"); });
  }

  /* ---------- Animated counters ---------- */
  function animateCounter(el) {
    var target = parseInt(el.getAttribute("data-count"), 10);
    if (isNaN(target)) return;
    if (reduceMotion) { el.textContent = String(target); return; }
    var duration = 1400;
    var start = null;
    function step(ts) {
      if (!start) start = ts;
      var p = Math.min((ts - start) / duration, 1);
      var eased = 1 - Math.pow(1 - p, 3);
      el.textContent = String(Math.round(eased * target));
      if (p < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  }

  var counters = document.querySelectorAll("[data-count]");
  if ("IntersectionObserver" in window) {
    var cio = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          animateCounter(entry.target);
          cio.unobserve(entry.target);
        }
      });
    }, { threshold: 0.6 });
    counters.forEach(function (el) { cio.observe(el); });
  } else {
    counters.forEach(animateCounter);
  }

  /* ---------- Rotating greeting ---------- */
  var greetings = ["Dia duit", "Hello", "Ahoy", "Fáilte", "Well hello"];
  var greetingEl = document.getElementById("greeting");
  if (greetingEl && !reduceMotion) {
    var gi = 0;
    setInterval(function () {
      gi = (gi + 1) % greetings.length;
      greetingEl.style.opacity = "0";
      setTimeout(function () {
        greetingEl.textContent = greetings[gi];
        greetingEl.style.opacity = "1";
      }, 300);
    }, 3800);
    greetingEl.style.transition = "opacity .3s";
  }

  /* ---------- Pi architecture: flow highlighting ---------- */
  var archStage = document.querySelector(".arch-stage");
  if (archStage) {
    var archFlows = archStage.querySelectorAll(".arch-flow");
    if (reduceMotion) {
      archStage.querySelectorAll(".arch-pulse").forEach(function (p) { p.remove(); });
    }
    archStage.querySelectorAll(".arch-card").forEach(function (card) {
      var node = card.getAttribute("data-node");
      card.addEventListener("mouseenter", function () {
        archFlows.forEach(function (f) {
          var links = (f.getAttribute("data-link") || "").split(" ");
          f.classList.toggle("lit", links.indexOf(node) !== -1);
        });
      });
      card.addEventListener("mouseleave", function () {
        archFlows.forEach(function (f) { f.classList.remove("lit"); });
      });
    });
  }

  /* ---------- "Currently" terminal: staged playback ---------- */
  var term = document.getElementById("currently");
  if (term && "IntersectionObserver" in window && !reduceMotion) {
    term.classList.add("anim");
    var playTerm = function () { term.classList.add("play"); };
    var termIo = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          playTerm();
          termIo.disconnect();
        }
      });
    }, { threshold: 0.45 });
    termIo.observe(term);
    /* safety net: never leave the output hidden if the observer never fires */
    setTimeout(playTerm, 6000);
  }

  /* ---------- Boot splash (homepage, once per session) ---------- */
  var bootScreen = document.getElementById("boot");
  if (bootScreen && document.documentElement.classList.contains("boot")) {
    var bootLines = [
      "Mounted /dev/maritime",
      "Started rtl-sdr — 162 MHz antenna locked",
      "Started ais-catcher — decoding ships",
      "Started noaa-sched — pass recorder armed",
      "Started adguard-home — DNS for the house",
      "Started tailscale — tailnet up",
      "Started cs2-dashboard :8001",
      "Started cs2-tracker :8092 — personal stats live",
      "Started shelfmate :8086 — book recs live",
      "Started maritime-dashboard :8000 — kiosk link up",
      "Started radar-agent — daily loop armed",
      "Started loop-heartbeat — dead-man's switch armed",
      "Started ntfy — notifications on tap",
      "Started pi-backup — nightly archives, Sunday drills",
      "Reached target — all stations reporting"
    ];
    var bootLinesEl = document.getElementById("boot-lines");
    var bootCmdLine = document.getElementById("boot-cmd-line");
    var bootCmd = document.getElementById("boot-cmd");
    var bootOut = document.getElementById("boot-out");
    var bootDone = false;
    var bootTimers = [];
    var bootStartedAt = 0;

    var bootFinish = function () {
      if (bootDone) return;
      bootDone = true;
      bootTimers.forEach(function (t) { clearTimeout(t); });
      bootScreen.classList.add("done");
      try { sessionStorage.setItem("booted", "1"); } catch (e) { /* private mode */ }
      setTimeout(function () {
        document.documentElement.classList.remove("boot");
        if (bootScreen.parentNode) bootScreen.parentNode.removeChild(bootScreen);
      }, 750);
    };

    /* clicks inside the first 800ms are usually just "focus the tab" —
       don't let them kill the boot before it starts */
    bootScreen.addEventListener("click", function () {
      if (Date.now() - bootStartedAt < 800) return;
      bootFinish();
    });
    document.addEventListener("keydown", bootFinish);

    var bootBegin = function () {
      bootStartedAt = Date.now();
      var bootAt = 500;
      bootLines.forEach(function (text) {
        bootAt += 120 + Math.random() * 130;
        bootTimers.push(setTimeout(function () {
          var row = document.createElement("div");
          row.className = "boot-line";
          var ok = document.createElement("span");
          ok.className = "boot-ok";
          ok.textContent = "[  OK  ]";
          row.appendChild(ok);
          row.appendChild(document.createTextNode(text));
          bootLinesEl.appendChild(row);
        }, bootAt));
      });

      /* typed ./welcome.sh once the units settle */
      bootAt += 550;
      bootTimers.push(setTimeout(function () {
        bootCmdLine.hidden = false;
        var cmd = "./welcome.sh";
        var i = 0;
        var typer = setInterval(function () {
          if (bootDone) { clearInterval(typer); return; }
          if (i < cmd.length) {
            bootCmd.textContent += cmd.charAt(i++);
          } else {
            clearInterval(typer);
            bootTimers.push(setTimeout(function () {
              bootOut.hidden = false;
              bootTimers.push(setTimeout(bootFinish, 950));
            }, 320));
          }
        }, 38);
      }, bootAt));
    };

    /* if the page loads in a background tab, hold the boot until the
       visitor actually looks at it */
    if (document.visibilityState === "visible") {
      bootBegin();
    } else {
      var bootOnVisible = function () {
        if (document.visibilityState === "visible") {
          document.removeEventListener("visibilitychange", bootOnVisible);
          bootBegin();
        }
      };
      document.addEventListener("visibilitychange", bootOnVisible);
    }
  }

  /* ---------- Footer year ---------- */
  var year = document.getElementById("year");
  if (year) year.textContent = String(new Date().getFullYear());
})();
