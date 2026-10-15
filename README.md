# FitFindr

> ### 👋 Start here
>
> **New to this repo? Read [RUNNING.md](RUNNING.md) first** — setup, every
> command, and what to do when something breaks.
>
> Once `python test.py` passes:
>
> ```bash
> python app.py listings --full -n 6      # read the data (Milestone 1)
> python app.py fields                    # what you can filter on
> python app.py ask 'vintage graphic tee under $30'
> ```
>
> All three tools are stubs, so that last command will do nothing useful yet.
> That's the starting position.

---
<!-- ═══════════════════════ UNIT 3 — THE BUILD ═══════════════════════ -->

## What This Does

FitFindr helps you shop for secondhand clothes. You type what you want in plain words, like "vintage graphic tee under $30, size M." It searches a list of 40 thrift listings and picks the best match. Then it shows you how to wear that item with clothes you already own, and writes a short caption you could post about your find. If nothing matches, it first tries again without your size, and then without your price limit. If it still finds nothing, it tells you what to change instead of making something up.

---

## Tool Inventory

### `search_listings`

- **What it does:** Filters the 40 thrift listings by price ceiling and size, scores the survivors by keyword overlap with the user's description, and returns the best matches.
- **Inputs:** `description` (str) — keywords such as "vintage graphic tee"; `size` (str or None) — e.g. "M", "W30 L30", "US 8.5"; `max_price` (float or None) — inclusive ceiling. `None` skips that filter.
- **Returns:** A list of at most `config.SEARCH_RESULT_LIMIT` listing dicts, best match first. Each dict has `id`, `title`, `description`, `category`, `style_tags` (list), `size`, `condition`, `price` (float), `colors` (list), `brand` (str or None), `platform`. Size matches on whole tokens, so "M" matches "S/M" and "M/L" but not "US 9". Listings that score zero on keywords are dropped.
- **When it has nothing:** An empty list `[]` — never `None`, never an exception. The loop branches on this: it drops the size, then the price cap, and searches again, and sets `session["error"]` only once neither is left.

### `suggest_outfit`

- **What it does:** Asks the model for one or two outfits built around the selected listing, using pieces from the user's wardrobe.
- **Inputs:** `new_item` (dict) — one listing dict from `search_listings`; `wardrobe` (dict) — `{"items": [...]}`, each item having `id`, `name`, `category`, `colors` (list), `style_tags` (list), `notes` (str or None).
- **Returns:** A non-empty str of outfit suggestions that name specific wardrobe pieces by `name`.
- **When it has nothing:** When `wardrobe["items"]` is empty, it returns general styling advice for the item as a non-empty str, with no invented wardrobe pieces. It does not return `""` or raise. If the model is unreachable, `generate()` raises `ModelUnavailable`, which the loop catches.

### `create_fit_card`

- **What it does:** Asks the model for a short social-media-style caption about the find.
- **Inputs:** `outfit` (str) — the text returned by `suggest_outfit`; `new_item` (dict) — the same listing dict.
- **Returns:** A str of two to four sentences that mentions the item, its price and its platform once each.
- **When it has nothing:** If `outfit` is empty or whitespace, it returns a message str ("No outfit to caption yet — run suggest_outfit() first and pass its result in as `outfit`.") and does not call the model or raise.

---

## Planning Loop

**Branch rule:** If `search_listings` returns an empty list, drop the size filter, then the price cap, and search again. If it is still empty with nothing left to drop, set `session["error"]` to a message telling the user what to change, then stop — `suggest_outfit` and `create_fit_card` never run. Otherwise, take the first result and continue on to `suggest_outfit` and then `create_fit_card`.

**Where it lives:** `agent.py::run_agent`

**How the query is parsed:** With regular expressions (regex), in `agent.py::parse_query`, not the model. One pattern finds a size after the word "size" or "sz" (for example "size M" or "size US 8.5"). Another finds a price after words like "under", "below" or "up to", or a bare "$40". Those pieces are cut out of the query, and what is left is the description. The parse runs once, before the loop starts.

**What moves through the session:** Every result is saved in the session, and the next step reads it back from there. In order:
1. `query` and `wardrobe` are set when the session is created.
2. `parsed` (description, size, max_price) is set from the query. If a search comes back empty, the loop sets size and then max_price to `None` in this field, so it always shows what was actually searched.
3. `relaxed` lists each limit that was dropped, such as `["size M"]`.
4. `search_results` is saved after every search, so it holds the latest one.
5. `selected_item` is `search_results[0]`.
6. `outfit_suggestion` is what `suggest_outfit` returns, given `selected_item` and `wardrobe`.
7. `fit_card` is what `create_fit_card` returns, given `outfit_suggestion` and `selected_item`.
8. `error` stays `None` unless the loop stops early. Then it holds the message, and `outfit_suggestion` and `fit_card` stay `None`.

