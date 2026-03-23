from datetime import datetime
from typing import Tuple
from extensions import db
from models.models import User, XPLog


XP_COMPLETE_MIN = 50
XP_COMPLETE_MAX = 200
XP_SKIP_PENALTY = -20
XP_QUIT_PENALTY = -50
XP_STREAK_BONUS = 100
XP_WIN_CHALLENGE = 500
XP_HELP_SOCIAL = 10

DIFFICULTY_MULTIPLIER = {
    "easy": 0.6,
    "medium": 1.0,
    "hard": 1.5,
}


def award_xp(user, delta, reason, task_id=None):
    # type: (User, int, str, int) -> None
    """Add or subtract XP from user and log it."""
    user.xp = max(0, user.xp + delta)
    user.level = user.level_from_xp()

    log = XPLog(
        user_id=user.id,
        delta=delta,
        reason=reason,
        task_id=task_id,
        timestamp=datetime.utcnow(),
    )
    db.session.add(log)


def complete_task_xp(user, task):
    # type: (User, object) -> Tuple[int, str]
    """Calculate and award XP for completing a task."""
    multiplier = DIFFICULTY_MULTIPLIER.get(task.difficulty, 1.0)
    xp = int(task.xp_value * multiplier)
    reason = "Completed: {}".format(task.title[:60])
    award_xp(user, xp, reason, task_id=task.id)
    return xp, reason


def skip_task_xp(user, task):
    # type: (User, object) -> Tuple[int, str]
    """Penalise XP for skipping a task."""
    reason = "Skipped: {}".format(task.title[:60])
    award_xp(user, XP_SKIP_PENALTY, reason, task_id=task.id)
    return XP_SKIP_PENALTY, reason


def quit_task_xp(user, task):
    # type: (User, object) -> Tuple[int, str]
    """Penalise XP for quitting a task."""
    reason = "Quit: {}".format(task.title[:60])
    award_xp(user, XP_QUIT_PENALTY, reason, task_id=task.id)
    return XP_QUIT_PENALTY, reason


def update_streak(user):
    # type: (User) -> bool
    """Update streak and award bonus if milestone hit. Returns True if streak bonus awarded."""
    user.streak += 1
    user.last_active = datetime.utcnow()
    if user.streak % 7 == 0:
        reason = "{}-day streak bonus!".format(user.streak)
        award_xp(user, XP_STREAK_BONUS, reason)
        return True
    return False
