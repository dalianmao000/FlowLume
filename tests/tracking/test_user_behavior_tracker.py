import pytest
import os
import tempfile
from src.tracking.user_behavior_tracker import UserBehaviorTracker, LearningEvent
from datetime import datetime


class TestUserBehaviorTracker:
    """UserBehaviorTracker 单元测试"""

    @pytest.fixture
    def temp_db(self):
        """临时数据库 fixture"""
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        yield path
        if os.path.exists(path):
            os.unlink(path)

    @pytest.fixture
    def tracker(self, temp_db):
        """Tracker instance with temp DB"""
        return UserBehaviorTracker(db_path=temp_db)

    def test_init_creates_tables(self, tracker):
        """测试数据库初始化"""
        import sqlite3
        with sqlite3.connect(tracker.db_path) as conn:
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            tables = [row[0] for row in cursor.fetchall()]
            assert "learning_events" in tables
            assert "user_progress" in tables

    def test_record_learning_event(self, tracker):
        """测试记录学习事件"""
        event = LearningEvent(
            event_id="test-001",
            user_id="user-001",
            event_type="start",
            module_id="mes_basic",
            timestamp=datetime.now().isoformat(),
            metadata={"source": "test"}
        )
        tracker.record_learning_event(event)

        # 验证事件已记录
        events = tracker.get_events_by_user("user-001")
        assert len(events) == 1
        assert events[0].event_id == "test-001"

    def test_adoption_score_on_completion(self, tracker):
        """测试完成模块后 adoption 分数增加"""
        # 记录一个完成事件
        event = LearningEvent(
            event_id="test-002",
            user_id="user-002",
            event_type="complete",
            module_id="mes_basic",
            timestamp=datetime.now().isoformat()
        )
        tracker.record_learning_event(event)

        score = tracker.get_adoption_score("user-002")
        assert score == 20.0  # 完成一个模块得 20 分

    def test_adoption_score_max_100(self, tracker):
        """测试 adoption 分数上限 100"""
        # 完成 6 个模块（应该达到 120，但上限 100）
        for i in range(6):
            event = LearningEvent(
                event_id=f"test-max-{i}",
                user_id="user-max",
                event_type="complete",
                module_id=f"module_{i}",
                timestamp=datetime.now().isoformat()
            )
            tracker.record_learning_event(event)

        score = tracker.get_adoption_score("user-max")
        assert score == 100.0  # 不超过 100

    def test_get_user_progress(self, tracker):
        """测试获取用户进度"""
        event = LearningEvent(
            event_id="test-003",
            user_id="user-003",
            event_type="complete",
            module_id="sap_basic",
            timestamp=datetime.now().isoformat()
        )
        tracker.record_learning_event(event)

        progress = tracker.get_user_progress("user-003")
        assert progress["user_id"] == "user-003"
        assert progress["adoption_score"] == 20.0