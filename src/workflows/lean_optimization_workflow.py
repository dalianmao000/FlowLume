"""Lean Optimization Agent - LangGraph State Machine Workflow.

This workflow orchestrates the entire lean optimization process:
1. Collect production/equipment/workforce data
2. Parse and validate event logs
3. Discover process paths from events
4. Calculate VSM (Value Stream Map) metrics
5. Identify waste (Muda/Mura/Muri)
6. Locate process bottlenecks
7. Generate Kaizen proposals
8. Simulate improvement effects
9. Human-in-the-loop for high-value proposals
10. Compile target state VSM
"""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from langgraph.graph import StateGraph, END

from src.agents.lean_optimization.lean_optimization_agent import (
    LeanOptimizationAgent,
    Bottleneck,
    KaizenProposal,
    AnalysisReport,
)
from src.agents.lean_optimization.vsm_calculator import VSMData
from src.agents.lean_optimization.waste_identifier import WasteItem
from src.agents.lean_optimization.event_log_models import (
    ProductionEvent,
    WorkforceEvent,
)


@dataclass
class LeanOptimizationWorkflowState:
    """Workflow state for Lean Optimization.

    Attributes:
        raw_data: Dict containing production/equipment/workforce events
        process_graph: Discovered process paths from events
        current_vsm: Current state VSM
        waste_list: List of identified waste
        bottlenecks: List of identified bottlenecks
        kaizen_proposals: List of improvement proposals
        target_vsm: Target state VSM after improvements
        human_approved: Whether human approved the proposal
        human_feedback: Feedback from human review
        is_high_value: Whether proposal is high-value requiring HITL
        final_report: Final compiled report
    """
    # Input
    raw_data: Dict[str, Any] = field(default_factory=dict)

    # Intermediate states
    process_graph: Optional[str] = None
    current_vsm: Optional[VSMData] = None
    waste_list: List[WasteItem] = field(default_factory=list)
    bottlenecks: List[Bottleneck] = field(default_factory=list)
    kaizen_proposals: List[KaizenProposal] = field(default_factory=list)
    target_vsm: Optional[VSMData] = None

    # Human review
    human_approved: bool = False
    human_feedback: Optional[str] = None
    is_high_value: bool = False

    # Final output
    final_report: Optional[str] = None

    # Retry mechanism
    retry_count: int = 0
    max_retries: int = 3


# Node function signatures - defined for potential reuse and testing
def collect_data_node(state: LeanOptimizationWorkflowState, agent: Optional[LeanOptimizationAgent] = None) -> dict:
    """Collect production/equipment/workforce data.

    This is the entry point node that initializes data collection.
    In a real implementation, this would fetch from external sources.
    For now, we use data already present in raw_data or generate defaults.
    """
    raw_data = state.raw_data

    # If no data provided, generate empty structures
    if not raw_data:
        raw_data = {
            "production_events": [],
            "workforce_events": [],
            "equipment_events": [],
        }

    return {"raw_data": raw_data}


def parse_events_node(state: LeanOptimizationWorkflowState) -> dict:
    """Parse and validate event logs from raw data.

    Validates that required event types are present and properly formatted.
    """
    raw_data = state.raw_data

    production_events = raw_data.get("production_events", [])
    workforce_events = raw_data.get("workforce_events", [])

    # Validate event data
    validation_errors = []

    if not production_events:
        validation_errors.append("No production events found")

    # Check for required event types
    event_types = {e.event_type for e in production_events} if production_events else set()
    required_types = {"OP_COMPLETE", "OP_START"}
    missing_types = required_types - event_types
    if missing_types:
        validation_errors.append(f"Missing required event types: {missing_types}")

    if validation_errors:
        return {
            "waste_list": [],
            "bottlenecks": [],
            "kaizen_proposals": [],
        }

    return {
        "process_graph": f"Discovered process with {len(set(e.operation for e in production_events))} operations",
    }


