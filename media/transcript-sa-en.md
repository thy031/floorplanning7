This is the narration from the Lab 07 clips. Timed from the Ava voiceover on `simulated_annealing_floorplan-short.mp4` (~2:38) and `simulated_annealing_floorplan-full.mp4` (~4:46). Technical terms corrected from the slides (`saSwap`, Metropolis, HPWL, \(e^{-\Delta C/T}\), B*-tree).

---

## Short clip (~2:38)

0:00 — Title
How do you arrange rectangular circuit blocks inside a tight chip boundary perfectly, without getting trapped in overlapping chaos or bad local guesses? That’s simulated annealing floorplan search.

0:11 — Toy instance
Take this toy floorplanning layout with modules A through E.

0:15 — Cost model
To separate great floorplans from invalid layouts, we define a cost function that heavily penalizes illegality. Our cost model adds a massive 1,000-point penalty tax whenever a packing is illegal.

0:33 — Energy landscape
The energy landscape: bad seed versus golden packing. The bad overflow seed sits at a cost of about 1,044, dominated almost entirely by that 1,000-point penalty tax. But here is the goal. The golden legal packing drops below the penalty floor to just 36, consisting purely of deadspace and a small wirelength proxy with zero illegality tax.

0:53 — Execution loop
Annealing must navigate this steep energy landscape to move from illegal chaos to legal perfection. Execution loop and the Metropolis criterion. So how does annealing find the global optimum? In the pseudocode execution loop, the algorithm proposes neighbor moves, such as an saSwap that exchanges module origin coordinates, and evaluates them using the Metropolis criterion. At high initial temperatures T, worsening moves are accepted with probability \(P = e^{-\Delta C / T}\), allowing the search to escape bad local seeds.

1:29 — Cooling
As the temperature cools down, cost falls below 1,000 and legality flips to true — exactly what a proper cooling schedule should prefer.

1:38 — Representation
Representation and topology edits. But here is the friction: annealing is only as good as its move set. Simple coordinate swapping serves as a starting point, but pairing annealing with B*-trees, sequence pairs, or soft-module aspect-ratio edits — like reshaping module A from 3×2 to 2×3 — unlocks true structural flexibility in advanced VLSI layouts.

2:04 — Common traps
In your implementation, watch out for these common traps: optimizing deadspace while accepting illegal states without penalty; forgetting to rescore and re-evaluate placement cost immediately after a swap; cooling so fast (quenching) that you never escape the initial bad seed.

2:24 — Your turn
Now it’s your turn in the lab. Open simulated-annealing-fp, demonstrate one improve step from bad to golden, match the starter metrics, take the quiz, and report your final parts, cost, and legality.

### Code slide (on screen)

```text
S_cand = saSwap(S_curr)   # swap origin coordinates
delta_C = cost(S_cand) - cost(S_curr)
accept if delta_C <= 0
else if rand() < e^(-delta_C/T)
```

---

## Full lecture (~4:46)

0:00 — Title
Imagine trying to pack heavy wooden blocks into a display box in complete darkness. If a single block spills over the edge or overlaps another, a strict referee hits you with a massive 1,000-point penalty fine. That is the core challenge of simulated annealing floorplan search.

0:16 — Why SA
In physical chip layout design, simulated annealing (SA) optimizes module placement by balancing spatial metrics while strictly outlawing illegal overlaps or boundary spills. Under our cost model, a messy initial overflow seed sits at an unbearable cost near 1,044, whereas a golden legal packing drops down to just 36. Simulated annealing naturally guides us out of that high-penalty chaos toward legal, low-cost layout perfection.

0:47 — Cost function
To separate great floorplans from bad ones, the algorithm relies on a clear composite cost function:

cost = C_deadspace + C_HPWL + C_legality

This function heavily penalizes any illegality.

1:03 — Pseudocode
In our pseudocode workflow, we start with an initial placement S0, a high starting temperature T0, and a steady cooling rate alpha. As long as temperature T stays above T_min, the algorithm explores neighboring layouts using saSwap, computes ΔC = cost(S_candidate) − cost(S_current), and tests the Metropolis acceptance rule. If a candidate placement is accepted and proves to be legal and lower in cost than S_best, we update S_best. Then we cool down with T = T × alpha.

1:38 — Two benchmark states
Let’s look at our two benchmark states side by side. On one side sits the bad overflow seed, marked false for legality due to overlapping modules and boundary spills, triggering that brutal +1,000 penalty tax on top of a deadspace + HPWL score of about 44, bringing total cost to approximately 1,044. On the other side sits our golden legal packing, marked true for legality, paying a penalty tax of 0, and keeping deadspace + HPWL down to about 36. With just one smart teaching step, we swap out the chaotic seed for the golden legal packing.

2:17 — Three cost terms
Examining our three cost terms in detail: C_deadspace measures wasted empty room inside the bounding box; C_HPWL acts as a half-perimeter wirelength proxy measuring routing distance; and C_legality slams down a +1,000 tax the moment an overlap or overflow occurs.

2:36 — Phase 1
Phase 1 opens at the bad overflow seed with a score of 1,044.4, dominated by the +1,000 penalty.

2:45 — Phase 2
In phase 2, we trigger our perturbation move engine, saSwap, which selects two modules at random and exchanges their lower-left (x, y) origin coordinates, while keeping their dimensions fixed. Under the Metropolis rule, helpful moves with ΔC ≤ 0 are accepted immediately, whereas worsening moves with ΔC > 0 are accepted with probability \(P_{\mathrm{accept}} = e^{-\Delta C / T}\). High temperatures give the algorithm freedom to escape bad seeds early on, while lower temperatures cool the solution into an optimal local minimum.

3:20 — Phase 3
In phase 3, executing saSwap on the conflicting modules removes the +1,000 penalty tax. Total cost falls below 1,000 to 35.7, reflecting deadspace and an HPWL proxy of 12.5, and legality flips to true, which is exactly what a cooling schedule should prefer.

3:40 — Move set
Of course, an annealing search is only as effective as the quality of its move set and spatial representation. While origin-coordinate swapping provides a simple baseline, production floorplanners pair annealing with B*-tree or sequence-pair representations to guarantee zero overlap by construction, alongside soft-module sizing and macro placement in the labs that follow.

4:04 — Pitfalls
Be careful to avoid three critical implementation pitfalls: accepting illegal states without applying the +1,000 penalty tax; forgetting to rescore and re-evaluate cost(S_candidate) immediately after an saSwap move; cooling temperature T too rapidly (quenching), which traps the algorithm inside the initial bad seed.

4:26 — Your turn
Demonstrate one improve step transitioning the layout from the bad overflow seed to the golden legal packing, bringing total cost below 1,000 and restoring legality to true. Next, we will extend our move set to include soft-module reshaping, flexing soft module A from a 3×2 to a 2×3 layout.

### Code slide (on screen)

```text
S_cand = saSwap(S_curr)
delta_C = cost(S_cand) - cost(S_curr)
IF delta_C <= 0 OR rand() < e^(-delta_C/T):
    S_curr = S_cand
    IF legal and better: S_best = S_curr
T = T * alpha
```
