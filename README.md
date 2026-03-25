# GRIND

**A personal intelligence engine that learns who you are — through behavior, not forms.**

GRIND is not a productivity app. It is a closed-loop AI system that builds a continuously evolving model of your mind: your knowledge, your gaps, your patterns, your avoidance behaviors, your peak performance hours. It does this silently, through the natural act of using it. The longer you use GRIND, the sharper it gets. Every session adds signal. Every completed task, every debrief answer, every skipped task — all of it feeds the model.

It runs entirely on your machine. No cloud. No accounts. No data leaving your computer except the API calls you make explicitly. One SQLite file. Yours.

---

## The Philosophy

Most productivity tools track what you *do*. GRIND tracks what you *understand*.

There's a critical difference. You can complete a task without actually learning anything. You can maintain a streak while coasting. You can log hours while going in circles. Standard tools reward the act of completion. GRIND rewards demonstrated understanding.

This is enforced through the debrief system. After every task, the AI asks you questions — not "did you finish?" but "explain it to me." Your answers are analyzed by the same AI that set the task. The depth of your response determines your XP multiplier. A brilliant answer on a hard task earns dramatically more than a shallow answer on an easy one. Over time, the system builds a body of *evidence* about what you actually know, not just what you've touched.

The algorithm uses this evidence to do three things:

1. **Calibrate future tasks** — harder if you're consistently deep, lighter if you're struggling or low-energy
2. **Build your profile** — strengths and weaknesses derived from demonstrated behavior, never self-report
3. **Map your knowledge graph** — a growing network of concepts you've encountered, weighted by evidence of mastery

---

## Features

### The Cold Start
The first time you open GRIND, there's no onboarding wizard. No "what are your goals?" form. No category selection. You're dropped into a conversation with the AI and it simply starts talking to you.

While it appears to just be curious, it's running a silent extraction protocol. After 6–8 exchanges, it has enough signal to write your first profile: your interests (inferred from what excites you), your vocabulary level (derived from how you write), your communication style (terse vs exploratory), your apparent strengths, your obvious gaps. This profile is committed to the database and becomes the seed from which everything else grows.

You never know exactly what it wrote about you. You can read it on the Profile page, but it was written from evidence, not from answers you volunteered.

### Adaptive Microtask Engine
Each session, GRIND generates exactly 4 tasks. Not more. The constraint is intentional — 4 high-quality, calibrated tasks you can complete in a focused 2–3 hour session are worth more than 20 generic ones.

Task generation is a two-step pipeline:

**Step 1 — Live research.** Before writing a single task, the system fires Serper API searches against your active domains. It looks for recent developments, common pitfalls, best current practices, and intermediate-to-advanced learning paths. This ensures your tasks are never stale — they reflect the current state of your field, not training data from 2 years ago.

**Step 2 — AI calibration.** The Groq AI receives your full profile, your domain levels, your recent performance data, and the live research context. It writes 4 tasks with specific types (learn, build, research, reflect), difficulty ratings (1–10), time limits (15, 30, or 45 minutes), and XP values. At least one task is designed to push you slightly beyond your comfort zone. At least one is immediately actionable.

The task descriptions are personal. The AI references what it knows about you — if it knows you prefer building over reading, the task will suggest a specific implementation challenge rather than "read the docs."

### Post-Task Debrief
Marking a task done does not complete it. The debrief does.

When you mark a task as done, the AI generates 3 questions specific to that exact task. Not generic comprehension questions — pointed, Socratic questions that expose whether you actually understood what you did.

A typical debrief:
- Q1: Direct knowledge check — "Walk me through what X actually does under the hood"
- Q2: Application — "How would you use this in a system that needs to handle Y constraint?"
- Q3: Edge case or limit — "What breaks this approach? Where does it fall apart?"

Your answers are evaluated by the AI, which produces a score (0–10), a brief piece of feedback (direct, not flattering), an XP multiplier (0.5× to 2.0×), and a list of concepts demonstrated and gaps revealed. Both lists feed the knowledge graph and the profile.

