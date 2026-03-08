# BUILD_PROCESS.md
## Decision Companion System — How It Actually Got Built

> This document is a honest record of how the project was built — every stage, every mistake, every change of direction, and the reason behind each decision. It's not a cleaned-up post-mortem. It's closer to a development diary.

**Project:** Decision Companion System (Vonnue Assignment)
**Period:** 23 February – 08 March 2026

---

## Table of Contents

1. [Stage 0 — Reading the Brief and Initial Research](#stage-0--reading-the-brief-and-initial-research)
2. [Stage 1 — First Thinking: What Kind of System Is This?](#stage-1--first-thinking-what-kind-of-system-is-this)
3. [Stage 2 — Trial Build: Python CLI on Gemini API (OpenAI Quota Ran Out)](#stage-2--trial-build-python-cli-on-gemini-api-openai-quota-ran-out)
4. [Stage 3 — The Problem with Equal Scoring: Adding Priority](#stage-3--the-problem-with-equal-scoring-adding-priority)
5. [Stage 4 — Redesigning the Scoring: From 5 Points to 100-Point Priority Weights](#stage-4--redesigning-the-scoring-from-5-points-to-100-point-priority-weights)
6. [Stage 5 — Moving to Django: Choosing the Framework](#stage-5--moving-to-django-choosing-the-framework)
7. [Stage 6 — Designing the Database Schema](#stage-6--designing-the-database-schema)
8. [Stage 7 — Building the Decision Tree: Categories, Subcategories, Criteria](#stage-7--building-the-decision-tree-categories-subcategories-criteria)
9. [Stage 8 — Building the Core Views and Scoring Engine](#stage-8--building-the-core-views-and-scoring-engine)
10. [Stage 9 — Bugs Encountered and How They Were Fixed](#stage-9--bugs-encountered-and-how-they-were-fixed)
11. [Stage 10 — Adding the AI Explanation Layer](#stage-10--adding-the-ai-explanation-layer)
12. [Stage 11 — Dynamic Criteria and Runtime Extra Criteria](#stage-11--dynamic-criteria-and-runtime-extra-criteria)
13. [Stage 12 — Home Page, Decision History, Login, and "Other" Category](#stage-12--home-page-decision-history-login-and-other-category)
14. [What I Would Do Differently](#what-i-would-do-differently)

---

## Stage 0 — Reading the Brief and Initial Research

**Date:** 23 February 2026

The first thing I did was read the brief properly — not just skim it. The phrase that actually changed how I approached the whole thing was:

> *"They care about how you build, not just what you build."*

So this isn't just a coding test. It's a system design and thinking test. The deliverables list made that obvious — README, BUILD_PROCESS.md, RESEARCH_LOG.md, and a design diagram were listed right next to the actual code.

**Initial research questions I had:**
- Does something like this already exist?
- What are the established academic methods for this kind of decision making?
- What have other developers done in this space?

**What I found:**

Searched for "Decision Helper System" and found **Qlik** — a business intelligence Decision Support System. Key observation: Qlik is powerful but totally opaque. It's built for enterprise analytics, not personal decisions, and it doesn't explain *why* it gives you a particular output. That confirmed to me that the explainability part of this assignment was a real design challenge, not just a box to tick.

Browsed `github.com/topics/decision-making` sorted by forks. Most open-source tools were either too narrow (built for one specific domain) or too simple (basic ranking, no weighting, no justification).

Looked into the main academic MCDM algorithms:
- **Weighted Scoring Model** — simplest, practical, fully explainable
- **AHP (Analytic Hierarchy Process)** — rigorous but needs pairwise comparisons; complex UX
- **TOPSIS** — academically strong but requires normalisation across all options at once

**Decision:** Weighted scoring is the right foundation for this. Most implementable, most explainable to a non-technical user, and most appropriate for a time-constrained assignment.

---

## Stage 1 — First Thinking: What Kind of System Is This?

**Date:** 23–28 February 2026

Before writing any code, I spent time thinking through what the system actually needed to do — and where it could go wrong.

**Three logic options I considered:**

**Option A — AI-Driven Confidence System**
Use an AI API to generate questions, evaluate answers, assign confidence scores, and declare the highest-confidence option the winner.

Why I rejected it: this makes the AI the decision-maker. The assignment explicitly requires explainable, non-black-box logic. If AI assigns a confidence of 0.82 to Option A, I can't explain *why* that's 0.82 and not 0.79. Also non-deterministic — same inputs could produce different rankings on different runs.

**Option B — Priority-Only (Lexicographic Model)**
User ranks criteria by importance (1st, 2nd, 3rd...). The option that scores best on the #1 priority wins, with lower priorities used only as tiebreakers.

Why I rejected this as a standalone approach: too simplistic. Ignores trade-offs entirely. If price is the top priority, the cheapest laptop always wins — even if it's terrible in every other way. Real decisions rarely hinge on a single criterion.

**Option C — Hybrid Weighted Scoring with Optional AI (the one I went with)**
Core idea: scoring and ranking are deterministic and owned by the system. AI is useful for generating evaluation questions and writing explanations, but it must never be in the actual decision path.

This resolved both previous problems: the system is fully explainable (every number traces back to user input), and it handles trade-offs (multiple weighted criteria competing in the final score).

**Key principle I established at this stage:**
> *Criteria are data, not logic. The scoring engine never changes. Only the data fed into it changes.*

This single principle shaped the entire architecture from here.

---

## Stage 2 — Trial Build: Python CLI on Gemini API (OpenAI Quota Ran Out)

**Date:** 28 February – 01 March 2026

Before building a web app, I built a minimal terminal prototype in Python to validate the concept. The goal was just to prove the flow worked end-to-end — not to build something production-ready.

The original plan was to use OpenAI for question generation. But during testing the quota ran out. So I switched to Gemini (Google), which had a free tier sufficient for development. From this point the whole project used Gemini.

Also — I decided to use **comma-separated input** for options at this stage. The user just types their options separated by commas (e.g. `MacBook Air, Lenovo ThinkPad, Dell XPS`). I chose this because it's the simplest possible way for a user to enter multiple items without needing extra form fields or dynamic buttons at this stage.

**What was built:**

```
User enters decision context
    ↓
Gemini API generates 5 evaluation questions
    ↓
User rates each option on each question (1–5)
    ↓
System sums raw scores
    ↓
Highest total wins
    ↓
System prints: "Best option: X — scored highest on Q1 and Q3"
```

**The Python skeleton:**

```python
def get_decision_context():
    return input("Enter decision context: ")

def get_options():
    raw = input("Enter your options separated by commas: ")
    return [o.strip() for o in raw.split(",")]

def generate_questions(context):
    prompt = f"Generate 5 evaluation questions for: {context}. Allow rating 1-5."
    response = model.generate_content(prompt)
    return parse_questions(response.text)

def collect_scores(options, questions):
    scores = {option: [] for option in options}
    for q in questions:
        print(f"\nQuestion: {q}")
        for option in options:
            rating = int(input(f"Rate {option} (1-5): "))
            scores[option].append(rating)
    return scores

def calculate_totals(scores):
    return {opt: sum(vals) for opt, vals in scores.items()}

def main():
    context = get_decision_context()
    options = get_options()
    questions = generate_questions(context)
    scores = collect_scores(options, questions)
    totals = calculate_totals(scores)
    best = max(totals, key=totals.get)
    print(f"\nBest Option: {best} — Score: {totals[best]}")
```

**What worked:**
- The flow was clean and understandable
- AI question generation was genuinely useful
- Comma-separated input for options worked well — easy for users to just type them out
- The scoring calculation was simple and correct
- The explanation was deterministic (rule-based, not AI-generated)

**What was immediately wrong:**

The scoring formula `total = sum(all scores)` had a critical flaw: every question was treated as equally important. In a laptop decision, "How well does it meet performance needs?" and "How good is the colour?" carry completely different real-world weight. Equal weighting produced answers that felt wrong.

Also: the OpenAI API quota had already run out before this stage, which forced the switch to Gemini. But because I hadn't set up a fallback, when the API was unavailable the whole flow just broke. That needed fixing.

**Fallback added:**
```python
def generate_questions(context):
    try:
        response = model.generate_content(...)
        return parse_questions(response.text)
    except Exception:
        return default_questions()

def default_questions():
    return [
        "How well does the option meet your primary goal?",
        "How cost-effective is this option?",
        "How reliable or stable is this option?",
        "How scalable or future-proof is this option?",
        "How well does this option fit your existing situation?"
    ]
```

**Conclusion from Stage 2:** the concept is valid. The flow works. But the scoring formula needs weights, and the system needs to be robust to API failure.

---

## Stage 3 — The Problem with Equal Scoring: Adding Priority

**Date:** 01 March 2026

The flat 100-point sum was producing results that didn't reflect how people actually make decisions. If someone is choosing a laptop on a budget, cost efficiency matters way more than screen resolution. The sum of all scores doesn't capture this.

**First attempt at fixing this: lexicographic priority**

Added a step where the user ranks criteria in order of importance (1, 2, 3...). The option that scored best on the #1 criterion won. If tied, #2 was checked, and so on.

**What improved:** the most important criterion now drove the result. Simple and fully explainable.

**What was still broken:** Option A could score 100 on criterion 1 (highest priority) and 1 on everything else. Option B could score 4 on criterion 1 and 5 on everything else. Priority-only logic would choose A, even though B is clearly better overall. Real decisions involve trade-offs, and lexicographic ordering ignores them entirely.

**Conclusion from Stage 3:** priority is the right concept but the wrong implementation. Priority should be a *weight* that amplifies a criterion's influence on the total — not an absolute override.

---

## Stage 4 — Redesigning the Scoring: From 5 Points to 100-Point Priority Weights

**Date:** 01–02 March 2026

This is the stage where the scoring formula became mathematically correct.

**The insight:** instead of ranking criteria (1st, 2nd, 3rd), let users assign a *percentage importance* to each criterion. These become weights in the final score formula.

**Formula designed:**
```
Final Score(option) = Σ [ (score / 100) × (priority / 100) ]
```

Both the score and the priority are normalized before being multiplied, so the final score is always between 0 and 1 regardless of how many criteria there are. Sessions with different numbers of criteria produce comparable scores.

**Why `score / 5`:** normalizes the 1-100 rating to a 0–1 decimal. Score scale never inflates the result.

**Why `priority / 100`:** treats the priority input as a proportion of total importance. Cost = 60 and Performance = 40 means Cost contributes 60% of total weight.

**Auto-normalization added:** users might enter priorities that don't sum to 100 (e.g. Cost = 40, Reliability = 60, Maintenance = 50 → total = 150). Rather than throwing an error, the system normalizes automatically:

```python
total_priority = sum(weight_map.values())
normalized_weight = criterion_weight / total_priority
contribution = (score / 100) * normalized_weight
```

This made the formula stable regardless of what the user entered.

**A critical UX discovery at this stage:**

When criteria are phrased as negatives — "Rate the Cost of this option (1-100)" — users don't know if 5 means "very expensive" (bad) or "very cheap" (good). Internally, a score inversion (`adjusted = 101 - score`) would be needed for cost, risk, and other "lower is better" criteria.

At first I added an `is_positive` boolean field to handle this in the engine. But this caused a lot of errors — the boolean flag was causing bugs in the scoring logic and making the data harder to manage. So I took the cleaner approach: rephrase all criteria positively.

- "Cost" → "Cost Efficiency" (100 = very affordable)
- "Risk" → "Risk Safety" (100 = very low risk)
- "Maintenance" → "Ease of Maintenance" (100 = very easy)

Now every criterion follows the same rule: **higher score = better**. No inversion logic needed in the engine. The `is_positive` field is kept in the database for engine flexibility, but the UI always presents positive phrasing and never confuses users with it.

**Scoring formula finalized. Moving to web application.**

---

## Stage 5 — Moving to Django: Choosing the Framework

**Date:** 02 March 2026

The CLI prototype proved the logic. Now it needed to become a web application.

| Framework | Why Considered | Why Rejected / Accepted |
|-----------|----------------|-------------------------|
| Flask | Lightweight, minimal | Too minimal — no admin panel, no built-in auth, no ORM |
| FastAPI | Modern, async | API-first; would need a separate frontend, adds complexity |
| Node.js | Common choice | Not Python; would need to rewrite validated scoring logic |
| **Django** | Full-stack, batteries included | **Accepted — ORM + admin panel + auth + migrations all built in** |

Django was the clear winner. The admin panel alone replaced the need for a separate data management interface. The built-in `@login_required` decorator and `User` model handled authentication without setup. Migrations tracked every schema change automatically.

**Project initialized:**
```bash
pip install django
django-admin startproject decision_system
cd decision_system
python manage.py startapp core
```

**Separation of concerns established from the start:**
- `core/models.py` — database schema only
- `core/views.py` — request handling only
- `core/services/scoring_engine.py` — scoring logic only, never mixed into views
- `core/seeds/initial_data.py` — decision tree seed data, not logic

---

## Stage 6 — Designing the Database Schema

**Date:** 02–03 March 2026

The database went through several iterations. The final schema was reached by working backward from: what does the system need to store to be fully reproducible and explainable?

### Iteration 1 — Flat logging table

Initial idea: just log everything in one table.
```sql
decision_logs(id, user_id, context, options TEXT, chosen_option, reason)
```
**Problem:** options stored as comma-separated text — impossible to query or relate to individual scores. Cannot reproduce how a result was reached.

### Iteration 2 — Normalized decision + options + results

```
Decision → Options → Scores → Result
```

Better, but still lacked criteria storage, weight storage, and template reuse.

### Iteration 3 — Full 8-table schema (FINAL)

The key insight that unlocked the final design: separate *template* criteria from *instance* criteria.

- `CategoryCriterion` = reusable template (admin-managed, never user-modified)
- `Criterion` = per-decision copy (user can adjust weights without touching the template)

```
Category
  └── SubCategory
        └── CategoryCriterion  (template — reusable across all decisions)

Decision  (per user, per session)
  ├── Option
  │     └── Score  (option × criterion × value 1-100)
  ├── Criterion  (copied from template at decision creation — fully modifiable)
  └── Result  (final winner, total score, AI explanation)
```

**Why copy rather than reference?** If `Criterion` references `CategoryCriterion` directly and the user adjusts a weight, they'd be modifying the template — affecting every future decision in that category. Copying into a decision-specific `Criterion` instance makes each decision fully independent.

**Migration challenges encountered:** adding `subcategory = ForeignKey(SubCategory)` to the existing `Decision` table failed because existing rows had no value for the new non-nullable field.

**Fix pattern used repeatedly during development:**
1. Temporarily set `null=True, blank=True` on the new field
2. Run migration — succeeds because NULLs are allowed
3. Seed the decision tree
4. Remove `null=True` and run migration again

---

## Stage 7 — Building the Decision Tree: Categories, Subcategories, Criteria

**Date:** 03 March 2026

With the schema in place, the decision tree needed to be designed and seeded. This required the most deliberate thinking about domain design.

**The challenge:** how to classify diverse decisions (laptop purchase, hiring, travel, investment) without hardcoding domain-specific logic?

**Solution:** all decisions share the same meta-dimensions regardless of domain — Cost, Performance/Benefit, Risk, Usability/Experience, Future Value, Compatibility/Fit. The criteria names change per domain; the scoring structure does not.

I used AI (Gemini) to help suggest what categories would be most useful and versatile. The idea was to look at the problem statement, identify the general categories people make decisions in, and then identify subcategories to make the system more flexible and cover more use cases.

**Decision tree built across 6 top-level categories:**

| Category | Subcategories |
|----------|--------------|
| Purchase Decisions | Electronics, Vehicles, Digital Products, Services, Assets |
| Technology Decisions | Infrastructure, Backend, Frontend, Database, DevOps, Security |
| Career Decisions | Education, Employment, Skill Development, Entrepreneurship, Transition |
| Financial Decisions | Investment, Loan/Financing |
| Travel & Lifestyle | Travel, Relocation, Lifestyle |
| Hiring Decisions | Candidate Evaluation |

Seeded using a shell script approach:
```bash
python manage.py shell
```
```python
from core.seeds.initial_data import run
run()
```

Not the most elegant approach but it worked for development.

---

## Stage 8 — Building the Core Views and Scoring Engine

**Date:** 03–05 March 2026

### Three primary views

**`decision_form` (GET + POST)**
- GET: renders form with Category and SubCategory dropdowns
- POST: creates `Decision` and `Option` objects, copies `CategoryCriterion` records into decision-specific `Criterion` instances, stores `decision_id` in session, redirects to `questions_page`

**`questions_page` (GET + POST)**
- GET: loads decision from session, fetches options and criteria, renders scoring sliders
- POST: deletes old scores for this decision, saves new scores, runs scoring engine, saves result, redirects to `result_page`

**`result_page` (GET)**
- Loads result from database, fetches ranked list, retrieves AI explanation, renders result template

### The Scoring Engine

Scoring logic was separated from views into `core/services/scoring_engine.py`. Mixing business logic into views creates untestable, unmaintainable code.

**Initial scoring function (weighted raw score):**
```python
def calculate_scores(decision):
    results = {}
    for option in decision.options.all():
        total = 0
        for score in Score.objects.filter(option=option, criterion__decision=decision):
            total += score.value * score.criterion.weight
        results[option] = total
    return results
```

**Problem identified immediately:** scores from a 3-criteria decision and a 7-criteria decision produce incomparable totals.

**Upgraded to normalized formula:**
```python
def calculate_scores(decision, weight_map=None):
    results = {}
    options = decision.options.all()
    criteria = decision.decision_criteria.all()

    if not weight_map:
        weight_map = {c.id: c.weight for c in criteria}

    total_weight = sum(weight_map.values())

    for option in options:
        total = 0.0
        for score in Score.objects.filter(option=option, criterion__decision=decision):
            cid = score.criterion.id
            adjusted_weight = weight_map.get(cid, score.criterion.weight)
            normalized_weight = adjusted_weight / total_weight
            normalized_score = score.value / 100
            total += normalized_score * normalized_weight
        results[option] = round(total * 100, 2)  # display as percentage

    return results
```

Final scores are percentages (0–100%). 78% vs 71% is immediately understandable to any user.

---

## Stage 9 — Bugs Encountered and How They Were Fixed

**Date:** 03–06 March 2026

This stage was messy. Documenting the bugs here because they were genuinely instructive.

---

### Bug 1: Score duplication on form re-submission

**Symptom:** Totals inflating unexpectedly. Winning option's score was sometimes double or triple what it should be.

**Root cause:** `Score.objects.create(...)` was called every time the form was POSTed. Refreshing or resubmitting created duplicate score rows. The total query then summed all historical scores for an option, not just the current session.

**Fix:**
```python
# Delete all existing scores for this decision before saving new ones
Score.objects.filter(option__decision=decision).delete()
```
Added as the very first line inside the POST block, before any new scores are created.

---

### Bug 2: Scores bleeding across decisions

**Symptom:** Option A in Decision 1 was affecting Option A in Decision 2 when option names were the same.

**Root cause:** The score query `Score.objects.filter(option=option)` did not scope to the current decision.

**Fix:**
```python
Score.objects.filter(option=option, criterion__decision=decision)
```
The `criterion__decision=decision` traversal through the FK chain ensures only scores from the correct decision are included.

---

### Bug 3: Migration conflict — ForeignKey type mismatch

**Error:**
```
django.db.utils.OperationalError: (1366, "Incorrect integer value: 'btech' for column 'chosen_option_id'")
```

**Root cause:** The `Result` model expected `chosen_option` to be an `Option` object (integer FK). The view was passing the option's *name* (a string) because `best_option` had been reassigned to the name string after the max calculation.

**Fix:**
```python
# Wrong
best_option = max(results, key=results.get).name

# Correct
best_option = max(results, key=results.get)
Result.objects.create(decision=decision, chosen_option=best_option, ...)
```

---

### Bug 4: Django template syntax breaking JavaScript

**Error:** browser parse errors; VS Code showing red squiggles throughout the JavaScript block.

**Root cause:** Django template tags (`{% for %}`, `{{ variable }}`) inside JavaScript string literals conflict with the JS parser.

**Wrong approach:**
```javascript
const OPTIONS = [
    {% for option in options %}
    { id: "{{ option.id }}", name: "{{ option.name }}" },
    {% endfor %}
];
```

**Fix using `json_script` filter:**
```html
{{ options_json|json_script:"options-data" }}

<script>
    const OPTIONS = JSON.parse(document.getElementById('options-data').textContent);
</script>
```
Django renders options as safe, escaped JSON. JavaScript reads it cleanly. No template syntax inside JS strings.

---

### Bug 5: Migration mismatch — "table has no column"

**Error:**
```
django.db.utils.OperationalError: table core_result has no column named reason
```

**Root cause:** a field had been renamed from `reason` to `explanation` in the model, but the migration history was in an inconsistent state — some applied, some not, conflicting with the actual MySQL table structure.

**Fix (development stage — data can be wiped):**
1. Delete all migration files except `__init__.py`
2. Drop and recreate the MySQL database
3. `python manage.py makemigrations && python manage.py migrate` — fresh start

Lesson: during active schema iteration, resetting migration history cleanly is faster than trying to patch a broken chain.

---

### Bug 6: Gemini API key not loading from .env

**Error:**
```
Unable to generate AI explanation: No API key was provided.
```

**Root cause:** `views.py` was calling `os.getenv("GEMINI_API_KEY")` before `load_dotenv()` was ever called. The `.env` file had not been read into the environment.

**Fix (Codex-assisted):**
```python
# At the top of views.py (before any os.getenv() calls)
from dotenv import load_dotenv
import os
load_dotenv()

import google.generativeai as genai
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
```

`load_dotenv()` must be called before any environment variable access.

**Additional note:** when uploading project files together with the `.env` file for help debugging, the API key got flagged and removed automatically. Learned the hard way not to share `.env` files — even in a debugging context.

---

### Bug 7: Anonymous user accessing protected views

**Error:**
```
ValueError: Cannot assign "<AnonymousUser>": "Decision.user" must be a "User" instance.
```

**Root cause:** the decision creation view tried to assign `request.user` to the Decision model's `user` ForeignKey. The user was not logged in — `request.user` was `AnonymousUser`.

**Fix:** add `@login_required` decorator to all views that access user data:
```python
from django.contrib.auth.decorators import login_required

@login_required
def decision_form(request):
    ...
```
Unauthenticated requests are redirected to the login page before the view function runs.

---

## Stage 10 — Adding the AI Explanation Layer

**Date:** 05–06 March 2026

With the scoring engine working correctly, the AI layer was added strictly for generating human-readable explanations *after* the ranking was already determined.

**Why Gemini instead of OpenAI:** the OpenAI API quota was exhausted during the CLI prototype stage. Gemini (Google) offered a free tier sufficient for development and demonstration.

**The prompt structure:**
```python
def generate_explanation(decision, results, best_option):
    ranked = sorted(results.items(), key=lambda x: x[1], reverse=True)
    criteria_info = [f"{c.name} (priority: {c.weight}%)" for c in decision.decision_criteria.all()]
    options_info = [f"{opt.name}: {score:.1f}%" for opt, score in ranked]

    prompt = f"""
    A user made a decision about: {decision.context}
    Options evaluated: {', '.join([o.name for o in decision.options.all()])}
    Criteria used: {', '.join(criteria_info)}
    Scores: {'; '.join(options_info)}
    Winner: {best_option.name}

    Write a 2-3 sentence explanation of why {best_option.name} was chosen.
    Reference specific criteria and their priorities. Be clear and direct.
    Do not use bullet points.
    """
    response = model.generate_content(prompt)
    return response.text
```

**Critical architectural rule enforced:** the AI call happens *after* `best_option` is already determined by the scoring engine. The AI receives the result as a fact and explains it. It cannot change the ranking.

**Fallback if AI unavailable:**
```python
try:
    explanation = generate_explanation(decision, results, best_option)
except Exception:
    explanation = (
        f"{best_option.name} scored highest overall with {results[best_option]:.1f}%. "
        f"It performed strongly across the weighted criteria for this decision."
    )
```
The system completes successfully whether or not the AI API responds.

---

## Stage 11 — Dynamic Criteria and Runtime Extra Criteria

**Date:** 06–07 March 2026

Users needed the ability to add criteria that aren't in the template — just for one session — without saving them to the database permanently.

**Why not save them to the database?** Saving user-added criteria to the database permanently would have caused a significant size increase over time — every user adding any custom criterion would bloat the template tables and affect other users' experiences. Keeping them session-only was the cleaner approach.

**Design decision:** runtime-only extra criteria are stored in the Django session, not the database.

**Use case example:** making a laptop decision and wanting to add "Brand sentimental value" as a temporary personal criterion. Valid for this one decision, but shouldn't appear in the Electronics template for everyone else.

**Implementation:** each extra criteria block generates inputs named `extra_name_N`, `extra_weight_N`, and `extra_N__<option_id>`. In the view, these are parsed from POST:

```python
extra_criteria = []
i = 1
while request.POST.get(f"extra_name_{i}"):
    name = request.POST.get(f"extra_name_{i}")
    weight = int(request.POST.get(f"extra_weight_{i}", 40))
    scores_per_option = {
        opt.id: int(request.POST.get(f"extra_{i}__{opt.id}", 3))
        for opt in options
    }
    if name not in [c.name for c in criteria]:  # duplicate check
        extra_criteria.append({"name": name, "weight": weight, "scores": scores_per_option})
    i += 1
```

Extra criteria are merged into the scoring calculation identically to database criteria, then discarded. Never written to the database. Weight normalization includes them in the total weight calculation.

---

## Stage 12 — Home Page, Decision History, Login, and "Other" Category

**Date:** 07–08 March 2026

### Home Page and History

Added to make the system feel like a complete product rather than a single-use tool.

**`home_page`** — displays all past decisions for the logged-in user, most recent first. Decision context truncated to a readable title length.

**`decision_history`** — full detail of a past decision: context, options evaluated, result, score breakdown per option, and AI explanation.

**Query:**
```python
decisions = Decision.objects.filter(user=request.user).order_by("-id")
```

### Login System

The login was added specifically so that decision history would be available to each user. Without authentication, there's no way to tie decisions back to a specific person. Django's built-in authentication system handled this without much additional setup.

Once the `@login_required` decorator was added to the protected views (see Bug 7 above), unauthenticated users get redirected to the login page automatically.

### "Other" Category

For decisions that don't fit any predefined category. When selected:
- `subcategory` is set to `NULL` on the Decision
- Criteria auto-loading is skipped
- User adds all criteria manually using the extra criteria system
- Stored in history normally

**View modification:**
```python
if category_id == "other":
    decision = Decision.objects.create(user=request.user, subcategory=None, context=context)
    # No criteria copying — user provides all via extra criteria
else:
    subcategory = SubCategory.objects.get(id=subcategory_id)
    decision = Decision.objects.create(user=request.user, subcategory=subcategory, context=context)
    for tc in subcategory.criteria.all():
        Criterion.objects.create(
            decision=decision, name=tc.name,
            weight=tc.default_weight, is_positive=tc.is_positive
        )
```

This made the system genuinely domain-agnostic: any decision, regardless of whether it fits a predefined category, can be evaluated using the same engine.

---

## What I Would Do Differently

**1. Design the schema before writing a single view.**
The database went through four iterations. Each change required migration resets or patches. Two hours of upfront schema design would have saved an estimated six hours of migration debugging.

**2. Build the scoring engine as a pure function first, completely isolated.**
The scoring engine was initially written inside the view and later extracted. Writing it as an isolated pure function (input: scores dict, weights dict → output: results dict) from the start, with no Django dependencies, would have made it testable immediately.

**3. Use environment variables from day one.**
The Gemini API key was temporarily hardcoded during development. This created a security risk and directly caused Bug 6. Starting with `.env` + `python-dotenv` from the first line of code would have prevented this entirely — and would have prevented the key getting removed when uploading files for help.

**4. Use a proper management command for seeding data.**
The `python manage.py shell → run()` approach works but is clunky and hard to discover. A proper Django management command (`python manage.py seed_data`) would be more professional and integrable into a deployment pipeline.

**5. Write one test before the first bug, not after.**
The scoring engine is a pure, deterministic function — ideal for unit testing. Writing zero tests during development meant every bug was found by running the full application and observing wrong outputs. A single unit test for the normalized scoring formula would have caught Bugs 1 and 2 before they caused confusion.

---

*BUILD_PROCESS.md — Decision Companion System — Vonnue Assignment — March 2026*

*This document is an honest record of the actual development process, including mistakes, pivots, and lessons learned. The goal is not a polished narrative but transparent, reflective engineering practice.*