---

## Sample Run

**One full query**

```
$ python app.py ask 'looking for a vintage graphic tee under $30'
```

```bash
  Found:    Y2K Baby Tee — Butterfly Print — $18.0 on depop

  Outfit:   Here are two outfit ideas combining the Y2K butterfly baby tee with pieces already in the wardrobe:

**Outfit 1: Casual Streetwear (Y2K meets 90s)**
*   **Top:** Y2K Baby Tee — Butterfly Print
*   **Bottoms:** Baggy straight-leg jeans (dark wash)
*   **Outerwear:** Vintage black denim jacket
*   **Shoes:** Chunky white sneakers
*   **Accessories:** Black crossbody bag
*   **Why it works:** The fitted silhouette of the baby tee balances out the volume of the baggy, high-waisted jeans for that classic Y2K proportions game. Layering the slightly cropped black denim jacket on top ties into the streetwear vibe, while the chunky white sneakers and crossbody bag keep it effortless and cohesive.

**Outfit 2: High-Low Contrast (Casual & Earthy)**
*   **Top:** Y2K Baby Tee — Butterfly Print
*   **Bottoms:** Wide-leg khaki trousers
*   **Accessories:** Brown leather belt, Black crossbody bag
*   **Shoes:** Black combat boots
*   **Why it works:** This outfit plays on the contrast between the sweet, graphic cottagecore/Y2K energy of the baby tee and the clean, minimal structure of the wide-leg khaki trousers. Tucking the baby tee in with the brown leather belt pulls the look together, and the black combat boots add an unexpected, grounded edge to the softer pink and purple tones in the butterfly print.

  Fit card: My inner 2003 pop star is screaming because I finally tracked down the exact butterfly baby tee I've been obsessing over for months. Scored this little gem on Depop for just $18, and it’s already becoming the anchor piece for everything from baggy jeans to wide-leg trousers. Excuse me while I go practice my lip-syncing in the mirror.
```

**The three tools, tested one at a time**

1. *search_listings*

```
$ python -c "from tools import search_listings; print(search_listings('graphic tee', max_price=30))"
```

```bash
[{'id': 'lst_002', 'title': 'Y2K Baby Tee — Butterfly Print', 'description': 'Super cute early 2000s baby tee with butterfly graphic. Fitted crop length. Tag says medium but fits like a small.', 'category': 'tops', 'style_tags': ['y2k', 'vintage', 'graphic tee', 'cottagecore'], 'size': 'S/M', 'condition': 'excellent', 'price': 18.0, 'colors': ['white', 'pink', 'purple'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_006', 'title': 'Graphic Tee — 2003 Tour Bootleg Style', 'description': 'Vintage-style bootleg tee with faded graphic. Slightly boxy fit. 100% cotton, soft and worn-in.', 'category': 'tops', 'style_tags': ['graphic tee', 'vintage', 'grunge', 'streetwear', 'band tee'], 'size': 'L', 'condition': 'good', 'price': 24.0, 'colors': ['black'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_017', 'title': 'Mesh Long-Sleeve Top — Black', 'description': 'Sheer black mesh long-sleeve. Great for layering under a graphic tee or over a bralette. Stretchy material, fits true to size.', 'category': 'tops', 'style_tags': ['y2k', 'grunge', 'goth', 'layering'], 'size': 'S/M', 'condition': 'excellent', 'price': 15.0, 'colors': ['black'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_033', 'title': 'Vintage Band Tee — Faded Grey', 'description': 'Faded grey band-style tee with distressed graphic. Crew neck. Fits boxy. Well-loved but no holes or major damage.', 'category': 'tops', 'style_tags': ['vintage', 'grunge', 'band tee', 'graphic tee', 'streetwear'], 'size': 'L', 'condition': 'fair', 'price': 19.0, 'colors': ['grey', 'charcoal'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_011', 'title': 'Low-Rise Cargo Pants — Khaki', 'description': 'Y2K era low-rise cargo pants. Lots of pockets. Khaki color, slightly distressed at the hems. Great for layering with a long tee.', 'category': 'bottoms', 'style_tags': ['y2k', 'cargo', '2000s', 'streetwear'], 'size': 'W29', 'condition': 'fair', 'price': 27.0, 'colors': ['khaki', 'tan'], 'brand': None, 'platform': 'poshmark'}, {'id': 'lst_015', 'title': 'Vintage Graphic Hoodie — Faded Black', 'description': 'Faded black pullover hoodie with barely-visible vintage graphic on the chest. Cozy interior. Some pilling but adds to the worn-in look.', 'category': 'tops', 'style_tags': ['vintage', 'grunge', 'graphic', 'streetwear'], 'size': 'L', 'condition': 'fair', 'price': 26.0, 'colors': ['black', 'charcoal'], 'brand': None, 'platform': 'depop'}]

```

