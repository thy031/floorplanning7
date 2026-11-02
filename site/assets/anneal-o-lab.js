/**
 * Anneal-O toy-box lab: fit blocks in a box, score 36 vs 1044, SA swaps.
 */
(function () {
  const OUTLINE = { w: 10, h: 8 };
  const GOLDEN = {
    A: { x: 0, y: 0, w: 3, h: 2 },
    B: { x: 3, y: 0, w: 2, h: 3 },
    C: { x: 5, y: 0, w: 2, h: 2 },
    D: { x: 0, y: 2, w: 3, h: 1 },
    E: { x: 7, y: 0, w: 2, h: 2 },
  };
  const BAD = {
    A: { x: 0, y: 0, w: 3, h: 2 },
    B: { x: 3, y: 0, w: 2, h: 3 },
    C: { x: 5, y: 0, w: 2, h: 2 },
    D: { x: 0, y: 2, w: 3, h: 1 },
    E: { x: 9, y: 0, w: 2, h: 2 },
  };
  const COLORS = {
    A: "#c45c26",
    B: "#2a6f6a",
    C: "#3d5a80",
    D: "#6b4c9a",
    E: "#b08900",
  };
  const GAP_POINTS = 44;
  const PENALTY = 1000;
  const TIDY = 36;
  const POCKET = { x: 7, y: 0, w: 2, h: 2 };

  function clone(pack) {
    const out = {};
    for (const [id, r] of Object.entries(pack)) out[id] = { ...r };
    return out;
  }
  function list(pack) {
    return Object.entries(pack).map(([id, r]) => ({ id, ...r }));
  }
  function overlap(a, b) {
    return !(a.x + a.w <= b.x || b.x + b.w <= a.x || a.y + a.h <= b.y || b.y + b.h <= a.y);
  }
  function inside(r) {
    return r.x >= 0 && r.y >= 0 && r.x + r.w <= OUTLINE.w && r.y + r.h <= OUTLINE.h;
  }
  function isLegal(pack) {
    const items = list(pack);
    for (const r of items) if (!inside(r)) return false;
    for (let i = 0; i < items.length; i++) {
      for (let j = i + 1; j < items.length; j++) {
        if (overlap(items[i], items[j])) return false;
      }
    }
    return true;
  }
  function trueCost(pack) {
    return isLegal(pack) ? TIDY : GAP_POINTS + PENALTY;
  }
  function swapIds(pack, a, b) {
    const next = clone(pack);
    const ax = next[a].x;
    const ay = next[a].y;
    next[a].x = next[b].x;
    next[a].y = next[b].y;
    next[b].x = ax;
    next[b].y = ay;
    return next;
  }
  function slideEHome(pack) {
    const next = clone(pack);
    next.E.x = POCKET.x;
    next.E.y = POCKET.y;
    return next;
  }

  window.mountAnnealOLab = function mountAnnealOLab(root) {
    if (!root) return;

    const state = {
      pack: clone(BAD),
      selected: null,
      step: 1,
      temp: 80,
      forgetPenalty: false,
      forgetRecount: false,
      coolFast: false,
      frozenScore: null,
      lastSpeech: "I'm Anneal-O. Let's tidy this toy box — fewer points win!",
      swapped: false,
    };

    function scoredCost(pack) {
      if (state.forgetPenalty) return GAP_POINTS;
      return trueCost(pack);
    }
    function shownCost() {
      if (state.forgetRecount && state.frozenScore != null) return state.frozenScore;
      return scoredCost(state.pack);
    }
    function tempValue() {
      return state.coolFast ? 1 : state.temp;
    }

    root.innerHTML = `
      <section class="anneal-lab" aria-label="Anneal-O toy-box lab">
        <h2>Interactive lab: Anneal-O’s toy box</h2>
        <div class="anneal-story">
          <p class="kicker">The main goal</p>
          <p class="goal">Imagine a magic toy box and wooden blocks of different sizes. Fit every block inside neatly — no overlapping, and nothing sticking out over the edges.</p>
        </div>
        <div class="score-cards">
          <article class="score-card good">
            <h3>Tidy box <span>good</span></h3>
            <p class="num">36</p>
            <p>All blocks fit with small gaps. Lowest score wins.</p>
          </article>
          <article class="score-card bad">
            <h3>Monster penalty <span>bad</span></h3>
            <p class="num">+1,000</p>
            <p>Even one spill or squash and the referee adds 1,000 bad points.</p>
          </article>
          <article class="score-card messy">
            <h3>Messy box</h3>
            <p class="num">1,044</p>
            <p>44 (gaps) + 1,000 (penalty) = 1,044. That is our starting mess.</p>
          </article>
        </div>
        <div class="phase-cards">
          <article class="phase hot">
            <h3>Hot phase 🔴</h3>
            <p>Anneal-O is energetic. It swaps blocks fast and may try silly, messy setups just to explore.</p>
          </article>
          <article class="phase cool">
            <h3>Cooling phase 🔵</h3>
            <p>The timer cools. Anneal-O calms down and mostly accepts moves that make the box tidier.</p>
          </article>
        </div>
        <div class="steps" role="tablist">
          <button type="button" class="step-card is-on" data-step="1">
            <div class="n">STEP 1</div>
            <h3>The messy start</h3>
            <p>Cost 1,044 — block E spills out. Penalty on.</p>
          </button>
          <button type="button" class="step-card" data-step="2">
            <div class="n">STEP 2</div>
            <h3>The magic swap</h3>
            <p>Click E, then the empty pocket — or play the 3-step story.</p>
          </button>
          <button type="button" class="step-card" data-step="3">
            <div class="n">STEP 3</div>
            <h3>The golden solution</h3>
            <p>Cost 36. Penalty gone. Anneal-O wins!</p>
          </button>
        </div>
        <div class="anneal-grid">
          <div class="anneal-box">
            <h3>Toy box (10 × 8)</h3>
            <p class="hint">Click a block to pick it. Click another block to swap corners. Click the dashed pocket to slide E home.</p>
            <div class="anneal-svg-wrap" id="anneal-svg"></div>
            <p class="hint" id="anneal-pick-hint"></p>
          </div>
          <div class="anneal-side">
            <div class="scoreboard messy" id="anneal-score">
              <div>Referee score <small>(lower is better)</small></div>
              <div class="score-big bad" id="anneal-score-num">1,044</div>
              <div class="score-eq" id="anneal-score-eq"></div>
            </div>
            <div class="anneal-robot">
              <div class="robot-head">
                <div class="robot-face hot" id="anneal-face">🤖</div>
                <div>
                  <strong>Anneal-O</strong>
                  <p class="speech" id="anneal-speech"></p>
                </div>
              </div>
              <div class="temp-row">
                <label for="anneal-temp"><span>Temperature</span><span id="anneal-temp-label">Hot</span></label>
                <input id="anneal-temp" type="range" min="1" max="100" value="80">
                <div class="temp-legend"><span>🔵 Cool — only neater</span><span>🔴 Hot — wild ideas OK</span></div>
              </div>
              <div class="anneal-actions">
                <button type="button" class="btn btn-primary" id="anneal-play">Play the 3-step story</button>
                <button type="button" class="btn btn-secondary" id="anneal-try">Let Anneal-O try a swap</button>
                <button type="button" class="btn btn-secondary" id="anneal-magic">Magic swap (E → pocket)</button>
                <button type="button" class="btn btn-ghost" id="anneal-reset">Reset messy start</button>
                <button type="button" class="btn btn-ghost" id="anneal-golden">Show golden</button>
                <button type="button" class="btn btn-secondary" id="anneal-recount" hidden>Recount score</button>
              </div>
              <div class="win-banner" id="anneal-win">🎉 Ta-da! All blocks snap inside. The 1,000 penalty vanishes and the score drops to 36. Anneal-O wins!</div>
            </div>
          </div>
        </div>
        <h3>3 mistakes to avoid — flip a switch and watch Anneal-O mess up</h3>
        <div class="pitfalls">
          <label class="pitfall">
            <input type="checkbox" id="pit-penalty">
            <div><strong>Forgetting the penalty</strong><span>If messy boxes are not punished, Anneal-O thinks spilling is fine (score stuck near 44).</span></div>
          </label>
          <label class="pitfall">
            <input type="checkbox" id="pit-recount">
            <div><strong>Forgetting to recount</strong><span>After a move the board changes, but the score stays frozen until you press Recount.</span></div>
          </label>
          <label class="pitfall">
            <input type="checkbox" id="pit-cool">
            <div><strong>Cooling down too fast</strong><span>Temperature snaps to ice-cold. Anneal-O refuses exploratory swaps and can stay stuck in the mess.</span></div>
          </label>
        </div>
      </section>
    `;

    const svgHost = root.querySelector("#anneal-svg");
    const speechEl = root.querySelector("#anneal-speech");
    const scoreEl = root.querySelector("#anneal-score");
    const scoreNum = root.querySelector("#anneal-score-num");
    const scoreEq = root.querySelector("#anneal-score-eq");
    const face = root.querySelector("#anneal-face");
    const tempInput = root.querySelector("#anneal-temp");
    const tempLabel = root.querySelector("#anneal-temp-label");
    const win = root.querySelector("#anneal-win");
    const recountBtn = root.querySelector("#anneal-recount");
    const pickHint = root.querySelector("#anneal-pick-hint");

    function say(msg) {
      state.lastSpeech = msg;
      speechEl.textContent = msg;
    }

    function draw() {
      const pad = 0.6;
      const maxX = 12;
      const cell = 32;
      const vb = `${-pad} ${-pad} ${maxX + pad * 2} ${OUTLINE.h + pad * 2}`;
      const items = list(state.pack);
      const grid = [];
      for (let x = 0; x <= OUTLINE.w; x++) {
        grid.push(`<line x1="${x}" y1="0" x2="${x}" y2="${OUTLINE.h}" stroke="#d5cdc0" stroke-width="0.03"/>`);
      }
      for (let y = 0; y <= OUTLINE.h; y++) {
        grid.push(`<line x1="0" y1="${y}" x2="${OUTLINE.w}" y2="${y}" stroke="#d5cdc0" stroke-width="0.03"/>`);
      }
      const pocketBusy = items.some((r) => overlap(r, POCKET));
      const pocket = pocketBusy
        ? ""
        : `<rect class="anneal-pocket" data-pocket="1" x="${POCKET.x}" y="${POCKET.y}" width="${POCKET.w}" height="${POCKET.h}"
             fill="rgba(15,107,92,.08)" stroke="#0f6b5c" stroke-width="0.08" stroke-dasharray="0.18 0.12" rx="0.08"/>
           <text x="${POCKET.x + 1}" y="${POCKET.y + 1.15}" text-anchor="middle" font-size="0.38" fill="#0f6b5c">empty pocket</text>`;
      const blocks = items
        .map((r) => {
          const sel = state.selected === r.id;
          const spill = !inside(r);
          return `<g class="anneal-block" data-id="${r.id}">
            <rect x="${r.x + 0.06}" y="${r.y + 0.06}" width="${r.w - 0.12}" height="${r.h - 0.12}"
              fill="${COLORS[r.id]}" stroke="${sel ? "#1c2421" : spill ? "#a33b3b" : "#fffdf8"}"
              stroke-width="${sel ? 0.14 : 0.07}" rx="0.12"/>
            <text x="${r.x + r.w / 2}" y="${r.y + r.h / 2 + 0.18}" text-anchor="middle"
              font-size="0.55" font-weight="700" fill="#fffdf8">${r.id}</text>
            ${spill ? `<text x="${r.x + r.w / 2}" y="${r.y - 0.18}" text-anchor="middle" font-size="0.32" fill="#a33b3b">spills!</text>` : ""}
          </g>`;
        })
        .join("");
      svgHost.innerHTML = `<svg viewBox="${vb}" role="img" aria-label="Toy box with five blocks">
        <rect x="-0.15" y="-0.15" width="${OUTLINE.w + 0.3}" height="${OUTLINE.h + 0.3}" fill="#fffdf8" stroke="#1c2421" stroke-width="0.12" rx="0.12"/>
        ${grid.join("")}
        ${pocket}
        ${blocks}
      </svg>`;
      svgHost.querySelectorAll("[data-id]").forEach((g) => {
        g.addEventListener("click", () => onBlock(g.getAttribute("data-id")));
      });
      const pocketEl = svgHost.querySelector("[data-pocket]");
      if (pocketEl) pocketEl.addEventListener("click", onPocket);
    }

    function freezeIfNeeded() {
      if (state.forgetRecount && state.frozenScore == null) {
        state.frozenScore = scoredCost(state.pack);
      }
    }

    function onBlock(id) {
      if (!state.selected) {
        state.selected = id;
        pickHint.textContent = `Picked ${id}. Click another block to swap, or the empty pocket.`;
        draw();
        return;
      }
      if (state.selected === id) {
        state.selected = null;
        pickHint.textContent = "";
        draw();
        return;
      }
      freezeIfNeeded();
      state.pack = swapIds(state.pack, state.selected, id);
      state.swapped = true;
      state.step = isLegal(state.pack) ? 3 : 2;
      say(`Swapped ${state.selected} ↔ ${id}. Always recount after a move!`);
      state.selected = null;
      pickHint.textContent = "";
      render();
    }

    function onPocket() {
      freezeIfNeeded();
      if (state.selected && state.selected !== "E") {
        say(`The pocket is sized for E (2×2). Pick E, then the pocket.`);
        return;
      }
      state.pack = slideEHome(state.pack);
      state.swapped = true;
      state.selected = null;
      state.step = 3;
      say("Magic swap! E slides into the empty pocket. Penalty gone if the box is legal.");
      pickHint.textContent = "";
      render();
    }

    function render() {
      const legal = isLegal(state.pack);
      const cost = shownCost();
      const actual = trueCost(state.pack);
      scoreNum.textContent = cost.toLocaleString();
      scoreNum.className = "score-big " + (cost >= PENALTY ? "bad" : "good");
      scoreEl.className = "scoreboard " + (legal && !state.forgetPenalty ? "tidy" : "messy");
      if (state.forgetPenalty) {
        scoreEq.textContent = "Bug on: no monster penalty. Score looks like gaps only.";
      } else if (state.forgetRecount && state.frozenScore != null && state.frozenScore !== actual) {
        scoreEq.textContent = "Score is frozen — press Recount! (true score may have changed)";
      } else if (legal) {
        scoreEq.textContent = "Tidy box score: 36 points. No penalty.";
      } else {
        scoreEq.textContent = "44 (gaps) + 1,000 (penalty) = 1,044 points!";
      }
      const t = tempValue();
      const hot = t >= 50;
      face.className = "robot-face " + (hot ? "hot" : "cool");
      face.textContent = hot ? "🔥" : "🧊";
      tempLabel.textContent = state.coolFast ? "Stuck cold" : hot ? "Hot" : "Cool";
      tempInput.disabled = state.coolFast;
      if (state.coolFast) tempInput.value = "1";
      recountBtn.hidden = !state.forgetRecount;
      win.classList.toggle("show", legal && !state.forgetPenalty && !(state.forgetRecount && state.frozenScore === 1044));
      root.querySelectorAll("[data-step]").forEach((btn) => {
        btn.classList.toggle("is-on", Number(btn.dataset.step) === state.step);
      });
      speechEl.textContent = state.lastSpeech;
      draw();
    }

    root.querySelectorAll("[data-step]").forEach((btn) => {
      btn.addEventListener("click", () => {
        const n = Number(btn.dataset.step);
        state.step = n;
        state.selected = null;
        state.frozenScore = null;
        if (n === 1) {
          state.pack = clone(BAD);
          say("Messy start: E sticks out. The referee hands us 1,000 bad points. Cost 1,044.");
        } else if (n === 2) {
          state.pack = clone(BAD);
          say("Hot phase: I might try wild swaps. Pick E and the empty pocket for the teaching swap.");
        } else {
          state.pack = clone(GOLDEN);
          say("Golden packing! Every block is inside. Score 36. That's what cooling should prefer.");
        }
        render();
      });
    });

    tempInput.addEventListener("input", () => {
      state.temp = Number(tempInput.value);
      if (!state.coolFast) {
        say(state.temp >= 50
          ? "Hot phase: I'm energetic. I may accept a messier swap just to explore."
          : "Cooling phase: I calm down. I mostly accept moves that tidy the box.");
      }
      render();
    });

    root.querySelector("#anneal-play").addEventListener("click", () => {
      const playBtn = root.querySelector("#anneal-play");
      playBtn.disabled = true;
      state.forgetPenalty = false;
      state.forgetRecount = false;
      state.coolFast = false;
      state.frozenScore = null;
      root.querySelector("#pit-penalty").checked = false;
      root.querySelector("#pit-recount").checked = false;
      root.querySelector("#pit-cool").checked = false;
      const wait = (ms) => new Promise((r) => setTimeout(r, ms));
      (async () => {
        state.pack = clone(BAD);
        state.step = 1;
        state.selected = null;
        state.temp = 80;
        tempInput.value = "80";
        say("Step 1 — messy start. Blocks spill out, so the referee adds 1,000 bad points. Score 1,044.");
        render();
        await wait(1400);
        state.step = 2;
        state.selected = "E";
        say("Step 2 — magic swap! Anneal-O picks two places and slides E toward the empty pocket.");
        render();
        await wait(1200);
        state.pack = slideEHome(state.pack);
        state.selected = null;
        state.step = 3;
        state.temp = 20;
        tempInput.value = "20";
        say("Step 3 — golden solution. Penalty vanishes. Score 36. Anneal-O wins!");
        render();
        playBtn.disabled = false;
      })();
    });

    root.querySelector("#anneal-try").addEventListener("click", () => {
      const ids = Object.keys(state.pack);
      let a = ids[Math.floor(Math.random() * ids.length)];
      let b = ids[Math.floor(Math.random() * ids.length)];
      if (a === b) b = ids[(ids.indexOf(a) + 1) % ids.length];
      const before = scoredCost(state.pack);
      freezeIfNeeded();
      const next = swapIds(state.pack, a, b);
      const after = scoredCost(next);
      const delta = after - before;
      const t = Math.max(tempValue(), 0.5);
      const accept = delta <= 0 || Math.random() < Math.exp(-delta / t);
      if (state.coolFast && delta > 0) {
        say(`Too cold! I refuse ${a}↔${b} because the score would get worse (Δ=${delta}). I'm stuck exploring.`);
        render();
        return;
      }
      if (accept) {
        state.pack = next;
        state.swapped = true;
        state.step = isLegal(state.pack) ? 3 : 2;
        say(delta < 0
          ? `Accepted ${a}↔${b}: neater by ${-delta} points.`
          : delta === 0
            ? `Accepted ${a}↔${b}: score unchanged${state.forgetPenalty ? " (penalty is off, so mess looks fine)" : ""}.`
            : `Hot enough to accept a sillier ${a}↔${b} (Δ=+${delta}).`);
      } else {
        say(`Rejected ${a}↔${b}. Δ=+${delta} is too messy for this temperature.`);
      }
      render();
    });

    root.querySelector("#anneal-magic").addEventListener("click", onPocket);
    root.querySelector("#anneal-reset").addEventListener("click", () => {
      state.pack = clone(BAD);
      state.step = 1;
      state.selected = null;
      state.frozenScore = state.forgetRecount ? scoredCost(BAD) : null;
      say("Back to the spill. Cost should be 1,044 if the penalty is on.");
      render();
    });
    root.querySelector("#anneal-golden").addEventListener("click", () => {
      freezeIfNeeded();
      state.pack = clone(GOLDEN);
      state.step = 3;
      say("Study layout: golden legal packing. Cost 36.");
      render();
    });
    recountBtn.addEventListener("click", () => {
      state.frozenScore = null;
      say("Recounted! After every swap, rescore immediately.");
      render();
    });

    root.querySelector("#pit-penalty").addEventListener("change", (e) => {
      state.forgetPenalty = e.target.checked;
      say(state.forgetPenalty
        ? "Penalty off. I no longer fear spills — messy boxes look cheap. Don't do this!"
        : "Penalty back on. Illegal packs cost about 1,044 again.");
      render();
    });
    root.querySelector("#pit-recount").addEventListener("change", (e) => {
      state.forgetRecount = e.target.checked;
      state.frozenScore = e.target.checked ? scoredCost(state.pack) : null;
      say(state.forgetRecount
        ? "Recount is frozen. Move blocks and watch the score lag until you press Recount."
        : "Auto-recount is back.");
      render();
    });
    root.querySelector("#pit-cool").addEventListener("change", (e) => {
      state.coolFast = e.target.checked;
      say(state.coolFast
        ? "I froze instantly. I will not take exploratory swaps. From a mess, I may give up."
        : "Warming back up. Hot first, then cool — that's annealing.");
      render();
    });

    say(state.lastSpeech);
    render();
  };

  function boot() {
    const root = document.getElementById("anneal-o-root");
    if (root) window.mountAnnealOLab(root);
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();
})();
