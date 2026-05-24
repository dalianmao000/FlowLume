"""Tests for Lean Optimization Agent - Main Agent Class."""

import pytest
from datetime import datetime, timedelta
from pathlib import Path
import sys
from unittest.mock import Mock, patch

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from agents.lean_optimization.event_log_models import ProductionEvent, WorkforceEvent, EventType
from agents.lean_optimization.vsm_calculator import VSMCalculator, VSMData, ProcessStep
from agents.lean_optimization.waste_identifier import WasteIdentifier, WasteItem, WasteType
from agents.lean_optimization.lean_optimization_agent import (
    LeanOptimizationAgent,
    AnalysisReport,
    Bottleneck,
    KaizenProposal,
)
from agents.lean_optimization.mock_production_data import (
    generate_production_events,
    generate_workforce_events,
    BASE_DATE,
)


class TestLeanOptimizationAgentInit:
    """Test LeanOptimizationAgent initialization."""

    def test_default_initialization(self):
        """Test creating agent with default settings."""
        agent = LeanOptimizationAgent()
        assert agent.llm is not None
        assert agent.vsm_calculator is not None
        assert agent.waste_identifier is not None
        assert agent.system_prompt is not None

    def test_custom_initialization(self):
        """Test creating agent with custom components."""
        mock_llm = Mock()
        mock_vsm = Mock()
        mock_waste = Mock()

        agent = LeanOptimizationAgent(
            llm_client=mock_llm,
            vsm_calculator=mock_vsm,
            waste_identifier=mock_waste,
        )

        assert agent.llm == mock_llm
        assert agent.vsm_calculator == mock_vsm
        assert agent.waste_identifier == mock_waste


class TestBottleneckDataclass:
    """Test Bottleneck dataclass."""

    def test_bottleneck_creation(self):
        """Test creating a Bottleneck instance."""
        bottleneck = Bottleneck(
            location="PAINTING",
            root_cause="Long changeover time",
            impact="Delays downstream processes",
            severity="high",
        )
        assert bottleneck.location == "PAINTING"
        assert bottleneck.root_cause == "Long changeover time"
        assert bottleneck.impact == "Delays downstream processes"
        assert bottleneck.severity == "high"


class TestKaizenProposalDataclass:
    """Test KaizenProposal dataclass."""

    def test_kaizen_proposal_creation(self):
        """Test creating a KaizenProposal instance."""
        proposal = KaizenProposal(
            title="Reduce Wait Times",
            description="Implement better scheduling",
            impact="20% reduction in lead time",
            effort="medium",
            priority="high",
            expected_improvement={"lead_time_reduction": 0.20},
        )
        assert proposal.title == "Reduce Wait Times"
        assert proposal.description == "Implement better scheduling"
        assert proposal.effort == "medium"
        assert proposal.priority == "high"
        assert proposal.expected_improvement["lead_time_reduction"] == 0.20

    def test_kaizen_proposal_default_expected_improvement(self):
        """Test KaizenProposal has empty dict as default for expected_improvement."""
        proposal = KaizenProposal(
            title="Test",
            description="Test desc",
            impact="Test impact",
            effort="low",
            priority="low",
        )
        assert proposal.expected_improvement == {}


class TestAnalysisReportDataclass:
    """Test AnalysisReport dataclass."""

    def test_analysis_report_creation(self):
        """Test creating an AnalysisReport instance."""
        vsm_data = VSMData()
        report = AnalysisReport(
            vsm_data=vsm_data,
            waste_items=[],
            bottlenecks=[],
            kaizen_proposals=[],
        )
        assert report.vsm_data == vsm_data
        assert report.waste_items == []
        assert report.bottlenecks == []
        assert report.kaizen_proposals == []
        assert report.target_vsm is None


class TestCalculateVSM:
    """Test calculate_vsm method."""

    def test_calculate_vsm_with_mock_data(self):
        """Test VSM calculation with mock data."""
        agent = LeanOptimizationAgent()
        production_events = generate_production_events(start_date=BASE_DATE, days=1)
        workforce_events = generate_workforce_events(start_date=BASE_DATE, days=1)

        vsm_data = agent.calculate_vsm(production_events, workforce_events)

        assert isinstance(vsm_data, VSMData)
        assert vsm_data.total_va_time >= 0
        assert vsm_data.total_nva_time >= 0
        assert vsm_data.total_lead_time >= 0

    def test_calculate_vsm_empty_events(self):
        """Test VSM calculation with empty events."""
        agent = LeanOptimizationAgent()

        vsm_data = agent.calculate_vsm([], [])

        assert isinstance(vsm_data, VSMData)
        assert vsm_data.total_va_time == 0
        assert vsm_data.total_nva_time == 0
        assert vsm_data.total_lead_time == 0