If you answer brilliantly, the feedback says so — once, specifically, without ceremony. If you answer shallowly, it calls that out too. The AI has no incentive to coddle you. It knows your history and it's keeping score.

### The Living Profile
The profile is never a form you fill out. It is a document the system maintains, updated after every session based on behavioral evidence.

It tracks:
- **Inferred interests** — what topics generate the longest, most detailed answers in chat and debriefs
- **Vocabulary level** — `beginner / intermediate / advanced / expert`, derived from how you write
- **Communication style** — terse, exploratory, detail-oriented, big-picture, etc.
- **Learning style** — how you approach new things (building first, reading first, asking first, etc.)
- **Demonstrated strengths** — things you've explained well under pressure
- **Identified weaknesses** — topics where debrief scores are consistently low, tasks you skip, questions you dodge
- **Domains** — the knowledge areas you're actively working in
- **Behavioral patterns** — average session length, time of day, skip rate, quality streak consistency
- **AI observations** — a running paragraph the AI maintains, updated after each session, about patterns it has noticed in your behavior

The AI observations field is the most interesting part. It's where the system writes things like: *"Shows strong intuition for system design problems but consistently avoids implementation questions. Answers are confident in theory, thin in specifics. This gap is narrowing."*

### GRIND Chat
The chat interface is not a generic chatbot. Every message the AI sends has your full profile in context. It knows your level, your history, your gaps, your current tasks.

When you ask it a question it thinks you should already know the answer to, it doesn't just answer. It asks you first. When you state something confidently that contradicts your debrief history, it pushes back. When you're clearly stalling or going in circles, it redirects.

The tone is that of a sharp mentor who has no interest in your comfort — only your growth. It respects you enough to be honest.

You can also trigger **Deep Dive mode** from the chat: enter any topic and the AI + Serper will produce a personalized briefing calibrated to your exact level and domain context. It covers what the thing actually is, why it matters for you specifically, how it works mechanically, what most people get wrong, and where to go deeper. Saved to your session.

### Knowledge Graph
Every concept encountered in tasks, debriefs, chat, and deep dives gets added as a node to your personal knowledge graph. Nodes that appear in multiple sessions grow brighter. Nodes where you demonstrated understanding (high debrief scores) develop higher mastery scores. Nodes that are frequently co-occurring in the same sessions get connected by edges.

The result, after weeks of use, is a genuine map of your mental territory — the concepts you've touched, the clusters you've built, the bridges between domains you've crossed, and the bright spots where you've demonstrated real mastery.

The graph is built entirely from evidence. No node is added because you said you know something. Nodes appear because the system encountered the concept in the context of your actual work.

The graph is interactive — force-directed, draggable, filterable by domain. Clicking a node shows its mastery score, evidence count, and connected concepts. You can trigger a deep dive on any node directly from the graph.

### XP and Domain Leveling
Each domain (Python, Machine Learning, Distributed Systems, History, whatever emerges from your usage) has its own level, starting at 1.

XP is not flat. The formula is:

```
XP earned = base_xp × debrief_multiplier
base_xp   = difficulty × 8
multiplier = 0.5 (shallow) → 2.0 (exceptional)
```

A difficulty-8 task answered brilliantly earns 128 XP. The same task answered shallowly earns 32 XP. A difficulty-3 task answered brilliantly earns 48 XP. The system rewards the combination of challenge and depth — not just showing up.

Leveling up within a domain (every 100 × level XP) is marked silently. No confetti. A milestone entry is created that says: *"Level 4 in Distributed Systems. The tasks are about to get harder."* They do.

### Quality Streaks
Two separate streaks run in parallel:

**Day streak** — Did you show up? Any session counts. This is the baseline.

**Quality streak** — Did you go deep? This increments only when your average debrief score for a session is 7.0 or above. Coasting sessions do not increment it. A session of 4 shallow completions resets it to zero.

The quality streak is the metric that actually matters. The AI references it in chat when relevant, particularly when it notices the day streak climbing while the quality streak stalls — that is exactly the coasting pattern it's designed to call out.

