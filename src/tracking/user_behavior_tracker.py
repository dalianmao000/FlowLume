import sqlite3
import json
from datetime import datetime
from typing import Optional, List, Dict
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class LearningEvent:
    """学习事件"""
    event_id: str
    user_id: str
    event_type: str  # "start", "complete", "quiz", "question", "emotion_detected"
    module_id: str
    timestamp: str
    metadata: Optional[dict] = None

    def to_dict(self) -> dict:
        return asdict(self)


class UserBehaviorTracker:
    """用户行为追踪器"""

    def __init__(self, db_path: str = "data/adoption.db"):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self):
        """初始化数据库表"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS learning_events (
                    event_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    module_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    metadata TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_user_id ON learning_events(user_id)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_module_id ON learning_events(module_id)
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS user_progress (
                    user_id TEXT PRIMARY KEY,
                    role TEXT,
                    skill_level TEXT,
                    adoption_score REAL DEFAULT 0.0,
                    last_activity TEXT,
                    modules_completed TEXT DEFAULT '[]',
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def record_learning_event(self, event: LearningEvent) -> None:
        """记录学习事件"""
        with sqlite3.connect(self.db_path) as conn:
            try:
                conn.execute(
                    """
                    INSERT INTO learning_events
                    (event_id, user_id, event_type, module_id, timestamp, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        event.event_id,
                        event.user_id,
                        event.event_type,
                        event.module_id,
                        event.timestamp,
                        json.dumps(event.metadata) if event.metadata else None,
                    )
                )
                # 更新用户进度
                self._update_user_progress(conn, event)
                conn.commit()
            except Exception:
                conn.rollback()
                raise

    def _update_user_progress(self, conn: sqlite3.Connection, event: LearningEvent):
        """更新用户进度"""
        # 获取当前进度
        cursor = conn.execute(
            "SELECT modules_completed, adoption_score, role, skill_level FROM user_progress WHERE user_id = ?",
            (event.user_id,)
        )
        row = cursor.fetchone()

        modules_completed = []
        adoption_score = 0.0
        role = None
        skill_level = None

        if row:
            modules_completed = json.loads(row[0]) if row[0] else []
            adoption_score = row[1]
            role = row[2]
            skill_level = row[3]

        # 更新进度
        if event.event_type == "complete":
            if event.module_id not in modules_completed:
                modules_completed.append(event.module_id)
            # 每完成一个模块加 20 分
            adoption_score = min(100.0, adoption_score + 20.0)

        if row:
            conn.execute("""
                UPDATE user_progress
                SET last_activity = ?, modules_completed = ?, adoption_score = ?, updated_at = ?
                WHERE user_id = ?
            """, (
                event.timestamp,
                json.dumps(modules_completed),
                adoption_score,
                datetime.now().isoformat(),
                event.user_id
            ))
        else:
            conn.execute("""
                INSERT INTO user_progress
                (user_id, role, skill_level, last_activity, modules_completed, adoption_score, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                event.user_id,
                role,
                skill_level,
                event.timestamp,
                json.dumps(modules_completed),
                adoption_score,
                datetime.now().isoformat()
            ))

    def get_adoption_score(self, user_id: str) -> float:
        """获取用户 adoption 分数"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT adoption_score FROM user_progress WHERE user_id = ?",
                (user_id,)
            )
            row = cursor.fetchone()
            return row[0] if row else 0.0

    def get_user_progress(self, user_id: str) -> dict:
        """获取用户完整进度"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT * FROM user_progress WHERE user_id = ?",
                (user_id,)
            )
            row = cursor.fetchone()
            if not row:
                return {}

            columns = [desc[0] for desc in conn.execute("SELECT * FROM user_progress LIMIT 0").description]
            return dict(zip(columns, row))

    def get_events_by_user(self, user_id: str, limit: int = 100) -> List[LearningEvent]:
        """获取用户所有事件"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT event_id, user_id, event_type, module_id, timestamp, metadata FROM learning_events WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?",
                (user_id, limit)
            )
            events = []
            for row in cursor.fetchall():
                data = {
                    "event_id": row[0],
                    "user_id": row[1],
                    "event_type": row[2],
                    "module_id": row[3],
                    "timestamp": row[4],
                    "metadata": json.loads(row[5]) if row[5] else None
                }
                events.append(LearningEvent(**data))
            return events

    def generate_heat_map_data(self, org_unit: str = "all") -> dict:
        """生成 adoption 热力图数据"""
        with sqlite3.connect(self.db_path) as conn:
            # 按模块统计完成率
            cursor = conn.execute("""
                SELECT module_id, COUNT(DISTINCT user_id) as completed_count
                FROM learning_events
                WHERE event_type = 'complete'
                GROUP BY module_id
            """)
            module_stats = [{"module": row[0], "count": row[1]} for row in cursor.fetchall()]

            # 用户分布
            cursor = conn.execute("""
                SELECT
                    CASE
                        WHEN adoption_score >= 80 THEN 'expert'
                        WHEN adoption_score >= 60 THEN 'proficient'
                        WHEN adoption_score >= 40 THEN 'learning'
                        ELSE 'beginner'
                    END as level,
                    COUNT(*) as count
                FROM user_progress
                GROUP BY level
            """)
            level_dist = [{"level": row[0], "count": row[1]} for row in cursor.fetchall()]

            return {
                "module_stats": module_stats,
                "level_distribution": level_dist,
                "total_users": sum(item["count"] for item in level_dist)
            }

    def export_report(self, format: str = "csv") -> str:
        """导出 adoption 报告"""
        import csv
        import io

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM user_progress")
            columns = [desc[0] for desc in cursor.description]

            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=columns)
            writer.writeheader()

            for row in cursor.fetchall():
                writer.writerow(dict(zip(columns, row)))

            return output.getvalue()