from flask import Blueprint, render_template, jsonify, request, session
from extensions import db
from models.models import Session as GrindSession, Task, Message, Milestone, WeeklyReport, KnowledgeNode
from services.profile import get_or_create_profile, update_streak, get_knowledge_graph_data
from services import ai as ai_service
from services import serper as serper_service
import json
from datetime import datetime

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    profile = get_or_create_profile()
    update_streak(profile)
    if not profile.cold_start_complete:
        return render_template("cold_start.html")
    return render_template("dashboard.html")


@main_bp.route("/dashboard")
def dashboard():
    profile = get_or_create_profile()
    if not profile.cold_start_complete:
        return render_template("cold_start.html")
    return render_template("dashboard.html")


@main_bp.route("/grind")
def grind():
    profile = get_or_create_profile()
    if not profile.cold_start_complete:
        return render_template("cold_start.html")
    return render_template("grind.html")


@main_bp.route("/chat")
def chat():
    profile = get_or_create_profile()
    if not profile.cold_start_complete:
        return render_template("cold_start.html")
    return render_template("chat.html")


@main_bp.route("/graph")
def graph():
    profile = get_or_create_profile()
    if not profile.cold_start_complete:
        return render_template("cold_start.html")
    return render_template("graph.html")


@main_bp.route("/profile")
def profile_page():
    return render_template("profile.html")


# ── API: Profile ──────────────────────────────────────────
@main_bp.route("/api/profile")
def api_profile():
    profile = get_or_create_profile()
    from models.models import DomainLevel
    domains = DomainLevel.query.all()
    milestones = Milestone.query.filter_by(seen=False).order_by(Milestone.created_at.desc()).limit(5).all()
    return jsonify({
        "profile": profile.to_dict(),
        "cold_start_complete": profile.cold_start_complete,
        "domains": [{"domain": d.domain, "level": d.level, "xp": d.xp, "xp_to_next": d.xp_to_next, "tasks_completed": d.tasks_completed} for d in domains],
        "milestones": [{"id": m.id, "title": m.title, "description": m.description, "type": m.milestone_type, "domain": m.domain} for m in milestones],
    })


@main_bp.route("/api/milestones/seen", methods=["POST"])
def mark_milestones_seen():
    Milestone.query.filter_by(seen=False).update({"seen": True})
    db.session.commit()
    return jsonify({"ok": True})


# ── API: Cold Start ───────────────────────────────────────
@main_bp.route("/api/cold-start/chat", methods=["POST"])
def cold_start_chat():
    data = request.json
    user_msg = data.get("message", "").strip()
    history = data.get("history", [])

    profile = get_or_create_profile()
    profile_ctx = ai_service.build_profile_context(profile)

    history.append({"role": "user", "content": user_msg})
    reply = ai_service.cold_start_response(history, profile_ctx)
    history.append({"role": "assistant", "content": reply})

    # After 8+ exchanges, extract and save profile
    user_turns = sum(1 for m in history if m["role"] == "user")
    complete = False
    if user_turns >= 6:
        extracted = ai_service.extract_profile_from_conversation(history)
        from services.profile import merge_profile_from_cold_start
        merge_profile_from_cold_start(profile, extracted)
        complete = True
        # Save cold start as a session
        gs = GrindSession(session_type="cold_start")
        db.session.add(gs)
        db.session.commit()
        for m in history:
            msg = Message(session_id=gs.id, role=m["role"], content=m["content"], message_type="cold_start")
            db.session.add(msg)
        db.session.commit()

    return jsonify({"reply": reply, "complete": complete, "turns": user_turns})


