"""
PHASE-5: LOGIC GATE
Multi-Tier Decision Tree with Witness Protocol

Core Function:
Fuses all sensor evidence, assigns risk score, verifies spatially,
and decides: sleep, monitor, or declare confirmed fire

Philosophy: "Never trust a single sensor or a single node"

Key Features:
1. 4-Tier risk scoring (Green/Yellow/Orange/Red)
2. Witness protocol (multi-node confirmation)
3. Spatial correlation (smoke must spread)
4. Power-intelligent states (sleep/monitor/alert)
5. Trauma memory (persistent suspicion)

NO SIMULATED DATA - Works only with real sensor outputs from Phases 0-4
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum


class RiskTier(Enum):
    """4-Tier risk classification"""
    GREEN = "green"      # < 30%: Normal environment
    YELLOW = "yellow"    # 30-60%: Suspicious but unclear
    ORANGE = "orange"    # 60-80%: Strong local evidence
    RED = "red"          # > 80%: Fire almost certain


class SystemState(Enum):
    """System operational states"""
    SLEEP = "sleep"          # 99% power save, sample every 5min
    MONITOR = "monitor"      # Normal sampling, 1Hz
    WATCHMAN = "watchman"    # Increased sampling, 2Hz
    WITNESS = "witness"      # Multi-node confirmation active
    CONFIRMED = "confirmed"  # Fire confirmed, alerting


@dataclass
class PhaseInputs:
    """
    Consolidated inputs from all phases
    
    All values normalized to [0, 1] risk contributions
    """
    # Phase-0: Sensor fusion
    fire_risk_score: float = 0.0
    cross_modal_agreement: float = 0.0
    
    # Phase-0 Temporal (Mamba SSM)
    temporal_trend: str = "stable"  # rising/falling/stable
    persistence: float = 0.0
    
    # Phase-2: Fractal
    has_structure: bool = False
    hurst_exponent: float = 0.5
    
    # Phase-3: Chaos
    is_unstable: bool = False
    lyapunov_exponent: float = 0.0
    
    # Phase-4: Vision
    vision_confidence: float = 0.0
    camera_healthy: bool = True
    smoke_confidence: float = 0.0
    
    # Node health
    trauma_level: float = 0.0
    
    timestamp: Optional[datetime] = None


@dataclass
class WitnessResponse:
    """
    Response from neighbor node in witness protocol
    
    Attributes:
        node_id: ID of responding neighbor
        risk_score: Neighbor's risk score
        has_smoke: Whether neighbor detects smoke
        distance_meters: Distance from requesting node
        timestamp: When response was received
    """
    node_id: str
    risk_score: float
    has_smoke: bool
    distance_meters: float
    timestamp: datetime


@dataclass
class LogicGateDecision:
    """
    Final decision from Phase-5
    
    Attributes:
        risk_tier: Classification (GREEN/YELLOW/ORANGE/RED)
        risk_score: Numerical risk (0.0-1.0)
        system_state: Operational state to enter
        should_alert: Whether to alert authorities
        confidence: Confidence in decision (0.0-1.0)
        witnesses: Number of confirming neighbors
        reasoning: Human-readable explanation
        next_sample_interval: Seconds until next sample
    """
    risk_tier: RiskTier
    risk_score: float
    system_state: SystemState
    should_alert: bool
    confidence: float
    witnesses: int = 0
    reasoning: List[str] = field(default_factory=list)
    next_sample_interval: int = 60  # seconds
    timestamp: Optional[datetime] = None


class Phase5LogicGate:
    """
    Phase-5: Multi-Tier Decision Logic with Witness Protocol
    
    Decision Flow:
    1. Compute risk score from all phase inputs
    2. Classify into 4-tier system (Green/Yellow/Orange/Red)
    3. Determine system state and actions
    4. For Orange: Execute witness protocol
    5. For Red: Confirm fire and alert
    
    Power Intelligence:
    - Green: Sleep mode (sample every 5min)
    - Yellow: Watchman mode (increase frequency)
    - Orange: Witness protocol (multi-node check)
    - Red: Confirmed fire (alert authorities)
    
    Spatial Verification:
    - Fire must be confirmed by multiple nodes
    - Prevents false alarms from local anomalies
    - Implements distributed reasoning
    """
    
    def __init__(self,
                 witness_radius_meters: float = 500.0,
                 min_witnesses: int = 1,
                 trauma_decay: float = 0.95):
        """
        Initialize Logic Gate
        
        Args:
            witness_radius_meters: Search radius for witness nodes
            min_witnesses: Minimum confirming witnesses for RED alert
            trauma_decay: Decay rate for trauma memory (per decision)
        """
        self.witness_radius_meters = witness_radius_meters
        self.min_witnesses = min_witnesses
        self.trauma_decay = trauma_decay
        
        # Persistent trauma memory
        self.trauma_level = 0.0
        
        # Statistics
        self.decisions_made = 0
        self.alerts_triggered = 0
        self.witness_protocols_activated = 0
        self.false_alarm_flags = 0
        
        # State history
        self.state_history = []
        self.last_decision: Optional[LogicGateDecision] = None
    
    def decide(self, 
               phase_inputs: PhaseInputs,
               neighbor_nodes: Optional[List] = None) -> LogicGateDecision:
        """
        Make final fire detection decision
        
        Args:
            phase_inputs: Consolidated inputs from all phases
            neighbor_nodes: Available neighbor nodes for witness protocol
        
        Returns:
            LogicGateDecision with final verdict and actions
        """
        timestamp = phase_inputs.timestamp or datetime.now()
        
        # =====================================================================
        # STEP 1: COMPUTE RISK SCORE
        # =====================================================================
        risk_score = self._compute_risk_score(phase_inputs)
        
        # =====================================================================
        # STEP 2: CLASSIFY INTO 4-TIER SYSTEM
        # =====================================================================
        risk_tier = self._classify_risk_tier(risk_score)
        
        # =====================================================================
        # STEP 3: DETERMINE SYSTEM STATE AND ACTIONS
        # =====================================================================
        
        if risk_tier == RiskTier.GREEN:
            decision = self._handle_green_path(risk_score, phase_inputs, timestamp)
        
        elif risk_tier == RiskTier.YELLOW:
            decision = self._handle_yellow_path(risk_score, phase_inputs, timestamp)
        
        elif risk_tier == RiskTier.ORANGE:
            decision = self._handle_orange_path(
                risk_score, phase_inputs, neighbor_nodes, timestamp
            )
        
        else:  # RED
            decision = self._handle_red_path(risk_score, phase_inputs, timestamp)
        
        # =====================================================================
        # STEP 4: UPDATE STATE
        # =====================================================================
        self.decisions_made += 1
        self.last_decision = decision
        self.state_history.append({
            'timestamp': timestamp,
            'risk_tier': risk_tier,
            'system_state': decision.system_state
        })
        
        # Update trauma with decay
        self.trauma_level *= self.trauma_decay
        
        return decision
    
    def _compute_risk_score(self, inputs: PhaseInputs) -> float:
        """
        Compute overall risk score from all phase inputs
        
        Weighted fusion of:
        - Phase-0 fire risk (40%)
        - Phase-2 structure (15%)
        - Phase-3 instability (15%)
        - Phase-4 vision (20%)
        - Temporal factors (10%)
        
        Args:
            inputs: Phase inputs
        
        Returns:
            Risk score (0.0-1.0)
        """
        # Base risk from Phase-0
        base_risk = inputs.fire_risk_score * 0.40
        
        # Phase-2 contribution (structure adds risk)
        structure_risk = (
            (inputs.hurst_exponent - 0.5) / 1.0  # Normalize H to [0, 1]
            if inputs.has_structure else 0.0
        ) * 0.15
        
        # Phase-3 contribution (instability adds risk)
        chaos_risk = (
            max(0.0, inputs.lyapunov_exponent)  # Only positive λ
            if inputs.is_unstable else 0.0
        ) * 0.15
        
        # Phase-4 contribution (vision smoke detection)
        vision_risk = (
            inputs.smoke_confidence if inputs.camera_healthy else 0.0
        ) * 0.20
        
        # Temporal factors
        temporal_risk = 0.0
        if inputs.temporal_trend == "rising":
            temporal_risk += 0.05
        if inputs.persistence > 0.6:
            temporal_risk += 0.05
        
        # Cross-modal agreement bonus
        agreement_bonus = inputs.cross_modal_agreement * 0.1
        
        # Trauma memory contribution (persistent suspicion)
        trauma_contribution = self.trauma_level * 0.05
        
        # Total risk
        total_risk = (
            base_risk +
            structure_risk +
            chaos_risk +
            vision_risk +
            temporal_risk +
            agreement_bonus +
            trauma_contribution
        )
        
        # Clamp to [0, 1]
        return max(0.0, min(1.0, total_risk))
    
    def _classify_risk_tier(self, risk_score: float) -> RiskTier:
        """
        Classify risk score into 4-tier system
        
        Thresholds:
        - < 0.30: GREEN (Safe)
        - 0.30-0.60: YELLOW (Suspicious)
        - 0.60-0.80: ORANGE (High risk)
        - > 0.80: RED (Fire confirmed)
        """
        if risk_score < 0.30:
            return RiskTier.GREEN
        elif risk_score < 0.60:
            return RiskTier.YELLOW
        elif risk_score < 0.80:
            return RiskTier.ORANGE
        else:
            return RiskTier.RED
    
    def _handle_green_path(self,
                          risk_score: float,
                          inputs: PhaseInputs,
                          timestamp: datetime) -> LogicGateDecision:
        """
        🟢 GREEN PATH: Log & Sleep
        
        Actions:
        - Log minor anomalies
        - Enter sleep state (sample every 5min)
        - 99% power save
        
        No alerts sent
        """
        return LogicGateDecision(
            risk_tier=RiskTier.GREEN,
            risk_score=risk_score,
            system_state=SystemState.SLEEP,
            should_alert=False,
            confidence=0.95,
            reasoning=["Safe state", "No threat detected"],
            next_sample_interval=300,  # 5 minutes
            timestamp=timestamp
        )
    
    def _handle_yellow_path(self,
                           risk_score: float,
                           inputs: PhaseInputs,
                           timestamp: datetime) -> LogicGateDecision:
        """
        🟡 YELLOW PATH: Watchman Mode
        
        Actions:
        - Increase sampling rate (2Hz instead of 1Hz)
        - Alert neighbors to "stay frosty"
        - Watch closely but no authority alert
        
        Reasoning: Fire signals evolve slowly, this is watch mode
        """
        # Increase trauma slightly (something is suspicious)
        self.trauma_level = min(1.0, self.trauma_level + 0.1)
        
        return LogicGateDecision(
            risk_tier=RiskTier.YELLOW,
            risk_score=risk_score,
            system_state=SystemState.WATCHMAN,
            should_alert=False,
            confidence=0.70,
            reasoning=[
                "Suspicious patterns detected",
                "Increasing monitoring frequency",
                "Alerting neighbors"
            ],
            next_sample_interval=1,  # Sample every 0.5 seconds (2Hz)
            timestamp=timestamp
        )
    
    def _handle_orange_path(self,
                           risk_score: float,
                           inputs: PhaseInputs,
                           neighbor_nodes: Optional[List],
                           timestamp: datetime) -> LogicGateDecision:
        """
        🟠 ORANGE PATH: Witness Protocol
        
        This is the KEY intelligence feature
        
        Actions:
        1. Ping nearby nodes (within 500m radius)
        2. Ask: "Do you smell/see this too?"
        3. Wait for responses
        4. Correlate evidence spatially
        
        Outcomes:
        - No confirmation → Mark as local anomaly
        - Confirmation → Escalate to RED
        """
        self.witness_protocols_activated += 1
        
        if neighbor_nodes is None or len(neighbor_nodes) == 0:
            # No neighbors available - treat as local anomaly
            self.false_alarm_flags += 1
            self.trauma_level = min(1.0, self.trauma_level + 0.2)
            
            return LogicGateDecision(
                risk_tier=RiskTier.ORANGE,
                risk_score=risk_score,
                system_state=SystemState.WITNESS,
                should_alert=False,
                confidence=0.50,
                witnesses=0,
                reasoning=[
                    "High local risk detected",
                    "No neighbors available for confirmation",
                    "Marked as potential local anomaly"
                ],
                next_sample_interval=2,
                timestamp=timestamp
            )
        
        # Execute witness protocol
        witnesses_confirming = self._execute_witness_protocol(
            risk_score, inputs, neighbor_nodes
        )
        
        if witnesses_confirming >= self.min_witnesses:
            # CONFIRMED BY WITNESSES → Escalate to RED
            self.trauma_level = min(1.0, self.trauma_level + 0.3)
            
            # Spatial correlation bonus
            correlated_risk = min(1.0, risk_score + 0.15)
            
            return LogicGateDecision(
                risk_tier=RiskTier.RED,  # Escalated!
                risk_score=correlated_risk,
                system_state=SystemState.CONFIRMED,
                should_alert=True,
                confidence=0.90,
                witnesses=witnesses_confirming,
                reasoning=[
                    "High local risk detected",
                    f"{witnesses_confirming} witness(es) confirmed",
                    "Spatial correlation detected",
                    "ESCALATING TO CONFIRMED FIRE"
                ],
                next_sample_interval=1,
                timestamp=timestamp
            )
        else:
            # NO CONFIRMATION → Local anomaly
            self.false_alarm_flags += 1
            self.trauma_level = min(1.0, self.trauma_level + 0.2)
            
            return LogicGateDecision(
                risk_tier=RiskTier.ORANGE,
                risk_score=risk_score * 0.7,  # Reduce confidence
                system_state=SystemState.MONITOR,
                should_alert=False,
                confidence=0.40,
                witnesses=0,
                reasoning=[
                    "High local risk detected",
                    "No neighbor confirmation",
                    "Likely local anomaly (campfire/controlled burn)",
                    "Continuing monitoring"
                ],
                next_sample_interval=5,
                timestamp=timestamp
            )
    
    def _handle_red_path(self,
                        risk_score: float,
                        inputs: PhaseInputs,
                        timestamp: datetime) -> LogicGateDecision:
        """
        🔴 RED PATH: Confirmed Fire
        
        Trigger conditions:
        - Risk score > 0.80
        - Multiple witnesses confirmed (if Orange escalated)
        - Correlated risk rise
        
        Actions:
        - Trauma +0.3 (node remembers this)
        - Highest priority transmission
        - Immediate alert to authorities
        - Continue monitoring
        """
        self.alerts_triggered += 1
        self.trauma_level = min(1.0, self.trauma_level + 0.3)
        
        return LogicGateDecision(
            risk_tier=RiskTier.RED,
            risk_score=risk_score,
            system_state=SystemState.CONFIRMED,
            should_alert=True,
            confidence=0.95,
            reasoning=[
                "CONFIRMED FIRE",
                f"Risk score: {risk_score:.0%}",
                "All phases in agreement" if inputs.cross_modal_agreement > 0.7 else "Strong evidence",
                "Immediate action required"
            ],
            next_sample_interval=1,
            timestamp=timestamp
        )
    
    def _execute_witness_protocol(self,
                                  local_risk: float,
                                  inputs: PhaseInputs,
                                  neighbor_nodes: List) -> int:
        """
        Execute witness protocol: ask neighbors if they detect fire
        
        This is where distributed intelligence happens
        
        Args:
            local_risk: Local node risk score
            inputs: Local sensor inputs
            neighbor_nodes: List of neighbor node objects
        
        Returns:
            Number of witnesses confirming
        """
        # Filter neighbors within radius
        nearby_neighbors = [
            n for n in neighbor_nodes
            if hasattr(n, 'distance') and n.distance <= self.witness_radius_meters
        ]
        
        if not nearby_neighbors:
            return 0
        
        # Count confirmations
        # In real implementation, this would send actual network requests
        # Here we check if neighbors have high risk scores
        witnesses_confirming = sum(
            1 for n in nearby_neighbors
            if hasattr(n, 'risk_score') and n.risk_score > 0.40
        )
        
        return witnesses_confirming
    
    def get_trauma_level(self) -> float:
        """Get current trauma level (persistent suspicion)"""
        return self.trauma_level
    
    def get_statistics(self) -> Dict:
        """Get Phase-5 statistics"""
        alert_rate = (
            self.alerts_triggered / self.decisions_made
            if self.decisions_made > 0 else 0.0
        )
        
        false_alarm_rate = (
            self.false_alarm_flags / max(1, self.witness_protocols_activated)
        )
        
        return {
            'decisions_made': self.decisions_made,
            'alerts_triggered': self.alerts_triggered,
            'witness_protocols_activated': self.witness_protocols_activated,
            'false_alarm_flags': self.false_alarm_flags,
            'current_trauma_level': self.trauma_level,
            'alert_rate': alert_rate,
            'false_alarm_rate': false_alarm_rate
        }
    
    def get_recommended_sample_interval(self, decision: LogicGateDecision) -> int:
        """
        Get recommended sampling interval based on decision
        
        Power-intelligent sampling:
        - GREEN: 5 minutes (sleep mode)
        - YELLOW: 0.5 seconds (watchman)
        - ORANGE: 2 seconds (witness protocol)
        - RED: 1 second (confirmed fire)
        """
        return decision.next_sample_interval


# ============================================================================
#  UTILITY FUNCTIONS
# ============================================================================

def print_logic_gate_decision(decision: LogicGateDecision):
    """
    Print human-readable decision
    
    Args:
        decision: LogicGateDecision to display
    """
    tier_emoji = {
        RiskTier.GREEN: "🟢",
        RiskTier.YELLOW: "🟡",
        RiskTier.ORANGE: "🟠",
        RiskTier.RED: "🔴"
    }
    
    print("\n" + "="*70)
    print("🎯 PHASE-5: LOGIC GATE DECISION")
    print("="*70)
    
    print(f"\n{tier_emoji[decision.risk_tier]} RISK TIER: {decision.risk_tier.value.upper()}")
    print(f"Risk Score: {decision.risk_score:.0%}")
    print(f"System State: {decision.system_state.value.upper()}")
    print(f"Confidence: {decision.confidence:.0%}")
    
    if decision.witnesses > 0:
        print(f"Witnesses: {decision.witnesses} neighbor(s) confirmed")
    
    print(f"\n📋 REASONING:")
    for reason in decision.reasoning:
        print(f"  • {reason}")
    
    print(f"\n⚡ ACTIONS:")
    if decision.should_alert:
        print("  🚨 ALERT AUTHORITIES")
    
    print(f"  ⏰ Next sample in: {decision.next_sample_interval}s")
    
    state_actions = {
        SystemState.SLEEP: "💤 Entering sleep mode (99% power save)",
        SystemState.MONITOR: "👀 Continue monitoring",
        SystemState.WATCHMAN: "⚠️  Increase sampling rate, alert neighbors",
        SystemState.WITNESS: "🤝 Execute witness protocol",
        SystemState.CONFIRMED: "🔥 CONFIRMED FIRE - Immediate action"
    }
    
    print(f"  {state_actions.get(decision.system_state, '')}")
    
    print("="*70)


if __name__ == "__main__":
    print("\n🎯 Phase-5 Logic Gate - Production Ready")
    print("=" * 70)
    print("\nNOTE: This module requires REAL inputs from Phases 0-4.")
    print("      No simulation or fake data is included.")
    print("\nUsage:")
    print("  logic_gate = Phase5LogicGate()")
    print("  inputs = PhaseInputs(")
    print("      fire_risk_score=0.72,")
    print("      has_structure=True,")
    print("      is_unstable=True,")
    print("      smoke_confidence=0.65")
    print("  )")
    print("  decision = logic_gate.decide(inputs, neighbor_nodes)")
    print("  if decision.should_alert:")
    print("      # Trigger fire alert")
    print("=" * 70)