2. *suggest_outfit*

```
python -c "from tools import suggest_outfit; from utils.data_loader import get_example_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_example_wardrobe()))"
```

```bash
Here are two specific outfit ideas using the vintage Levi's 501 jeans and pieces already in the wardrobe:

**Outfit 1: Casual Streetwear Contrast**
* **Top:** White ribbed tank top (tucked in)
* **Bottoms:** Vintage Levi's 501 Jeans — Medium Wash
* **Outerwear:** Vintage black denim jacket
* **Shoes:** Chunky white sneakers
* **Accessories:** Black crossbody bag
* *Why it works:* The medium wash of the 501s will pop nicely against the black denim jacket for a classic "denim-on-denim" look. Tucking in the fitted white tank balances the straight-leg fit of the jeans, while the chunky white sneakers lean into an effortless streetwear aesthetic.

**Outfit 2: Edgy & Relaxed**
* **Top:** Black cropped zip hoodie
* **Bottoms:** Vintage Levi's 501 Jeans — Medium Wash
* **Shoes:** Black combat boots
* **Accessories:** Brown leather belt and Black crossbody bag
* *Why it works:* Pairing the medium-wash 501s with the black cropped zip hoodie creates an easy, balanced silhouette. Adding the brown leather belt and black combat boots brings in a touch of grunge, playing on the vintage nature of the jeans.
```

3. *create_fit_card*

```
python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('jeans and white sneakers', load_listings()[0]))"
```

```bash
Nothing beats the heavy, stiff-in-the-best-way cotton of jeans made decades before you were born. I finally tracked down these vintage Levi's 501s on Depop for $38 and immediately paired them with my cleanest white sneakers for a Sunday morning diner run. They’re broken in just enough to feel like they were made for me instead of the ghost who wore them in 1994.
```
---

## How I Used AI

<!-- Two specific moments. What you asked, what came back, what you changed.

     "I used Claude to help me code" is not enough.

     "I gave Claude my search_listings spec. It returned None on no match
     instead of an empty list, so I changed it" is the level we want. -->

**Moment 1**

- *What I asked for:* I asked Claude to check my first version of `run_agent` for a real agent loop.
- *What came back:* It pointed out that my `while True` was not really a loop. Every path ended in a `return`, so it ran exactly once and `check_iterations` could never trip. It suggested parsing the query once before the loop, and retrying on an empty result by dropping the size and then the price cap.
- *What I changed:* I accepted the retry and rewrote the loop that way. I also made the loop read everything back through `session`, including `session["parsed"]`, so the session shows what was really searched. Then I updated my Branch rule in this README to match the new behavior.

**Moment 2**

- *What I asked for:* I asked Claude to test `create_fit_card` on its own, using the same item and outfit five times.
- *What came back:* All five captions were word-for-word identical. Turning the cache off gave five different captions, but only 2 different opening sentences, because the model kept starting with "Scored these…".
- *What I changed:* I added a line to the prompt telling the model not to open with "Scored" or "Found" and to pick a new way in. The rerun gave 5 different openings out of 5. I also learned that `run_eval.py` already turns the cache off, so I revised criterion 4 to say "cache off" without lowering the 4-of-5 target.

**Moment 3**

- *What I asked for:* I asked Claude to write a handler for `ModelUnavailable` in my loop, and then to test it on its end, including the 503 error I got in the first run.
- *What came back:* It put the two model calls (`suggest_outfit` and `create_fit_card`) in one `try`. If either one fails, the loop saves the message in `session["error"]`, adds a `stop` step to the trace, and returns. For the test, it made the model client raise the exact 503 text from my crashed run, so the real `generate()` code ran. The run stopped with a message and no stack trace, both when the first call failed and when the second one did. The test also showed two problems I had not seen. The message the user gets is the raw 503 text, and a 503 is never retried.
- *What I changed:* I kept the handler as Claude wrote it. I did not fix the two problems. I wrote them down in "What's Still Broken" instead. I also wrote in "The Improvement" that this run did not hit a real 503, so the handler was only proven by the test, not by the run.


