# Lab 07 — Simulated annealing floorplan search

Local browser lab for **learn_floorplanning** module `module03-01-simulated-annealing-fp` (Lab 07). Toy instance: five rectangles **A–E** in a **10×8** outline.

Simulated annealing searches packings with:

1. Cost \(C = C_{\mathrm{deadspace}} + C_{\mathrm{HPWL}} + C_{\mathrm{legality}}\).
2. Neighbor move **saSwap** (swap two modules’ origin coordinates; sizes stay fixed).
3. Metropolis accept: take improvements always; take worsening moves with \(P = e^{-\Delta C / T}\).
4. Cool \(T \leftarrow T \times \alpha\) until \(T_{\min}\).

Live course pages:

- [Simulated annealing floorplan lab](https://yongfu-li.github.io/eda-learning/courses/learn_floorplanning/labs/simulated-annealing-fp/index.html)
- [simulated-annealing-fp tool](https://yongfu-li.github.io/eda-learning/tools/simulated-annealing-fp/index.html)
- [Module on GitHub](https://github.com/SJTU-YONGFU-RESEARCH-GRP/eda-learning/tree/main/courses/learn_floorplanning/module03-01-simulated-annealing-fp)

## Run the page

Serve from this folder so video, captions (`.vtt` as `text/vtt`), and relative assets load:

```bash
cd floorplanning_l7
python3 serve.py 8777
```

Open [http://127.0.0.1:8777/](http://127.0.0.1:8777/) (redirects to the lab) or the lab URL directly:

[http://127.0.0.1:8777/courses/learn_floorplanning/labs/simulated-annealing-fp/index.html](http://127.0.0.1:8777/courses/learn_floorplanning/labs/simulated-annealing-fp/index.html).

`serve.py` publishes **`site/`** on port **8777**. The real page is `site/courses/learn_floorplanning/labs/simulated-annealing-fp/index.html`: a thin shell that `pages.js` fills from `catalog.json`, Anneal-O, quiz, and `course-media/`. The root `index.html` in this folder only exists so GitHub Pages / a folder deploy has an entry point; it redirects into `site/`.

Plain `python3 -m http.server` from `site/` also works; use `serve.py` so WebVTT captions get the right MIME type.

Standalone tool (same Anneal-O board): [http://127.0.0.1:8777/tools/simulated-annealing-fp/index.html](http://127.0.0.1:8777/tools/simulated-annealing-fp/index.html).

## What is on the page

| Tab | Contents |
| --- | --- |
| **Lab** | Short (~2:38) or full (~4:46) clip. Captions are **in the player** (CC or ⋮ → Captions). Steps and quiz. |
| **Interactive lab** | Anneal-O toy box: messy start (1,044) → magic swap → golden (36). Hot vs cool, three pitfall switches |
| **Course notes** | Slide PDF generated with the explainer (`slides.pdf`) |

## Starter packing

Outline **10×8**. Modules A–E. Illegal layouts pay **+1,000**.

| State | Legal | Cost (approx.) |
| --- | --- | ---: |
| Bad overflow seed (E spills) | false | **1,044** (≈44 deadspace/HPWL + 1,000 penalty) |
| Golden legal packing | true | **36** (deadspace + HPWL proxy, no penalty) |

One teaching improve step: swap E into the empty pocket (or load golden). Cost falls below 1,000 and legality flips to true.

Cost sketch:

```text
cost = C_deadspace + C_HPWL + C_legality
S_cand = saSwap(S_curr)          # swap origin coordinates
delta_C = cost(S_cand) - cost(S_curr)
accept if delta_C <= 0
else if rand() < e^(-delta_C/T)
T = T * alpha
```

## Anneal-O playthrough

1. **Messy start** — E out of the box, score 1,044, penalty on.
2. **Magic swap** — click E then the dashed pocket (or play the 3-step story).
3. **Golden** — score 36, penalty gone.

Pitfall switches (leave them off for a fair run):

- Forgetting the **+1,000** legality tax.
- Forgetting to **rescore** after a swap.
- **Quenching** (cooling too fast) so pairwise swaps never escape the bad seed.

## Videos and captions

Under `media/` (sources) and `site/course-media/learn_floorplanning/module03-01-simulated-annealing-fp/` (what the lab page serves):

| File | Role |
| --- | --- |
| `video-short.mp4` / `simulated_annealing_floorplan-short.mp4` | Short clip (~2:38) |
| `video-full.mp4` / `simulated_annealing_floorplan-full.mp4` | Full lecture (~4:46) |
| `simulated_annealing_floorplan.mp4` | Combined (~7:23) |
| `sa-*-en.vtt` / `sa-*-zh.vtt` / `sa-*-bilingual.vtt` | Player tracks |
| `transcript-sa-en.md` / `transcript-sa-zh.md` | Timed narration (中文 terms locked below) |
| `media/watch.html` | Standalone player (serve `media/` if you open this file) |
| `simulated_annealing_floorplan.pdf` | Slide PDF generated with the videos |

Captions follow the English voiceover timeline. Rebuild VTT from the transcripts:

```bash
python3 media/generate_captions.py
```

That writes `media/captions/` and copies short/full tracks into `site/course-media/...`.

Locked 中文 terms (same table as the Chinese transcript):

| English | 中文 |
| --- | --- |
| Simulated annealing (SA) | 模拟退火 |
| Floorplan / floorplanning | 布局规划 |
| Outline | 轮廓 |
| Deadspace | 空白（死区） |
| HPWL | 半周长线长 |
| Metropolis | Metropolis 准则 |
| Cooling schedule | 降温日程 |
| Quenching | 淬火 |
| saSwap | saSwap |
| B*-tree | B*-树 |
| Sequence pair | 序列对 |
| Soft module | 软模块 |
| Golden packing | 黄金合法解 |
| Bad overflow seed | 溢出坏种子 |

Optional media rebuild (Ava TTS MP3s + matplotlib/moviepy; needs the project venv):

```bash
# from floorplanning_l7, after uv venv + reportlab matplotlib moviepy pillow
.venv/bin/python media/media_creation.py
```

## Quiz

Six recall items, all from the short/full clips (`transcript-sa-en.md`):

1. Illegal packings add a **+1,000** penalty tax.
2. Bad seed ≈ **1,044**, golden ≈ **36**.
3. **saSwap** exchanges origin coordinates and keeps sizes.
4. Metropolis: worsening moves accepted with \(P = e^{-\Delta C / T}\).
5. Annealing is only as good as its **move set** (B*-tree / sequence pair / soft-module edits).
6. **Quenching** = cooling too fast, stuck in the bad seed.

Passing score is 67%.

## Pitfalls (from the notes)

- Optimizing deadspace while accepting illegal states **without** the +1,000 tax.
- Forgetting to recompute `cost(S_candidate)` immediately after saSwap.
- Cooling \(T\) too fast (quenching) so the search never leaves the bad seed.
- Coordinate swap is a teaching baseline; production floorplanners pair SA with **B\*-trees** or **sequence pairs**. Soft-module reshape (A from 3×2 to 2×3) is the next lab.

## Layout

```text
floorplanning_l7/
  README.md
  serve.py                 HTTP server for site/ (WebVTT MIME)
  site/                    Local EDA Algorithms Platform slice
    assets/                pages.js, catalog.json, Anneal-O, quiz
    courses/learn_floorplanning/labs/simulated-annealing-fp/
    tools/simulated-annealing-fp/
    course-media/learn_floorplanning/module03-01-simulated-annealing-fp/
  media/
    transcript-sa-en.md
    transcript-sa-zh.md
    captions/              WebVTT (en / zh / bilingual)
    watch.html
    generate_captions.py
    media_creation.py      Animated explainer + PDF
    make_sa_video.py       Alternate gTTS paper-card clip
    simulated_annealing_floorplan*.mp4
```