### Session Closing Hook
When all tasks in a session are resolved (done or skipped), the session closes and the AI generates a closing hook — a 2–3 sentence piece of text that dangles an unresolved thread.

It might reference something you said in the debrief that contradicted something earlier. It might mention a concept that came up today that connects to something from three weeks ago. It might pose a question it wants you to think about before the next session.

The hook is designed to create an open loop — the psychological pull of an unresolved question that makes the next session feel like a continuation, not a restart.

### Milestone Detection
After every debrief, the system compares your score against your historical scores for that domain. If your score represents a statistically significant improvement — particularly if you explain something well that you've struggled with before — a milestone is triggered.

The milestone text is generated by the AI, specific to the task and your history: *"Three weeks ago you couldn't explain why this matters. Today you explained the edge case before I asked about it. That's a real shift."*

Milestones appear as a brief toast notification. They are not gamified badges. They are the system noticing that something real changed.

### Weekly Intelligence Report
Every Sunday, GRIND generates a weekly report — a personal briefing from the AI written like a letter from a sharp coach who has been watching you all week.

The report covers:
- What you actually worked on
- How your profile shifted this week based on evidence
- What the AI now knows about you that it didn't last week
- An honest assessment of where you currently are vs where you want to be
- 3 specific recommendations for next week based on your gap map

The report is written in prose, not as a dashboard of statistics. It is designed to be read, not scanned. Exportable as markdown.

---

## Architecture

### System Overview

```
┌─────────────────────────────────────────────────────┐
│  Browser (localhost:5000)                           │
│  Vanilla HTML · DM Sans · Instrument Serif · Mono   │
│  Light/dark theme · No frameworks · No build step   │
└───────────────┬─────────────────────────────────────┘
                │ HTTP
┌───────────────▼─────────────────────────────────────┐
│  Flask Application (app.py)                         │
│  Application factory · Blueprint routing            │
│  Session management · API endpoints                 │
└──────┬────────────┬──────────────┬──────────────────┘
       │            │              │
┌──────▼──────┐ ┌───▼────────┐ ┌──▼──────────────────┐
│  services/  │ │  models/   │ │  routes/             │
│  ai.py      │ │  models.py │ │  main.py             │
│  serper.py  │ │  SQLite DB │ │  20+ API endpoints   │
│  profile.py │ │  8 tables  │ │                      │
└──────┬──────┘ └────────────┘ └──────────────────────┘
       │
┌──────▼────────────────────────────┐
│  External APIs                    │
│  Groq  → llama-3.3-70b-versatile  │
│  Serper → Google Search JSON API  │
└───────────────────────────────────┘
```

### Database Schema (SQLite — `grind.db`)

**Profile** — one row, always. The living model of you.
```
id · created_at · updated_at
inferred_interests  (JSON array)
communication_style (text)
vocabulary_level    (beginner|intermediate|advanced|expert)
learning_style      (text)
strengths           (JSON array)
weaknesses          (JSON array)
domains             (JSON array)
avg_session_minutes (float)
peak_hours          (JSON array)
skip_patterns       (JSON array)
ai_observations     (text — AI's running notes)
total_xp            (int)
global_level        (int)
day_streak          (int)
quality_streak      (int)
last_active_date    (string)
cold_start_complete (bool)
```

**Sessions** — one row per grind session.
```
id · created_at · ended_at · duration_minutes
xp_earned · quality_score · session_type
closing_hook · is_weekly_report
```

**Tasks** — 4 per session.
```
id · session_id · created_at · completed_at
title · description · task_type · difficulty · time_limit_minutes
status · xp_value · domain
debrief_questions (JSON) · debrief_answers (JSON)
debrief_score · ai_feedback
```

**Messages** — every chat exchange, stored with session.
```
id · session_id · created_at · role · content · message_type
```

**KnowledgeNode** — one per unique concept encountered.
```
id · concept (unique) · domain · first_seen · last_touched
evidence_count · mastery_score (0–1) · connections (JSON)
```

