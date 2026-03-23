import json
import re
from typing import List, Dict, Optional
from groq import Groq
from config import config

client = Groq(api_key=config.GROQ_API_KEY)


DOMAINS = [
    "JEE / NEET preparation",
    "UPSC / government exams",
    "Competitive programming",
    "Web development",
    "Machine learning / AI",
    "Startup / entrepreneurship",
    "Fitness / athletics",
    "Language learning",
    "Creative writing",
    "Music / instrument",
    "Mathematics",
    "Other",
]


def _safe_json(text):
    # type: (str) -> Optional[dict]
    """Extract JSON from LLM response, handling markdown fences."""
    text = text.strip()
    # Remove ```json ... ``` or ``` ... ```
    text = re.sub(r"```(?:json)?", "", text).strip()
    text = text.rstrip("`").strip()
    try:
        return json.loads(text)
    except (ValueError, KeyError):
        # Try to find first { ... } block
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except (ValueError, KeyError):
                pass
    return None


def generate_onboarding_questions(domain, domain_detail):
    # type: (str, str) -> List[Dict]
    """Generate 5 targeted onboarding questions based on user domain."""
    prompt = """You are an intelligent productivity coach building a user profile.
The user has selected domain: {domain}
Additional detail they provided: {detail}

Generate exactly 5 short, specific questions to understand:
1. Their current level / experience
2. How much time per day they can commit
3. Their biggest weakness or blocker
4. Their specific goal or target
5. Their current routine or method

Return ONLY valid JSON, no extra text, no markdown:
{{"questions": [{{"id": 1, "question": "..."}}, {{"id": 2, "question": "..."}}, {{"id": 3, "question": "..."}}, {{"id": 4, "question": "..."}}, {{"id": 5, "question": "..."}}]}}""".format(
        domain=domain, detail=domain_detail or "not provided"
    )

    try:
        response = client.chat.completions.create(
            model=config.GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=600,
            temperature=0.7,
        )
        text = response.choices[0].message.content
        data = _safe_json(text)
        if data and "questions" in data:
            return data["questions"]
    except Exception as e:
        print("Groq onboarding questions error: {}".format(e))

    # Fallback generic questions
    return [
        {"id": 1, "question": "What is your current experience level in this domain? (beginner / intermediate / advanced)"},
        {"id": 2, "question": "How many hours per day can you dedicate to this?"},
        {"id": 3, "question": "What is your biggest weakness or challenge right now?"},
        {"id": 4, "question": "What is your main goal or target? (be specific)"},
        {"id": 5, "question": "Describe your current routine or study method briefly."},
    ]


def build_user_model(domain, domain_detail, questions, answers):
    # type: (str, str, List[Dict], List[str]) -> Dict
    """Build user model JSON from onboarding answers."""
    qa_pairs = "\n".join(
        "Q: {}\nA: {}".format(q["question"], a)
        for q, a in zip(questions, answers)
    )

    prompt = """You are a productivity AI building a user profile model.
Domain: {domain}
Detail: {detail}

Onboarding Q&A:
{qa}

Based on this, create a JSON user model with these exact fields:
- level_estimate: "beginner" / "intermediate" / "advanced"
- hours_per_day: number (float)
- weak_areas: list of strings (max 3)
- goals: list of strings (max 3)
- current_method: short string
- preferred_task_difficulty: "easy" / "medium" / "hard"
- recommended_task_types: list of strings (max 4, e.g. "solve problems", "build projects", "read and summarise", "write explanations")
- notes: short string about this user

Return ONLY valid JSON, no markdown, no extra text.""".format(
        domain=domain, detail=domain_detail, qa=qa_pairs
    )

    try:
        response = client.chat.completions.create(
            model=config.GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.5,
        )
        text = response.choices[0].message.content
        data = _safe_json(text)
        if data:
            return data
    except Exception as e:
        print("Groq build_user_model error: {}".format(e))

    return {
        "level_estimate": "beginner",
        "hours_per_day": 2,
        "weak_areas": ["unknown"],
        "goals": ["improve in {}".format(domain)],
        "current_method": "self study",
        "preferred_task_difficulty": "medium",
        "recommended_task_types": ["solve problems", "build projects"],
        "notes": "Profile built with fallback defaults.",
    }