class TestIdentifyWaste:
    """Test identify_waste method."""

    def test_identify_waste_with_vsm_data(self):
        """Test waste identification with VSM data."""
        agent = LeanOptimizationAgent()
        production_events = generate_production_events(start_date=BASE_DATE, days=1)

        # First calculate VSM
        vsm_data = agent.calculate_vsm(production_events, [])

        # Then identify waste
        waste_items = agent.identify_waste(vsm_data, production_events)

        assert isinstance(waste_items, list)
        # Waste items may or may not be found depending on data


class TestLocateBottlenecks:
    """Test locate_bottlenecks method."""

    def test_locate_bottlenecks_with_mock_data(self):
        """Test bottleneck identification with mock data."""
        # Mock the LLM to avoid actual API calls
        agent = LeanOptimizationAgent()
        production_events = generate_production_events(start_date=BASE_DATE, days=1)
        vsm_data = agent.calculate_vsm(production_events, [])

        # Mock LLM to avoid actual API calls
        with patch.object(agent.llm, 'generate', return_value="Mock bottleneck analysis"):
            bottlenecks = agent.locate_bottlenecks(vsm_data)

        assert isinstance(bottlenecks, list)
        for bottleneck in bottlenecks:
            assert isinstance(bottleneck, Bottleneck)
            assert bottleneck.location is not None
            assert bottleneck.root_cause is not None
            assert bottleneck.severity in ["low", "medium", "high", "critical"]


class TestGenerateKaizenProposals:
    """Test generate_kaizen_proposals method."""

    def test_generate_proposals_with_mock_data(self):
        """Test Kaizen proposal generation with mock data."""
        agent = LeanOptimizationAgent()
        production_events = generate_production_events(start_date=BASE_DATE, days=1)
        vsm_data = agent.calculate_vsm(production_events, [])

        # Mock the LLM to avoid actual API calls
        with patch.object(agent.llm, 'generate', return_value="Mock analysis"):
            waste_items = agent.identify_waste(vsm_data, production_events)
            bottlenecks = agent.locate_bottlenecks(vsm_data)
            proposals = agent.generate_kaizen_proposals(vsm_data, waste_items, bottlenecks)

        assert isinstance(proposals, list)
        if proposals:
            for proposal in proposals:
                assert isinstance(proposal, KaizenProposal)
                assert proposal.title is not None
                assert proposal.description is not None
                assert proposal.priority in ["high", "medium", "low"]


class TestSimulateImprovement:
    """Test simulate_improvement method."""

    def test_simulate_improvement_returns_vsm_data(self):
        """Test improvement simulation returns VSMData."""
        agent = LeanOptimizationAgent()

        # Create a basic VSM
        process_steps = [
            ProcessStep(name="CUTTING", va_time=1000, nva_time=200, wait_time=500, inventory=50),
            ProcessStep(name="WELDING", va_time=2000, nva_time=300, wait_time=1000, inventory=100),
        ]
        vsm_data = VSMData(
            process_steps=process_steps,
            total_va_time=3000,
            total_nva_time=500,
            total_lead_time=4500,
            inventory_positions={"CUTTING": 50, "WELDING": 100},
            takt_time=100,
        )

        proposal = KaizenProposal(
            title="Test Improvement",
            description="Test proposal",
            impact="Test impact",
            effort="low",
            priority="high",
            expected_improvement={
                "lead_time_reduction": 0.20,
                "inventory_reduction": 0.30,
                "va_time_improvement": 0.10,
            },
        )

        simulated_vsm = agent.simulate_improvement(proposal, vsm_data)

        assert isinstance(simulated_vsm, VSMData)
        assert simulated_vsm.total_lead_time < vsm_data.total_lead_time
        assert simulated_vsm.total_va_time < vsm_data.total_va_time

    def test_simulate_improvement_with_defaults(self):
        """Test improvement simulation with default improvements."""
        agent = LeanOptimizationAgent()

        process_steps = [
            ProcessStep(name="TEST", va_time=1000, nva_time=200, wait_time=500, inventory=100),
        ]
        vsm_data = VSMData(
            process_steps=process_steps,
            total_va_time=1000,
            total_nva_time=200,
            total_lead_time=1700,
            inventory_positions={"TEST": 100},
            takt_time=100,
        )

        proposal = KaizenProposal(
            title="Test",
            description="Test",
            impact="Test",
            effort="low",
            priority="low",
        )

        simulated_vsm = agent.simulate_improvement(proposal, vsm_data)

        assert isinstance(simulated_vsm, VSMData)
        # Default improvements should be applied