**DomainLevel** — one per domain discovered.
```
id · domain (unique) · level · xp · xp_to_next
tasks_completed · tasks_skipped · avg_difficulty
```

**Milestone** — breakthrough moments.
```
id · created_at · title · description · milestone_type · domain · seen
```

**WeeklyReport** — Sunday reports.
```
id · week_start · generated_at · content · xp_gained · tasks_completed · new_concepts
```

### AI Pipeline (`services/ai.py`)

Every function that calls Groq is structured the same way: build a rich context string from the profile, construct a prompt with specific output instructions, call the model, parse the result.

The model used is `llama-3.3-70b-versatile` — Groq's fastest high-quality model. At Groq's inference speed, typical response times are 0.5–2 seconds for most calls.

Key functions:
- `cold_start_response()` — conversational, profiling without revealing it
- `extract_profile_from_conversation()` — structured JSON extraction from chat history
- `generate_tasks()` — 4 calibrated tasks with full profile + live research context
- `generate_debrief_questions()` — 3 Socratic questions specific to the completed task
- `evaluate_debrief()` — scores answers, generates feedback, extracts concepts and gaps
- `chat_response()` — full profile in context, challenger personality
- `generate_closing_hook()` — open-loop session ending
- `deep_dive()` — personalized topic briefing with Serper research
- `detect_milestone()` — statistical comparison against historical scores
- `update_profile_observations()` — AI's running notes about behavioral patterns

### Research Pipeline (`services/serper.py`)

Before task generation, the system fires 2–3 Serper searches against your active domains. Queries are constructed programmatically based on your domain names and vocabulary level:

```
"latest {domain} techniques tools 2024"
"{domain} learning path intermediate to advanced"
```

Results are passed as context to the task generation prompt, giving the AI access to current information it wouldn't have from training data alone.

Deep dives use a similar pipeline — 3 targeted searches on the topic before the AI writes the briefing.

---

## Setup

