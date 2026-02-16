"""Anomaly detection service for AdTech Intelligence.

Provides rule-based anomaly detection on performance metrics.
In production, this would run as a scheduled job; here we expose
a trigger endpoint for demo purposes.
"""

from datetime import date, datetime, timedelta
from typing import Optional

from sqlmodel import Session, func, select

from ..models import (
    AnomalySeverity,
    AnomalyStatus,
    AnomalyType,
    AtAnomaly,
    AtAnomalyRule,
    AtPerformanceMetric,
    AtPlacement,
    RuleConditionType,
)


class AnomalyService:
    """Rule-based anomaly detection over campaign performance metrics."""

    def run_detection(
        self,
        db: Session,
        lookback_override: Optional[int] = None,
    ) -> list[AtAnomaly]:
        """Run all enabled anomaly rules and return newly created anomalies."""
        rules = db.exec(
            select(AtAnomalyRule).where(AtAnomalyRule.enabled == True)
        ).all()

        new_anomalies: list[AtAnomaly] = []
        for rule in rules:
            lookback = lookback_override or rule.lookback_days
            detected = self._evaluate_rule(db, rule, lookback)
            new_anomalies.extend(detected)

        if new_anomalies:
            for a in new_anomalies:
                db.add(a)
            db.commit()

        return new_anomalies

    def _evaluate_rule(
        self,
        db: Session,
        rule: AtAnomalyRule,
        lookback_days: int,
    ) -> list[AtAnomaly]:
        """Evaluate a single rule against recent metrics."""
        cutoff = date.today() - timedelta(days=lookback_days)

        if rule.condition_type == RuleConditionType.threshold:
            return self._check_threshold(db, rule, cutoff)
        elif rule.condition_type == RuleConditionType.deviation:
            return self._check_deviation(db, rule, cutoff)
        elif rule.condition_type == RuleConditionType.trend:
            return self._check_trend(db, rule, cutoff)
        return []

    def _check_threshold(
        self, db: Session, rule: AtAnomalyRule, cutoff: date
    ) -> list[AtAnomaly]:
        """Check if any metric value breaches a fixed threshold."""
        col = getattr(AtPerformanceMetric, rule.metric_name, None)
        if col is None:
            return []

        stmt = (
            select(AtPerformanceMetric)
            .where(AtPerformanceMetric.metric_date >= cutoff)
            .where(col < rule.threshold_value if rule.threshold_value > 0 else col > abs(rule.threshold_value))
            .limit(10)
        )
        violations = db.exec(stmt).all()

        anomalies = []
        for v in violations:
            anomaly = AtAnomaly(
                placement_id=v.placement_id,
                rule_id=rule.id,
                anomaly_type=AnomalyType.performance_drop,
                severity=AnomalySeverity.medium,
                title=f"{rule.name} triggered on placement {v.placement_id}",
                description=f"Metric '{rule.metric_name}' = {getattr(v, rule.metric_name)} "
                            f"breached threshold {rule.threshold_value}.",
                metric_name=rule.metric_name,
                expected_value=rule.threshold_value,
                actual_value=float(getattr(v, rule.metric_name)),
                deviation_pct=0.0,
                suggested_actions=["Review placement performance.", "Check for technical issues."],
            )
            anomalies.append(anomaly)
        return anomalies

    def _check_deviation(
        self, db: Session, rule: AtAnomalyRule, cutoff: date
    ) -> list[AtAnomaly]:
        """Check if recent metrics deviate significantly from the average."""
        col = getattr(AtPerformanceMetric, rule.metric_name, None)
        if col is None:
            return []

        avg_val = db.exec(
            select(func.avg(col)).where(AtPerformanceMetric.metric_date >= cutoff)
        ).one()
        if not avg_val:
            return []

        # Check the latest day
        latest = db.exec(
            select(AtPerformanceMetric)
            .where(AtPerformanceMetric.metric_date >= cutoff)
            .order_by(AtPerformanceMetric.metric_date.desc())
            .limit(1)
        ).first()
        if not latest:
            return []

        actual = float(getattr(latest, rule.metric_name))
        deviation = ((actual - float(avg_val)) / float(avg_val)) * 100 if avg_val else 0

        if abs(deviation) >= abs(rule.threshold_value):
            return [
                AtAnomaly(
                    placement_id=latest.placement_id,
                    rule_id=rule.id,
                    anomaly_type=AnomalyType.performance_drop if deviation < 0 else AnomalyType.impression_spike,
                    severity=AnomalySeverity.high if abs(deviation) > 50 else AnomalySeverity.medium,
                    title=f"{rule.name} — {deviation:+.1f}% deviation",
                    description=f"Metric '{rule.metric_name}' deviated {deviation:+.1f}% from the "
                                f"{rule.lookback_days}-day average ({float(avg_val):.2f} → {actual:.2f}).",
                    metric_name=rule.metric_name,
                    expected_value=round(float(avg_val), 2),
                    actual_value=actual,
                    deviation_pct=round(deviation, 2),
                    suggested_actions=["Investigate root cause.", "Compare with previous periods."],
                )
            ]
        return []

    def _check_trend(
        self, db: Session, rule: AtAnomalyRule, cutoff: date
    ) -> list[AtAnomaly]:
        """Check for a sustained upward or downward trend."""
        # Simplified: compare first half average to second half average
        col = getattr(AtPerformanceMetric, rule.metric_name, None)
        if col is None:
            return []

        midpoint = cutoff + timedelta(days=rule.lookback_days // 2)

        first_half = db.exec(
            select(func.avg(col)).where(
                AtPerformanceMetric.metric_date >= cutoff,
                AtPerformanceMetric.metric_date < midpoint,
            )
        ).one()
        second_half = db.exec(
            select(func.avg(col)).where(AtPerformanceMetric.metric_date >= midpoint)
        ).one()

        if not first_half or not second_half:
            return []

        change_pct = ((float(second_half) - float(first_half)) / float(first_half)) * 100

        if (rule.threshold_value < 0 and change_pct <= rule.threshold_value) or \
           (rule.threshold_value > 0 and change_pct >= rule.threshold_value):
            return [
                AtAnomaly(
                    rule_id=rule.id,
                    anomaly_type=AnomalyType.conversion_decline if change_pct < 0 else AnomalyType.impression_spike,
                    severity=AnomalySeverity.high,
                    title=f"{rule.name} — {change_pct:+.1f}% trend",
                    description=f"Metric '{rule.metric_name}' shows a {change_pct:+.1f}% trend "
                                f"over {rule.lookback_days} days.",
                    metric_name=rule.metric_name,
                    expected_value=round(float(first_half), 2),
                    actual_value=round(float(second_half), 2),
                    deviation_pct=round(change_pct, 2),
                    suggested_actions=["Review campaign strategy.", "Adjust targeting or creative."],
                )
            ]
        return []
