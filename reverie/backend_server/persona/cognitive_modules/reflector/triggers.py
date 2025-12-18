"""
Reflection Trigger Strategies

Different approaches to deciding when an agent should generate reflections.
The original paper uses an importance threshold approach where reflections
trigger when accumulated importance exceeds a threshold.

These strategies allow experimentation with alternative trigger conditions.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, TYPE_CHECKING
import datetime

if TYPE_CHECKING:
    from reverie.backend_server.models import Memory


@dataclass(frozen=True)
class ReflectionContext:
    """
    Immutable context for reflection trigger decisions.
    
    Contains all state needed to decide whether to trigger reflection,
    without directly accessing mutable scratch state.
    """
    # Importance-based state
    importance_trigger_max: float
    importance_trigger_curr: float  # Counts down to 0
    importance_accumulated: float   # importance_ele_n in original
    
    # Time-based state  
    current_time: datetime.datetime
    last_reflection_time: Optional[datetime.datetime] = None
    
    # Event-based state
    total_events: int = 0
    total_thoughts: int = 0
    events_since_reflection: int = 0
    thoughts_since_reflection: int = 0
    
    # Memory state
    has_memories: bool = True


@dataclass
class TriggerResult:
    """
    Result of a reflection trigger check.
    
    Provides information about whether to reflect and what reset actions to take.
    """
    should_reflect: bool
    reset_importance_counter: bool = False
    reset_event_counter: bool = False
    reason: str = ""  # Explanation for logging/debugging


class ReflectionTrigger(ABC):
    """
    Abstract base class for reflection trigger strategies.
    
    Determines when an agent should generate reflections from their experiences.
    Different implementations enable experimentation with alternative triggering
    conditions beyond the original importance threshold approach.
    
    Example usage:
        trigger = ImportanceThresholdTrigger()
        context = ReflectionContext(importance_trigger_max=150, ...)
        result = trigger.check(context)
        if result.should_reflect:
            run_reflection()
    """
    
    @abstractmethod
    def check(self, context: ReflectionContext) -> TriggerResult:
        """
        Check if reflection should be triggered.
        
        Args:
            context: Immutable context with current state.
            
        Returns:
            TriggerResult indicating whether to reflect.
        """
        pass


class ImportanceThresholdTrigger(ReflectionTrigger):
    """
    Original paper's trigger: reflect when accumulated importance exceeds threshold.
    
    The agent accumulates importance from experiences. When importance_trigger_curr
    counts down to 0 or below, reflection is triggered and the counter resets to
    importance_trigger_max.
    
    Formula: trigger when importance_trigger_curr <= 0
    """
    
    def check(self, context: ReflectionContext) -> TriggerResult:
        # Must have memories to reflect on
        if not context.has_memories:
            return TriggerResult(
                should_reflect=False,
                reason="No memories to reflect on"
            )
        
        if context.importance_trigger_curr <= 0:
            return TriggerResult(
                should_reflect=True,
                reset_importance_counter=True,
                reason=f"Importance threshold reached (curr={context.importance_trigger_curr}, max={context.importance_trigger_max})"
            )
        
        return TriggerResult(
            should_reflect=False,
            reason=f"Importance not yet accumulated (curr={context.importance_trigger_curr})"
        )


class EventCountTrigger(ReflectionTrigger):
    """
    Trigger reflection after N events/thoughts.
    
    Simple alternative: reflect every N experiences regardless of importance.
    Useful for more regular reflection intervals.
    """
    
    def __init__(self, event_threshold: int = 50, thought_threshold: int = 20):
        """
        Args:
            event_threshold: Number of events before triggering.
            thought_threshold: Number of thoughts before triggering.
        """
        self.event_threshold = event_threshold
        self.thought_threshold = thought_threshold
    
    def check(self, context: ReflectionContext) -> TriggerResult:
        if not context.has_memories:
            return TriggerResult(should_reflect=False, reason="No memories")
        
        events_exceeded = context.events_since_reflection >= self.event_threshold
        thoughts_exceeded = context.thoughts_since_reflection >= self.thought_threshold
        
        if events_exceeded or thoughts_exceeded:
            reason = []
            if events_exceeded:
                reason.append(f"events={context.events_since_reflection}/{self.event_threshold}")
            if thoughts_exceeded:
                reason.append(f"thoughts={context.thoughts_since_reflection}/{self.thought_threshold}")
            
            return TriggerResult(
                should_reflect=True,
                reset_event_counter=True,
                reason=f"Event count threshold reached: {', '.join(reason)}"
            )
        
        return TriggerResult(
            should_reflect=False,
            reason=f"Counts below threshold (events={context.events_since_reflection}, thoughts={context.thoughts_since_reflection})"
        )


class TimedTrigger(ReflectionTrigger):
    """
    Trigger reflection at regular time intervals.
    
    Reflect every N simulated hours/minutes. Useful for regular
    "daily reflection" type patterns.
    """
    
    def __init__(self, interval_minutes: int = 180):
        """
        Args:
            interval_minutes: Simulated time between reflections.
        """
        self.interval = datetime.timedelta(minutes=interval_minutes)
    
    def check(self, context: ReflectionContext) -> TriggerResult:
        if not context.has_memories:
            return TriggerResult(should_reflect=False, reason="No memories")
        
        if context.last_reflection_time is None:
            # Never reflected before, but have memories
            return TriggerResult(
                should_reflect=True,
                reason="Initial reflection (no previous reflection time)"
            )
        
        elapsed = context.current_time - context.last_reflection_time
        if elapsed >= self.interval:
            return TriggerResult(
                should_reflect=True,
                reason=f"Time interval reached ({elapsed} >= {self.interval})"
            )
        
        return TriggerResult(
            should_reflect=False,
            reason=f"Time interval not reached ({elapsed} < {self.interval})"
        )


class AlwaysTrigger(ReflectionTrigger):
    """
    Always trigger reflection.
    
    Useful for testing or aggressive reflection strategies.
    """
    
    def check(self, context: ReflectionContext) -> TriggerResult:
        if not context.has_memories:
            return TriggerResult(should_reflect=False, reason="No memories")
        return TriggerResult(should_reflect=True, reason="Always trigger")


class NeverTrigger(ReflectionTrigger):
    """
    Never trigger reflection.
    
    Useful for baseline experiments without reflection.
    """
    
    def check(self, context: ReflectionContext) -> TriggerResult:
        return TriggerResult(should_reflect=False, reason="Reflection disabled")


class CompositeTrigger(ReflectionTrigger):
    """
    Combine multiple triggers with AND/OR logic.
    
    Example: Trigger when importance threshold reached OR time interval passed.
    """
    
    def __init__(self, 
                 triggers: List[ReflectionTrigger],
                 require_all: bool = False):
        """
        Args:
            triggers: List of trigger strategies to combine.
            require_all: If True, all must trigger (AND). If False, any triggers (OR).
        """
        self.triggers = triggers
        self.require_all = require_all
    
    def check(self, context: ReflectionContext) -> TriggerResult:
        if not self.triggers:
            return TriggerResult(should_reflect=False, reason="No triggers configured")
        
        results = [t.check(context) for t in self.triggers]
        triggered_results = [r for r in results if r.should_reflect]
        
        if self.require_all:
            # AND: All must trigger
            should_reflect = len(triggered_results) == len(self.triggers)
        else:
            # OR: Any can trigger
            should_reflect = len(triggered_results) > 0
        
        if should_reflect:
            reasons = [r.reason for r in triggered_results]
            return TriggerResult(
                should_reflect=True,
                reset_importance_counter=any(r.reset_importance_counter for r in triggered_results),
                reset_event_counter=any(r.reset_event_counter for r in triggered_results),
                reason=f"Composite trigger ({'+'.join(reasons)})"
            )
        
        non_triggered_reasons = [r.reason for r in results if not r.should_reflect]
        return TriggerResult(
            should_reflect=False,
            reason=f"Composite not met: {', '.join(non_triggered_reasons)}"
        )


class HighImportanceEventTrigger(ReflectionTrigger):
    """
    Trigger reflection immediately after high-importance events.
    
    Instead of accumulating importance, this triggers when any single
    event exceeds a poignancy threshold. Useful for immediate processing
    of emotionally significant events.
    """
    
    def __init__(self, 
                 poignancy_threshold: float = 8.0,
                 recent_window: int = 5):
        """
        Args:
            poignancy_threshold: Minimum poignancy to trigger.
            recent_window: Number of recent memories to check.
        """
        self.threshold = poignancy_threshold
        self.window = recent_window
    
    def check(self, context: ReflectionContext) -> TriggerResult:
        # This trigger needs access to recent memories, which isn't in context
        # In practice, you'd extend the context or pass memories directly
        # For now, we fall back to importance-based approximation
        if not context.has_memories:
            return TriggerResult(should_reflect=False, reason="No memories")
        
        # Use accumulated importance as proxy (high accumulation suggests high events)
        avg_importance = context.importance_accumulated / max(context.events_since_reflection, 1)
        if avg_importance >= self.threshold:
            return TriggerResult(
                should_reflect=True,
                reset_importance_counter=True,
                reason=f"High average importance detected ({avg_importance:.1f} >= {self.threshold})"
            )
        
        return TriggerResult(
            should_reflect=False,
            reason=f"Average importance below threshold ({avg_importance:.1f})"
        )