<!-- ═══════════════════════ UNIT 4 — THE TEST ═══════════════════════

     Don't fill these in during unit 3.
     ═══════════════════════════════════════════════════════════════════ -->

---

## Run Log — Before

<!-- Five criteria, five tries each, in this exact format.

     Five, because your criteria are written out of five. Mark each try PASS
     or FAIL, count the passes, and read that count against your target — a
     row targeting 4 of 5 with three PASS cells is MISSED (3/5).

     `python run_eval.py --label before` runs everything and writes the table
     into results/. Paste it here and fill in the verdicts. -->

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1. Matching query completes all three tools | 4 of 5 | PASS | PASS | PASS | PASS | PASS | 5/5 — MET |
| 2. Impossible query stops before the second tool | 5 of 5 | PASS | PASS | PASS | PASS | PASS | 5/5 — MET |
| 3. Item search picked is the item suggest_outfit used | 5 of 5 | PASS | PASS | PASS | PASS | PASS | 5/5 — MET |
| 4. Fit card gives different words on repeat runs | 4 of 5 | PASS | PASS | PASS | PASS | PASS | 5/5 — MET |
| 5. Search results respect the price ceiling | 5 of 5 | PASS | PASS | PASS | PASS | PASS | 5/5 — MET |

Source: `results/run_2026-10-14_2243_before.md`, produced by `run_eval.py::main` (5 tries per scenario, caching off, temperature 0.9).

- **Criterion 1** (`vintage graphic tee under $30`): all 5 tries finished without stopping early. Each had 10 search results, picked the Y2K Baby Tee — Butterfly Print ($18.0, depop), and ended with a fit card.
- **Criterion 2** (`designer ballgown size XXS under $5`): all 5 tries stopped early with "No listings matched that query. Try a different size, a higher price ceiling, or a broader description." Each had 0 search results and no selected item, and the trace shows no `suggest_outfit` step.
- **Criterion 3** (`vintage graphic hoodie`): in all 5 tries the selected item was Vintage Graphic Hoodie — Faded Black, and the trace shows both `suggest_outfit` and `create_fit_card` receiving `lst_015`. The file prints the selected item's title, not its id, so I matched them by title.
- **Criterion 4** (`leather bomber jacket`): all 5 tries selected 90s Leather Bomber — Black ($75.0, depop). The 5 fit cards had 5 different first sentences, and all 5 contained "$75". This run repeats the same item, but the outfit text is written by the model each try, so it isn't one fixed outfit.
- **Criterion 5** (`jacket under $45`): all 5 tries returned 3 results (90s Track Jacket, Denim Jacket — Light Wash, Cropped, and Shacket — Olive Canvas) and selected the 90s Track Jacket at exactly $45.0, so the ceiling is inclusive. The file prints only the selected item's price. The other two prices ($42 and $33) come from `data/listings.json`.
- **Diagnostic, empty wardrobe** (`denim jacket under $50`, not one of the five): all 5 tries completed and picked the Denim Jacket — Light Wash, Cropped ($42.0, poshmark).

**Real output from one try per criterion**, pasted as text from `results/run_2026-10-14_2243_before.md`, each from try 1. The trace comes from `agent.py::run_agent` through `trace.py::step`. The search steps come from `tools.py::search_listings`, called through `mcp_server.py`. The fit card comes from `tools.py::create_fit_card`. `run_eval.py::main` wrote it all to the file.

Criterion 1 - `vintage graphic tee under $30`: finished with a fit card.

