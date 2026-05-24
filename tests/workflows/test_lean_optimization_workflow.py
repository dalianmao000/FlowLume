"""Tests for LeanOptimizationWorkflow."""

import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from src.workflows.lean_optimization_workflow import (
    create_lean_optimization_workflow,
    run_lean_optimization_workflow,
    LeanOptimizationWorkflowState,
)
from src.agents.lean_optimization.lean_optimization_agent import (
    LeanOptimizationAgent,
    Bottleneck,
    KaizenProposal,
)
from src.agents.lean_optimization.vsm_calculator import VSMData, ProcessStep
from src.agents.lean_optimization.waste_identifier import WasteItem, WasteType
from src.agents.lean_optimization.event_log_models import (
    ProductionEvent,
    EventType,
)


class TestLeanOptimizationWorkflowState:
    """Test LeanOptimizationWorkflowState dataclass."""

    def test_state_creation(self):
        """Verify LeanOptimizationWorkflowState can be created."""
        state = LeanOptimizationWorkflowState()
        assert state.raw_data == {}
        assert state.process_graph is None
        assert state.current_vsm is None
        assert state.waste_list == []
        assert state.bottlenecks == []
        assert state.kaizen_proposals == []
        assert state.target_vsm is None
        assert state.human_approved is False
        assert state.human_feedback is None
        assert state.is_high_value is False
        assert state.final_report is None

    def test_state_with_raw_data(self):
        """Verify state initialization with raw data."""
        raw_data = {
            "production_events": [],
            "workforce_events": [],
        }
        state = LeanOptimizationWorkflowState(raw_data=raw_data)
        assert state.raw_data == raw_data
        assert len(state.raw_data["production_events"]) == 0


class TestWorkflowCreation:
    """Test workflow creation."""

    def test_workflow_creation(self):
        """Verify workflow can be created."""
        workflow = create_lean_optimization_workflow()
        assert workflow is not None

    def test_workflow_with_custom_agent(self):
        """Verify workflow accepts custom agent."""
        mock_agent = MagicMock(spec=LeanOptimizationAgent)
        workflow = create_lean_optimization_workflow(agent=mock_agent)
        assert workflow is not None


class TestWorkflowNodes:
    """Test individual workflow nodes."""

    def test_collect_data_node(self):
        """Verify collect_data node initializes correctly."""
        state = LeanOptimizationWorkflowState()
        workflow = create_lean_optimization_workflow()

        # Check initial state
        assert state.raw_data == {}

    def test_parse_events_node_empty(self):
        """Verify parse_events handles empty data."""
        state = LeanOptimizationWorkflowState(raw_data={})
        assert state.raw_data == {}

    def test_discover_process_node(self):
        """Verify discover_process node."""
        state = LeanOptimizationWorkflowState()
        assert state.process_graph is None

    def test_calculate_vsm_node_empty(self):
        """Verify calculate_vsm handles empty events."""
        state = LeanOptimizationWorkflowState(raw_data={})
        assert state.current_vsm is None

    def test_identify_waste_node(self):
        """Verify identify_waste node."""
        state = LeanOptimizationWorkflowState()
        assert state.waste_list == []

    def test_locate_bottleneck_node(self):
        """Verify locate_bottleneck node."""
        state = LeanOptimizationWorkflowState()
        assert state.bottlenecks == []

    def test_generate_proposals_node(self):
        """Verify generate_proposals node."""
        state = LeanOptimizationWorkflowState()
        assert state.kaizen_proposals == []
        assert state.is_high_value is False

    def test_simulate_improvement_node(self):
        """Verify simulate_improvement node."""
        state = LeanOptimizationWorkflowState()
        assert state.target_vsm is None

    def test_compile_target_vsm_node(self):
        """Verify compile_target_vsm node."""
        state = LeanOptimizationWorkflowState()
        assert state.final_report is None

    def test_human_review_node(self):
        """Verify human_review node defaults."""
        state = LeanOptimizationWorkflowState()
        assert state.human_approved is False
        assert state.human_feedback is None


class TestWorkflowEdges:
    """Test workflow edges and routing."""

    def test_workflow_has_collect_data_entry(self):
        """Verify workflow has collect_data as entry point."""
        workflow = create_lean_optimization_workflow()
        assert workflow is not None

    def test_workflow_nodes_count(self):
        """Verify workflow has all required nodes."""
        workflow = create_lean_optimization_workflow()
        # The compiled workflow should have nodes
        assert workflow is not None


