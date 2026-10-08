# Acceptance criteria — FitFindr

Five criteria that say what "working" means for this agent, written in unit 3
**before** any results existed.

An acceptance criterion names a target: a number, a count, a rate, or something
a person could plainly observe. *"The agent handles errors"* is an opinion.
*"When search returns nothing, the agent stops before calling the second tool,
in 5 of 5 tries"* is a criterion.

Under each one, write a sentence or two on **why that target** and not a
stricter one. A reason that says something about your tools, your loop, or the
data earns credit; *"80% seemed reasonable"* does not.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

**Two are written for you. You write three.**

---

## 1. A matching query completes all three tools

Given a query that matches at least one listing, the agent completes all three
tool calls and returns a fit card — in at least 4 of 5 tries.

**Why this target:**
`search_listings` and the regex parser are deterministic, so the same query
gives the same results on every run. A wording miss (say "denim jacket" against
a listing tagged only "jean jacket") would fail all 5 runs, not 1, so I rule it
out by choosing a query I have checked against the data. What does vary between
runs is the two model calls, `suggest_outfit` and `create_fit_card`: a rate
limit, a timeout or an empty reply can sink one run. 4 of 5 leaves room for one
transient model failure without hiding a loop bug, which would fail every run.

---

## 2. An impossible query stops before the second tool

Given a query that matches no listings, the agent stops before calling
`suggest_outfit` and returns a message naming what to change — 5 of 5 tries.

**Why this target:**
The loop retries without size, then without the price cap, before it gives up,
so the query has to be impossible on its description alone: no listing shares a
keyword with "designer ballgown", whatever the size or price. The stop is then a
deterministic check on an empty list in `agent.py::run_agent`, and no model call
happens before it, so nothing can vary between runs. That is why the bar is 5 of
5 rather than 4.

---

## 3. The item search picked is the item suggest_outfit actually used

On a matching query, with `suggest_outfit` and `create_fit_card` wrapped so each
records the `id` of the item it received, all of these are the same `id`: the
item `suggest_outfit` received, the item `create_fit_card` received,
`session["selected_item"]`, and the first entry of `session["search_results"]`
from the final search — in 5 of 5 runs.

**Why this target:**
Passing the selected item along is plain handoff through the session — no model
call, no branching — so nothing should change between runs. A mismatch would
mean a real bug in the loop's data flow, not normal variation. The "final
search" wording matters: the loop overwrites `search_results` on every retry, so
a stale item from an earlier, emptier search is the failure this catches.

---

## 4. The fit card gives different words on repeat runs

Given the same item and outfit passed to `create_fit_card` 5 times, with
`CACHE_ENABLED` left on as shipped, at least 4 of the 5 captions have a first
sentence (text up to the first `.`, `!` or `?`) that no other caption shares, and
at least 4 of the 5 captions contain the item's price (for example "$38").

**Why this target:**
`TEMPERATURE` is 0.9, so the wording should vary, but two captions can still
open alike by chance; allowing 4 distinct openings out of 5 tolerates one
collision. It still catches the two real failures: the cache handing back the
same text five times (1 distinct opening) and `TEMPERATURE` set to 0. The price
check is separate because the model can drop it from a caption that reads well;
the prompt asks for it, so 4 of 5 allows one lapse.

---

## 5. Search results respect the price ceiling

Calling `search_listings` directly with five different `max_price` values (15,
20, 30, 45, 100), each paired with a description that returns at least one
listing, every listing returned has `price <= max_price` — and a ceiling equal
to a listing's exact price includes that listing. 5 of 5 ceilings.

**Why this target:**
This is a plain numeric filter in `tools.py::search_listings` — no model call
and no fuzzy matching — so it behaves the same on every run, and a broken
filter fails every time it's broken. Each case must return something, because an
empty list would satisfy "every listing is under the ceiling" without proving
anything. The boundary case is there because the tool is specified as
inclusive. This tests the tool, not the agent: the loop drops the price cap on
a retry, and that is recorded in `session["relaxed"]`.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 4 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath it, like this:

         ## 4. Something about the fit card

         The fit card is different every time.

         **Why this target:** ...

         > **Revised in unit 4:** For 5 different items, the 5 fit cards share
         > no opening sentence.
         >
         > **Why revised:** "different" wasn't checkable — two cards that
         > differed by one word still counted. The new version is something I
         > can actually score.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "I said the empty search stops it 5 of 5 times, but I got 3 of 5,
            so 3 of 5 is more realistic."

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.
     ───────────────────────────────────────────────────────────────────────── -->
