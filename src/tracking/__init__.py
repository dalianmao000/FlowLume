"""
User behavior tracking module.

Stores interaction logs, emotion signals, and context in SQLite
for analysis and agent decision-making.
"""

from src.tracking.user_behavior_tracker import UserBehaviorTracker

__all__ = ["UserBehaviorTracker"]