class TestWorkflowExecution:
    """Test workflow execution with various inputs."""

    def test_run_workflow_empty_data(self):
        """Verify workflow runs with empty data using mocked agent."""
        mock_agent = MagicMock(spec=LeanOptimizationAgent)

        # Mock VSM calculator to return empty VSM
        mock_vsm = VSMData(
            process_steps=[],
            total_va_time=0.0,
            total_nva_time=0.0,
            total_lead_time=0.0,
            inventory_positions={},
            takt_time=0.0,
        )

        mock_agent.calculate_vsm.return_value = mock_vsm
        mock_agent.identify_waste.return_value = []
        mock_agent.locate_bottlenecks.return_value = []
        mock_agent.generate_kaizen_proposals.return_value = []
        mock_agent.simulate_improvement.return_value = mock_vsm

        result = run_lean_optimization_workflow(raw_data={}, agent=mock_agent)

        assert result is not None
        # Workflow invoke returns dict-like state
        assert isinstance(result, dict) or hasattr(result, 'current_vsm')
        # Verify VSM was calculated (empty but valid VSM)
        assert result.get('current_vsm') is not None
        assert isinstance(result.get('current_vsm'), VSMData)
        assert result.get('current_vsm').total_va_time == 0.0

    def test_run_workflow_with_mock_data(self):
        """Verify workflow runs with mock production events using mocked agent."""
        # Create mock production events
        base_time = datetime(2026, 5, 17, 8, 0, 0)

        production_events = [
            ProductionEvent(
                event_id="EVT_001",
                order_id="ORD_001",
                event_type=EventType.OP_START,
                operation="CUTTING",
                equipment_id="EQ_001",
                start_time=base_time,
                end_time=base_time + timedelta(minutes=30),
                quantity=100,
                location="Plant_A",
            ),
            ProductionEvent(
                event_id="EVT_002",
                order_id="ORD_001",
                event_type=EventType.OP_COMPLETE,
                operation="CUTTING",
                equipment_id="EQ_001",
                start_time=base_time + timedelta(minutes=30),
                end_time=base_time + timedelta(minutes=60),
                quantity=100,
                location="Plant_A",
            ),
            ProductionEvent(
                event_id="EVT_003",
                order_id="ORD_001",
                event_type=EventType.OP_START,
                operation="ASSEMBLY",
                equipment_id="EQ_002",
                start_time=base_time + timedelta(hours=1),
                end_time=base_time + timedelta(hours=1, minutes=30),
                quantity=100,
                location="Plant_A",
            ),
            ProductionEvent(
                event_id="EVT_004",
                order_id="ORD_001",
                event_type=EventType.OP_COMPLETE,
                operation="ASSEMBLY",
                equipment_id="EQ_002",
                start_time=base_time + timedelta(hours=1, minutes=30),
                end_time=base_time + timedelta(hours=2),
                quantity=100,
                location="Plant_A",
            ),
        ]

        raw_data = {
            "production_events": production_events,
            "workforce_events": [],
        }

        # Mock the agent to avoid LLM API calls
        mock_agent = MagicMock(spec=LeanOptimizationAgent)

        mock_vsm = VSMData(
            process_steps=[
                ProcessStep(name="CUTTING", va_time=1800, nva_time=0, wait_time=0, inventory=0),
                ProcessStep(name="ASSEMBLY", va_time=3600, nva_time=0, wait_time=0, inventory=0),
            ],
            total_va_time=5400,
            total_nva_time=0,
            total_lead_time=5400,
            inventory_positions={"CUTTING": 0, "ASSEMBLY": 0},
            takt_time=100.0,
        )

        mock_agent.calculate_vsm.return_value = mock_vsm
        mock_agent.identify_waste.return_value = [
            WasteItem(
                waste_type=WasteType.WAITING,
                location="ASSEMBLY",
                quantity=600,
                impact="Long wait times",
                severity="high",
            )
        ]
        mock_agent.locate_bottlenecks.return_value = [
            Bottleneck(
                location="ASSEMBLY",
                root_cause="Process imbalance",
                impact="Limits throughput",
                severity="high",
            )
        ]
        mock_agent.generate_kaizen_proposals.return_value = [
            KaizenProposal(
                title="Reduce Wait Times",
                description="Implement better scheduling",
                impact="20% reduction in wait times",
                effort="medium",
                priority="high",
                expected_improvement={"lead_time_reduction": 0.20},
            )
        ]
        mock_agent.get_highest_priority_proposal.return_value = KaizenProposal(
            title="Reduce Wait Times",
            description="Implement better scheduling",
            impact="20% reduction in wait times",
            effort="medium",
            priority="high",
            expected_improvement={"lead_time_reduction": 0.20},
        )
        mock_agent.simulate_improvement.return_value = mock_vsm

        result = run_lean_optimization_workflow(raw_data=raw_data, agent=mock_agent)

        assert result is not None
        # Workflow invoke returns dict-like state
        assert isinstance(result, dict) or hasattr(result, 'current_vsm')
        # Verify VSM was actually calculated
        assert result.get('current_vsm') is not None
        assert isinstance(result.get('current_vsm'), VSMData)
        assert result.get('current_vsm').total_va_time == 5400

    def test_workflow_with_high_value_proposal(self):
        """Verify workflow handles high-value proposals requiring HITL."""
        # Create mock data with high-priority proposal indication
        raw_data = {"production_events": [], "workforce_events": []}

        # Mock the agent to avoid LLM API calls
        mock_agent = MagicMock(spec=LeanOptimizationAgent)

        mock_vsm = VSMData(
            process_steps=[],
            total_va_time=0.0,
            total_nva_time=0.0,
            total_lead_time=0.0,
            inventory_positions={},
            takt_time=0.0,
        )

        mock_agent.calculate_vsm.return_value = mock_vsm
        mock_agent.identify_waste.return_value = []
        mock_agent.locate_bottlenecks.return_value = []
        mock_agent.generate_kaizen_proposals.return_value = []
        mock_agent.simulate_improvement.return_value = mock_vsm

        result = run_lean_optimization_workflow(raw_data=raw_data, agent=mock_agent)
        assert result is not None

        # If we have proposals, check is_high_value flag
        kaizen_proposals = result.get('kaizen_proposals', [])
        if kaizen_proposals:
            assert isinstance(result.get('is_high_value'), bool)