# ── API: Tasks ────────────────────────────────────────────
@main_bp.route("/api/tasks/generate", methods=["POST"])
def generate_tasks():
    profile = get_or_create_profile()
    from models.models import DomainLevel
    domain_levels = DomainLevel.query.all()

    # Live research
    domains = profile.get_domains()
    serper_ctx = serper_service.research_for_tasks(domains, profile.communication_style)

    tasks_data = ai_service.generate_tasks(profile, domain_levels, serper_ctx)

    # Create a new session
    gs = GrindSession(session_type="normal")
    db.session.add(gs)
    db.session.commit()

    created_tasks = []
    for t in tasks_data:
        task = Task(
            session_id=gs.id,
            title=t.get("title", "Task"),
            description=t.get("description", ""),
            task_type=t.get("task_type", "learn"),
            difficulty=t.get("difficulty", 5),
            time_limit_minutes=t.get("time_limit_minutes", 30),
            domain=t.get("domain", "general"),
            xp_value=t.get("xp_value", 40),
        )
        db.session.add(task)
        db.session.flush()
        created_tasks.append({
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "task_type": task.task_type,
            "difficulty": task.difficulty,
            "time_limit_minutes": task.time_limit_minutes,
            "domain": task.domain,
            "xp_value": task.xp_value,
            "status": task.status,
        })
    db.session.commit()
    return jsonify({"session_id": gs.id, "tasks": created_tasks})


@main_bp.route("/api/tasks/current")
def current_tasks():
    gs = GrindSession.query.filter_by(session_type="normal").order_by(GrindSession.created_at.desc()).first()
    if not gs:
        return jsonify({"tasks": [], "session_id": None})
    tasks = Task.query.filter_by(session_id=gs.id).all()
    return jsonify({
        "session_id": gs.id,
        "tasks": [{
            "id": t.id, "title": t.title, "description": t.description,
            "task_type": t.task_type, "difficulty": t.difficulty,
            "time_limit_minutes": t.time_limit_minutes, "domain": t.domain,
            "xp_value": t.xp_value, "status": t.status,
            "debrief_questions": t.get_debrief_questions(),
            "ai_feedback": t.ai_feedback,
        } for t in tasks]
    })


@main_bp.route("/api/tasks/<int:task_id>/start", methods=["POST"])
def start_task(task_id):
    task = Task.query.get_or_404(task_id)
    task.status = "in_progress"
    db.session.commit()
    return jsonify({"ok": True})


@main_bp.route("/api/tasks/<int:task_id>/skip", methods=["POST"])
def skip_task(task_id):
    task = Task.query.get_or_404(task_id)
    task.status = "skipped"
    db.session.commit()
    return jsonify({"ok": True})


@main_bp.route("/api/tasks/<int:task_id>/debrief/start", methods=["POST"])
def start_debrief(task_id):
    task = Task.query.get_or_404(task_id)
    if not task.get_debrief_questions():
        questions = ai_service.generate_debrief_questions(task)
        task.debrief_questions = json.dumps(questions)
        db.session.commit()
    return jsonify({"questions": task.get_debrief_questions()})


@main_bp.route("/api/tasks/<int:task_id>/debrief/submit", methods=["POST"])
def submit_debrief(task_id):
    task = Task.query.get_or_404(task_id)
    data = request.json
    answers = data.get("answers", [])
    questions = task.get_debrief_questions()

    profile = get_or_create_profile()
    eval_data = ai_service.evaluate_debrief(task, questions, answers, profile)

    score = eval_data.get("score", 5)
    multiplier = eval_data.get("xp_multiplier", 1.0)
    xp_earned = int(task.xp_value * multiplier)

    task.debrief_answers = json.dumps(answers)
    task.debrief_score = score
    task.ai_feedback = eval_data.get("feedback", "")
    task.status = "done"
    task.completed_at = datetime.utcnow()
    db.session.commit()

    from services.profile import apply_debrief_results, add_xp, ensure_domain
    ensure_domain(task.domain)
    apply_debrief_results(profile, task, eval_data)
    add_xp(profile, task.domain, xp_earned)

    # Check for milestone
    from models.models import Task as TaskModel
    historical = [t.debrief_score for t in TaskModel.query.filter(
        TaskModel.domain == task.domain,
        TaskModel.debrief_score > 0
    ).order_by(TaskModel.completed_at).all()]

    milestone_text = ai_service.detect_milestone(profile, task, score, historical)
    if milestone_text:
        m = Milestone(title="Breakthrough", description=milestone_text, domain=task.domain)
        db.session.add(m)
        db.session.commit()

    # Quality streak update
    if score >= 7:
        profile.quality_streak += 1
    else:
        profile.quality_streak = 0
    db.session.commit()

    return jsonify({
        "score": score,
        "feedback": eval_data.get("feedback", ""),
        "xp_earned": xp_earned,
        "milestone": milestone_text,
        "new_strengths": eval_data.get("new_strengths", []),
        "new_weaknesses": eval_data.get("new_weaknesses", []),
    })


