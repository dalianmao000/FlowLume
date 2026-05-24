"""Lean Optimization Agent - Main Agent Class for VSM and Waste Analysis.

This module provides the LeanOptimizationAgent class that orchestrates:
- VSM (Value Stream Map) calculation from production events
- Waste identification (7 types of muda)
- Bottleneck analysis using LLM
- Kaizen proposal generation
- Improvement simulation
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any

from src.llm.claude_client import ClaudeClient
from src.prompts.lean_optimization import (
    SYSTEM_PROMPT,
    VSM_ANALYSIS_PROMPT,
    WASTE_ANALYSIS_PROMPT,
    BOTTLENECK_ANALYSIS_PROMPT,
    KAIZEN_PROPOSAL_PROMPT,
    TARGET_STATE_VSM_PROMPT,
)

from .vsm_calculator import VSMCalculator, VSMData
from .waste_identifier import WasteIdentifier, WasteItem, WasteType
from .event_log_models import ProductionEvent, WorkforceEvent


@dataclass
class Bottleneck:
    """Represents a process bottleneck in the production line.

    Attributes:
        location: Where the bottleneck occurs (process step name)
        root_cause: Root cause analysis of why it's a bottleneck
        impact: Description of the impact on overall throughput
        severity: Bottleneck severity (low/medium/high/critical)
    """

    location: str
    root_cause: str
    impact: str
    severity: str


@dataclass
class KaizenProposal:
    """Represents a Kaizen improvement proposal.

    Attributes:
        title: Short title for the proposal
        description: Detailed description of the improvement
        impact: Expected business impact
        effort: Implementation effort (low/medium/high)
        priority: Proposal priority (high/medium/low)
        expected_improvement: Dict with expected metric improvements
    """

    title: str
    description: str
    impact: str
    effort: str
    priority: str
    expected_improvement: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AnalysisReport:
    """Complete analysis report for lean optimization.

    Attributes:
        vsm_data: Value Stream Map data
        waste_items: List of identified waste items
        bottlenecks: List of identified bottlenecks
        kaizen_proposals: List of Kaizen improvement proposals
        target_vsm: Predicted future state VSM after improvements
    """

    vsm_data: VSMData
    waste_items: List[WasteItem]
    bottlenecks: List[Bottleneck]
    kaizen_proposals: List[KaizenProposal]
    target_vsm: Optional[VSMData] = None


class LeanOptimizationAgent:
    """Main agent for Lean Optimization and continuous improvement.

    Orchestrates VSM calculation, waste identification, bottleneck analysis,
    and Kaizen proposal generation to provide comprehensive lean optimization
    insights for manufacturing processes.

    Attributes:
        llm: LLM client for generating analyses and proposals
        vsm_calculator: Calculator for Value Stream Map metrics
        waste_identifier: Identifier for the 7 types of muda
    """

    def __init__(
        self,
        llm_client: Optional[ClaudeClient] = None,
        vsm_calculator: Optional[VSMCalculator] = None,
        waste_identifier: Optional[WasteIdentifier] = None,
    ):
        """Initialize the LeanOptimizationAgent.

        Args:
            llm_client: LLM client for generating analyses. If not provided,
                        a new ClaudeClient will be created.
            vsm_calculator: Calculator for VSM metrics. If not provided,
                           a new VSMCalculator will be created.
            waste_identifier: Identifier for waste items. If not provided,
                             a new WasteIdentifier will be created.
        """
        self.llm = llm_client or ClaudeClient()
        self.vsm_calculator = vsm_calculator or VSMCalculator()
        self.waste_identifier = waste_identifier or WasteIdentifier()
        self.system_prompt = SYSTEM_PROMPT

    def analyze_production_data(
        self,
        production_events: List[ProductionEvent],
        equipment_events: List[Any],
        workforce_events: List[WorkforceEvent],
    ) -> AnalysisReport:
        """Perform complete lean analysis on production data.

        This method orchestrates the full analysis pipeline:
        1. Calculate VSM from events
        2. Identify waste from VSM and events
        3. Locate bottlenecks
        4. Generate Kaizen proposals
        5. Simulate improvements

        Args:
            production_events: List of ProductionEvent objects
            equipment_events: List of EquipmentEvent objects (currently unused)
            workforce_events: List of WorkforceEvent objects

        Returns:
            AnalysisReport with complete analysis results
        """
        # Step 1: Calculate VSM
        vsm_data = self.calculate_vsm(production_events, workforce_events)

        # Step 2: Identify waste
        waste_items = self.identify_waste(vsm_data, production_events)

        # Step 3: Locate bottlenecks
        bottlenecks = self.locate_bottlenecks(vsm_data)

        # Step 4: Generate Kaizen proposals
        kaizen_proposals = self.generate_kaizen_proposals(
            vsm_data, waste_items, bottlenecks
        )

        # Step 5: Simulate improvements and predict target VSM
        target_vsm = None
        if kaizen_proposals:
            # Use the highest priority proposal for simulation
            priority_proposal = self._get_highest_priority_proposal(kaizen_proposals)
            if priority_proposal:
                target_vsm = self.simulate_improvement(priority_proposal, vsm_data)

        return AnalysisReport(
            vsm_data=vsm_data,
            waste_items=waste_items,
            bottlenecks=bottlenecks,
            kaizen_proposals=kaizen_proposals,
            target_vsm=target_vsm,
        )

    def calculate_vsm(
        self,
        production_events: List[ProductionEvent],
        workforce_events: List[WorkforceEvent],
    ) -> VSMData:
        """Calculate Value Stream Map from production events.

        Args:
            production_events: List of ProductionEvent objects
            workforce_events: List of WorkforceEvent objects (for future use)

        Returns:
            VSMData object with calculated metrics
        """
        # Calculate available time and demand from events
        available_time, demand = self._calculate_time_and_demand(production_events)

        return self.vsm_calculator.calculate_from_events(
            production_events=production_events,
            workforce_events=workforce_events,
            available_time=available_time,
            demand=demand,
        )

    def identify_waste(
        self,
        vsm_data: VSMData,
        events: List[ProductionEvent],
    ) -> List[WasteItem]:
        """Identify waste from VSM data and events.

        Args:
            vsm_data: VSMData object containing process metrics
            events: List of ProductionEvent objects

        Returns:
            List of WasteItem objects identified
        """
        return self.waste_identifier.identify_all(events, vsm_data)

    def locate_bottlenecks(self, vsm_data: VSMData) -> List[Bottleneck]:
        """Locate process bottlenecks using VSM data.

        Uses the LLM with BOTTLENECK_ANALYSIS_PROMPT to analyze
        the VSM data and identify bottlenecks.

        Args:
            vsm_data: VSMData object containing process metrics

        Returns:
            List of Bottleneck objects identified
        """
        # Handle empty VSM data - no bottlenecks can be identified
        if not vsm_data.process_steps:
            return []

        # Build process info for the prompt
        process_info = self._build_process_info(vsm_data)

        # Calculate customer takt if available
        customer_takt = f"Customer takt time: {vsm_data.takt_time:.1f} seconds" if vsm_data.takt_time > 0 else "Customer takt time: Not available"

        # Build process data for table format
        process_data = ""
        for i, step in enumerate(vsm_data.process_steps[:4]):  # Limit to 4 steps for table
            process_data += f"| {step.name} | {step.va_time:.0f} | {step.nva_time:.0f} | {step.wait_time:.0f} |\n"

        # Calculate utilization for each step
        util_values = []
        for step in vsm_data.process_steps[:4]:
            if vsm_data.takt_time > 0:
                util = min(100, (vsm_data.takt_time / step.va_time) * 100) if step.va_time > 0 else 50
            else:
                util = 50
            util_values.append(util)

        # Build inventory info
        inventory_info = self._build_inventory_info(vsm_data)

        # Build prompt with VSM data
        prompt = BOTTLENECK_ANALYSIS_PROMPT.format(
            process_info=process_info,
            process_1=vsm_data.process_steps[0].name if len(vsm_data.process_steps) > 0 else "N/A",
            tt_1=vsm_data.process_steps[0].va_time if len(vsm_data.process_steps) > 0 else 0,
            util_1=util_values[0] if len(util_values) > 0 else 50,
            status_1="Constraint" if util_values[0] > 80 else "Normal" if len(util_values) > 0 else "N/A",
            process_2=vsm_data.process_steps[1].name if len(vsm_data.process_steps) > 1 else "N/A",
            tt_2=vsm_data.process_steps[1].va_time if len(vsm_data.process_steps) > 1 else 0,
            util_2=util_values[1] if len(util_values) > 1 else 50,
            status_2="Constraint" if len(util_values) > 1 and util_values[1] > 80 else "Normal",
            process_3=vsm_data.process_steps[2].name if len(vsm_data.process_steps) > 2 else "N/A",
            tt_3=vsm_data.process_steps[2].va_time if len(vsm_data.process_steps) > 2 else 0,
            util_3=util_values[2] if len(util_values) > 2 else 50,
            status_3="Constraint" if len(util_values) > 2 and util_values[2] > 80 else "Normal",
            process_4=vsm_data.process_steps[3].name if len(vsm_data.process_steps) > 3 else "N/A",
            tt_4=vsm_data.process_steps[3].va_time if len(vsm_data.process_steps) > 3 else 0,
            util_4=util_values[3] if len(util_values) > 3 else 50,
            status_4="Constraint" if len(util_values) > 3 and util_values[3] > 80 else "Normal",
            customer_takt=customer_takt,
            inventory_buildup=inventory_info,
            changeover_time="Changeover analysis: Data not available",
            bottleneck_impact_on_capacity="To be analyzed",
            bottleneck_impact_on_leadtime="To be analyzed",
            bottleneck_impact_on_inventory="To be analyzed",
            man_factor="To be analyzed",
            machine_factor="To be analyzed",
            material_factor="To be analyzed",
            method_factor="To be analyzed",
            environment_factor="To be analyzed",
            measurement_factor="To be analyzed",
            short_term_measures="To be determined",
            medium_term_measures="To be determined",
            long_term_measures="To be determined",
            capacity_improvement=0,
            leadtime_reduction=0,
            inventory_reduction=0,
            bottleneck_process_1="To be determined",
            bottleneck_tt_1=0,
            gap_1=0,
            bottleneck_util_1=0,
            bottleneck_priority_1=0,
            bottleneck_process_2="N/A",
            bottleneck_tt_2=0,
            gap_2=0,
            bottleneck_util_2=0,
            bottleneck_priority_2=0,
        )

        # Generate bottleneck analysis using LLM
        analysis = self.llm.generate(self.system_prompt, prompt)

        # Parse the LLM response to extract bottlenecks
        bottlenecks = self._parse_bottlenecks_from_analysis(analysis, vsm_data)

        # If no bottlenecks found via LLM, use fallback analysis
        if not bottlenecks:
            bottlenecks = self._identify_bottlenecks_fallback(vsm_data)

        return bottlenecks

    def generate_kaizen_proposals(
        self,
        vsm_data: VSMData,
        waste_items: List[WasteItem],
        bottlenecks: List[Bottleneck],
    ) -> List[KaizenProposal]:
        """Generate Kaizen improvement proposals.

        Args:
            vsm_data: VSMData object containing process metrics
            waste_items: List of identified WasteItem objects
            bottlenecks: List of identified Bottleneck objects

        Returns:
            List of KaizenProposal objects
        """
        # Build waste analysis summary
        waste_summary = self._build_waste_summary(waste_items)

        # Build bottleneck analysis summary
        bottleneck_summary = self._build_bottleneck_summary(bottlenecks)

        # Calculate current state metrics
        current_capacity = self._estimate_capacity_utilization(vsm_data)
        current_lead_time = self._estimate_lead_time_days(vsm_data)
        current_wip = sum(vsm_data.inventory_positions.values())
        current_defect_rate = self._estimate_defect_rate(waste_items)

        # Build the prompt
        prompt = KAIZEN_PROPOSAL_PROMPT.format(
            problem_description=f"VSM Analysis reveals inefficiencies in production process with {len(waste_items)} waste items identified",
            current_capacity_util=current_capacity,
            current_lead_time=current_lead_time,
            current_wip=current_wip,
            current_defect_rate=current_defect_rate,
            waste_analysis_results=waste_summary,
            bottleneck_analysis_results=bottleneck_summary,
            kaizen_title="Production Process Improvement",
            current_problem="Production process has inefficiencies leading to extended lead times and excess inventory",
            smart_specific="Reduce lead time and inventory levels",
            smart_measurable="20% reduction in lead time, 30% reduction in WIP",
            smart_achievable="Through waste elimination and bottleneck relief",
            smart_relevant="Improve customer delivery and reduce working capital",
            smart_timebound="3-6 months",
            target_capacity_util=current_capacity + 10,
            target_lead_time=current_lead_time * 0.8,
            target_wip=int(current_wip * 0.7),
            target_defect_rate=max(0, current_defect_rate - 2),
            capacity_improvement=10,
            leadtime_reduction=20,
            wip_reduction=30,
            defect_reduction=2,
            why1="Why is lead time extended?",
            cause1="Excess wait time between operations",
            why2="Why is there wait time?",
            cause2="Unbalanced process capacities",
            why3="Why are capacities unbalanced?",
            cause3="Bottleneck at painting operation",
            why4="Why is painting a bottleneck?",
            cause4="Long changeover and processing time",
            why5="Why is changeover long?",
            root_cause="Legacy equipment with no quick-release fixtures",
            measure_1_title="Implement SMED for Painting",
            measure_1_content="Apply Single-Minute Exchange of Die (SMED) techniques to reduce painting changeover time by 50%",
            measure_1_owner="Production Engineering",
            measure_1_timeline="4-6 weeks",
            measure_1_resources="External SMED consultant, maintenance team",
            measure_1_expected_effect="50% reduction in changeover time",
            measure_2_title="Introduce Kanban Pull System",
            measure_2_content="Implement Kanban cards between ASSEMBLY and PAINTING to reduce WIP by 30%",
            measure_2_owner="Production Planning",
            measure_2_timeline="2-4 weeks",
            measure_2_resources="Kanban cards, visual management tools",
            measure_2_expected_effect="30% reduction in WIP inventory",
            measure_3_title="Cross-Training Program",
            measure_3_content="Train operators to work at multiple stations to reduce waiting due to resource constraints",
            measure_3_owner="HR/Training",
            measure_3_timeline="8 weeks",
            measure_3_resources="Training time, additional staffing during training",
            measure_3_expected_effect="20% improvement in labor utilization",
            prep_phase_time="2 weeks",
            prep_phase_actions="Document current processes, identify improvement team",
            prep_phase_owner="Process Engineering Manager",
            prep_phase_checkpoint="Team formed, baseline metrics captured",
            impl_phase_time="4-8 weeks",
            impl_phase_actions="Implement improvements, train staff, monitor progress",
            impl_phase_owner="Production Manager",
            impl_phase_checkpoint="Weekly reviews, KPI tracking",
            verify_phase_time="2-4 weeks",
            verify_phase_actions="Validate improvements, document learnings",
            verify_phase_owner="Quality Manager",
            verify_phase_checkpoint="Final report, knowledge sharing",
            business_value="Reduced lead time improves delivery performance; Lower inventory frees working capital",
            annual_cost_saving=500000,
            capacity_revenue=300000,
            quality_cost_reduction=100000,
            total_annual_benefit=900000,
            risk_1="Resistance to change",
            risk_1_impact="Medium",
            risk_1_probability=30,
            risk_1_countermeasure="Early engagement, training, quick wins demonstration",
            risk_2="Implementation delays",
            risk_2_impact="Low",
            risk_2_probability=20,
            risk_2_countermeasure="Weekly milestone reviews, contingency planning",
        )

        # Generate Kaizen proposal using LLM
        proposal_text = self.llm.generate(self.system_prompt, prompt)

        # Parse the LLM response to extract proposals
        proposals = self._parse_kaizen_proposals(proposal_text, vsm_data, waste_items)

        # If no proposals found, generate fallback proposals
        if not proposals:
            proposals = self._generate_fallback_proposals(vsm_data, waste_items, bottlenecks)

        return proposals

    def simulate_improvement(
        self,
        proposal: KaizenProposal,
        vsm_data: VSMData,
    ) -> VSMData:
        """Simulate and predict improved VSM after implementing a proposal.

        Args:
            proposal: KaizenProposal to simulate
            vsm_data: Current VSMData object

        Returns:
            Predicted VSMData after improvement
        """
        # Parse expected improvements from the proposal
        improvement = proposal.expected_improvement

        # Calculate reduction factors based on proposal
        lead_time_reduction = improvement.get("lead_time_reduction", 0.15)  # Default 15%
        inventory_reduction = improvement.get("inventory_reduction", 0.20)  # Default 20%
        va_time_improvement = improvement.get("va_time_improvement", 0.10)  # Default 10%

        # Create a simulated VSM with improvements
        simulated_steps = []
        for step in vsm_data.process_steps:
            from .vsm_calculator import ProcessStep

            # Apply improvements to each step
            improved_step = ProcessStep(
                name=step.name,
                va_time=step.va_time * (1 - va_time_improvement),
                nva_time=step.nva_time * (1 - lead_time_reduction),
                wait_time=step.wait_time * (1 - lead_time_reduction),
                inventory=int(step.inventory * (1 - inventory_reduction)),
                takt_time=step.takt_time,
            )
            simulated_steps.append(improved_step)

        # Recalculate totals
        total_va_time = sum(s.va_time for s in simulated_steps)
        total_nva_time = sum(s.nva_time for s in simulated_steps)
        total_lead_time = total_va_time + total_nva_time + sum(s.wait_time for s in simulated_steps)

        from .vsm_calculator import VSMData as VSMDataClass

        return VSMDataClass(
            process_steps=simulated_steps,
            total_va_time=total_va_time,
            total_nva_time=total_nva_time,
            total_lead_time=total_lead_time,
            inventory_positions={s.name: s.inventory for s in simulated_steps},
            takt_time=vsm_data.takt_time,
        )

    # Helper methods

    def _calculate_time_and_demand(
        self, events: List[ProductionEvent]
    ) -> tuple:
        """Calculate available time and demand from events.

        Returns:
            Tuple of (available_time_seconds, demand_units)
        """
        if not events:
            return None, None

        # Calculate time span
        start_times = [e.start_time for e in events]
        min_time = min(start_times)
        max_time = max(start_times)
        available_time = (max_time - min_time).total_seconds()

        # Estimate demand from ORDER_CREATED events
        order_events = [e for e in events if e.event_type == "ORDER_CREATED"]
        demand = sum(e.quantity for e in order_events)

        return available_time, demand

    def _build_process_info(self, vsm_data: VSMData) -> str:
        """Build process information string for prompts."""
        lines = ["Process Steps:"]
        for i, step in enumerate(vsm_data.process_steps):
            lines.append(
                f"{i+1}. {step.name}: VA={step.va_time:.0f}s, NVA={step.nva_time:.0f}s, "
                f"Wait={step.wait_time:.0f}s, Inventory={step.inventory}"
            )
        return "\n".join(lines)

    def _build_inventory_info(self, vsm_data: VSMData) -> str:
        """Build inventory information string for prompts."""
        lines = ["Inventory Positions:"]
        for name, qty in vsm_data.inventory_positions.items():
            lines.append(f"- {name}: {qty} units")
        return "\n".join(lines)

    def _parse_bottlenecks_from_analysis(
        self, analysis: str, vsm_data: VSMData
    ) -> List[Bottleneck]:
        """Parse bottlenecks from LLM analysis text.

        Args:
            analysis: LLM-generated analysis text
            vsm_data: VSMData for additional context

        Returns:
            List of Bottleneck objects
        """
        bottlenecks = []

        # Look for bottleneck patterns in the analysis
        if "bottleneck" in analysis.lower() or "constraint" in analysis.lower():
            # Try to identify processes mentioned as bottlenecks
            for step in vsm_data.process_steps:
                if any(keyword in analysis.lower() for keyword in [step.name.lower(), "constraint", "bottleneck"]):
                    # Estimate severity based on wait time and inventory
                    severity = "medium"
                    if step.wait_time > 1800 or step.inventory > 200:
                        severity = "high"
                    elif step.wait_time > 600 or step.inventory > 100:
                        severity = "medium"
                    else:
                        severity = "low"

                    bottlenecks.append(
                        Bottleneck(
                            location=step.name,
                            root_cause=f"Process capacity constraint at {step.name}",
                            impact=f"Affects throughput with {step.wait_time:.0f}s wait and {step.inventory} units inventory",
                            severity=severity,
                        )
                    )

        return bottlenecks

    def _identify_bottlenecks_fallback(self, vsm_data: VSMData) -> List[Bottleneck]:
        """Fallback method to identify bottlenecks when LLM analysis is not helpful.

        Args:
            vsm_data: VSMData object

        Returns:
            List of Bottleneck objects
        """
        bottlenecks = []

        # Identify bottlenecks based on high wait times and inventory
        for step in vsm_data.process_steps:
            # High wait time indicates bottleneck
            if step.wait_time > 1800:  # > 30 minutes
                bottlenecks.append(
                    Bottleneck(
                        location=step.name,
                        root_cause="Extended wait time due to process imbalance",
                        impact=f"Wait time of {step.wait_time:.0f}s delays downstream processes",
                        severity="high" if step.wait_time > 3600 else "medium",
                    )
                )

            # High inventory indicates bottleneck (upstream buildup)
            if step.inventory > 200:
                bottlenecks.append(
                    Bottleneck(
                        location=step.name,
                        root_cause="Accumulated WIP due to downstream constraint",
                        impact=f"{step.inventory} units accumulated, indicating downstream bottleneck",
                        severity="high" if step.inventory > 500 else "medium",
                    )
                )

        return bottlenecks

    def _build_waste_summary(self, waste_items: List[WasteItem]) -> str:
        """Build waste summary string for prompts."""
        if not waste_items:
            return "No waste items identified."

        # Group by waste type
        by_type: Dict[WasteType, List[WasteItem]] = {}
        for item in waste_items:
            if item.waste_type not in by_type:
                by_type[item.waste_type] = []
            by_type[item.waste_type].append(item)

        lines = ["Identified Waste:"]
        for waste_type, items in by_type.items():
            total_quantity = sum(item.quantity for item in items)
            lines.append(f"- {waste_type.value}: {len(items)} instances, total impact: {total_quantity:.0f}")

        return "\n".join(lines)

    def _build_bottleneck_summary(self, bottlenecks: List[Bottleneck]) -> str:
        """Build bottleneck summary string for prompts."""
        if not bottlenecks:
            return "No bottlenecks identified."

        lines = ["Identified Bottlenecks:"]
        for bn in bottlenecks:
            lines.append(f"- {bn.location}: {bn.root_cause} (Severity: {bn.severity})")

        return "\n".join(lines)

    def _estimate_capacity_utilization(self, vsm_data: VSMData) -> float:
        """Estimate current capacity utilization percentage."""
        if not vsm_data.process_steps or vsm_data.takt_time == 0:
            return 70.0  # Default assumption

        # Calculate utilization based on takt time vs actual times
        total_time = sum(s.va_time + s.nva_time for s in vsm_data.process_steps)
        avg_time_per_step = total_time / len(vsm_data.process_steps) if vsm_data.process_steps else 0

        if avg_time_per_step > 0:
            utilization = min(95.0, (vsm_data.takt_time / avg_time_per_step) * 100)
            return max(50.0, utilization)

        return 70.0

    def _estimate_lead_time_days(self, vsm_data: VSMData) -> float:
        """Estimate lead time in days."""
        if vsm_data.total_lead_time == 0:
            return 5.0  # Default assumption

        # Convert seconds to days (assuming 8-hour work days)
        seconds_per_day = 8 * 3600
        return max(1.0, vsm_data.total_lead_time / seconds_per_day)

    def _estimate_defect_rate(self, waste_items: List[WasteItem]) -> float:
        """Estimate defect rate percentage."""
        defect_items = [w for w in waste_items if w.waste_type == WasteType.DEFECTS]
        if not defect_items:
            return 3.0  # Default assumption

        # Estimate based on defect quantities
        total_defects = sum(item.quantity for item in defect_items)
        # Rough estimate: assume 3% defect rate if defects found
        return min(15.0, max(1.0, total_defects * 0.1))

    def _get_highest_priority_proposal(
        self, proposals: List[KaizenProposal]
    ) -> Optional[KaizenProposal]:
        """Get the highest priority proposal."""
        priority_order = {"high": 0, "medium": 1, "low": 2}

        sorted_proposals = sorted(
            proposals, key=lambda p: priority_order.get(p.priority, 1)
        )

        return sorted_proposals[0] if sorted_proposals else None

    def _parse_kaizen_proposals(
        self,
        proposal_text: str,
        vsm_data: VSMData,
        waste_items: List[WasteItem],
    ) -> List[KaizenProposal]:
        """Parse Kaizen proposals from LLM text.

        Args:
            proposal_text: LLM-generated proposal text
            vsm_data: VSMData for context
            waste_items: List of WasteItem for context

        Returns:
            List of KaizenProposal objects
        """
        proposals = []

        # Look for proposal patterns in text
        if "measure" in proposal_text.lower() or "improvement" in proposal_text.lower():
            # Create a basic proposal from the text
            proposals.append(
                KaizenProposal(
                    title="Production Process Improvement",
                    description=proposal_text[:500] if len(proposal_text) > 500 else proposal_text,
                    impact="Reduced lead time and inventory",
                    effort="medium",
                    priority="high",
                    expected_improvement={
                        "lead_time_reduction": 0.20,
                        "inventory_reduction": 0.30,
                        "va_time_improvement": 0.10,
                    },
                )
            )

        return proposals

    def _generate_fallback_proposals(
        self,
        vsm_data: VSMData,
        waste_items: List[WasteItem],
        bottlenecks: List[Bottleneck],
    ) -> List[KaizenProposal]:
        """Generate fallback proposals when LLM parsing fails.

        Args:
            vsm_data: VSMData object
            waste_items: List of WasteItem objects
            bottlenecks: List of Bottleneck objects

        Returns:
            List of KaizenProposal objects
        """
        proposals = []

        # Analyze waste types and create targeted proposals
        waste_types_present = {w.waste_type for w in waste_items}

        # Proposal 1: Address waiting waste
        if WasteType.WAITING in waste_types_present:
            proposals.append(
                KaizenProposal(
                    title="Reduce Wait Times Between Operations",
                    description="Implement better scheduling and coordination to reduce wait times between operations. Use cross-training to balance workload.",
                    impact="20-30% reduction in wait times",
                    effort="medium",
                    priority="high",
                    expected_improvement={
                        "lead_time_reduction": 0.20,
                        "inventory_reduction": 0.10,
                        "va_time_improvement": 0.05,
                    },
                )
            )

        # Proposal 2: Address inventory waste
        if WasteType.INVENTORY in waste_types_present:
            proposals.append(
                KaizenProposal(
                    title="Implement Kanban Pull System",
                    description="Introduce Kanban cards to limit WIP and create pull-based production flow between stations.",
                    impact="30-40% reduction in inventory",
                    effort="medium",
                    priority="high",
                    expected_improvement={
                        "lead_time_reduction": 0.10,
                        "inventory_reduction": 0.35,
                        "va_time_improvement": 0.05,
                    },
                )
            )

        # Proposal 3: Address transport waste
        if WasteType.TRANSPORT in waste_types_present:
            proposals.append(
                KaizenProposal(
                    title="Optimize Material Flow Layout",
                    description="Redesign production layout to minimize material movement and transport between operations.",
                    impact="15-25% reduction in transport time",
                    effort="high",
                    priority="medium",
                    expected_improvement={
                        "lead_time_reduction": 0.15,
                        "inventory_reduction": 0.15,
                        "va_time_improvement": 0.05,
                    },
                )
            )

        # Proposal 4: Address defect waste
        if WasteType.DEFECTS in waste_types_present:
            proposals.append(
                KaizenProposal(
                    title="Quality Improvement Program",
                    description="Implement poka-yoke (mistake-proofing) fixtures and enhanced QC at bottleneck operations.",
                    impact="30-50% reduction in defects",
                    effort="medium",
                    priority="high",
                    expected_improvement={
                        "lead_time_reduction": 0.05,
                        "inventory_reduction": 0.10,
                        "va_time_improvement": 0.15,
                    },
                )
            )

        # Proposal 5: Bottleneck relief
        if bottlenecks:
            # Focus on the highest severity bottleneck
            top_bottleneck = bottlenecks[0]
            proposals.append(
                KaizenProposal(
                    title=f"Address Bottleneck at {top_bottleneck.location}",
                    description=f"Investigate and resolve the bottleneck at {top_bottleneck.location}. Root cause: {top_bottleneck.root_cause}",
                    impact=f"Relieve {top_bottleneck.location} constraint to improve overall throughput",
                    effort="high",
                    priority=top_bottleneck.severity,
                    expected_improvement={
                        "lead_time_reduction": 0.25,
                        "inventory_reduction": 0.20,
                        "va_time_improvement": 0.15,
                    },
                )
            )

        # Default proposal if none created
        if not proposals:
            proposals.append(
                KaizenProposal(
                    title="Continuous Improvement Program",
                    description="Establish regular Kaizen events to drive ongoing process improvement and waste elimination.",
                    impact="Sustained improvement culture",
                    effort="low",
                    priority="medium",
                    expected_improvement={
                        "lead_time_reduction": 0.15,
                        "inventory_reduction": 0.20,
                        "va_time_improvement": 0.10,
                    },
                )
            )

        return proposals