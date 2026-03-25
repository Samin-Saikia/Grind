from extensions import db
from datetime import datetime
import json

class Profile(db.Model):
    __tablename__ = "profile"
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    # Core identity (AI-inferred, never user-filled)
    inferred_interests = db.Column(db.Text, default="[]")
    communication_style = db.Column(db.Text, default="")
    vocabulary_level = db.Column(db.String(20), default="unknown")
    learning_style = db.Column(db.Text, default="")
    # Strengths and gaps (JSON arrays)
    strengths = db.Column(db.Text, default="[]")
    weaknesses = db.Column(db.Text, default="[]")
    domains = db.Column(db.Text, default="[]")
    # Behavioral patterns
    avg_session_minutes = db.Column(db.Float, default=0)
    peak_hours = db.Column(db.Text, default="[]")
    skip_patterns = db.Column(db.Text, default="[]")
    # AI's running notes on you
    ai_observations = db.Column(db.Text, default="")
    # Total XP and level
    total_xp = db.Column(db.Integer, default=0)
    global_level = db.Column(db.Integer, default=1)
    # Streaks
    day_streak = db.Column(db.Integer, default=0)
    quality_streak = db.Column(db.Integer, default=0)
    last_active_date = db.Column(db.String(20), default="")
    # Cold start done?
    cold_start_complete = db.Column(db.Boolean, default=False)

    def get_interests(self):
        try: return json.loads(self.inferred_interests)
        except: return []

    def get_strengths(self):
        try: return json.loads(self.strengths)
        except: return []

    def get_weaknesses(self):
        try: return json.loads(self.weaknesses)
        except: return []

    def get_domains(self):
        try: return json.loads(self.domains)
        except: return []

    def to_dict(self):
        return {
            "interests": self.get_interests(),
            "communication_style": self.communication_style,
            "vocabulary_level": self.vocabulary_level,
            "learning_style": self.learning_style,
            "strengths": self.get_strengths(),
            "weaknesses": self.get_weaknesses(),
            "domains": self.get_domains(),
            "avg_session_minutes": self.avg_session_minutes,
            "peak_hours": json.loads(self.peak_hours) if self.peak_hours else [],
            "skip_patterns": json.loads(self.skip_patterns) if self.skip_patterns else [],
            "ai_observations": self.ai_observations,
            "total_xp": self.total_xp,
            "global_level": self.global_level,
            "day_streak": self.day_streak,
            "quality_streak": self.quality_streak,
        }


class Session(db.Model):
    __tablename__ = "sessions"
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    ended_at = db.Column(db.DateTime, nullable=True)
    duration_minutes = db.Column(db.Float, default=0)
    xp_earned = db.Column(db.Integer, default=0)
    quality_score = db.Column(db.Float, default=0)  # 0-10
    session_type = db.Column(db.String(30), default="normal")  # cold_start, normal, deep_dive
    tasks = db.relationship("Task", backref="session", lazy=True)
    messages = db.relationship("Message", backref="session", lazy=True)
    # AI's end-of-session hook (the open loop)
    closing_hook = db.Column(db.Text, default="")
    # Weekly report flag
    is_weekly_report = db.Column(db.Boolean, default=False)


class Task(db.Model):
    __tablename__ = "tasks"
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey("sessions.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default="")
    task_type = db.Column(db.String(20), default="learn")  # learn, build, research, reflect
    difficulty = db.Column(db.Integer, default=5)  # 1-10
    time_limit_minutes = db.Column(db.Integer, default=30)
    status = db.Column(db.String(20), default="pending")  # pending, in_progress, done, skipped
    xp_value = db.Column(db.Integer, default=10)
    # Domain this task belongs to
    domain = db.Column(db.String(100), default="")
    # Debrief
    debrief_questions = db.Column(db.Text, default="[]")
    debrief_answers = db.Column(db.Text, default="[]")
    debrief_score = db.Column(db.Float, default=0)  # 0-10, AI evaluated
    ai_feedback = db.Column(db.Text, default="")

    def get_debrief_questions(self):
        try: return json.loads(self.debrief_questions)
        except: return []


class Message(db.Model):
    __tablename__ = "messages"
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey("sessions.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    role = db.Column(db.String(10), nullable=False)  # user / assistant
    content = db.Column(db.Text, nullable=False)
    message_type = db.Column(db.String(30), default="chat")  # chat, cold_start, debrief, challenge


class KnowledgeNode(db.Model):
    __tablename__ = "knowledge_nodes"
    id = db.Column(db.Integer, primary_key=True)
    concept = db.Column(db.String(200), unique=True, nullable=False)
    domain = db.Column(db.String(100), default="")
    first_seen = db.Column(db.DateTime, default=datetime.utcnow)
    last_touched = db.Column(db.DateTime, default=datetime.utcnow)
    evidence_count = db.Column(db.Integer, default=1)
    mastery_score = db.Column(db.Float, default=0.1)  # 0-1
    connections = db.Column(db.Text, default="[]")  # list of concept names

    def get_connections(self):
        try: return json.loads(self.connections)
        except: return []


class DomainLevel(db.Model):
    __tablename__ = "domain_levels"
    id = db.Column(db.Integer, primary_key=True)
    domain = db.Column(db.String(100), unique=True, nullable=False)
    level = db.Column(db.Integer, default=1)
    xp = db.Column(db.Integer, default=0)
    xp_to_next = db.Column(db.Integer, default=100)
    tasks_completed = db.Column(db.Integer, default=0)
    tasks_skipped = db.Column(db.Integer, default=0)
    avg_difficulty = db.Column(db.Float, default=5.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Milestone(db.Model):
    __tablename__ = "milestones"
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default="")
    milestone_type = db.Column(db.String(30), default="breakthrough")
    domain = db.Column(db.String(100), default="")
    seen = db.Column(db.Boolean, default=False)


class WeeklyReport(db.Model):
    __tablename__ = "weekly_reports"
    id = db.Column(db.Integer, primary_key=True)
    week_start = db.Column(db.String(20), nullable=False)
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)
    content = db.Column(db.Text, default="")
    xp_gained = db.Column(db.Integer, default=0)
    tasks_completed = db.Column(db.Integer, default=0)
    new_concepts = db.Column(db.Integer, default=0)
