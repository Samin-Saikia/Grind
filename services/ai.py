import json
import re
from groq import Groq
from config import config

client = Groq(api_key=config.GROQ_API_KEY)
MODEL = "llama-3.3-70b-versatile"


def _chat(messages, temperature=0.7, max_tokens=2048):
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content


def _extract_json(text):
    match = re.search(r'\{.*\}', text, re.DOTALL)
    if match:
        try: return json.loads(match.group())
        except: pass
    match = re.search(r'\[.*\]', text, re.DOTALL)
    if match:
        try: return json.loads(match.group())
        except: pass
    return None


def build_profile_context(profile):
    if not profile:
        return "No profile yet. This is a new user."
    p = profile.to_dict()
    return f"""USER PROFILE (AI-inferred, never user-filled):
- Interests: {', '.join(p['interests']) if p['interests'] else 'still discovering'}
- Communication style: {p['communication_style'] or 'unknown'}
- Vocabulary level: {p['vocabulary_level']}
- Learning style: {p['learning_style'] or 'unknown'}
- Strengths: {', '.join(p['strengths']) if p['strengths'] else 'none detected yet'}
- Weaknesses: {', '.join(p['weaknesses']) if p['weaknesses'] else 'none detected yet'}
- Domains active: {', '.join(p['domains']) if p['domains'] else 'none yet'}
- Avg session: {p['avg_session_minutes']:.0f} mins
- AI observations: {p['ai_observations'] or 'none yet'}
- XP: {p['total_xp']} | Level: {p['global_level']}
- Day streak: {p['day_streak']} | Quality streak: {p['quality_streak']}"""


def cold_start_response(history, profile_context):
    system = f"""You are GRIND — a personal intelligence engine. This is the user's very first conversation with you.

Your hidden mission: learn everything about this person through natural conversation. You are building their profile silently while appearing to just chat.

Discover:
1. What they care about, what excites them
2. How they think and communicate
3. Their vocabulary and knowledge level
4. Their goals, frustrations, energy
5. How they approach problems

Rules:
- NEVER mention that you're profiling them
- Be genuinely curious, warm but sharp
- Ask ONE question at a time, naturally
- React to what they say before asking more
- After 6-8 exchanges, start weaving in a subtle challenge to test their depth
- Keep responses under 120 words. Be punchy, not verbose.
- You have a slight edge to you — you're not a therapist, you're a sparring partner

{profile_context}"""

    messages = [{"role": "system", "content": system}] + history
    return _chat(messages, temperature=0.8)


def extract_profile_from_conversation(history):
    convo_text = "\n".join([f"{m['role'].upper()}: {m['content']}" for m in history])
    prompt = f"""Analyze this conversation and extract a profile of the user. Return ONLY valid JSON, no other text.

Conversation:
{convo_text}

Return this exact JSON structure:
{{
  "interests": ["list of inferred interests"],
  "communication_style": "brief description",
  "vocabulary_level": "beginner|intermediate|advanced|expert",
  "learning_style": "brief description",
  "strengths": ["list of apparent strengths"],
  "weaknesses": ["list of apparent weaknesses or gaps"],
  "domains": ["list of knowledge domains mentioned or implied"],
  "ai_observations": "2-3 sentences of sharp observations about this person"
}}"""

    result = _chat([{"role": "user", "content": prompt}], temperature=0.3, max_tokens=800)
    data = _extract_json(result)
    return data or {}


def generate_tasks(profile, domain_levels, serper_context=""):
    profile_ctx = build_profile_context(profile)
    domains_str = json.dumps([{"domain": d.domain, "level": d.level, "avg_difficulty": d.avg_difficulty} for d in domain_levels]) if domain_levels else "[]"

    prompt = f"""You are GRIND's task engine. Generate exactly 4 microtasks for this user's next session.

{profile_ctx}

Domain levels: {domains_str}

Recent research context:
{serper_context or 'No live research available'}

Rules for tasks:
- Each task must be calibrated to the user's level in that domain (harder if they're advanced, easier to rebuild momentum if they've been struggling)
- Task types: learn, build, research, reflect
- Time limits: 15, 30, or 45 minutes
- Difficulty: 1-10 (must be honest, not flattering)
- XP: difficulty × 8 for a solid completion
- At least one task should push them slightly outside comfort
- At least one task should be immediately actionable (not just "read about X")
- The description should feel personal, referencing what you know about them

Return ONLY this JSON:
{{
  "tasks": [
    {{
      "title": "short punchy title",
      "description": "2-3 sentences, specific and personal",
      "task_type": "learn|build|research|reflect",
      "difficulty": 1-10,
      "time_limit_minutes": 15|30|45,
      "domain": "domain name",
      "xp_value": number
    }}
  ]
}}"""

    result = _chat([{"role": "user", "content": prompt}], temperature=0.7, max_tokens=1200)
    data = _extract_json(result)
    return data.get("tasks", []) if data else []


def generate_debrief_questions(task):
    prompt = f"""Generate 3 sharp debrief questions for this completed task. These test actual understanding, not just "did you do it."

Task: {task.title}
Description: {task.description}
Type: {task.task_type}
Difficulty: {task.difficulty}/10

Rules:
- Question 1: Direct knowledge check (explain X, how does Y work)
- Question 2: Application (how would you use this in Z situation)
- Question 3: Edge case or challenge (what breaks this, what's the hardest part)
- Questions should be specific to THIS task, not generic
- Be Socratic, not multiple choice

Return ONLY JSON:
{{"questions": ["q1", "q2", "q3"]}}"""

    result = _chat([{"role": "user", "content": prompt}], temperature=0.6, max_tokens=400)
    data = _extract_json(result)
    return data.get("questions", ["What did you learn?", "How would you apply this?", "What confused you?"]) if data else ["What did you learn?", "How would you apply this?", "What confused you?"]


