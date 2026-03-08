# Decision Companion System

> A multi-criteria decision tool that helps users compare options using weighted scoring — with AI-generated explanations powered by Gemini. Built with Python, Django, and MySQL.

---

## Table of Contents

1. [What This Project Is](#1-what-this-project-is)
2. [Assumptions I Made](#2-assumptions-i-made)
3. [How I Structured the Solution — and Why](#3-how-i-structured-the-solution--and-why)
4. [Design Choices and Trade-offs](#4-design-choices-and-trade-offs)
5. [How the Scoring Works](#5-how-the-scoring-works)
6. [Edge Cases I Thought About](#6-edge-cases-i-thought-about)
7. [How to Run the Project](#7-how-to-run-the-project)
8. [Project Structure](#8-project-structure)
9. [Database Schema](#9-database-schema)
10. [Decision Domain Tree](#10-decision-domain-tree)
11. [What I Would Improve with More Time](#11-what-i-would-improve-with-more-time)

---

## 1. What This Project Is

The assignment was asking for a Decision Companion System — basically a tool where a user can put in their options, rate them on different criteria, and the system tells them which one is best with a reason why.

When I first read the brief I honestly thought it was just a scoring tool. But the more I read the more I realized the point was more about *how* you think and build it, not just what the final thing looks like. The deliverables list kind of gave it away — they asked for a README, a BUILD_PROCESS.md, a RESEARCH_LOG.md and a design diagram alongside the actual code.

So the real challenge was building something that:

- Is **not** a black box — every score should trace back to what the user actually entered
- Works even if the AI API goes down
- Can handle different kinds of decisions (not just one specific use case like "pick a laptop")
- Is genuinely dynamic — user changes something, the output changes too

That last point shaped basically every decision I made from the beginning.

### The Core Problem with Most Existing Tools

I looked at things like Qlik (a big business intelligence DSS platform) and a bunch of GitHub projects. Most of them are either way too complex for a personal decision or they just give you a result without telling you why. The assignment needed the opposite of that.

---

## 2. Assumptions I Made

| # | Assumption | Why I Made It |
|---|-----------|---------------|
| A-1 | Users are non-technical | The UI should use plain language — sliders, dropdowns, percentages. No raw formulas shown. |
| A-2 | Decisions usually involve 2–10 options | More than 10 is impractical to score manually. Less than 2 isn't really a decision. |
| A-3 | Criteria are different per domain but structurally similar | A laptop decision and a career decision both have some version of cost, risk, and value. Same engine works for both. |
| A-4 | Users already know what their options are | The system doesn't search for alternatives. It evaluates what you already have in mind. |
| A-5 | People think in percentages for importance | "Cost matters 60%, design matters 40%" makes more sense than "weight = 1.7". |
| A-6 | The AI explanation is just for readability | The ranking happens first. Then AI just writes a sentence explaining the numbers in a human way. |
| A-7 | Each user's decisions are private | Tied to a logged-in account and stored in their history. |
| A-8 | "Not hardcoded" means the engine logic never changes | All the domain-specific stuff (categories, criteria, weights) lives in the database, not in code. |

---

## 3. How I Structured the Solution — and Why

### It Didn't Start Here

The system went through a few stages before it became what it is now. I think it's worth explaining the evolution because some of the earlier decisions are what made the final architecture make sense.

---

#### Stage 1 — First Prototype: AI Questions, Score Out of 5

The very first version was a Python CLI. User enters a decision context, the AI generates 5 questions, user rates each option 1–5, system adds up and picks the winner.

**What worked:** the flow made sense and AI question generation was actually useful — it gave relevant questions from a short description.

**What didn't work:** every question was treated as equally important. Asking "how cost-effective is it?" carries way more weight than "how does it look?" for most decisions. Equal weighting gives wrong answers.

Also the OpenAI API quota ran out during testing so I had to switch to Gemini. From that point the whole project used Gemini.

---

#### Stage 2 — Adding Priority (Lexicographic)

I added a step where users rank criteria 1st, 2nd, 3rd. The option that scores best on the top criterion wins.

**What improved:** priority now matters.

**What was still wrong:** if Laptop A is the cheapest (top priority) but terrible at everything else, it still wins. Real decisions involve trade-offs, not just one winning criterion. This approach is too rigid.

---

#### Stage 3 — Hybrid Weighted Scoring (the Final Approach)

Instead of ranking, users assign a *percentage* to each criterion. These percentages become weights in the final formula.

**Formula:**
```
Final Score(option) = Σ [ (score / 5) × (priority / total_priority) ]
```

Both the score and the weight get normalized before being multiplied — so the final score is always between 0 and 1 no matter how many criteria there are. This means different decisions with different numbers of questions produce comparable scores.

Two validation methods run together:
1. **Weighted Score** — the formula above, gives the full picture
2. **Priority Dominance** — which option scored best on the top criterion

If both agree → confident recommendation. If they disagree → the system says so and shows both results.

---

#### Stage 4 — Making Criteria Dynamic

Once the scoring logic was right, I needed to solve how the system knows *which* criteria to use for different decision types.

The wrong approach would be:
```python
if domain == "laptop":
    score = price * 0.5 + battery * 0.3 + performance * 0.2
```

This hardcodes everything. Adding a new domain = changing code.

The right approach: **criteria live in the database, not the code**.

```
Category  (e.g. "Purchase Decision")
  └── SubCategory  (e.g. "Electronics")
        └── CategoryCriterion  (e.g. "Cost Efficiency", weight=40)
        └── CategoryCriterion  (e.g. "Performance", weight=35)
        └── CategoryCriterion  (e.g. "Build Quality", weight=25)
```

When a user creates a decision, the relevant criteria get *copied* into their specific decision instance. They can adjust the weights. The original template stays untouched.

Adding a new decision category requires zero code changes — just add rows in the admin panel.

---

#### Stage 5 — Switching to Percentage Weights (0–100)

Originally weights were stored as floats like `1.0`, `1.5`. Changed to integers representing percentages (1–100) because users understand "this criterion is 60% important" way more naturally than a decimal weight. Also auto-normalizes if the user's percentages don't add up to exactly 100.

---

### Final Architecture: Three Layers

```
┌─────────────────────────────────────────┐
│           INPUT LAYER                   │
│  User picks category + subcategory,     │
│  enters options, adjusts weights,       │
│  optionally adds custom criteria        │
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│         DECISION ENGINE                 │
│  Deterministic weighted scoring         │
│  Score(option) = Σ[(s/5)×(p/100)]      │
│  Priority dominance check               │
│  Conflict resolution rule               │
│  Result stored in MySQL                 │
└────────────────┬────────────────────────┘
                 │
┌────────────────▼────────────────────────┐
│        EXPLANATION ENGINE               │
│  Gemini generates a readable            │
│  explanation AFTER ranking is done      │
│  Fallback: rule-based text if API fails │
│  AI does NOT change the ranking         │
└─────────────────────────────────────────┘
```

---

## 4. Design Choices and Trade-offs

### Django over Flask/FastAPI

Picked Django because the timeline was tight and I needed an admin panel, authentication, an ORM, and migrations all working out of the box. Django gives all of that. Flask would have needed me to build each of those pieces separately.

Trade-off: Django is heavier. For a pure API project Flask would be cleaner. But for this, Django was the right call.

---

### MySQL over NoSQL

The data is strongly relational — a Decision has Options, Options have Scores, Scores reference Criteria, and Criteria belong to SubCategories. All of that benefits from foreign keys and JOIN queries. A document store would require me to manage those relationships in application code, which is worse.

Trade-off: SQL requires defined schemas and migrations. This caused some pain during early development when I was changing models often — I ended up resetting migrations a few times. A document store would have been more flexible during that phase.

---

### Criteria in the Database, Not Code

This is the decision I'm most confident about. The scoring engine has zero domain knowledge. It just runs the formula on whatever criteria it finds for the current decision. This means the system is genuinely extensible — not just claiming to be.

Trade-off: the database has to be seeded before it works. The seed script (`core/seeds/initial_data.py`) must be run after the first migration.

---

### AI as Explanation Only — Not Decision Maker

If AI decided the weights or made the ranking, I couldn't explain why Option A beat Option B. The system produces the ranking deterministically first. Then Gemini is called with the result as a fact and asked to describe it in plain English. The ranking cannot change at that point.

Trade-off: the explanation is sometimes a bit generic. But it's always accurate — it never contradicts the actual numbers.

---

### Fallback Mode When AI is Unavailable

The system works fully without any AI. If Gemini fails (quota exceeded, network error, key missing), the system falls back to 5 generic evaluation questions and generates a rule-based explanation. The decision still completes.

---

### Positive Criteria Phrasing

All criteria are phrased positively — "Cost Efficiency" not "Cost", "Ease of Maintenance" not "Maintenance Complexity". If you ask someone to "Rate the Cost (1–5)" they don't know if 5 means expensive (bad) or cheap (good). By rephrasing, 5 always means good across every criterion. No score inversion needed in the engine.

The `is_positive` boolean is still in the database for engine flexibility, but the UI never exposes it confusingly to users.

---

### Runtime-Only Extra Criteria

Users can add criteria that aren't in the template during a session. These are stored in the Django session (not the database) and discarded after the result is saved. This gives flexibility without polluting the template data that everyone else uses.

---

## 5. How the Scoring Works

### The Formula

```
Final Score(option) = Σ [ (score_ij / 100) × (priority_j / total_priority) ]
```

Where:
- `score_ij` = user's rating (1–5) of option `i` on criterion `j`
- `priority_j` = importance weight assigned to criterion `j` (0–100)
- `total_priority` = sum of all criterion priorities (auto-normalized)

### Example

| Criterion | Priority | Option A Score | Option B Score |
|-----------|----------|----------------|----------------|
| Cost Efficiency | 40 | 4 | 2 |
| Performance | 35 | 3 | 5 |
| Build Quality | 25 | 5 | 4 |
| **Total Priority** | **100** | | |

**Option A:**
```
(80/100 × 40/100) + (60/100 × 35/100) + (100/100 × 25/100)
= 0.32 + 0.21 + 0.25
= 0.78 → displayed as 78%
```

**Option B:**
```
(40/100 × 40/100) + (100/100 × 35/100) + (80/100 × 25/100)
= 0.16 + 0.35 + 0.20
= 0.71 → displayed as 71%
```

**Result:** Option A wins (78% vs 71%).

**AI Explanation:** *"Option A scored highest overall, performing strongly in Cost Efficiency (your highest-priority criterion) and Build Quality. Although Option B outperformed it in Performance, Option A's advantage in cost-effectiveness — which you weighted most heavily — gave it the edge."*

---

## 6. Edge Cases I Thought About

| Edge Case | How It's Handled |
|-----------|-----------------|
| User submits scoring form twice | All existing scores for the decision are deleted before new ones are saved |
| Priorities don't add up to 100 | Auto-normalized: `priority / total_priority`. Works whether user enters 40+60 or 80+120. |
| AI API quota exceeded or unavailable | Falls back to 5 generic evaluation questions. System still completes. |
| User picks "Other" category (no template) | SubCategory set to NULL. User adds all criteria manually. Same scoring engine runs. |
| User adds a custom criterion with a duplicate name | Duplicate check prevents double-counting. Ignored silently. |
| No scores submitted | Guard clause redirects to form with an error. No result saved. |
| All options tie | System reports the tie and suggests adjusting priorities or adding more differentiating criteria. |
| Migration conflict (non-nullable FK on existing rows) | Temporary fix: set `null=True`, run migration, seed data, then remove null and migrate again. |
| Anonymous user accessing protected pages | `@login_required` redirects to login before any view function runs. |
| Gemini API key missing from environment | `python-dotenv` loads `.env` at startup. If key not found, fallback mode activates. |

---

## 7. How to Run the Project

### Prerequisites

- Python 3.11+
- MySQL 8.0+ (or SQLite for a quick dev setup — see note below)
- Git

---

### Step 1 — Clone the Repository

```bash
git clone <your-repo-url>
cd decision_system
```

---

### Step 2 — Create and Activate a Virtual Environment

```bash
python -m venv env

# Windows
env\Scripts\activate

# Mac / Linux
source env/bin/activate
```

---

### Step 3 — Install Dependencies

```bash
pip install -r requirements.txt
```

Key packages used:
```
django
mysqlclient
python-dotenv
google-generativeai
```

---

### Step 4 — Configure Environment Variables

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_gemini_api_key_here
SECRET_KEY=your_django_secret_key_here
DEBUG=True
DATABASE_URL=mysql://root:yourpassword@localhost:3306/db_name
```

And in Railway's **Variables** tab put your PostgreSQL URL:
```
DATABASE_URL=postgresql://postgres:DbxaVtczVftezmQmvKgHuladmEobHGLI@switchyard.proxy.rlwy.net:48422/railway
```

Also add `mysqlclient` back to `requirements.txt` since you need it for local MySQL:
```
mysqlclient
psycopg2-binary
```

> **Note:** If you don't have a Gemini API key the system still works — it falls back to generic questions automatically.

> **SQLite alternative:** To skip MySQL setup during development, change `settings.py`:
> ```python
> DATABASES = {
>   'default': dj_database_url.config(
>       default=os.environ.get('DATABASE_URL')
>   )
>}
> ```

---

### Step 5 — Create the MySQL Database

```sql
CREATE DATABASE decision_system CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

---

### Step 6 — Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

---

### Step 7 — Seed the Decision Tree

The categories, subcategories, and default criteria need to be loaded before the system works.

```bash
python manage.py shell
```

Inside the shell:
```python
from core.seeds.initial_data import run
run()
```

You should see:
```
Initial decision tree inserted successfully!
```

---


### Step 8 — Start the Server

```bash
python manage.py runserver
```

| URL | What It Does |
|-----|-------------|
| `http://127.0.0.1:8000/` | Home page — your decision history |
| `http://127.0.0.1:8000/decision/` | Start a new decision |
| `http://127.0.0.1:8000/admin/` | Admin panel — manage categories, criteria, view data |

---

### Step 9 — Using the System

1. **Register / Log In** — create a user account
2. **Create a Decision** — select a category and subcategory, enter the options you want to compare
3. **Score Options** — rate each option on each criterion from 1 (poor) to 5 (excellent)
4. **Adjust Priorities** — set how important each criterion is as a percentage (auto-normalized)
5. **Add Custom Criteria** — optionally add criteria not in the template, for this session only
6. **Finalize** — system computes the ranking, saves the result, and calls Gemini for an explanation
7. **View History** — all past decisions are saved and accessible from the home page

---

## 8. Project Structure

```
decision_system/
│
├── decision_system/           # Django project config
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── core/                      # Main application
│   ├── models.py              # All 8 database models
│   ├── views.py               # All view functions
│   ├── urls.py                # URL routing
│   ├── admin.py               # Admin panel registrations
│   ├── forms.py
│   │
│   ├── seeds/
│   │   ├── __init__.py
│   │   └── initial_data.py    # Decision tree seed script
│   │
│   └── templates/
│       └── core/
│       |   ├── home_page.html
│       |   ├── decision_form.html
│       |   ├── questions_page.html
│       |   ├── result_page.html
│       |   └── history_detail.html
│       └── registration/
│
├── .env                       # API keys and DB credentials (not committed)
├── .gitignore
├── requirements.txt
├── manage.py
├── README.md
├── BUILD_PROCESS.md
└── RESEARCH_LOG.md
```

---

## 9. Database Schema

```
Category
  id, name
  └── SubCategory
        id, name, category_id (FK)
        └── CategoryCriterion         ← reusable template
              id, name, default_weight, is_positive, subcategory_id (FK)

Decision
  id, user_id (FK), subcategory_id (FK), context, created_at
  ├── Option
  │     id, name, decision_id (FK)
  │     └── Score
  │           id, option_id (FK), criterion_id (FK), value (1–5)
  │
  ├── Criterion                        ← copied per decision (user-editable)
  │     id, name, weight, is_positive, decision_id (FK)
  │
  └── Result
        id, decision_id (OneToOne), chosen_option_id (FK), total_score, explanation
```

**Key design note:** `CategoryCriterion` stores the reusable templates. When a decision is created, criteria are **copied** into `Criterion` instances linked to that specific decision. So users can tweak weights for one decision without affecting the template for everyone else.

---

## 10. Decision Domain Tree

The following categories and subcategories are seeded into the database at setup:

```
Purchase Decisions
├── Electronics (Laptop, Phone, Tablet)
├── Vehicles (Car, Bike)
├── Digital Products (Software, Subscriptions)
├── Services (Internet, Insurance)
└── Assets (Real Estate, Gold, Equipment)

Technology Decisions
├── Infrastructure (Cloud: AWS vs Azure vs GCP)
├── Backend Framework (Django vs Node vs Spring)
├── Frontend Framework (React vs Vue vs Angular)
├── Database (PostgreSQL vs MySQL vs MongoDB)
├── DevOps (CI/CD, Containerisation)
└── Security (Auth providers, IAM)

Career Decisions
├── Education (MBA, Specialisation, Online vs Offline)
├── Employment (Startup vs Corporate, Remote vs Onsite)
├── Skill Development (Certification, Course selection)
├── Entrepreneurship (Startup vs employment, Funding)
└── Career Transition (Industry switch, Role change)

Financial Decisions
├── Investment (Mutual funds, Crypto, Stocks)
└── Loan / Financing (Home loan, Education loan)

Travel & Lifestyle Decisions
├── Travel (Vacation, Destination, Package)
├── Relocation (City, Country, Residential area)
└── Lifestyle (Fitness program, Coworking space, Remote vs office)

Hiring Decisions
└── Candidate Evaluation
      (Technical Skills, Experience, Communication, Cultural Fit,
       Salary Expectation, Reliability, Retention, Growth Potential)
```

Users can also select **"Other"** to define their own criteria from scratch — making the system domain-agnostic for anything that doesn't fit a predefined category.

---

## 11. What I Would Improve with More Time


### 1 Numeric Constraints for Budget and Time

Instead of only qualitative comparison, users would be able to enter numerical limits such as maximum budget or available time.
Options that exceed these limits would automatically receive a lower score, making the system closer to a real-world constraint-based decision model.

### 2. AI-Generated Guiding Questions for Criteria

An LLM could generate short guiding questions for each criterion to help users evaluate options more easily.
For example, if the criterion is Maintenance Effort, the system might ask:

“How frequently will this option require maintenance?”

“Does it require specialized knowledge to maintain?”
This would reduce ambiguity and make scoring more consistent.

### 3. Criterion and Category Review System

After completing a decision, users could leave reviews or notes for each criterion and category.
Over time this would help understand:

Which criteria were actually useful

Which categories users rely on most

Whether certain criteria lead to better decisions

### 4. Expanding the Category Library

Currently the system uses a limited set of predefined categories.
With more development time, I would expand the category library so the system can support a wider range of decision contexts (technology, purchases, career choices, etc.).
A richer category set would make the system more flexible and applicable to more real-world problems.
---

## Notes on AI Usage

AI tools (ChatGPT, Google Gemini, OpenAI Codex) were used throughout the project as research and development aids.

- **ChatGPT** was used to evaluate architectural options, design the schema, reason through scoring formulas, and debug issues. Many suggestions were modified or rejected after review.
- **Gemini** was used to research domain categories and generate questions. Output was adapted, not copied.
- **Codex** was used to debug the `.env` API key loading issue specifically — the key wasn't loading because `load_dotenv()` wasn't being called before `os.getenv()`. Uploading files together with the `.env` during that session also caused the API key to get flagged and removed, which was a lesson learned about what not to share.

The AI suggestion I was most careful to reject: using AI to determine weights, confidence scores, or rankings. In this system, AI generates questions and explains results — it never makes the decision itself.

Full details of all prompts, what was accepted, rejected, and modified are in `RESEARCH_LOG.md`.

---

*Decision Companion System — Vonnue Assignment — March 2026*