```
selected_item: Y2K Baby Tee — Butterfly Print ($18.0, depop)
search_results: 10

[1] search_listings (via MCP)
      in:  description='vintage graphic tee', size=None, max_price=30.0
      out: 10 items: Y2K Baby Tee — Butterfly Print, Graphic Tee — 2003 Tour Bootleg Style, Vintage Band Tee — Faded Grey … +7 more
      →    found results, moving on
[2] select item
      in:  search_results[0]
      out: Y2K Baby Tee — Butterfly Print ($18.0, depop)
[3] suggest_outfit
      in:  item={'id': 'lst_002', 'title': 'Y2K Baby Tee — Butterfly Print', 'description': 'Super cute early 2000s baby …
      out: Here are two outfit ideas combining the new Y2K Butterfly Baby Tee with pieces already in the wardrobe:  ### O…
[4] create_fit_card
      in:  outfit (1353 chars), item={'id': 'lst_002', 'title': 'Y2K Baby Tee — Butterfly Print', 'description': 'Super c…
      out: My inner fourteen-year-old just won a small, highly specific war against my current closet. I finally tracked …

Fit card:
My inner fourteen-year-old just won a small, highly specific war against my current closet. I finally tracked down this butterfly print Y2K baby tee on Depop for just $18.00, and honestly, styling it with baggy denim and chunky sneakers instantly cures all my outfit fatigue. Let the early-2000s renaissance continue.
```

Criterion 2 - `designer ballgown size XXS under $5`: stopped at step 6, no `suggest_outfit` or `create_fit_card`.

```
selected_item: (none)
search_results: 0

[1] search_listings (via MCP)
      in:  description='designer ballgown', size='XXS', max_price=5.0
      out: [] (empty)
[2] relax
      →    branch: empty, dropping size XXS
[3] search_listings (via MCP)
      in:  description='designer ballgown', size=None, max_price=5.0
      out: [] (empty)
[4] relax
      →    branch: empty, dropping price limit $5
[5] search_listings (via MCP)
      in:  description='designer ballgown', size=None, max_price=None
      out: [] (empty)
[6] stop
      out: No listings matched that query. Try a different size, a higher price ceiling, or a broader description.
      →    branch: empty and nothing left to drop, stopping
```

Criterion 3 - `vintage graphic hoodie`: `selected_item` is the hoodie, and the trace shows `suggest_outfit` receiving `lst_015`.

```
selected_item: Vintage Graphic Hoodie — Faded Black ($26.0, depop)
search_results: 10

[1] search_listings (via MCP)
      in:  description='vintage graphic hoodie', size=None, max_price=None
      out: 10 items: Vintage Graphic Hoodie — Faded Black, Y2K Baby Tee — Butterfly Print, Graphic Tee — 2003 Tour Bootleg Style … +7 more
      →    found results, moving on
[2] select item
      in:  search_results[0]
      out: Vintage Graphic Hoodie — Faded Black ($26.0, depop)
[3] suggest_outfit
      in:  item={'id': 'lst_015', 'title': 'Vintage Graphic Hoodie — Faded Black', 'description': 'Faded black pullover h…
      out: Here are two specific outfit ideas using the new Vintage Graphic Hoodie and pieces already in your wardrobe:  …
[4] create_fit_card
      in:  outfit (1360 chars), item={'id': 'lst_015', 'title': 'Vintage Graphic Hoodie — Faded Black', 'description': 'F…
      out: There is genuinely nothing better than a hoodie that looks like it survived three different underground 90s me…

Fit card:
There is genuinely nothing better than a hoodie that looks like it survived three different underground 90s metal tours. Snagged this faded black vintage graphic piece on depop for just $26, and honestly, it’s about to become my entire personality. Whether I'm throwing it on with baggy indigo denim and combat boots or balancing out the grunge with crisp khaki trousers, the fit is officially sorted.
```

Criterion 4 - `leather bomber jacket`: try 1's fit card (the other four tries wrote different first sentences).

```
selected_item: 90s Leather Bomber — Black ($75.0, depop)
search_results: 7

[1] search_listings (via MCP)
      in:  description='leather bomber jacket', size=None, max_price=None
      out: 7 items: 90s Leather Bomber — Black, 90s Track Jacket — Navy/White Stripe, Denim Jacket — Light Wash, Cropped … +4 more
      →    found results, moving on
[2] select item
      in:  search_results[0]
      out: 90s Leather Bomber — Black ($75.0, depop)
[3] suggest_outfit
      in:  item={'id': 'lst_022', 'title': '90s Leather Bomber — Black', 'description': 'Genuine leather bomber jacket. C…
      out: Here are two specific outfit combinations using the new 90s Leather Bomber and pieces from your wardrobe:  ###…
[4] create_fit_card
      in:  outfit (1468 chars), item={'id': 'lst_022', 'title': '90s Leather Bomber — Black', 'description': 'Genuine lea…
      out: There is something deeply spiritual about driving home at midnight in a jacket that smells faintly of someone …

Fit card:
There is something deeply spiritual about driving home at midnight in a jacket that smells faintly of someone else's cigarettes and 1998. Snagged this ultimate black 90s leather bomber on Depop for $75, and honestly, the math is just working in my favor. Currently debating whether to lean into the chunky sneaker streetwear agenda or go full grunge with my heaviest combat boots.
```