class TestAnalyzeProductionData:
    """Test analyze_production_data method (full pipeline)."""

    def test_analyze_production_data_full_pipeline(self):
        """Test complete analysis pipeline."""
        agent = LeanOptimizationAgent()
        production_events = generate_production_events(start_date=BASE_DATE, days=1)
        workforce_events = generate_workforce_events(start_date=BASE_DATE, days=1)

        # Mock the LLM to avoid actual API calls
        with patch.object(agent.llm, 'generate', return_value="Mock analysis"):
            report = agent.analyze_production_data(
                production_events,
                workforce_events,
            )

        assert isinstance(report, AnalysisReport)
        assert isinstance(report.vsm_data, VSMData)
        assert isinstance(report.waste_items, list)
        assert isinstance(report.bottlenecks, list)
        assert isinstance(report.kaizen_proposals, list)

    def test_analyze_production_data_empty_events(self):
        """Test analysis with empty events."""
        agent = LeanOptimizationAgent()

        # Mock LLM to avoid actual API calls
        with patch.object(agent.llm, 'generate', return_value="Mock analysis"):
            report = agent.analyze_production_data([], [])

        assert isinstance(report, AnalysisReport)
        assert report.vsm_data.total_lead_time == 0


class TestHelperMethods:
    """Test agent helper methods."""

    def test_estimate_capacity_utilization(self):
        """Test capacity utilization estimation."""
        agent = LeanOptimizationAgent()
        vsm_data = VSMData(takt_time=100)
        capacity = agent._estimate_capacity_utilization(vsm_data)
        assert 0 <= capacity <= 100

    def test_estimate_lead_time_days(self):
        """Test lead time estimation."""
        agent = LeanOptimizationAgent()
        vsm_data = VSMData(total_lead_time=72000)  # 20 hours in seconds
        lead_time = agent._estimate_lead_time_days(vsm_data)
        assert lead_time >= 0

    def test_estimate_defect_rate(self):
        """Test defect rate estimation."""
        agent = LeanOptimizationAgent()
        defect_items = [
            WasteItem(
                waste_type=WasteType.DEFECTS,
                location="TEST",
                quantity=10,
                impact="Test defect",
                severity="medium",
            )
        ]
        rate = agent._estimate_defect_rate(defect_items)
        assert rate >= 0

    def test_build_process_info(self):
        """Test process info string building."""
        agent = LeanOptimizationAgent()
        vsm_data = VSMData(
            process_steps=[
                ProcessStep(name="CUTTING", va_time=100, nva_time=10, wait_time=50, inventory=20),
            ]
        )
        info = agent._build_process_info(vsm_data)
        assert "CUTTING" in info
        assert "100" in info

    def test_build_waste_summary(self):
        """Test waste summary string building."""
        agent = LeanOptimizationAgent()
        waste_items = [
            WasteItem(
                waste_type=WasteType.WAITING,
                location="TEST",
                quantity=100,
                impact="Test wait",
                severity="medium",
            )
        ]
        summary = agent._build_waste_summary(waste_items)
        assert "WAITING" in summary

    def test_build_bottleneck_summary(self):
        """Test bottleneck summary string building."""
        agent = LeanOptimizationAgent()
        bottlenecks = [
            Bottleneck(
                location="TEST",
                root_cause="Test cause",
                impact="Test impact",
                severity="high",
            )
        ]
        summary = agent._build_bottleneck_summary(bottlenecks)
        assert "TEST" in summary
        assert "high" in summary

    def test_get_highest_priority_proposal(self):
        """Test getting highest priority proposal."""
        agent = LeanOptimizationAgent()
        proposals = [
            KaizenProposal(
                title="Low Priority",
                description="Test",
                impact="Test",
                effort="low",
                priority="low",
            ),
            KaizenProposal(
                title="High Priority",
                description="Test",
                impact="Test",
                effort="high",
                priority="high",
            ),
            KaizenProposal(
                title="Medium Priority",
                description="Test",
                impact="Test",
                effort="medium",
                priority="medium",
            ),
        ]

        highest = agent._get_highest_priority_proposal(proposals)
        assert highest.priority == "high"


class TestEndToEndWithMockData:
    """End-to-end tests with mock data."""

    def test_full_analysis_pipeline_with_mock_data(self):
        """Test full analysis pipeline with mock data."""
        agent = LeanOptimizationAgent()
        production_events = generate_production_events(start_date=BASE_DATE, days=3)
        workforce_events = generate_workforce_events(start_date=BASE_DATE, days=3)

        # Mock LLM calls
        with patch.object(agent.llm, 'generate', return_value="Mock bottleneck analysis"):
            report = agent.analyze_production_data(
                production_events,
                workforce_events,
            )

        # Verify report structure
        assert report.vsm_data is not None
        assert len(report.vsm_data.process_steps) > 0

        # Verify waste identification
        assert isinstance(report.waste_items, list)

        # Verify bottleneck analysis
        assert isinstance(report.bottlenecks, list)

        # Verify Kaizen proposals
        assert isinstance(report.kaizen_proposals, list)

    def test_vsm_calculation_consistency(self):
        """Test that VSM calculation produces consistent results."""
        agent = LeanOptimizationAgent()
        events = generate_production_events(start_date=BASE_DATE, days=1)

        vsm1 = agent.calculate_vsm(events, [])
        vsm2 = agent.calculate_vsm(events, [])

        # Same input should produce same output
        assert vsm1.total_va_time == vsm2.total_va_time
        assert vsm1.total_nva_time == vsm2.total_nva_time