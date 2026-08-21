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

  /* ---------- Copy email ---------- */
  var copyBtn = document.getElementById("copy-email");
  var copyLabel = document.getElementById("copy-email-label");
  if (copyBtn) {
    copyBtn.addEventListener("click", function () {
      var email = copyBtn.getAttribute("data-email");
      var done = function () {
        copyBtn.classList.add("copied");
        if (copyLabel) copyLabel.textContent = "Copied — " + email;
        setTimeout(function () {
          copyBtn.classList.remove("copied");
          if (copyLabel) copyLabel.textContent = "Copy email address";
        }, 2400);
      };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(email).then(done, done);
      } else {
        var ta = document.createElement("textarea");
        ta.value = email;
        document.body.appendChild(ta);
        ta.select();
        try { document.execCommand("copy"); } catch (e) { /* no-op */ }
        document.body.removeChild(ta);
        done();
      }
    });
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
    var termIo = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          term.classList.add("play");
          termIo.disconnect();
        }
      });
    }, { threshold: 0.45 });
    termIo.observe(term);
  }

  /* ---------- Footer year ---------- */
  var year = document.getElementById("year");
  if (year) year.textContent = String(new Date().getFullYear());
})();