Criterion 5 - `jacket under $45`: 3 results, and the selected jacket is exactly $45.0.

```
selected_item: 90s Track Jacket — Navy/White Stripe ($45.0, poshmark)
search_results: 3

[1] search_listings (via MCP)
      in:  description='jacket', size=None, max_price=45.0
      out: 3 items: 90s Track Jacket — Navy/White Stripe, Denim Jacket — Light Wash, Cropped, Shacket — Olive Canvas
      →    found results, moving on
[2] select item
      in:  search_results[0]
      out: 90s Track Jacket — Navy/White Stripe ($45.0, poshmark)
[3] suggest_outfit
      in:  item={'id': 'lst_004', 'title': '90s Track Jacket — Navy/White Stripe', 'description': 'Authentic 90s track ja…
      out: Here are two specific outfit combinations using the new 90s track jacket and pieces already in your wardrobe: …
[4] create_fit_card
      in:  outfit (1263 chars), item={'id': 'lst_004', 'title': '90s Track Jacket — Navy/White Stripe', 'description': 'A…
      out: I’ve been chasing this exact shade of navy for three months, so seeing it pop up on Poshmark for $45 felt susp…

Fit card:
I’ve been chasing this exact shade of navy for three months, so seeing it pop up on Poshmark for $45 felt suspiciously like fate. Zipped up with khakis or thrown over a white tank, this 90s track jacket is officially my lazy-day uniform. Now I just need somewhere cool to wear it.
```

---

## Verdicts and Diagnoses

<!-- MET or MISSED per criterion against LAST UNIT's target, plus a sentence on
     how you decided.

     Then, for every miss: which of the four places it happened — a tool, the
     loop's branch, the session, or the model's output — AND the mechanism.

     Not a diagnosis:  "The fit card was bad."
     A diagnosis:      "The fit card criterion missed on 2 of 5 items. Both had
                        an empty brand field. My prompt puts the brand in the
                        first sentence, so the card opened with a blank and read
                        like a fragment. The tool worked; the prompt assumed a
                        field that isn't always there."

     Look for a pattern. Three misses on the same tool is one problem, not
     three. -->

| # | Criterion | Target | Verdict | How I decided |
|---|---|---|---|---|
| 1 | Matching query completes all three tools | 4 of 5 | MET | 5 of 5 tries finished with `error` unset and a fit card (`results/run_2026-10-14_2243_before.md`, "matching query completes"). |
| 2 | Impossible query stops before the second tool | 5 of 5 | MET | 5 of 5 tries stopped at step 6 with the "No listings matched…" message, 0 search results, and no `suggest_outfit` or `create_fit_card` step in the trace. |
| 3 | Item search picked is the item suggest_outfit used | 5 of 5 | MET | In 5 of 5 tries the trace shows `suggest_outfit` and `create_fit_card` both receiving `lst_015`, and the selected item was the Vintage Graphic Hoodie, which is `lst_015`. I matched by title because the file prints the selected item's title, not its id. |
| 4 | Fit card gives different words on repeat runs | 4 of 5 | MET | The 5 fit cards had 5 different first sentences, and all 5 contained "$75". Same item each try, but the model wrote a new outfit each time, so the input wasn't one fixed outfit. `run_eval.py` turns the cache off, and the criterion as written says cache on, so I scored it with the cache off. |
| 5 | Search results respect the price ceiling | 5 of 5 | MET | `jacket under $45` returned 3 results in 5 of 5 tries, and the selected 90s Track Jacket is exactly $45.0, so the ceiling is inclusive. The file prints only the selected item's price. The other two ($42 and $33) come from `data/listings.json`. The scenario tests one ceiling through `run_agent`, not five through `search_listings` directly. |

**Diagnoses**

No criterion was missed in this run, so there is no miss to diagnose. Two things I noticed are worth recording:

- **A model outage, not a loop failure.** In an earlier run (`results/run_2026-10-14_2214_before.md`), try 3 of the empty-wardrobe diagnostic crashed with `ModelUnavailable: Couldn't reach the model: 503 UNAVAILABLE`. The problem was on the model's side, not in a tool, the loop's branch or the session. The service was overloaded, and at that point `run_agent` had no handler for `ModelUnavailable`, so the try crashed instead of giving a message. I fixed this in The Improvement below. It was not one of the five criteria, and it did not happen again in the later run.
- **Criteria 4 and 5 are scored through a proxy.** `run_eval.py` only runs `run_agent`, so criterion 4 repeats the same item with a new model outfit each try, and criterion 5 checks one ceiling. Both pass, but they test a little less than the criteria as written (a fixed outfit, and five ceilings through `search_listings`).