def discover_process_node(state: LeanOptimizationWorkflowState) -> dict:
    """Discover process paths from events.

    Analyzes event sequences to identify process flow and dependencies.
    """
    raw_data = state.raw_data
    production_events = raw_data.get("production_events", [])

    if not production_events:
        return {"process_graph": "No process discovered"}

    # Discover unique operations and their order
    operations = list(dict.fromkeys(e.operation for e in production_events))
    process_info = f"Process flow: {' -> '.join(operations)}"

    return {"process_graph": process_info}


def calculate_vsm_node(state: LeanOptimizationWorkflowState, agent: Optional[LeanOptimizationAgent] = None) -> dict:
    """Calculate VSM metrics from production events.

    Computes value-added time, non-value-added time, lead time,
    takt time, and inventory positions.
    """
    if agent is None:
        agent = LeanOptimizationAgent()

    raw_data = state.raw_data
    production_events = raw_data.get("production_events", [])
    workforce_events = raw_data.get("workforce_events", [])

    if not production_events:
        # Return empty VSM data if no events
        empty_vsm = VSMData(
            process_steps=[],
            total_va_time=0.0,
            total_nva_time=0.0,
            total_lead_time=0.0,
            inventory_positions={},
            takt_time=0.0,
        )
        return {"current_vsm": empty_vsm}

    # Calculate VSM using the agent's method
    vsm_data = agent.calculate_vsm(production_events, workforce_events)

    return {"current_vsm": vsm_data}


def identify_waste_node(state: LeanOptimizationWorkflowState, agent: Optional[LeanOptimizationAgent] = None) -> dict:
    """Identify waste (Muda/Mura/Muri) from VSM and events.

    Detects the 7 types of muda waste in the process.
    """
    if agent is None:
        agent = LeanOptimizationAgent()

    raw_data = state.raw_data
    production_events = raw_data.get("production_events", [])
    current_vsm = state.current_vsm

    if current_vsm is None:
        return {"waste_list": []}

    # Identify waste using the agent's method
    waste_items = agent.identify_waste(current_vsm, production_events)

    return {"waste_list": waste_items}


def locate_bottleneck_node(state: LeanOptimizationWorkflowState, agent: Optional[LeanOptimizationAgent] = None) -> dict:
    """Locate process bottlenecks from VSM data.

    Identifies constraints that limit overall process throughput.
    """
    if agent is None:
        agent = LeanOptimizationAgent()

    current_vsm = state.current_vsm

    if current_vsm is None:
        return {"bottlenecks": []}

    # Locate bottlenecks using the agent's method
    bottlenecks = agent.locate_bottlenecks(current_vsm)

    return {"bottlenecks": bottlenecks}


def generate_proposals_node(state: LeanOptimizationWorkflowState, agent: Optional[LeanOptimizationAgent] = None) -> dict:
    """Generate Kaizen improvement proposals.

    Creates targeted improvement suggestions based on identified
    waste and bottlenecks.
    """
    if agent is None:
        agent = LeanOptimizationAgent()

    current_vsm = state.current_vsm
    waste_list = state.waste_list
    bottlenecks = state.bottlenecks

    if current_vsm is None:
        return {"kaizen_proposals": []}

    # Generate proposals using the agent's method
    proposals = agent.generate_kaizen_proposals(
        current_vsm, waste_list, bottlenecks
    )

    # Determine if any proposal is high-value (high priority or high impact)
    is_high_value = any(
        p.priority == "high" or p.effort == "low"
        for p in proposals
    ) if proposals else False

    return {
        "kaizen_proposals": proposals,
        "is_high_value": is_high_value,
    }


