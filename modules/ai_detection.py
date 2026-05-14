"""
Medisynth Live – Explainable AI Detection Engine
Advanced rule-based detection with arrhythmia analysis, multi-vital correlation,
risk prediction, and visible step-by-step reasoning.
"""

import time
import math
from dataclasses import dataclass, field
from typing import List, Optional, Dict
import numpy as np
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


@dataclass
class ThinkingStep:
    """A single reasoning step for the AI thinking panel."""
    timestamp: float
    message: str
    icon: str = "🔍"
    severity: str = "info"  # info, warning, critical


@dataclass
class Detection:
    """A detected condition with explainable evidence."""
    condition: str
    severity: str  # normal, warning, critical
    confidence: float
    evidence: List[str]
    recommendation: str
    duration_s: float = 0


@dataclass
class RiskPrediction:
    """3-minute forward risk prediction."""
    predicted_hr: float
    predicted_spo2: float
    predicted_score: float
    confidence: float
    trend_direction: str  # improving, stable, deteriorating
    time_to_critical_s: Optional[float] = None
    hr_upper: float = 0
    hr_lower: float = 0


@dataclass
class AIAnalysisResult:
    """Complete AI analysis output."""
    thinking_steps: List[ThinkingStep]
    detections: List[Detection]
    overall_status: str  # stable, monitoring, critical
    summary: str
    timestamp: float = 0
    risk_prediction: Optional[RiskPrediction] = None
    anomaly_score: float = 0.0  # 0-1 composite anomaly