---

## Loop Trace

<!-- One full run, printed step by step, with the MCP call visible in it.

     `python app.py ask '...' --trace` once you've added the trace.step()
     calls in Milestone 2.

     Worth pasting BOTH the happy path and the empty-search path. The empty
     one should be visibly shorter, because it stops. If your two traces are
     the same length, your branch isn't working — and this is the fastest way
     anyone will ever find that out. -->

**Happy path**

```
python app.py ask 'vintage graphic tee under $30' --trace
```
``` bash
[1] search_listings (via MCP)
      in:  description='vintage graphic tee', size=None, max_price=30.0
      out: 10 items: Y2K Baby Tee — Butterfly Print, Graphic Tee — 2003 Tour Bootleg Style, Vintage Band Tee — Faded Grey … +7 more
      →    found results, moving on
[2] select item
      in:  search_results[0]
      out: Y2K Baby Tee — Butterfly Print ($18.0, depop)
[3] suggest_outfit
      in:  item={'id': 'lst_002', 'title': 'Y2K Baby Tee — Butterfly Print', 'description': 'Super cute early 2000s baby' …
      out: Here are two outfit ideas combining the Y2K butterfly baby tee with pieces already in the wardrobe:  **Outfit …
[4] create_fit_card
      in:  outfit (1311 chars), item={'id': 'lst_002', 'title': 'Y2K Baby Tee — Butterfly Print', 'description': 'Super'…
      out: My inner 2003 pop star is screaming because I finally tracked down the exact butterfly baby tee I've been obse…
```

**Empty search**

```
python app.py ask 'Barcelona soccer jersey under $20' --trace
```

```bash
[1] search_listings (via MCP)
      in:  description='Barcelona soccer jersey', size=None, max_price=20.0
      out: [] (empty)
[2] relax
      →    branch: empty, dropping price limit $20
[3] search_listings (via MCP)
      in:  description='Barcelona soccer jersey', size=None, max_price=None
      out: [] (empty)
[4] stop
      out: No listings matched that query. Try a different size, a higher price ceiling, or a broader description.
      →    branch: empty and nothing left to drop, stopping

  No listings matched that query. Try a different size, a higher price ceiling, or a broader description.
```

**On the MCP move:** I moved `search_listings` onto an MCP server. In `mcp_server.py` I registered it as a tool with typed inputs (`description` as str, `size` as str or None, `max_price` as float or None) and a description that names the types and units and says an empty search returns an empty list. In `agent.py` I replaced the direct call with `call_tool("search_listings", {...})`, and I log it in the trace as `search_listings (via MCP)`. Nothing behaved differently that I could see. The tool still returns a list of listing dictionaries, and an empty search still comes back as `[]`, so the branch that relaxes the size and price, and then stops, works the same way. Every run in `results/` goes through MCP and none of them hit an error. I did not run the old direct call next to the MCP call to compare them, and I did not time them. One thing to know: `call_tool` starts the server for each call, so an impossible query starts it three times, once for each search.

---

## The Improvement

<!-- What you changed, why your diagnosis pointed at it, and the after-run in
     the same table format. One change, measured properly.

     `python run_eval.py --label after` -->

**What I changed:** I added a handler for `ModelUnavailable` in `agent.py::run_agent`. The two model calls (`suggest_outfit` and `create_fit_card`) now sit inside one `try`. If either raises `ModelUnavailable`, the loop saves the message in `session["error"]`, adds a `stop` step to the trace ("model unavailable, stopping"), and returns the session instead of crashing. If only `create_fit_card` fails, the outfit is kept and `fit_card` stays `None`.

**Which failure it was meant to fix:** The crash in `results/run_2026-10-14_2214_before.md`, empty-wardrobe diagnostic, try 3: `ModelUnavailable: Couldn't reach the model: 503 UNAVAILABLE… high demand`. The model service was overloaded, nothing in the loop caught the error, and that try ended as a crash instead of a message. It's a model-side failure, but the loop's job is to turn it into something the user can act on.

### Run Log — After