def simulate_improvement_node(state: LeanOptimizationWorkflowState, agent: Optional[LeanOptimizationAgent] = None) -> dict:
    """Simulate improvement effects on VSM.

    Applies proposed improvements to predict the target state VSM.
    """
    if agent is None:
        agent = LeanOptimizationAgent()

    kaizen_proposals = state.kaizen_proposals
    current_vsm = state.current_vsm

    if not kaizen_proposals or current_vsm is None:
        return {"target_vsm": current_vsm}

    # Get highest priority proposal for simulation
    priority_proposal = agent._get_highest_priority_proposal(kaizen_proposals)

    if priority_proposal is None:
        return {"target_vsm": current_vsm}

    # Simulate the improvement
    target_vsm = agent.simulate_improvement(priority_proposal, current_vsm)

    return {"target_vsm": target_vsm}


def compile_target_vsm_node(state: LeanOptimizationWorkflowState) -> dict:
    """Compile target state VSM with improvements.

    Generates the final target state VSM report with all improvements.
    """
    current_vsm = state.current_vsm
    target_vsm = state.target_vsm
    kaizen_proposals = state.kaizen_proposals
    waste_list = state.waste_list
    bottlenecks = state.bottlenecks

    # Build report string
    report_parts = []

    report_parts.append("# Lean Optimization Report\n")

    # Current state summary
    if current_vsm:
        report_parts.append("## Current State VSM\n")
        report_parts.append(f"- Total VA Time: {current_vsm.total_va_time:.0f}s\n")
        report_parts.append(f"- Total NVA Time: {current_vsm.total_nva_time:.0f}s\n")
        report_parts.append(f"- Total Lead Time: {current_vsm.total_lead_time:.0f}s\n")
        report_parts.append(f"- Takt Time: {current_vsm.takt_time:.1f}s\n")
        report_parts.append(f"- Process Steps: {len(current_vsm.process_steps)}\n")

    # Identified waste
    if waste_list:
        report_parts.append(f"\n## Identified Waste ({len(waste_list)} items)\n")
        for waste in waste_list[:5]:  # Limit to first 5
            report_parts.append(
                f"- {waste.waste_type.value}: {waste.impact} (Severity: {waste.severity})\n"
            )

    # Identified bottlenecks
    if bottlenecks:
        report_parts.append(f"\n## Identified Bottlenecks ({len(bottlenecks)} items)\n")
        for bn in bottlenecks[:3]:  # Limit to first 3
            report_parts.append(
                f"- {bn.location}: {bn.root_cause} (Severity: {bn.severity})\n"
            )

    # Kaizen proposals
    if kaizen_proposals:
        report_parts.append(f"\n## Kaizen Proposals ({len(kaizen_proposals)} items)\n")
        for prop in kaizen_proposals[:3]:  # Limit to first 3
            report_parts.append(
                f"- {prop.title}: {prop.description[:100]}... (Priority: {prop.priority}, Effort: {prop.effort})\n"
            )

    # Target state VSM
    if target_vsm:
        report_parts.append("\n## Target State VSM (After Improvements)\n")
        report_parts.append(f"- Total VA Time: {target_vsm.total_va_time:.0f}s\n")
        report_parts.append(f"- Total NVA Time: {target_vsm.total_nva_time:.0f}s\n")
        report_parts.append(f"- Total Lead Time: {target_vsm.total_lead_time:.0f}s\n")
        report_parts.append(f"- Takt Time: {target_vsm.takt_time:.1f}s\n")

        # Calculate improvements
        if current_vsm and current_vsm.total_lead_time > 0:
            lead_time_reduction = (
                (current_vsm.total_lead_time - target_vsm.total_lead_time)
                / current_vsm.total_lead_time
                * 100
            )
            report_parts.append(
                f"- Lead Time Reduction: {lead_time_reduction:.1f}%\n"
            )

    final_report = "".join(report_parts)

    return {"final_report": final_report}


