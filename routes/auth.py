import json
import os
from flask import Blueprint, render_template, redirect, url_for, request, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from extensions import db
from models.models import User, Task
from services.ai_service import (
    generate_onboarding_questions,
    build_user_model,
    generate_tasks,
    DOMAINS,
)

auth_bp = Blueprint("auth", __name__)

# ── Access control config ─────────────────────────────────────────────────────
# Set INVITE_CODE in Render env vars to require a code on registration.
# Set MAX_USERS to cap total registrations (0 = unlimited).
INVITE_CODE = os.environ.get("INVITE_CODE", "")          # e.g. "grind2025"
MAX_USERS   = int(os.environ.get("MAX_USERS", "10"))      # default: cap at 10


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    # Hard user cap check
    if MAX_USERS > 0 and User.query.count() >= MAX_USERS:
        return render_template("auth/closed.html", reason="cap")

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")
        invite  = request.form.get("invite_code", "").strip()

        # Invite code check (only enforced if INVITE_CODE is set)
        if INVITE_CODE and invite != INVITE_CODE:
            flash("Invalid invite code.", "error")
            return render_template("auth/register.html", require_invite=bool(INVITE_CODE))

        if not username or not email or not password:
            flash("All fields are required.", "error")
            return render_template("auth/register.html", require_invite=bool(INVITE_CODE))

        if len(username) < 3 or len(username) > 30:
            flash("Username must be 3-30 characters.", "error")
            return render_template("auth/register.html", require_invite=bool(INVITE_CODE))

        if password != confirm:
            flash("Passwords do not match.", "error")
            return render_template("auth/register.html", require_invite=bool(INVITE_CODE))

        if len(password) < 6:
            flash("Password must be at least 6 characters.", "error")
            return render_template("auth/register.html", require_invite=bool(INVITE_CODE))

        if User.query.filter_by(email=email).first():
            flash("Email already registered.", "error")
            return render_template("auth/register.html", require_invite=bool(INVITE_CODE))

        if User.query.filter_by(username=username).first():
            flash("Username already taken.", "error")
            return render_template("auth/register.html", require_invite=bool(INVITE_CODE))

        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        login_user(user)
        flash("Account created. Now let's set you up.", "success")
        return redirect(url_for("auth.onboarding_domain"))

    return render_template("auth/register.html", require_invite=bool(INVITE_CODE))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        remember = request.form.get("remember") == "on"

        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            flash("Invalid email or password.", "error")
            return render_template("auth/login.html")

        login_user(user, remember=remember)

        if not user.onboarded:
            return redirect(url_for("auth.onboarding_domain"))

        return redirect(url_for("main.dashboard"))

    return render_template("auth/login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("main.index"))


# ── Onboarding Step 1: Domain selection ──────────────────────────────────────

@auth_bp.route("/onboarding/domain", methods=["GET", "POST"])
@login_required
def onboarding_domain():
    if current_user.onboarded:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        domain = request.form.get("domain", "").strip()
        domain_detail = request.form.get("domain_detail", "").strip()

        if not domain:
            flash("Please select a domain.", "error")
            return render_template("auth/onboarding_domain.html", domains=DOMAINS)

        current_user.domain = domain
        current_user.domain_detail = domain_detail
        db.session.commit()

        # Generate questions via Groq and store in session
        questions = generate_onboarding_questions(domain, domain_detail)
        session["onboarding_questions"] = questions

        return redirect(url_for("auth.onboarding_questions"))

    return render_template("auth/onboarding_domain.html", domains=DOMAINS)


# ── Onboarding Step 2: Answer AI questions ───────────────────────────────────

@auth_bp.route("/onboarding/questions", methods=["GET", "POST"])
@login_required
def onboarding_questions():
    if current_user.onboarded:
        return redirect(url_for("main.dashboard"))

    questions = session.get("onboarding_questions")
    if not questions:
        return redirect(url_for("auth.onboarding_domain"))

    if request.method == "POST":
        answers = []
        for q in questions:
            answer = request.form.get("answer_{}".format(q["id"]), "").strip()
            answers.append(answer if answer else "Not provided")

        # Build user model from answers
        user_model = build_user_model(
            current_user.domain,
            current_user.domain_detail,
            questions,
            answers,
        )
        current_user.user_model_json = json.dumps(user_model)

        # Generate first batch of tasks
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

        current_user.onboarded = True
        db.session.commit()
        session.pop("onboarding_questions", None)

        flash("Your first tasks are ready. Start grinding.", "success")
        return redirect(url_for("main.dashboard"))

    return render_template("auth/onboarding_questions.html", questions=questions)