Source: `results/run_2026-10-14_2340_after.md`, produced by `run_eval.py::main` (5 tries per scenario, caching off, temperature 0.9). Same scenarios as the before run.

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1. Matching query completes all three tools | 4 of 5 | PASS | PASS | PASS | PASS | PASS | 5/5 — MET |
| 2. Impossible query stops before the second tool | 5 of 5 | PASS | PASS | PASS | PASS | PASS | 5/5 — MET |
| 3. Item search picked is the item suggest_outfit used | 5 of 5 | PASS | PASS | PASS | PASS | PASS | 5/5 — MET |
| 4. Fit card gives different words on repeat runs | 4 of 5 | PASS | PASS | PASS | PASS | PASS | 5/5 — MET |
| 5. Search results respect the price ceiling | 5 of 5 | PASS | PASS | PASS | PASS | PASS | 5/5 — MET |

- **Criterion 1** (`vintage graphic tee under $30`): 5 of 5 tries finished with a fit card, 10 search results, Y2K Baby Tee ($18, depop).
- **Criterion 2** (`designer ballgown size XXS under $5`): 5 of 5 tries stopped at step 6 with the "No listings matched…" message and no `suggest_outfit` or `create_fit_card` step.
- **Criterion 3** (`vintage graphic hoodie`): in 5 of 5 tries the trace shows `suggest_outfit` and `create_fit_card` both receiving `lst_015`, the selected Vintage Graphic Hoodie.
- **Criterion 4** (`leather bomber jacket`): 5 different first sentences and all 5 captions contain "$75".
- **Criterion 5** (`jacket under $45`): 3 results in 5 of 5 tries, and the selected 90s Track Jacket is exactly $45.0.
- **Diagnostic, empty wardrobe** (`denim jacket under $50`): 5 of 5 tries completed. No try crashed.

**Did it help, and how do I know:** The table did not change. All five criteria were MET before and are MET after, and no try crashed in either run. That does not prove the handler works, because the 503 did not happen in this run, so the handler never ran. I only know it works from a test where I made the model client raise the exact 503 text from the crashed run. When the 503 hit `suggest_outfit`, the loop stopped at step 3 with `error` set and no outfit or fit card. When it hit `create_fit_card`, the loop kept the outfit, left `fit_card` as `None`, and set the same `error`. So I can say a model failure now ends the run with a message, and nothing the criteria measure got worse. I can't say this run proved it, because no real failure happened.

---

## What's Still Broken

<!-- For each criterion still missed: what you'd do, and why you stopped where
     you did. "I ran out of time" is fine if it's true. Pretending nothing is
     left is not. -->

No criterion is MISSED in the after run, but these are still weak or untested:

- **The user is not told when a limit was dropped.** When a search comes back empty, the loop drops the size and then the price limit and records it in `session["relaxed"]`. Nothing outside `agent.py` reads that field, so someone who asked for size XS and got a different size is not told. I'd print `relaxed` in the app and in `_show()`. I stopped because no criterion measures it.
- **A 503 still ends the run.** The handler turns it into a message, but a short overload still stops the whole search. `generate()` only retries rate limits, not a 503, even though the service says these spikes are usually temporary. A retry with a short wait would probably save most of these runs.
- **The 503 message is hard to read.** The user sees the raw text ("Couldn't reach the model: 503 UNAVAILABLE. {'error': {…"), because `generate.py` only rewrites key, 404 and network errors. I'd add a plain sentence like "The model is busy right now, try again in a minute."
- **The handler has not seen a real failure.** The 503 did not happen in the after run. The only evidence it works is my test, where I made the model client raise the same 503 text. In that test the real `generate()` code produced `ModelUnavailable`, the loop stopped with no stack trace, and `run_eval.py` recorded the try as stopped early, not crashed.
- **Criteria 4 and 5 are scored through a proxy.** `run_eval.py` only runs `run_agent`. Criterion 4 repeats the same item but the model writes a new outfit each try, and criterion 5 checks a single ceiling ($45) instead of five. A direct test of `create_fit_card` with a fixed outfit, and of `search_listings` with five ceilings, would match the criteria as written.
- **The fit card check compares whole sentences.** Two captions that open "There is genuinely nothing better than a hoodie…" and "There is literally nothing better than a thrift find…" count as different even though a reader would call them the same. Comparing the first few words would be stricter.
- **Search results are loosely ranked.** A query like "vintage graphic tee" also returns a belt, cargo pants and a slip dress, because one shared word is enough to score. The loop only takes the first result, so it hasn't mattered, but a cutoff of two matching words would clean up the list.

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**