def human_review_node(state: LeanOptimizationWorkflowState) -> dict:
    """Human-in-the-loop node for high-value proposals.

    For high-value proposals, requires human approval before proceeding.
    In PoC, auto-approves unless explicit reject feedback is provided.
    """
    is_high_value = state.is_high_value
    human_feedback = state.human_feedback

    human_approved = False

    if is_high_value:
        # High-value proposals require explicit approval
        if human_feedback is None:
            # No feedback yet - default to approved in PoC
            human_approved = True
        elif "reject" in str(human_feedback).lower():
            human_approved = False
        else:
            human_approved = True
    else:
        # Non-high-value proposals are auto-approved
        human_approved = True

    return {"human_approved": human_approved}


def create_lean_optimization_workflow(
    agent: Optional[LeanOptimizationAgent] = None,
) -> StateGraph:
    """Create the Lean Optimization workflow.

    Args:
        agent: Optional LeanOptimizationAgent. If not provided,
               a new one will be created.

    Returns:
        Compiled StateGraph for the Lean Optimization workflow
    """
    # Build the state graph
    workflow = StateGraph(LeanOptimizationWorkflowState)

    # Add nodes
    workflow.add_node("collect_data", lambda s: collect_data_node(s, agent))
    workflow.add_node("parse_events", parse_events_node)
    workflow.add_node("discover_process", discover_process_node)
    workflow.add_node("calculate_vsm", lambda s: calculate_vsm_node(s, agent))
    workflow.add_node("identify_waste", lambda s: identify_waste_node(s, agent))
    workflow.add_node("locate_bottleneck", lambda s: locate_bottleneck_node(s, agent))
    workflow.add_node("generate_proposals", lambda s: generate_proposals_node(s, agent))
    workflow.add_node("simulate_improvement", lambda s: simulate_improvement_node(s, agent))
    workflow.add_node("compile_target_vsm", compile_target_vsm_node)
    workflow.add_node("human_review", human_review_node)

    # Set entry point
    workflow.set_entry_point("collect_data")

    # Add edges
    workflow.add_edge("collect_data", "parse_events")
    workflow.add_edge("parse_events", "discover_process")
    workflow.add_edge("discover_process", "calculate_vsm")
    workflow.add_edge("calculate_vsm", "identify_waste")
    workflow.add_edge("calculate_vsm", "locate_bottleneck")
    workflow.add_edge("identify_waste", "generate_proposals")
    workflow.add_edge("locate_bottleneck", "generate_proposals")
    workflow.add_edge("generate_proposals", "simulate_improvement")
    workflow.add_edge("simulate_improvement", "compile_target_vsm")

    # Conditional edge: compile_target_vsm -> human_review (high value) or END (low value)
    def high_value_route(state: LeanOptimizationWorkflowState) -> str:
        if state.is_high_value:
            return "high_value_proposal"
        return "low_value_proposal"

    workflow.add_conditional_edges(
        "compile_target_vsm",
        high_value_route,
        {
            "high_value_proposal": "human_review",
            "low_value_proposal": END,
        }
    )

    # Human review conditional edges
    def human_review_route(state: LeanOptimizationWorkflowState) -> str:
        if state.human_approved:
            return "approved"
        return "rejected"

    workflow.add_conditional_edges(
        "human_review",
        human_review_route,
        {
            "approved": END,
            "rejected": "collect_data",  # Loop back for re-processing
        }
    )

    return workflow.compile()


def run_lean_optimization_workflow(
    raw_data: Optional[Dict[str, Any]] = None,
    agent: Optional[LeanOptimizationAgent] = None,
) -> LeanOptimizationWorkflowState:
    """Run the Lean Optimization workflow and return final state.

    Args:
        raw_data: Optional dict containing production/equipment/workforce events
        agent: Optional LeanOptimizationAgent instance

    Returns:
        Final LeanOptimizationWorkflowState after workflow completion
    """
    workflow = create_lean_optimization_workflow(agent)

    initial_state = LeanOptimizationWorkflowState(raw_data=raw_data or {})
    final_state = workflow.invoke(initial_state)

    return final_state