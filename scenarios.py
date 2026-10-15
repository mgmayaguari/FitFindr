"""
The runs your test needs. ← UNIT 4, MILESTONE 3

Each of your five criteria needs something run against it. A criterion about
the empty-search branch needs an impossible query. One about the fit card needs
the same item run more than once. Working that out is Milestone 3's first step,
and this file is where you write it down.

`run_eval.py` runs everything here five times and writes the run log — five
because your criteria are written out of five.

Three scenarios are filled in to show the shape. Add or change whatever your
own criteria need — these are a starting point, not a fixed set.
"""

SCENARIOS = [
    {
        # A query the data can match. Criterion 1.
        "name": "matching query completes",
        "query": "vintage graphic tee under $30",
        "wardrobe": "example",
        "criterion": 1,
    },
    {
        # A query nothing can match. Criterion 2 — the branch.
        "name": "impossible query stops early",
        "query": "designer ballgown size XXS under $5",
        "wardrobe": "example",
        "criterion": 2,
    },
    {
        # A user with nothing saved. One of unit 4's three failure modes.
        "name": "empty wardrobe",
        "query": "denim jacket under $50",
        "wardrobe": "empty",
        "criterion": None,
    },
    {
        # A clean single-item match. Criterion 3 — state handoff: the id in
        # session["selected_item"] should be the same id passed into
        # suggest_outfit's new_item argument. Any normal query works here;
        # what matters is what ends up in the session, not what was typed.
        "name": "selected item flows into suggest_outfit",
        "query": "vintage graphic hoodie",
        "wardrobe": "example",
        "criterion": 3,
    },
    {
        # "leather bomber jacket" scores highest against a single listing
        # (lst_022, $75), so the same item is selected every try — run_eval.py
        # already runs each scenario 5 times, which gives 5 fit cards for the
        # same item to compare captions across (the outfit text will also
        # differ a little each try, since it comes from the model too).
        # Criterion 4.
        "name": "fit card caption varies across repeated runs",
        "query": "leather bomber jacket",
        "wardrobe": "example",
        "criterion": 4,
    },
    {
        # A query where several listings share the "jacket" keyword at
        # different prices (lst_004 at exactly $45, lst_007 at $42, lst_032
        # at $33) — a good boundary case for the ceiling filter, including an
        # item priced right at max_price. Criterion 5.
        "name": "search results respect the price ceiling",
        "query": "jacket under $45",
        "wardrobe": "example",
        "criterion": 5,
    },
]

WARDROBES = ("example", "empty")


def validate() -> list[str]:
    """Complain about anything malformed, before a long run rather than during."""
    problems = []
    for i, scenario in enumerate(SCENARIOS, 1):
        if not scenario.get("query", "").strip():
            problems.append(f"scenario {i} has no query")
        if scenario.get("wardrobe") not in WARDROBES:
            problems.append(
                f"scenario {i} has wardrobe {scenario.get('wardrobe')!r} — "
                f"it should be one of {WARDROBES}"
            )
    return problems