def generate_tasks(domain, user_model):
    # type: (str, Dict) -> List[Dict]
    """Generate 3 micro-tasks for the user based on their model."""
    prompt = """You are a productivity task engine. Generate exactly 3 micro-tasks.

User domain: {domain}
User level: {level}
Weak areas: {weak}
Goals: {goals}
Preferred difficulty: {diff}
Recommended task types: {types}
Hours available per day: {hours}

Rules:
- Each task must be specific and actionable, not vague
- Each task must be completable in under 45 minutes
- Tasks should slightly challenge the user but not overwhelm them
- Make tasks progressive: task 1 = warmup, task 2 = core, task 3 = stretch
- The deliverable must be crystal clear (solve X, write Y, build Z, explain W)

Return ONLY valid JSON, no markdown:
{{"tasks": [{{"title": "...", "description": "...", "difficulty": "easy/medium/hard", "xp_value": 50-200, "time_estimate_minutes": 10-45}}, ...]}}""".format(
        domain=domain,
        level=user_model.get("level_estimate", "beginner"),
        weak=", ".join(user_model.get("weak_areas", [])),
        goals=", ".join(user_model.get("goals", [])),
        diff=user_model.get("preferred_task_difficulty", "medium"),
        types=", ".join(user_model.get("recommended_task_types", [])),
        hours=user_model.get("hours_per_day", 2),
    )

    try:
        response = client.chat.completions.create(
            model=config.GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=800,
            temperature=0.8,
        )
        text = response.choices[0].message.content
        data = _safe_json(text)
        if data and "tasks" in data:
            return data["tasks"]
    except Exception as e:
        print("Groq generate_tasks error: {}".format(e))

    return [
        {
            "title": "Define your goal clearly",
            "description": "Write a 5-sentence paragraph explaining exactly what you want to achieve in this domain and why it matters to you personally.",
            "difficulty": "easy",
            "xp_value": 50,
            "time_estimate_minutes": 15,
        },
        {
            "title": "Identify your top 3 weaknesses",
            "description": "List your top 3 weakest areas in this domain with a one-line explanation of why each feels hard.",
            "difficulty": "medium",
            "xp_value": 75,
            "time_estimate_minutes": 20,
        },
        {
            "title": "Complete one beginner exercise",
            "description": "Find and complete one beginner-level exercise or problem in your domain. Document your approach and result.",
            "difficulty": "medium",
            "xp_value": 100,
            "time_estimate_minutes": 30,
        },
    ]


def update_user_model(domain, current_model, task_history):
    # type: (str, Dict, List[Dict]) -> Dict
    """Update user model based on recent task performance."""
    history_text = "\n".join(
        "- Task: {} | Status: {} | Difficulty: {}".format(
            t.get("title", ""), t.get("status", ""), t.get("difficulty", "")
        )
        for t in task_history[-10:]  # last 10 tasks
    )

    done_count = sum(1 for t in task_history if t.get("status") == "done")
    skip_count = sum(1 for t in task_history if t.get("status") == "skipped")
    quit_count = sum(1 for t in task_history if t.get("status") == "quit")

    prompt = """You are updating a user's productivity profile based on their task history.

Domain: {domain}
Current model: {model}

Recent task history (last 10):
{history}

Summary: {done} completed, {skip} skipped, {quit} quit.

Update the user model JSON. Adjust:
- preferred_task_difficulty (up if completing well, down if quitting/skipping a lot)
- weak_areas (based on where they struggle)
- notes (short observation about their pattern)
- Keep all other fields, update only what makes sense

Return ONLY valid JSON of the full updated model, no markdown.""".format(
        domain=domain,
        model=json.dumps(current_model),
        history=history_text,
        done=done_count,
        skip=skip_count,
        quit=quit_count,
    )

    try:
        response = client.chat.completions.create(
            model=config.GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=500,
            temperature=0.4,
        )
        text = response.choices[0].message.content
        data = _safe_json(text)
        if data:
            return data
    except Exception as e:
        print("Groq update_user_model error: {}".format(e))

    return current_model