class AIDetectionEngine:
    """Explainable AI engine with arrhythmia detection, multi-vital correlation,
    and 3-minute risk prediction."""

    def __init__(self):
        self.hr_history: List[float] = []
        self.spo2_history: List[float] = []
        self.bp_sys_history: List[float] = []
        self.rr_history: List[float] = []
        self.temp_history: List[float] = []
        self.timestamps: List[float] = []
        self.tachy_start: Optional[float] = None
        self.brady_start: Optional[float] = None
        self.hypoxia_start: Optional[float] = None
        self.hyper_bp_start: Optional[float] = None
        self.hypo_bp_start: Optional[float] = None
        self.tachypnea_start: Optional[float] = None
        self.fever_start: Optional[float] = None
        self.last_analysis: Optional[AIAnalysisResult] = None

    def analyze(self, hr: float, spo2: float,
                bp_sys: float = 120, bp_dia: float = 80,
                rr: float = 16, temp: float = 36.8,
                baseline_hr: Optional[float] = None,
                baseline_spo2: Optional[float] = None,
                confidence: float = 100) -> AIAnalysisResult:
        now = time.time()
        self.hr_history.append(hr)
        self.spo2_history.append(spo2)
        self.bp_sys_history.append(bp_sys)
        self.rr_history.append(rr)
        self.temp_history.append(temp)
        self.timestamps.append(now)

        # Keep bounded
        max_pts = config.HISTORY_MAX_POINTS
        for hist in [self.hr_history, self.spo2_history, self.bp_sys_history,
                     self.rr_history, self.temp_history, self.timestamps]:
            if len(hist) > max_pts:
                del hist[:-max_pts]

        steps: List[ThinkingStep] = []
        detections: List[Detection] = []

        # Step 1: Heart Rate
        steps.append(ThinkingStep(now, "Analyzing heart rate pattern…", "💓", "info"))
        hr_det = self._check_heart_rate(hr, now)
        if hr_det:
            detections.append(hr_det)
            steps.append(ThinkingStep(now, f"HR {hr:.0f} bpm — {hr_det.condition} detected", "⚠️", hr_det.severity))

        # Step 2: SpO₂
        steps.append(ThinkingStep(now, "Checking oxygen saturation levels…", "🫁", "info"))
        spo2_det = self._check_spo2(spo2, now)
        if spo2_det:
            detections.append(spo2_det)
            steps.append(ThinkingStep(now, f"SpO₂ {spo2:.1f}% — {spo2_det.condition} detected", "⚠️", spo2_det.severity))

        # Step 3: Blood Pressure
        steps.append(ThinkingStep(now, "Evaluating blood pressure…", "🩸", "info"))
        bp_det = self._check_blood_pressure(bp_sys, bp_dia, now)
        if bp_det:
            detections.append(bp_det)
            steps.append(ThinkingStep(now, f"BP {bp_sys:.0f}/{bp_dia:.0f} — {bp_det.condition}", "⚠️", bp_det.severity))

        # Step 4: Respiratory Rate
        rr_det = self._check_respiratory_rate(rr, now)
        if rr_det:
            detections.append(rr_det)
            steps.append(ThinkingStep(now, f"RR {rr:.0f} — {rr_det.condition}", "⚠️", rr_det.severity))

        # Step 5: Temperature
        temp_det = self._check_temperature(temp, now)
        if temp_det:
            detections.append(temp_det)
            steps.append(ThinkingStep(now, f"Temp {temp:.1f}°C — {temp_det.condition}", "⚠️", temp_det.severity))

        # Step 6: Baseline comparison
        if baseline_hr is not None:
            steps.append(ThinkingStep(now, "Comparing with personalized baseline…", "📊", "info"))
            dev_det = self._check_baseline_deviation(hr, spo2, baseline_hr, baseline_spo2 or 97.5)
            if dev_det:
                detections.append(dev_det)
                steps.append(ThinkingStep(now, f"Baseline deviation: {dev_det.evidence[0]}", "📈", dev_det.severity))

        # Step 7: Arrhythmia detection
        if len(self.hr_history) >= config.ARRHYTHMIA_WINDOW:
            steps.append(ThinkingStep(now, "Analyzing heart rhythm variability…", "💗", "info"))
            arr_det = self._check_arrhythmia()
            if arr_det:
                detections.append(arr_det)
                steps.append(ThinkingStep(now, f"Rhythm: {arr_det.condition}", "⚠️", arr_det.severity))

        # Step 8: Multi-vital correlation (shock)
        if len(self.hr_history) >= 5:
            steps.append(ThinkingStep(now, "Cross-correlating vital signs…", "🔗", "info"))
            shock_det = self._check_shock_pattern(hr, spo2, bp_sys)
            if shock_det:
                detections.append(shock_det)
                steps.append(ThinkingStep(now, f"Compound: {shock_det.condition}", "🚨", shock_det.severity))

        # Step 9: Trend analysis
        if len(self.hr_history) >= 5:
            steps.append(ThinkingStep(now, "Evaluating vital sign trends…", "📉", "info"))
            trend_det = self._check_trends()
            if trend_det:
                detections.append(trend_det)
                steps.append(ThinkingStep(now, f"Trend alert: {trend_det.condition}", "🔺", trend_det.severity))

        # Step 10: Risk Prediction
        risk_pred = None
        if len(self.hr_history) >= config.PREDICTION_MIN_POINTS:
            steps.append(ThinkingStep(now, "Computing 3-minute risk prediction…", "🔮", "info"))
            risk_pred = self._predict_risk()
            if risk_pred and risk_pred.trend_direction == "deteriorating":
                steps.append(ThinkingStep(now, f"Predicted: deteriorating trend ahead", "⚠️", "warning"))

        # Anomaly score
        anomaly = self._compute_anomaly_score(hr, spo2, bp_sys, rr, temp)

        # Final verdict
        overall = self._determine_overall_status(detections)
        summary = self._generate_summary(detections, hr, spo2)
        if detections:
            icon = "🔴" if overall == "critical" else "🟡"
            steps.append(ThinkingStep(now, summary, icon, overall))
        else:
            steps.append(ThinkingStep(now, "All vital signs within normal parameters ✓", "🟢", "info"))

        result = AIAnalysisResult(
            thinking_steps=steps, detections=detections,
            overall_status=overall, summary=summary, timestamp=now,
            risk_prediction=risk_pred, anomaly_score=anomaly,
        )
        self.last_analysis = result
        return result

    # ── Heart Rate ──
    def _check_heart_rate(self, hr: float, now: float) -> Optional[Detection]:
        if hr > config.TACHYCARDIA_HR_THRESHOLD:
            if self.tachy_start is None:
                self.tachy_start = now
            duration = now - self.tachy_start
            if duration >= config.SUSTAINED_DURATION_S:
                severity = "critical" if hr > 140 else "warning"
                return Detection(
                    condition="Tachycardia", severity=severity,
                    confidence=min(95, 70 + duration),
                    evidence=[f"HR {hr:.0f} bpm exceeds {config.TACHYCARDIA_HR_THRESHOLD} bpm", f"Sustained for {duration:.0f}s"],
                    recommendation="Monitor closely. Seek medical attention if persistent.",
                    duration_s=duration,
                )
            return Detection(
                condition="Elevated Heart Rate", severity="warning", confidence=60,
                evidence=[f"HR {hr:.0f} bpm — above normal range"],
                recommendation="Monitoring for sustained elevation.",
            )
        else:
            self.tachy_start = None

        if hr < config.BRADYCARDIA_HR_THRESHOLD:
            if self.brady_start is None:
                self.brady_start = now
            duration = now - self.brady_start
            if duration >= config.SUSTAINED_DURATION_S:
                return Detection(
                    condition="Bradycardia", severity="warning", confidence=min(90, 65 + duration),
                    evidence=[f"HR {hr:.0f} bpm below {config.BRADYCARDIA_HR_THRESHOLD} bpm", f"Sustained for {duration:.0f}s"],
                    recommendation="May require medical evaluation.", duration_s=duration,
                )
        else:
            self.brady_start = None
        return None

    # ── SpO₂ ──
    def _check_spo2(self, spo2: float, now: float) -> Optional[Detection]:
        if spo2 < config.HYPOXIA_SPO2_THRESHOLD:
            if self.hypoxia_start is None:
                self.hypoxia_start = now
            duration = now - self.hypoxia_start
            severity = "critical" if spo2 < 88 or duration >= config.HYPOXIA_SUSTAINED_S else "warning"
            return Detection(
                condition="Hypoxia", severity=severity,
                confidence=min(95, 70 + duration * 2),
                evidence=[f"SpO₂ {spo2:.1f}% below {config.HYPOXIA_SPO2_THRESHOLD}%", f"Duration: {duration:.0f}s"],
                recommendation="Immediate medical attention recommended.",
                duration_s=duration,
            )
        else:
            self.hypoxia_start = None
        return None

    # ── Blood Pressure ──
    def _check_blood_pressure(self, sys: float, dia: float, now: float) -> Optional[Detection]:
        if sys > config.HYPERTENSION_SYS_THRESHOLD or dia > config.HYPERTENSION_DIA_THRESHOLD:
            if self.hyper_bp_start is None:
                self.hyper_bp_start = now
            duration = now - self.hyper_bp_start
            severity = "critical" if sys > 180 or dia > 120 else "warning"
            return Detection(
                condition="Hypertension", severity=severity,
                confidence=min(90, 65 + duration),
                evidence=[f"BP {sys:.0f}/{dia:.0f} mmHg — elevated", f"Duration: {duration:.0f}s"],
                recommendation="Hypertensive crisis risk. Monitor and treat.",
                duration_s=duration,
            )
        else:
            self.hyper_bp_start = None

        if sys < config.HYPOTENSION_SYS_THRESHOLD:
            if self.hypo_bp_start is None:
                self.hypo_bp_start = now
            duration = now - self.hypo_bp_start
            severity = "critical" if sys < 80 else "warning"
            return Detection(
                condition="Hypotension", severity=severity,
                confidence=min(85, 60 + duration),
                evidence=[f"BP {sys:.0f}/{dia:.0f} mmHg — low", f"Duration: {duration:.0f}s"],
                recommendation="Risk of organ hypoperfusion. Immediate action needed.",
                duration_s=duration,
            )
        else:
            self.hypo_bp_start = None
        return None

    # ── Respiratory Rate ──
    def _check_respiratory_rate(self, rr: float, now: float) -> Optional[Detection]:
        if rr > config.TACHYPNEA_RR_THRESHOLD:
            if self.tachypnea_start is None:
                self.tachypnea_start = now
            duration = now - self.tachypnea_start
            severity = "critical" if rr > 30 else "warning"
            return Detection(
                condition="Tachypnea", severity=severity, confidence=min(85, 60 + duration),
                evidence=[f"RR {rr:.0f} breaths/min — elevated"],
                recommendation="Rapid breathing detected. Evaluate cause.",
                duration_s=duration,
            )
        else:
            self.tachypnea_start = None

        if rr < config.BRADYPNEA_RR_THRESHOLD:
            return Detection(
                condition="Bradypnea", severity="warning", confidence=70,
                evidence=[f"RR {rr:.0f} breaths/min — abnormally slow"],
                recommendation="Monitor respiratory effort.",
            )
        return None

    # ── Temperature ──
    def _check_temperature(self, temp: float, now: float) -> Optional[Detection]:
        if temp > config.FEVER_TEMP_THRESHOLD:
            if self.fever_start is None:
                self.fever_start = now
            duration = now - self.fever_start
            severity = "critical" if temp > 39.5 else "warning"
            return Detection(
                condition="Fever", severity=severity, confidence=min(90, 65 + duration),
                evidence=[f"Temperature {temp:.1f}°C — elevated"],
                recommendation="Possible infection or inflammatory response.",
                duration_s=duration,
            )
        else:
            self.fever_start = None

        if temp < config.HYPOTHERMIA_TEMP_THRESHOLD:
            return Detection(
                condition="Hypothermia", severity="critical", confidence=80,
                evidence=[f"Temperature {temp:.1f}°C — dangerously low"],
                recommendation="Immediate warming required.",
            )
        return None

    # ── Baseline Deviation ──
    def _check_baseline_deviation(self, hr, spo2, bl_hr, bl_spo2) -> Optional[Detection]:
        hr_dev = abs(hr - bl_hr) / max(bl_hr, 1) * 100
        spo2_dev = abs(spo2 - bl_spo2) / max(bl_spo2, 1) * 100
        max_dev = max(hr_dev, spo2_dev)

        if max_dev > config.DEVIATION_CRITICAL_PCT:
            return Detection(
                condition="Critical Baseline Deviation", severity="critical", confidence=85,
                evidence=[f"HR deviation: {hr_dev:.1f}%", f"SpO₂ deviation: {spo2_dev:.1f}%"],
                recommendation="Significant deviation from personal baseline detected.",
            )
        elif max_dev > config.DEVIATION_WARNING_PCT:
            return Detection(
                condition="Baseline Deviation", severity="warning", confidence=70,
                evidence=[f"HR deviation: {hr_dev:.1f}%", f"SpO₂ deviation: {spo2_dev:.1f}%"],
                recommendation="Moderate deviation from personal baseline.",
            )
        return None

    # ── Arrhythmia Detection (HRV analysis) ──
    def _check_arrhythmia(self) -> Optional[Detection]:
        window = self.hr_history[-config.ARRHYTHMIA_WINDOW:]
        if len(window) < 5:
            return None
        # Calculate HR variability as coefficient of variation
        rr_intervals = [60.0 / max(h, 30) for h in window]  # Convert HR to RR intervals
        cv = np.std(rr_intervals) / max(np.mean(rr_intervals), 0.01)

        if cv > config.HRV_IRREGULARITY_THRESHOLD:
            # Check for alternating pattern (bigeminy-like)
            diffs = np.diff(window)
            alternating = sum(1 for i in range(len(diffs) - 1) if diffs[i] * diffs[i + 1] < 0) / max(len(diffs) - 1, 1)

            severity = "critical" if cv > 0.4 else "warning"
            evidence = [
                f"HR variability CV: {cv:.3f} (threshold: {config.HRV_IRREGULARITY_THRESHOLD})",
                f"Alternating pattern score: {alternating:.0%}",
            ]
            return Detection(
                condition="Irregular Rhythm (Arrhythmia)", severity=severity,
                confidence=min(85, 55 + cv * 100),
                evidence=evidence,
                recommendation="Cardiac rhythm irregularity detected. ECG recommended.",
            )
        return None

    # ── Multi-Vital Correlation (Shock Detection) ──
    def _check_shock_pattern(self, hr, spo2, bp_sys) -> Optional[Detection]:
        if hr > config.SHOCK_HR_MIN and bp_sys < config.SHOCK_SYS_MAX and spo2 < config.SHOCK_SPO2_MAX:
            return Detection(
                condition="Shock Pattern Detected", severity="critical", confidence=90,
                evidence=[
                    f"Tachycardia (HR {hr:.0f})",
                    f"Hypotension (SYS {bp_sys:.0f})",
                    f"Hypoxemia (SpO₂ {spo2:.1f}%)",
                    "Multi-vital correlation: shock triad",
                ],
                recommendation="🚨 CRITICAL: Shock pattern identified. Immediate emergency intervention required.",
            )
        return None

    # ── Trend Analysis ──
    def _check_trends(self) -> Optional[Detection]:
        if len(self.hr_history) < 5:
            return None
        recent = self.hr_history[-8:]
        x = np.arange(len(recent))
        slope = np.polyfit(x, recent, 1)[0]
        if abs(slope) > config.TREND_SLOPE_THRESHOLD:
            direction = "increasing" if slope > 0 else "decreasing"
            return Detection(
                condition=f"Rapid HR {direction}", severity="warning", confidence=65,
                evidence=[f"HR slope: {slope:+.1f} bpm/reading", f"Over last {len(recent)} readings"],
                recommendation=f"Heart rate is rapidly {direction}.",
            )
        return None

    # ── Risk Prediction ──
    def _predict_risk(self) -> Optional[RiskPrediction]:
        n = len(self.hr_history)
        if n < config.PREDICTION_MIN_POINTS:
            return None

        recent_hr = np.array(self.hr_history[-20:])
        recent_spo2 = np.array(self.spo2_history[-20:])
        x = np.arange(len(recent_hr))

        # Linear trend extrapolation
        hr_coeffs = np.polyfit(x, recent_hr, 1)
        spo2_coeffs = np.polyfit(x, recent_spo2, 1)

        # Predict 3 min ahead (~90 readings at 2s intervals)
        future_x = len(recent_hr) + 90
        pred_hr = hr_coeffs[0] * future_x + hr_coeffs[1]
        pred_spo2 = spo2_coeffs[0] * future_x + spo2_coeffs[1]
        pred_spo2 = max(70, min(100, pred_spo2))
        pred_hr = max(30, min(220, pred_hr))

        # Confidence based on R² and data volume
        hr_residuals = recent_hr - np.polyval(hr_coeffs, x)
        hr_std = np.std(hr_residuals) if len(hr_residuals) > 1 else 10
        conf = max(30, min(85, 80 - hr_std * 2))

        # Confidence bounds
        hr_upper = pred_hr + 2 * hr_std
        hr_lower = pred_hr - 2 * hr_std

        # Rough predicted score
        hr_penalty = max(0, abs(pred_hr - 70) - 25) * 0.8
        spo2_penalty = max(0, (95 - pred_spo2)) * 4
        pred_score = max(0, min(100, 100 - hr_penalty - spo2_penalty))

        # Trend direction
        hr_slope = hr_coeffs[0]
        spo2_slope = spo2_coeffs[0]
        if hr_slope > 0.5 or spo2_slope < -0.1:
            direction = "deteriorating"
        elif hr_slope < -0.3 and spo2_slope >= 0:
            direction = "improving"
        else:
            direction = "stable"

        # Time to critical (if deteriorating)
        ttc = None
        if direction == "deteriorating" and pred_score < 40 and pred_score < 60:
            current_score = 100 - max(0, abs(recent_hr[-1] - 70) - 25) * 0.8 - max(0, (95 - recent_spo2[-1])) * 4
            if current_score > 40:
                score_slope = (pred_score - current_score) / 90  # per reading
                if score_slope < 0:
                    readings_to_critical = (40 - current_score) / score_slope
                    ttc = readings_to_critical * config.UPDATE_INTERVAL_S

        return RiskPrediction(
            predicted_hr=round(pred_hr, 1),
            predicted_spo2=round(pred_spo2, 1),
            predicted_score=round(pred_score, 0),
            confidence=round(conf, 0),
            trend_direction=direction,
            time_to_critical_s=round(ttc, 0) if ttc else None,
            hr_upper=round(hr_upper, 1),
            hr_lower=round(hr_lower, 1),
        )

    # ── Anomaly Score ──
    def _compute_anomaly_score(self, hr, spo2, bp_sys, rr, temp) -> float:
        """Composite anomaly score (0-1) using normalized deviation from healthy ranges."""
        scores = []
        scores.append(min(1.0, max(0, abs(hr - 72) - 20) / 80))
        scores.append(min(1.0, max(0, 97 - spo2) / 15))
        scores.append(min(1.0, max(0, abs(bp_sys - 120) - 15) / 60))
        scores.append(min(1.0, max(0, abs(rr - 16) - 4) / 16))
        scores.append(min(1.0, max(0, abs(temp - 36.8) - 0.5) / 2.5))
        # Weighted average
        weights = [0.3, 0.25, 0.2, 0.15, 0.1]
        return round(sum(s * w for s, w in zip(scores, weights)), 3)

    def _determine_overall_status(self, detections: List[Detection]) -> str:
        if any(d.severity == "critical" for d in detections):
            return "critical"
        if any(d.severity == "warning" for d in detections):
            return "monitoring"
        return "stable"

    def _generate_summary(self, detections: List[Detection], hr: float, spo2: float) -> str:
        if not detections:
            return f"All vitals normal — HR {hr:.0f} bpm, SpO₂ {spo2:.1f}%"
        critical = [d for d in detections if d.severity == "critical"]
        if critical:
            conditions = ", ".join(d.condition for d in critical)
            return f"⚠️ CRITICAL: {conditions} — immediate attention required"
        conditions = ", ".join(d.condition for d in detections)
        return f"⚠️ Monitoring: {conditions.lower()} detected"

    def reset(self):
        for h in [self.hr_history, self.spo2_history, self.bp_sys_history,
                  self.rr_history, self.temp_history, self.timestamps]:
            h.clear()
        self.tachy_start = None
        self.brady_start = None
        self.hypoxia_start = None
        self.hyper_bp_start = None
        self.hypo_bp_start = None
        self.tachypnea_start = None
        self.fever_start = None
        self.last_analysis = None
