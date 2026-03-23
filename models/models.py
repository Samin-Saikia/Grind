from datetime import datetime
from typing import Optional
from flask_login import UserMixin
from extensions import db, bcrypt


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    bio = db.Column(db.String(300), default="")
    profile_pic_url = db.Column(db.String(500), default="")
    domain = db.Column(db.String(100), default="")
    domain_detail = db.Column(db.String(300), default="")
    xp = db.Column(db.Integer, default=0)
    streak = db.Column(db.Integer, default=0)
    level = db.Column(db.Integer, default=1)
    onboarded = db.Column(db.Boolean, default=False)
    user_model_json = db.Column(db.Text, default="{}")
    last_active = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    tasks = db.relationship("Task", backref="user", lazy=True, cascade="all, delete-orphan")
    xp_logs = db.relationship("XPLog", backref="user", lazy=True, cascade="all, delete-orphan")
    posts = db.relationship("Post", backref="user", lazy=True, cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    def level_from_xp(self):
        # Every 500 XP = 1 level
        return max(1, self.xp // 500 + 1)

    def xp_to_next_level(self):
        next_level_xp = self.level_from_xp() * 500
        return next_level_xp - self.xp

    def xp_progress_percent(self):
        current_level_start = (self.level_from_xp() - 1) * 500
        current_level_end = self.level_from_xp() * 500
        progress = self.xp - current_level_start
        total = current_level_end - current_level_start
        if total == 0:
            return 0
        return int((progress / total) * 100)

    def __repr__(self):
        return "<User {}>".format(self.username)


class Task(db.Model):
    __tablename__ = "tasks"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    domain = db.Column(db.String(100), default="")
    difficulty = db.Column(db.String(20), default="medium")  # easy / medium / hard
    xp_value = db.Column(db.Integer, default=100)
    time_estimate = db.Column(db.Integer, default=30)  # minutes
    status = db.Column(db.String(20), default="pending")  # pending / done / skipped / quit
    completion_note = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return "<Task {}>".format(self.title)


class XPLog(db.Model):
    __tablename__ = "xp_log"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    delta = db.Column(db.Integer, nullable=False)  # positive or negative
    reason = db.Column(db.String(200), nullable=False)
    task_id = db.Column(db.Integer, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return "<XPLog {} {}>".format(self.delta, self.reason)


class Post(db.Model):
    __tablename__ = "posts"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    content = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return "<Post {}>".format(self.id)


class InspireList(db.Model):
    __tablename__ = "inspire_list"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    target_user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Guild(db.Model):
    __tablename__ = "guilds"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.String(500), default="")
    domain = db.Column(db.String(100), default="")
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    xp_pool = db.Column(db.Integer, default=0)
    is_public = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    members = db.relationship("GuildMember", backref="guild", lazy=True, cascade="all, delete-orphan")


class GuildMember(db.Model):
    __tablename__ = "guild_members"

    id = db.Column(db.Integer, primary_key=True)
    guild_id = db.Column(db.Integer, db.ForeignKey("guilds.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    role = db.Column(db.String(20), default="member")  # admin / member
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)


class Challenge(db.Model):
    __tablename__ = "challenges"

    id = db.Column(db.Integer, primary_key=True)
    challenger_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    challenged_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    guild_id_a = db.Column(db.Integer, db.ForeignKey("guilds.id"), nullable=True)
    guild_id_b = db.Column(db.Integer, db.ForeignKey("guilds.id"), nullable=True)
    challenge_type = db.Column(db.String(20), default="1v1")  # 1v1 / guild
    start_time = db.Column(db.DateTime, nullable=True)
    end_time = db.Column(db.DateTime, nullable=True)
    winner_id = db.Column(db.Integer, nullable=True)
    status = db.Column(db.String(20), default="pending")  # pending / active / completed / declined
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