def evaluate_debrief(task, questions, answers, profile):
    profile_ctx = build_profile_context(profile)
    qa_pairs = "\n".join([f"Q: {q}\nA: {a}" for q, a in zip(questions, answers)])

    prompt = f"""Evaluate this task debrief. You are harsh but fair — you reward genuine understanding, not word count.

{profile_ctx}

Task: {task.title} (difficulty {task.difficulty}/10)
{qa_pairs}

Return ONLY JSON:
{{
  "score": 0-10,
  "feedback": "2-3 sentences. Be direct. Call out gaps. Acknowledge genuine insight. Reference their specific answers.",
  "xp_multiplier": 0.5-2.0,
  "new_strengths": ["any new strengths revealed"],
  "new_weaknesses": ["any gaps revealed"],
  "new_concepts": ["concepts demonstrated or encountered"]
}}"""

    result = _chat([{"role": "user", "content": prompt}], temperature=0.4, max_tokens=600)
    data = _extract_json(result)
    return data or {"score": 5, "feedback": "Noted.", "xp_multiplier": 1.0, "new_strengths": [], "new_weaknesses": [], "new_concepts": []}


def chat_response(history, profile, current_tasks=None):
    profile_ctx = build_profile_context(profile)
    tasks_ctx = ""
    if current_tasks:
        tasks_ctx = f"\nCurrent tasks: {json.dumps([{'title': t.title, 'status': t.status} for t in current_tasks])}"

    system = f"""You are GRIND — a personal AI intelligence engine. You know this user deeply.

{profile_ctx}
{tasks_ctx}

Your personality:
- Sharp, direct, no filler words
- You challenge the user when they're wrong or vague
- You ask follow-up questions that expose gaps
- If they ask something you think they should already know, test them first before answering
- You remember everything from their profile and reference it naturally
- You're invested in their growth, not their comfort
- Responses are concise: 80-150 words max unless explaining something complex
- Occasionally reference their current streak or level when relevant
- End responses with a hook, question, or challenge when appropriate"""

    messages = [{"role": "system", "content": system}] + history
    return _chat(messages, temperature=0.75)


def generate_closing_hook(session_summary, profile):
    profile_ctx = build_profile_context(profile)
    prompt = f"""Generate a closing hook for this session — one unresolved thread that will pull the user back tomorrow.

{profile_ctx}
Session summary: {session_summary}

Rules:
- 2-3 sentences max
- Reference something specific from today's session
- Leave a question or discovery dangling — don't resolve it
- Make them feel like stopping now means missing something
- Tone: intriguing, not manipulative

Return plain text only, no JSON."""

    return _chat([{"role": "user", "content": prompt}], temperature=0.8, max_tokens=200)


def generate_weekly_report(profile, sessions_data, tasks_data):
    profile_ctx = build_profile_context(profile)
    prompt = f"""Write a weekly intelligence report for this user. This is their personal coach speaking.

{profile_ctx}

This week's data:
- Sessions: {sessions_data}
- Tasks completed: {tasks_data}

Format as markdown. Include:
## This week
Brief narrative of what happened

## What I now know about you
2-3 new observations from this week's behavior

## Where you actually are
Honest assessment of current level vs stated goals

## The gap
What stands between you and where you want to be

## Next week
3 specific recommendations

Tone: like a smart friend who won't bullshit you. Max 400 words."""

    return _chat([{"role": "user", "content": prompt}], temperature=0.7, max_tokens=800)


def detect_milestone(profile, task, debrief_score, historical_scores):
    if not historical_scores or len(historical_scores) < 3:
        return None

    avg_historical = sum(historical_scores[:-1]) / len(historical_scores[:-1])
    if debrief_score >= 8.5 and avg_historical < 6.5:
        prompt = f"""The user just had a breakthrough debrief score ({debrief_score}/10, up from avg {avg_historical:.1f}).

Task: {task.title}
Domain: {task.domain}

Write a 2-sentence milestone acknowledgment. Be specific. Reference the actual task. Don't be generic or over-celebratory — be quietly impressed.

Return plain text only."""
        text = _chat([{"role": "user", "content": prompt}], temperature=0.6, max_tokens=150)
        return text
    return None


def update_profile_observations(profile, new_data):
    prompt = f"""Update this user's AI observations based on new data. Be a sharp observer.

Current observations: {profile.ai_observations or 'none yet'}

New data points:
{json.dumps(new_data)}

Write 2-4 sentences of updated observations. Be specific. Notice patterns. Call out contradictions between their stated goals and their behavior if any. Don't repeat what's already noted.

Return plain text only."""

    return _chat([{"role": "user", "content": prompt}], temperature=0.5, max_tokens=300)


def deep_dive(topic, profile, serper_context=""):
    profile_ctx = build_profile_context(profile)
    prompt = f"""Do a deep dive on this topic for the user, calibrated to their exact level.

{profile_ctx}

Topic: {topic}

Live research context:
{serper_context or 'Using training knowledge only'}

Format as markdown:
## {topic}

### What it actually is
Clear, level-appropriate explanation

### Why it matters (for you specifically)
Connect to their domains and goals

### The core mechanics
How it works, not just what it is

### What most people get wrong
The non-obvious parts

### Where to go deep
3-5 specific resources, papers, or next steps calibrated to their level

### The open question
One unresolved or debated aspect to think about

Tone: like a brilliant friend explaining, not a textbook. Max 600 words."""

    return _chat([{"role": "user", "content": prompt}], temperature=0.7, max_tokens=1500)
