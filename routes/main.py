import json
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from extensions import db
from models.models import Task, XPLog, User
from services.ai_service import generate_tasks, update_user_model
from services.xp_service import complete_task_xp, skip_task_xp, quit_task_xp, update_streak

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    return render_template("index.html")


@main_bp.route("/dashboard")
@login_required
def dashboard():
    pending_tasks = Task.query.filter_by(
        user_id=current_user.id, status="pending"
    ).order_by(Task.created_at.desc()).all()

    completed_today = Task.query.filter(
        Task.user_id == current_user.id,
        Task.status == "done",
        Task.completed_at >= datetime.utcnow().replace(hour=0, minute=0, second=0),
    ).count()

    recent_xp = XPLog.query.filter_by(user_id=current_user.id)\
        .order_by(XPLog.timestamp.desc()).limit(5).all()

    user_model = {}
    try:
        user_model = json.loads(current_user.user_model_json or "{}")
    except (ValueError, KeyError):
        pass

    return render_template(
        "dashboard.html",
        pending_tasks=pending_tasks,
        completed_today=completed_today,
        recent_xp=recent_xp,
        user_model=user_model,
    )


@main_bp.route("/tasks/complete/<int:task_id>", methods=["POST"])
@login_required
def complete_task(task_id):
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first_or_404()

    if task.status != "pending":
        flash("This task is already resolved.", "error")
        return redirect(url_for("main.dashboard"))

    note = request.form.get("note", "").strip()
    if not note:
        flash("Write a short completion note before marking done.", "error")
        return redirect(url_for("main.dashboard"))

    task.status = "done"
    task.completion_note = note
    task.completed_at = datetime.utcnow()

    xp, reason = complete_task_xp(current_user, task)
    streak_bonus = update_streak(current_user)

    db.session.commit()
    _maybe_refresh_tasks()

    msg = "+{} XP — {}".format(xp, reason)
    if streak_bonus:
        msg += " | Streak bonus!"
    flash(msg, "success")
    return redirect(url_for("main.dashboard"))


@main_bp.route("/tasks/skip/<int:task_id>", methods=["POST"])
@login_required
def skip_task(task_id):
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first_or_404()

    if task.status != "pending":
        flash("Task already resolved.", "error")
        return redirect(url_for("main.dashboard"))

    task.status = "skipped"
    task.completed_at = datetime.utcnow()
    xp, reason = skip_task_xp(current_user, task)
    db.session.commit()

    flash("{} XP — {}".format(xp, reason), "warning")
    return redirect(url_for("main.dashboard"))


@main_bp.route("/tasks/quit/<int:task_id>", methods=["POST"])
@login_required
def quit_task(task_id):
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first_or_404()

    if task.status != "pending":
        flash("Task already resolved.", "error")
        return redirect(url_for("main.dashboard"))

    task.status = "quit"
    task.completed_at = datetime.utcnow()
    xp, reason = quit_task_xp(current_user, task)
    db.session.commit()

    flash("{} XP — {}".format(xp, reason), "error")
    return redirect(url_for("main.dashboard"))


@main_bp.route("/tasks/generate", methods=["POST"])
@login_required
def generate_new_tasks():
    """Manually trigger new task generation."""
    pending_count = Task.query.filter_by(
        user_id=current_user.id, status="pending"
    ).count()

    if pending_count >= 3:
        flash("You still have {} pending tasks. Finish those first.".format(pending_count), "warning")
        return redirect(url_for("main.dashboard"))

    _generate_fresh_tasks()
    flash("New tasks generated based on your updated profile.", "success")
    return redirect(url_for("main.dashboard"))


def _maybe_refresh_tasks():
    """Auto-generate new tasks if user has fewer than 2 pending."""
    pending_count = Task.query.filter_by(
        user_id=current_user.id, status="pending"
    ).count()
    if pending_count < 2:
        _generate_fresh_tasks()


def _generate_fresh_tasks():
    """Generate new tasks using current user model, update model from history first."""
    # Pull last 10 tasks for context
    recent = Task.query.filter_by(user_id=current_user.id)\
        .order_by(Task.created_at.desc()).limit(10).all()

    history = [
        {"title": t.title, "status": t.status, "difficulty": t.difficulty}
        for t in recent
    ]

    try:
        user_model = json.loads(current_user.user_model_json or "{}")
    except (ValueError, KeyError):
        user_model = {}

    if history:
        user_model = update_user_model(current_user.domain, user_model, history)
        current_user.user_model_json = json.dumps(user_model)

    tasks_data = generate_tasks(current_user.domain, user_model)
    for t in tasks_data:
        task = Task(
            user_id=current_user.id,
            title=t.get("title", "Task"),
            description=t.get("description", ""),
            domain=current_user.domain,
            difficulty=t.get("difficulty", "medium"),
            xp_value=int(t.get("xp_value", 100)),
            time_estimate=int(t.get("time_estimate_minutes", 30)),
            status="pending",
        )
        db.session.add(task)

    db.session.commit()


@main_bp.route("/profile")
@login_required
def profile():
    all_tasks = Task.query.filter_by(user_id=current_user.id)\
        .order_by(Task.created_at.desc()).limit(20).all()
    xp_history = XPLog.query.filter_by(user_id=current_user.id)\
        .order_by(XPLog.timestamp.desc()).limit(20).all()

    stats = {
        "total_done": Task.query.filter_by(user_id=current_user.id, status="done").count(),
        "total_skipped": Task.query.filter_by(user_id=current_user.id, status="skipped").count(),
        "total_quit": Task.query.filter_by(user_id=current_user.id, status="quit").count(),
    }

    return render_template("profile.html", all_tasks=all_tasks, xp_history=xp_history, stats=stats)


@main_bp.route("/profile/edit", methods=["GET", "POST"])
@login_required
def edit_profile():
    if request.method == "POST":
        bio = request.form.get("bio", "").strip()[:300]
        current_user.bio = bio
        db.session.commit()
        flash("Profile updated.", "success")
        return redirect(url_for("main.profile"))
    return render_template("edit_profile.html")