# ── API: Chat ─────────────────────────────────────────────
@main_bp.route("/api/chat", methods=["POST"])
def api_chat():
    data = request.json
    user_msg = data.get("message", "").strip()
    history = data.get("history", [])

    profile = get_or_create_profile()
    gs = GrindSession.query.filter_by(session_type="normal").order_by(GrindSession.created_at.desc()).first()
    current_tasks = Task.query.filter_by(session_id=gs.id).all() if gs else []

    history.append({"role": "user", "content": user_msg})
    reply = ai_service.chat_response(history, profile, current_tasks)

    if gs:
        db.session.add(Message(session_id=gs.id, role="user", content=user_msg, message_type="chat"))
        db.session.add(Message(session_id=gs.id, role="assistant", content=reply, message_type="chat"))
        db.session.commit()

    return jsonify({"reply": reply})


# ── API: Deep Dive ────────────────────────────────────────
@main_bp.route("/api/deep-dive", methods=["POST"])
def deep_dive():
    data = request.json
    topic = data.get("topic", "").strip()
    if not topic:
        return jsonify({"error": "No topic provided"}), 400

    profile = get_or_create_profile()
    serper_ctx = serper_service.research_topic(topic, profile.vocabulary_level)
    result = ai_service.deep_dive(topic, profile, serper_ctx)
    return jsonify({"content": result, "topic": topic})


# ── API: Session close ────────────────────────────────────
@main_bp.route("/api/session/<int:session_id>/close", methods=["POST"])
def close_session(session_id):
    gs = GrindSession.query.get_or_404(session_id)
    profile = get_or_create_profile()
    tasks = Task.query.filter_by(session_id=session_id).all()
    summary = f"Completed {sum(1 for t in tasks if t.status=='done')}/{len(tasks)} tasks"
    hook = ai_service.generate_closing_hook(summary, profile)
    gs.closing_hook = hook
    gs.ended_at = datetime.utcnow()
    db.session.commit()
    return jsonify({"hook": hook})


# ── API: Knowledge Graph ──────────────────────────────────
@main_bp.route("/api/graph")
def api_graph():
    return jsonify(get_knowledge_graph_data())


# ── API: Export ───────────────────────────────────────────
@main_bp.route("/api/export")
def export_data():
    profile = get_or_create_profile()
    from models.models import DomainLevel
    domains = DomainLevel.query.all()
    sessions = GrindSession.query.all()
    tasks = Task.query.all()
    nodes = KnowledgeNode.query.all()

    export = {
        "profile": profile.to_dict(),
        "domains": [{"domain": d.domain, "level": d.level, "xp": d.xp, "tasks_completed": d.tasks_completed} for d in domains],
        "sessions": [{"id": s.id, "type": s.session_type, "created_at": str(s.created_at), "xp_earned": s.xp_earned} for s in sessions],
        "tasks": [{"title": t.title, "domain": t.domain, "status": t.status, "score": t.debrief_score, "feedback": t.ai_feedback} for t in tasks],
        "knowledge_nodes": [{"concept": n.concept, "domain": n.domain, "mastery": n.mastery_score, "evidence": n.evidence_count} for n in nodes],
    }
    from flask import Response
    import json
    return Response(
        json.dumps(export, indent=2),
        mimetype="application/json",
        headers={"Content-Disposition": "attachment; filename=grind_export.json"}
    )