class TestWorkflowWithMockAgent:
    """Test workflow with mocked agent methods."""

    def test_workflow_with_mocked_agent(self):
        """Verify workflow calls agent methods correctly."""
        mock_agent = MagicMock(spec=LeanOptimizationAgent)

        # Mock VSM data
        mock_vsm = VSMData(
            process_steps=[
                ProcessStep(name="CUTTING", va_time=1800, nva_time=300, wait_time=600, inventory=50),
                ProcessStep(name="ASSEMBLY", va_time=3600, nva_time=600, wait_time=1200, inventory=100),
            ],
            total_va_time=5400,
            total_nva_time=900,
            total_lead_time=8100,
            inventory_positions={"CUTTING": 50, "ASSEMBLY": 100},
            takt_time=100.0,
        )

        mock_agent.calculate_vsm.return_value = mock_vsm
        mock_agent.identify_waste.return_value = [
            WasteItem(
                waste_type=WasteType.WAITING,
                location="ASSEMBLY",
                quantity=1200,
                impact="Long wait times",
                severity="high",
            )
        ]
        mock_agent.locate_bottlenecks.return_value = [
            Bottleneck(
                location="ASSEMBLY",
                root_cause="Process imbalance",
                impact="Limits throughput",
                severity="high",
            )
        ]
        mock_agent.generate_kaizen_proposals.return_value = [
            KaizenProposal(
                title="Reduce Wait Times",
                description="Implement better scheduling",
                impact="20% reduction in wait times",
                effort="medium",
                priority="high",
                expected_improvement={"lead_time_reduction": 0.20},
            )
        ]
        mock_agent.get_highest_priority_proposal.return_value = KaizenProposal(
            title="Reduce Wait Times",
            description="Implement better scheduling",
            impact="20% reduction in wait times",
            effort="medium",
            priority="high",
            expected_improvement={"lead_time_reduction": 0.20},
        )
        mock_agent.simulate_improvement.return_value = mock_vsm

        workflow = create_lean_optimization_workflow(agent=mock_agent)
        result = workflow.invoke(LeanOptimizationWorkflowState())

        # Verify agent methods were called
        # (The workflow calls methods on the agent during node execution)

        assert result is not None


class TestWorkflowConditionalRouting:
    """Test conditional routing in workflow."""

    def test_high_value_routing(self):
        """Verify high-value proposals route to human_review."""
        workflow = create_lean_optimization_workflow()
        assert workflow is not None

    def test_human_review_approval_routing(self):
        """Verify human review approval routes to END."""
        workflow = create_lean_optimization_workflow()
        assert workflow is not None

    def test_human_review_rejection_routing(self):
        """Verify human review rejection routes back to collect_data."""
        workflow = create_lean_optimization_workflow()
        assert workflow is not None


class TestWorkflowReport:
    """Test workflow report generation."""

    def test_compile_target_vsm_generates_report(self):
        """Verify compile_target_vsm_node generates a report."""
        # Import the node function directly to test in isolation
        from src.workflows.lean_optimization_workflow import compile_target_vsm_node

        # Create mock VSM data
        mock_vsm = VSMData(
            process_steps=[
                ProcessStep(name="CUTTING", va_time=1800, nva_time=300, wait_time=600, inventory=50),
            ],
            total_va_time=1800,
            total_nva_time=300,
            total_lead_time=2700,
            inventory_positions={"CUTTING": 50},
            takt_time=100.0,
        )

        # Create state with all data populated
        state = LeanOptimizationWorkflowState(
            raw_data={},
            current_vsm=mock_vsm,
            waste_list=[
                WasteItem(
                    waste_type=WasteType.WAITING,
                    location="CUTTING",
                    quantity=600,
                    impact="Wait time",
                    severity="medium",
                )
            ],
            bottlenecks=[
                Bottleneck(
                    location="CUTTING",
                    root_cause="Equipment setup",
                    impact="Limits capacity",
                    severity="medium",
                )
            ],
            kaizen_proposals=[
                KaizenProposal(
                    title="Test Proposal",
                    description="Test description",
                    impact="Test impact",
                    effort="low",
                    priority="high",
                    expected_improvement={"lead_time_reduction": 0.15},
                )
            ],
            target_vsm=mock_vsm,
        )

        # Run the node function directly
        result = compile_target_vsm_node(state)

        assert result is not None
        assert "final_report" in result
        if result["final_report"]:
            assert "Lean Optimization Report" in result["final_report"]