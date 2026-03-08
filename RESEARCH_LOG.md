# RESEARCH_LOG.md
## Decision Companion System — Full Research & Development Log

> **Project:** Decision Companion System (Vonnue Assignment)
> **AI Tools Used:** ChatGPT (Custom GPT), Google Gemini AI, OpenAI Codex
> **Research Period:** 23 February 2026 – 08 March 2026
> **ChatGPT Session URL:** https://chatgpt.com/g/g-p-69a71ffe81f08191aef04ed178bac9f4-decision-companion-system/c/699326ba-daac-8323-a283-c1924fdbf65e
> **Tech Stack Decided:** Python · Django · MySQL · Gemini API
> **Log Compiled:** 08 March 2026

---

## TABLE OF CONTENTS

1. [Purpose of This Log](#1-purpose-of-this-log)
2. [All AI Prompts Used (Chronological)](#2-all-ai-prompts-used-chronological)
3. [All Search Queries](#3-all-search-queries)
4. [References That Influenced the Approach](#4-references-that-influenced-the-approach)
5. [Decisions: Accepted, Rejected, or Modified from AI Output](#5-decisions-accepted-rejected-or-modified-from-ai-output)
6. [Architecture Evolution Summary](#6-architecture-evolution-summary)
7. [Key Technical Decisions Log](#7-key-technical-decisions-log)

---

## 1. Purpose of This Log

This document records every AI prompt, search query, reference, and decision made during the research and development of the **Decision Companion System**. It is required as part of the project deliverables and is meant to show transparency, responsible AI use, and clear engineering thinking.

The assignment from **Vonnue** required:
- A Multi-Criteria Decision-Making (MCDM) system
- Dynamic (not hardcoded) inputs
- Explainable logic (no black-box AI)
- Ranked output with justified recommendation
- Deliverables: Git repo, README, design diagram, BUILD_PROCESS.md, RESEARCH_LOG.md

---

## 2. All AI Prompts Used (Chronological)

Below are all prompts submitted across all AI tools (ChatGPT, Gemini, Codex), in chronological order. Each prompt is numbered and categorized by phase and tool.

---

### PHASE 0 — Early Discovery Research *(23 February 2026)*

---

**[P-000-G1] — Google Search**
> Search query: `Decision Helper System`

**What was found:**
Discovered **Qlik** — a Business Intelligence / Decision Support System (DSS) platform.
- URL: https://www.qlik.com/us/business-intelligence/decision-support-system
- Description: DSS is analytics software used to gather and analyze data to help inform and improve business decision-making. Modern DSS tools use real-time analytics and AI to support planning by turning data into actionable insights.

**How it influenced the project:**
Confirmed that structured, data-driven decision support systems already exist in the enterprise space. Key observation: these are analytical tools built for business intelligence, not general-purpose personal decision companions. This gap confirmed the assignment's design intent and differentiation opportunity.

**Status:** ✅ Accepted as reference point — used to justify why the system must be *explainable* (unlike enterprise black-box DSS tools) and *generalizable* (not domain-locked).

---

**[P-000-G2] — GitHub Exploration**
> URLs visited:
> - https://github.com/topics/decision-making?l=html&o=asc&s=forks

**What was found:**
Explored open-source decision-making projects on GitHub (filtered by HTML, sorted by forks). Surveyed how other developers had implemented decision tools at a smaller scale.

**How it influenced the project:**
Helped understand the scope of existing open-source implementations and identify what was commonly missing: explainability, multi-domain support, and weighted multi-criteria ranking.

**Status:** ✅ Used as background research. No specific code was reused.

---

### PHASE 1 — Understanding the Assignment

---

**[P-001]**
> *Uploaded: `decision_question.pdf`*
> "What do you understand after reading this pdf, explain if there are any existing solutions that exist."

**AI Response Summary:** AI identified this as a Multi-Criteria Decision-Making (MCDM) system assignment. Explained that the real evaluation is on: system design thinking, documentation quality, explainability, and responsible AI use. Listed existing solutions: Weighted Scoring Model, AHP (Analytic Hierarchy Process), TOPSIS, Airfocus, Trello plugins, Notion templates, Amazon/Netflix (ML-based black-box systems).

---

### PHASE 2 — Evaluating Logic Options

---

**[P-002]**
> "Tell me the feasibility of each of the options for the logic I am to give you now:
> 1. Using AI model to generate dynamic questions and with the answers relating to this make a point-based system where each of their answers is evaluated and the one with best confidence is taken as the decision.
> 2. Listing the priority by the user and based on the priority selecting the best answer.
> If you have any other better option tell me."

**AI Response Summary:** Evaluated both options across: technical feasibility, explainability, design maturity, risk level, and assignment fit.
- Option 1: Medium-High feasibility but risky — violates "not black box" requirement. Non-deterministic.
- Option 2: Very High feasibility, fully explainable — but too simple, doesn't handle trade-offs (Lexicographic Decision Model).
- Recommended **Option 3 (Hybrid)**: Weighted Scoring + Optional AI Assistance.

---

**[P-003]**
> "But as we are trying to implement the system for different types of scenarios so the criteria can always alter."

**AI Response Summary:** Introduced the concept of making criteria "first-class data" not hardcoded logic. Recommended a Domain-Agnostic Decision Engine split into 3 layers: (1) Input Layer, (2) Decision Engine (generic core), (3) Explanation Engine.

---

**[P-004]**
> "Now I am to design a system — tell me if this is heavily dependent on AI. I will use ChatGPT or any other API to generate questions regarding my specific task, and by using a NoSQL database or SQL if it allows for some kind of data structure as struct or object to store each category of question asked by the API and the point corresponding to that category. Now using the points in each category rank the result."

**AI Response Summary:** Defined clear boundary between AI-safe and AI-dangerous usage. If AI only generates questions → Not heavily AI dependent. If AI decides priority/weighting/ranking → Heavily AI dependent and violates assignment. Improved Architecture recommended: AI generates initial question set, system controls all weights and ranking.

---

### PHASE 3 — Input Design and Comma-Separated Options

---

**[P-005]**
> "I want users to be able to enter multiple options. What's the easiest way for a user to input them?"

**AI Response Summary:** Suggested several approaches: individual form fields, dynamic add/remove buttons, comma-separated text input. Each has trade-offs between simplicity and UX quality.

**Decision Made:** chose comma-separated input for the initial CLI prototype because it requires no extra UI logic — user just types options as a list. This was later replaced with proper form fields in the Django web app but the concept proved the flow.

**Status:** ✅ Accepted for prototype. Modified to proper fields in the web app version.

---

### PHASE 4 — Identifying Categories and Subcategories

---

**[P-006]**
> "I need to identify the general categories of decisions that people make and then subcategories under each to make the system versatile. Help me think through this from the problem statement."

**AI Response Summary:** Suggested 6 broad categories based on common human decision-making domains: Purchase Decisions, Technology Decisions, Career Decisions, Financial Decisions, Travel & Lifestyle Decisions, and Hiring Decisions. Under each, suggested subcategories that would cover common real-world use cases.

**How it influenced the project:** this became the seeded decision tree. The categories were derived from reading the problem statement broadly and thinking about what kinds of decisions people actually face. AI helped expand on initial ideas but the final list was reviewed and trimmed.

**Status:** ✅ Accepted and adapted — used as the basis for the seeded Category/SubCategory/CategoryCriterion database structure.

---

### PHASE 5 — Scoring System Design

---

**[P-007]**
> "I have a scoring system where users rate each option out of 5. The problem is every question has equal weight. How do I fix this?"

**AI Response Summary:** Recommended weighted scoring. User assigns a priority percentage to each criterion. Final score = sum of (score/5 × priority/total_priority). Explained the mathematical benefit of normalization — makes sessions with different numbers of questions comparable.

---

**[P-008]**
> "I tried adding an is_positive boolean to handle criteria where lower is better (like cost). But it's causing a lot of bugs and errors in my code. What's the cleaner way to handle this?"

**AI Response Summary:** Suggested two approaches: (1) keep the boolean and fix the inversion logic, (2) rephrase all criteria positively so inversion is never needed. Strongly recommended option 2 as the cleaner UX and engineering approach.

**Decision Made:** discarded the boolean-driven inversion logic. Rephrased all criteria positively. "Cost" → "Cost Efficiency", "Risk" → "Risk Safety", etc. The `is_positive` field was kept in the database for flexibility but the UI always presents positive phrasing.

**Status:** ✅ Accepted — positive phrasing approach adopted. Boolean retained in schema for engine flexibility only.

---

### PHASE 6 — Moving to Django

---

**[P-009]**
> "What Python web framework should I use? I need admin panel, authentication, and a database ORM built in."

**AI Response Summary:** Compared Flask, FastAPI, Django. Recommended Django for this use case: ORM + admin panel + built-in auth + migrations = all requirements met out of the box.

**Status:** ✅ Accepted — Django chosen.

---

**[P-010]**
> "Help me design the database schema for this system. I need to store categories, subcategories, criteria templates, decisions, options, scores per option per criterion, and results."

**AI Response Summary:** Suggested the 8-table normalized schema: Category, SubCategory, CategoryCriterion, Decision, Option, Criterion (copied per decision), Score, Result. Specifically recommended separating CategoryCriterion (reusable templates) from Criterion (per-decision instance copies).

**Status:** ✅ Accepted with modifications — the template/instance separation was the key insight that made the schema correct.

---

### PHASE 7 — Bugs and Debugging

---

**[P-011]**
> "My scores are doubling every time I resubmit the form. What's going wrong?"

**AI Response Summary:** Identified root cause as duplicate `Score.objects.create()` calls on each POST. Solution: delete all existing scores for the decision before saving new ones at the start of every POST handler.

**Status:** ✅ Accepted — fix implemented.

---

**[P-012]**
> "I'm getting an error: 'Incorrect integer value: btech for column chosen_option_id'. What does this mean?"

**AI Response Summary:** Identified type mismatch — `best_option` had been assigned `.name` (a string) but the ForeignKey field expects an object instance. Fix: pass the object, not the name string.

**Status:** ✅ Accepted — fix implemented.

---

**[P-013]**
> "Django template tags inside my JavaScript are causing errors. VS Code is showing red squiggles everywhere in the JS block."

**AI Response Summary:** Introduced `json_script` filter as the clean solution: render data as a JSON element in the HTML, read it with `JSON.parse()` in JavaScript. No template tags inside JS strings.

**Status:** ✅ Accepted — `json_script` approach implemented.

---

**[P-014]** *(Codex-assisted)*
> "My Gemini API key isn't loading from the .env file. I'm getting 'No API key was provided' even though the key is in .env."

**AI Response Summary:** Identified that `os.getenv()` was being called before `load_dotenv()`. Fix: call `load_dotenv()` at the top of `views.py` before any environment variable access.

**Additional note:** when uploading files to get help with this bug, the `.env` file was included in the upload. This caused the API key to be detected and automatically removed/flagged. Lesson learned: never share `.env` files, even for debugging purposes.

**Status:** ✅ Accepted — fix implemented. `.env` handling improved from this point.

---

### PHASE 8 — AI Explanation Layer

---

**[P-015]**
> "I want to add an AI-generated explanation for the result. But the AI should only explain the result — it should not be able to change it. How do I structure this?"

**AI Response Summary:** Confirmed the correct pattern: run scoring engine first, store result, then call AI with the result as a fact to generate the explanation. Explanation should be called only on finalization to reduce API costs.

**Status:** ✅ Accepted — AI explanation layer implemented post-ranking.

---

### PHASE 9 — Extra Criteria and Session Storage

---

**[P-016]**
> "Users want to add criteria that aren't in the template, but I don't want to save these to the database permanently because it would cause a lot of data bloat over time. What's the best approach?"

**AI Response Summary:** Recommended storing runtime extra criteria in the Django session. They exist only for the duration of the scoring flow and are merged into the calculation with the permanent criteria. Never written to the database.

**Status:** ✅ Accepted — session-based runtime criteria implemented.

---

### PHASE 10 — Login and History

---

**[P-017]**
> "I want to add login so that each user has their own decision history. What's the simplest way to do this in Django?"

**AI Response Summary:** Django's built-in `User` model and `@login_required` decorator handle this entirely. Add `user = ForeignKey(User)` to the Decision model. Filter decision history by `request.user`.

**Status:** ✅ Accepted — login and per-user history implemented.

---

## 3. All Search Queries

| # | Query | Platform | What Was Found |
|---|-------|----------|---------------|
| S-001 | `Decision Helper System` | Google | Qlik DSS — enterprise business intelligence platform |
| S-002 | `decision-making` (topics, filtered HTML, sorted forks) | GitHub | Open-source decision tools — mostly narrow or oversimplified |
| S-003 | `weighted scoring model MCDM` | Google | Academic references on Weighted Scoring, AHP, TOPSIS |
| S-004 | `Django vs Flask vs FastAPI comparison 2025` | Google | Framework comparison articles — confirmed Django as right choice |
| S-005 | `python-dotenv load_dotenv not working` | Google | Stack Overflow — confirmed load_dotenv must precede os.getenv() |
| S-006 | `django json_script template filter` | Google | Django docs — confirmed json_script as the correct approach |
| S-007 | `Django login_required decorator tutorial` | Google | Django docs — confirmed @login_required usage |

---

## 4. References That Influenced the Approach

| Reference | Type | How It Influenced the Project |
|-----------|------|-------------------------------|
| Qlik DSS (qlik.com) | Industry tool | Confirmed need for explainability — Qlik is opaque, assignment needs the opposite |
| GitHub decision-making topics | Open source survey | Showed existing tools are too narrow or too simple; confirmed the gap this project fills |
| Django documentation (docs.djangoproject.com) | Official docs | Used for: migrations, ForeignKey, @login_required, json_script filter, session management |
| Python-dotenv documentation | Library docs | Confirmed correct usage of load_dotenv() |
| ChatGPT full session (477 pages, 19,285 lines) | AI conversation | Primary research and decision-making reference throughout the project |
| Google Gemini AI sessions (02 March 2026) | AI conversation | Category/subcategory generation, explanation prompt design |
| OpenAI Codex session (03 March 2026) | AI debugging | .env key loading bug resolution |

---

## 5. Decisions: Accepted, Rejected, or Modified from AI Output

### ✅ ACCEPTED

| # | AI Suggestion | Why Accepted |
|---|---------------|--------------|
| A-001 | Hybrid weighted scoring + optional AI assistance (Option 3) | Best balance of explainability, design maturity, and assignment compliance. |
| A-002 | Making criteria "first-class data" (dynamic, not hardcoded) | Core architectural principle that makes the system domain-agnostic. |
| A-003 | 3-layer architecture: Input → Decision Engine → Explanation Engine | Clean separation of concerns; improves testability and documentation clarity. |
| A-004 | Using SQL (MySQL) over NoSQL | Data is strongly relational; SQL ensures referential integrity and analytics support. |
| A-005 | Django as the web framework | Strong built-in ORM, admin panel, auth, migrations — reduces boilerplate for assignment timeline. |
| A-006 | AI = content generator only (NOT decision authority) | Keeps system compliant with "not black box" requirement. Core scoring is deterministic. |
| A-007 | Fallback mode when AI API unavailable (5 generic questions) | Shows production-level fault tolerance and aligns with "system must work without AI." |
| A-008 | Normalized scoring: `Final = Σ[(score/5) × (priority/total_priority)]` | Mathematically stable. Final score always 0–1 regardless of raw weight values entered. |
| A-009 | Positive criteria phrasing over inversion logic | Avoids confusing UX. "How cost-effective?" is clearer than "Rate cost (where lower = better)." |
| A-010 | `json_script` filter to pass Django data to JavaScript | Eliminates Django/JS template conflict cleanly; safer escaping. |
| A-011 | 8-table database schema (Category, SubCategory, CategoryCriterion, Decision, Option, Criterion, Score, Result) | Clean normalized design with template isolation and per-decision instance copies of criteria. |
| A-012 | Copy criteria from CategoryCriterion into Criterion per decision instance | Allows per-decision weight customization without modifying reusable templates. |
| A-013 | Unlimited runtime-only extra criteria (not saved to DB) | Gives users flexibility without polluting template data or causing database size increase. |
| A-014 | `Score.objects.filter(option__decision=decision).delete()` before saving fresh scores | Prevents score duplication on form re-submission. |
| A-015 | Home page + decision history with card layout | Gives the system a complete product feel beyond a single-use tool. |

---

### ❌ REJECTED

| # | AI / Own Suggestion | Why Rejected |
|---|---------------------|--------------|
| R-001 | Option 1 — Pure AI confidence-based decision (AI assigns confidence, highest wins) | Violates "not black box" requirement. Non-deterministic, hard to explain. |
| R-002 | Option 2 — Priority-only lexicographic model as sole approach | Too simple. Doesn't handle trade-offs. Would not stand out. |
| R-003 | AI parsing full CVs for hiring decisions | Token limits, NLP complexity, explainability failure, time cost for assignment scope. |
| R-004 | Handlebars for frontend templating | Pushes toward full SPA architecture; adds unnecessary complexity for an assignment focused on backend logic. |
| R-005 | Separate AI model for option name normalization | Wasteful API dependency for a task Python `.strip().title()` handles natively. |
| R-006 | AI deciding question priority/weights | Highest risk category. If AI controls weights → controls outcome → becomes decision authority → violates assignment. |
| R-007 | Using `openai.ChatCompletion.create()` (old SDK) and OpenAI generally | Deprecated SDK. Additionally, OpenAI quota ran out during CLI prototype. Switched to Gemini entirely. |
| R-008 | Storing extra/runtime criteria in DB permanently by default | Creates data noise and size increase; runtime criteria are temporary and should stay in session. |
| R-009 | AHP (pairwise comparison) as scoring method | Too complex UX for general users; weighted scoring achieves the same result more accessibly. |
| R-010 | TOPSIS as primary algorithm | Requires cross-option normalization simultaneously; adds complexity without proportional benefit at this scale. |
| R-011 | Boolean `is_positive` field driving score inversion logic | Caused a lot of errors in the scoring logic. Replaced by positive criteria phrasing. |

---

### 🔄 MODIFIED

| # | Original AI Suggestion | Modification Made | Reason |
|---|------------------------|-------------------|--------|
| M-001 | Use predefined templates per domain (Laptop, Hiring, etc.) | Changed to: templates stored in DB under Category/SubCategory hierarchy, user selects not hardcodes | Avoids hardcoded logic while keeping structured starting points. |
| M-002 | `weight = models.FloatField(default=1.0)` | Changed to `weight = models.IntegerField(default=40)` (percentage) | More intuitive for users entering 40%, 60% etc. instead of decimals. |
| M-003 | `is_positive = models.BooleanField(default=True)` as active engine logic | Retained in schema but removed from active inversion logic; all criteria rephrased positively | Boolean caused bugs; positive phrasing resolves the UX problem more cleanly. |
| M-004 | Simple `{% for option in options %}` loop inside JavaScript | Modified to use `json_script` filter + `JSON.parse()` | Removes editor errors, safer escaping, cleaner backend/frontend separation. |
| M-005 | 3-page flow: Decision Form → Questions → Result | Modified to include: Home page (decision history) + Login + Other category support | More complete product; matches real-world app UX. |
| M-006 | Call Gemini/OpenAI on every form submission | Modified to: call AI only on finalization | API tokens are limited; explanation should be generated once on "Finalize Decision" click. |
| M-007 | Comma-separated input for options | Used in CLI prototype; replaced with proper form fields in the Django web app | Better UX for a web interface. |
| M-008 | Score out of 5 summed directly | Changed to score out of 5 normalized with 100-point priority weights | Raw sum doesn't produce comparable results across sessions with different numbers of criteria. |

---

## 6. Architecture Evolution Summary

### Stage 1: Initial Idea
- AI-driven confidence-based system
- **Problem:** Black box, violates assignment requirement

### Stage 2: Priority-Only Lexicographic Model
- User ranks criteria by priority, best option wins on highest priority
- **Problem:** Too simple, doesn't handle trade-offs

### Stage 3: Hybrid Weighted Scoring (Adopted)
- Weighted scoring engine (deterministic)
- AI assists only with question generation
- **Improvement:** Explainable, deterministic, AI-safe

### Stage 4: Domain-Agnostic Template Engine
- Criteria as first-class data (not hardcoded)
- Domain tree: Category → SubCategory → Criteria identified from problem statement and AI suggestions
- Comma-separated input used for options in the CLI prototype
- **Improvement:** Extensible to any decision domain

### Stage 5: Full Django Web Application
- Django + MySQL
- 8-table normalized schema
- Gemini API (switched from OpenAI after quota ran out)
- Score out of 5 initially, then changed to 100-point priority weights with auto-normalization
- **Improvement:** Production-grade structure

### Stage 6: Advanced Scoring Features
- Percentage-based priorities (0–100 IntegerField, not FloatField)
- Positive criteria phrasing — replaced is_positive boolean inversion which was causing too many errors
- Dynamic runtime extra criteria (session-stored, not in DB, to avoid data bloat)
- Weight normalization
- **Improvement:** Mathematically stable, UX-friendly

### Stage 7: Complete Product
- Home page + Decision history
- Login system so each user has access to their own history
- "Other" custom category
- JavaScript dynamic criteria blocks
- AI explanation on finalize using Gemini
- API key properly loaded from .env using python-dotenv (after Bug 6 where uploading .env with files caused key removal)
- **Improvement:** Full end-to-end product experience

---

## 7. Key Technical Decisions Log

| Decision | Option Chosen | Option Rejected | Justification |
|----------|--------------|-----------------|---------------|
| Scoring algorithm | Weighted scoring (deterministic) | AI confidence model | Explainability requirement |
| Secondary ranking | Lexicographic priority check | None (single method) | Two-method validation adds confidence |
| AI role | Question generation + explanation only | AI-as-decision-maker | Assignment: "not black box" |
| Database | MySQL (relational) | NoSQL (MongoDB) | Strongly relational data model |
| Framework | Django (server-side templates) | Flask, FastAPI, Node | Admin panel + ORM + auth built-in |
| Frontend | Django templates + minimal JS | React, Vue, Handlebars | Assignment is backend-focused |
| Criteria storage | DB (Category/SubCategory/Criterion tables) | Hardcoded in Python | Extensibility, admin-manageable |
| Weight input | Percentage (0–100) | Decimal (0–1) | More intuitive for users |
| Negative criteria UX | Positive phrasing ("Cost Efficiency") | Boolean inversion (`is_positive`) | Boolean caused too many errors; positive phrasing is cleaner |
| Extra criteria | Session-stored runtime only | Always save to DB | Avoids polluting templates and causing database size increase |
| AI fallback | 5 generic evaluation questions | Hard fail on quota error | "System must work without AI" |
| AI provider | Gemini (Google) | OpenAI | OpenAI quota exhausted during CLI prototype stage |
| Data seeding | Shell script (`initial_data.py`) + `manage.py shell` | Fixtures / Management command | Simpler for development stage |

---

*This RESEARCH_LOG.md was compiled from all AI-assisted sessions conducted between 23 February and 08 March 2026, including: the full ChatGPT conversation (477 pages, 19,285 lines), Google Gemini AI sessions (02 March 2026), and OpenAI Codex debugging sessions (03 March 2026), all undertaken as part of the Decision Companion System project for Vonnue.*

*AI tools used: ChatGPT, Google Gemini AI, OpenAI Codex. All AI outputs were reviewed, evaluated, and selectively integrated — the final system reflects independent engineering judgment, not uncritical AI acceptance.*