### Prerequisites
- Python 3.9 or higher
- A [Groq API key](https://console.groq.com) — free tier available, generous limits
- A [Serper API key](https://serper.dev) — free tier: 2,500 searches/month (sufficient for heavy use)

### Installation

```bash
# 1. Extract and enter the directory
unzip grind.zip
cd grind

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate      # Mac / Linux
# venv\Scripts\activate       # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
```

Edit `.env`:
```bash
GROQ_API_KEY=gsk_your_key_here
SERPER_API_KEY=your_key_here
SECRET_KEY=any_long_random_string_here
```

```bash
# 5. Run
python app.py
```

Open **http://localhost:5000**

The SQLite database (`grind.db`) is created automatically on first run. No migrations, no setup commands.

### Dependencies

```
Flask==2.2.5           # Web framework
Flask-SQLAlchemy==3.0.5 # ORM layer
SQLAlchemy==2.0.21     # Database toolkit
groq==0.9.0            # Groq API client
requests==2.31.0       # HTTP for Serper
python-dotenv==1.0.0   # .env file loading
Werkzeug==2.2.3        # WSGI utilities
httpx==0.27.2          # Async HTTP (Groq dependency)
```

No frontend build step. No npm. No webpack. Pure HTML, CSS, and vanilla JavaScript served directly by Flask.

---

## Usage Guide

### First Session (Cold Start)
Open `localhost:5000` for the first time. You'll see the cold start screen — a brief explanation and a "Begin" button.

Click it. The AI opens a conversation. Just talk. It will ask you things. Answer naturally. Don't try to optimize your answers — the more authentic you are, the better the profile it builds.

After 6+ exchanges, it will extract your profile and redirect you to the dashboard. This happens automatically, without announcement.

From that point, every feature is unlocked.

### Daily Workflow
The intended rhythm is one session per day, 60–120 minutes.

1. Open GRIND at `localhost:5000`
2. Go to **Grind** → click **Generate session**
3. The AI researches your domains and generates 4 tasks (15–30 seconds)
4. Work through the tasks. Click **Start** to begin a task and start the timer
5. When done, click **Mark done + Debrief** — answer the 3 questions honestly
6. Your XP, profile, and knowledge graph update immediately after each debrief
7. When all tasks are resolved, the session closes with a closing hook

### Chat Usage
The chat is always available. Use it to:
- Ask questions in your domain (the AI knows your level — no over-explaining)
- Request a **Deep Dive** on any topic
- Get challenged on something you think you know
- Ask the AI what it thinks your biggest gap is right now

The AI has your full profile in every conversation. It will reference things from past sessions, push back on things that contradict your history, and adjust its explanation depth to your demonstrated level.

### Knowledge Graph Navigation
Go to **Graph** to see your knowledge map. Larger, brighter nodes = more evidence of mastery. Connected nodes = co-occurred in the same sessions.

Filter by domain using the dropdown. Click any node to see its mastery score and evidence count. From the node panel, click **Deep dive this** to trigger a full deep dive on that concept in the chat.

The graph becomes meaningful around session 5–8. Before that, it's sparse. After 30+ sessions, it's a genuine map of your intellectual territory.

### Exporting Your Data
Click **Export data** in the sidebar at any time, or go to `localhost:5000/api/export`.

The export is a structured JSON file containing:
- Your full profile (everything the AI knows about you)
- All domain levels and XP history
- Every session metadata record
- Every task with debrief scores and feedback
- Your complete knowledge graph (nodes and edges)

This file is yours. It can be imported into any tool that reads JSON, pasted into a notebook, or archived.

---

## Design System

### Theme: Deep Signal

Two modes, one identity.

**Dark mode** (default): Deep space navy backgrounds (`#0d0f1a` → `#272c48`) with electric violet accents (`#7c6dfa`). The navy is not pure black — it has a blue-purple undertone that makes the violet accent feel coherent, not arbitrary. Text is warm white (`#eeeaf8`), not cold. The overall feeling is a late-night research session in a tool designed for serious work.

**Light mode**: Warm ivory parchment backgrounds (`#f5f2eb` → `#fdfcf9`) with deep indigo accents (`#4f46e5`). The ivory has a slight warmth that prevents the clinical feel of pure white. The indigo is authoritative and calm. The feeling is a premium research journal — physical, deliberate, considered.

Both modes are designed to look intentional, not like "dark mode = black background + same colors."

### Typography

Three typefaces, each with a specific role:

**Instrument Serif** (display, italic) — Used for page titles, scores, and the cold start headline. The italic variant specifically. Serif italics in UI contexts signal that something is being *named* rather than *labeled* — a distinction that matters when the tool is about building intellectual identity.

**JetBrains Mono** (monospace) — Used for all data: XP values, level indicators, section labels, timestamps, API output. Monospace type makes data feel precise and honest. It also visually separates functional information from prose.

**DM Sans** (body, UI) — Used for all body text, buttons, descriptions, and chat messages. Clean, optical-size aware, reads well at 13–15px. Neutral without being anonymous.

### Color Encoding
Colors are not decorative — each carries semantic meaning:

- **Violet/indigo** — accent, primary actions, active states, XP
- **Blue** — `learn` task type
- **Green** — `build` task type, success states, high scores
- **Purple** — `research` task type
- **Pink** — `reflect` task type
- **Amber** — warnings, timer alerts, mid scores
- **Red** — errors, skip indicators, low scores

The knowledge graph uses domain-specific colors derived deterministically from the domain name (hash-based), ensuring the same domain always gets the same color across sessions.

---

## API Reference

All endpoints return JSON except `/api/export` (JSON file download).

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET`  | `/api/profile` | Full profile, domains, unseen milestones |
| `POST` | `/api/cold-start/chat` | Cold start conversation turn |
| `POST` | `/api/tasks/generate` | Generate new session + 4 tasks |
| `GET`  | `/api/tasks/current` | Current session tasks |
| `POST` | `/api/tasks/:id/start` | Begin a task (starts timer) |
| `POST` | `/api/tasks/:id/skip` | Skip a task |
| `POST` | `/api/tasks/:id/debrief/start` | Generate debrief questions |
| `POST` | `/api/tasks/:id/debrief/submit` | Submit answers, get evaluation |
| `POST` | `/api/chat` | Chat message (full profile context) |
| `POST` | `/api/deep-dive` | Deep dive on a topic |
| `POST` | `/api/session/:id/close` | Close session, generate hook |
| `GET`  | `/api/graph` | Knowledge graph nodes and edges |
| `POST` | `/api/milestones/seen` | Mark milestones as seen |
| `GET`  | `/api/export` | Full data export as JSON |

---

## Data & Privacy

**Your data never leaves your machine** except for the content you explicitly send to Groq and Serper via API calls.

What is sent to Groq:
- Your profile (ai_observations, strengths, weaknesses, interests, etc.)
- Task content and debrief answers
- Chat messages

What is sent to Serper:
- Search queries based on your domain names

What stays local:
- The SQLite database file (`grind.db`)
- All session history
- All XP and level data
- The knowledge graph

To delete all your data: delete `grind.db`. On next startup, GRIND starts from scratch.

---

## File Structure

```
grind/
├── app.py                  # Application factory, entry point
├── config.py               # Environment config, API keys
├── extensions.py           # SQLAlchemy instance
├── requirements.txt        # Python dependencies
├── .env.example            # Environment template
├── .gitignore
│
├── models/
│   └── models.py           # All 8 SQLAlchemy models
│
├── routes/
│   └── main.py             # All Flask routes and API endpoints
│
├── services/
│   ├── ai.py               # All Groq API calls and prompt engineering
│   ├── serper.py           # Serper search API integration
│   └── profile.py          # Profile update logic, XP, knowledge graph
│
├── static/
│   ├── css/
│   │   └── main.css        # Complete design system, light + dark
│   └── js/
│       └── app.js          # Shared utilities, profile loader, theme
│
└── templates/
    ├── base.html           # Sidebar, theme toggle, milestone toast
    ├── cold_start.html     # First session, standalone page
    ├── dashboard.html      # Stats, observations, deep dive
    ├── grind.html          # Task engine, timer, debrief overlays
    ├── chat.html           # Full chat interface
    ├── graph.html          # D3 knowledge graph
    └── profile.html        # Profile page, radar chart
```

---

## Roadmap

These features are designed and ready to be built when needed:

**Near term**
- Weekly report auto-generation (Sunday cron via APScheduler)
- Session quality score visualization over time
- Gap map — visual "you are here → you want to be there" per domain
- Mood/energy inference from response latency and session patterns

**Medium term**
- Spaced repetition — the system surfaces concepts from your graph that are fading (low recent evidence) and builds review tasks around them
- Custom domains — manually seed a domain with a goal statement; the AI uses this as a calibration anchor
- Deep dive library — searchable archive of all deep dives you've triggered
- Task history with filter and search

**Long term**
- Local model support — run against Ollama/local LLMs for fully air-gapped operation
- Import from notes — paste your Obsidian notes, the system extracts concepts and seeds the knowledge graph
- Time-series analysis — visualize how your skill radar has shifted month over month

---

## Acknowledgements

Built on:
- [Flask](https://flask.palletsprojects.com/) — lightweight, predictable, stays out of the way
- [Groq](https://groq.com/) — inference fast enough to feel like thinking
- [Serper](https://serper.dev/) — clean Google Search API
- [D3.js](https://d3js.org/) — knowledge graph visualization
- [Instrument Serif](https://fonts.google.com/specimen/Instrument+Serif), [JetBrains Mono](https://www.jetbrains.com/lp/mono/), [DM Sans](https://fonts.google.com/specimen/DM+Sans) — the typefaces that make the thing feel like itself

---

*GRIND is a personal tool. It is designed for one user. It has no multi-user support, no authentication beyond a session secret, and no intention of becoming a SaaS product. It is yours.*