"""
Medisynth Live – Patient Dashboard View
Each section renders exactly ONCE. No duplicate panels.
"""

import streamlit as st
from ui.components import (
    render_health_gauge, render_vital_card, render_bp_card,
    render_ai_reasoning, render_score_breakdown,
    render_risk_prediction, render_anomaly_score, render_detection_card,
    render_confidence_badge, create_vitals_chart, render_session_info,
    render_medisynth_panel, render_data_source_label, render_business_model,
    render_emergency_notification,
    create_score_history_chart,
)


def render_patient_view(state: dict):
    """Render the Patient dashboard — single render, no duplicates."""
    score_result = state.get("score_result")
    ai_result = state.get("ai_result")
    processed = state.get("processed")
    baseline = state.get("baseline_engine")
    deviation = state.get("deviation")
    emergency = state.get("emergency_system")
    analytics = state.get("analytics")
    synthetic = state.get("synthetic_engine")
    notif_svc = state.get("notification_service")
    location = state.get("location")
    hr_history = state.get("hr_history", [])
    spo2_history = state.get("spo2_history", [])
    hr_raw = state.get("hr_raw_history", [])
    spo2_raw = state.get("spo2_raw_history", [])
    bp_sys_history = state.get("bp_sys_history", [])
    rr_history = state.get("rr_history", [])
    temp_history = state.get("temp_history", [])
    mode = state.get("mode", "normal")

    # ── Header ──
    if analytics:
        render_session_info(analytics.session_id, analytics.get_elapsed_str(), analytics.total_readings)
    render_data_source_label(mode)

    # ── Emergency Alert (at TOP if active) ──
    if emergency and emergency.active_alert:
        render_emergency_notification(emergency.active_alert, emergency.contacts, location)
        # Show real delivery results
        if notif_svc:
            _show_delivery_log(notif_svc)
        if st.button("✕ Dismiss Alert", key="pt_dismiss"):
            emergency.dismiss_alert()
            st.rerun()

    # ── Row 1: Gauge + Chart + AI ──
    col_score, col_chart, col_ai = st.columns([1, 1.8, 1.2])

    with col_score:
        if score_result:
            render_health_gauge(
                score_result.score, score_result.status_label,
                score_result.status_color, score_result.status_emoji,
            )
            if analytics and len(analytics.score_all) > 2:
                prev, curr = analytics.score_all[-2], score_result.score
                diff = curr - prev
                arrow = "↑" if diff > 0.5 else "↓" if diff < -0.5 else "→"
                color = "#00d4aa" if diff > 0 else "#ff4757" if diff < -0.5 else "#7986cb"
                st.html(f'<div style="text-align:center; font-size:0.8rem; margin-top:-6px;"><span style="color:#7986cb;">Score: </span><span style="color:{color}; font-weight:700; font-family:\'JetBrains Mono\',monospace;">{prev:.0f} → {curr:.0f} {arrow}</span></div>')

    with col_chart:
        show_raw = st.toggle("Show Raw Data", key="pt_raw", value=False)
        if hr_history and spo2_history:
            fig = create_vitals_chart([], hr_history, spo2_history, hr_raw=hr_raw, spo2_raw=spo2_raw, show_raw=show_raw)
            st.plotly_chart(fig, use_container_width=True, key="pt_chart")

    with col_ai:
        if ai_result:
            render_ai_reasoning(ai_result.thinking_steps)

    # ── Row 2: 5 Vital Cards ──
    if processed:
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            render_vital_card("Heart Rate", processed.clean_hr, "bpm", "💓", "#00d4aa",
                              _trend(hr_history), hr_history[-20:])
        with c2:
            render_vital_card("SpO₂", processed.clean_spo2, "%", "🫁", "#a78bfa",
                              _trend(spo2_history, True), spo2_history[-20:])
        with c3:
            render_bp_card(processed.clean_bp_sys, processed.clean_bp_dia, bp_sys_history[-20:])
        with c4:
            render_vital_card("Resp Rate", processed.clean_rr, "br/min", "🌬️", "#38bdf8",
                              _trend(rr_history), rr_history[-20:])
        with c5:
            render_vital_card("Temp", processed.clean_temp, "°C", "🌡️", "#fbbf24",
                              _trend(temp_history), temp_history[-20:])

    # ── Row 3: Analysis columns ──
    col_left, col_right = st.columns([1.5, 1.5])

    with col_left:
        # Score breakdown
        if score_result:
            render_score_breakdown(score_result.breakdown)
        # Detections
        if ai_result and ai_result.detections:
            st.html('<div class="section-header">🔬 AI DETECTIONS</div>')
            for det in ai_result.detections:
                render_detection_card(det)
        # Risk prediction
        if ai_result and ai_result.risk_prediction:
            render_risk_prediction(ai_result.risk_prediction)

    with col_right:
        # Anomaly + Score trend
        if ai_result:
            render_anomaly_score(ai_result.anomaly_score)
        if analytics and len(analytics.score_all) > 3:
            st.html('<div class="section-header">📈 SCORE TREND</div>')
            fig = create_score_history_chart(analytics.score_all[-60:])
            st.plotly_chart(fig, use_container_width=True, key="pt_score_chart")
        # Medisynth panel
        if synthetic and analytics:
            render_medisynth_panel(synthetic, analytics, mode)
        # Baseline deviation
        if baseline and baseline.has_baseline() and deviation and processed:
            _show_baseline(baseline, deviation, processed)
        # Confidence
        if processed:
            render_confidence_badge(processed.confidence, processed.noise_level)

    # ── Bottom: Business Model (ONCE) ──
    render_business_model()


def _show_delivery_log(notif_svc):
    results = notif_svc.get_last_results(5)
    if not results:
        return
    items = ""
    for r in results:
        color = "#00d4aa" if r.success else "#ff4757"
        if r.success:
            txt = f"✔ {r.provider} — {r.message_preview[:45]}"
        else:
            txt = f"✕ {r.error[:45]}"
        items += f'<div style="display:flex; justify-content:space-between; padding:3px 0; font-size:0.7rem; border-bottom:1px solid rgba(255,255,255,0.03);"><span style="color:#c5cae9;">{r.recipient}</span><span style="color:{color};">{txt}</span></div>'
    st.html(f'<div style="background:rgba(15,20,40,0.4); border:1px solid rgba(255,255,255,0.06); border-radius:10px; padding:10px; margin:6px 0;"><div style="color:#7986cb; font-size:0.65rem; font-weight:600; letter-spacing:1px; margin-bottom:4px;">📡 DELIVERY LOG</div>{items}</div>')


def _show_baseline(baseline, deviation, processed):
    bl = baseline.baseline
    hr_dev = processed.clean_hr - bl.hr_mean
    hr_color = "#ff4757" if abs(deviation.hr_deviation_pct) > 30 else "#ffb347" if abs(deviation.hr_deviation_pct) > 15 else "#00d4aa"
    spo2_dev = processed.clean_spo2 - bl.spo2_mean
    spo2_color = "#ff4757" if abs(deviation.spo2_deviation_pct) > 5 else "#ffb347" if abs(deviation.spo2_deviation_pct) > 3 else "#00d4aa"
    st.html(f"""
    <div class="glass-card">
        <div class="section-header">📊 BASELINE DEVIATION</div>
        <div style="font-size:0.75rem;">
            <div style="display:flex; justify-content:space-between; padding:3px 0;"><span style="color:#7986cb;">HR</span><span style="color:{hr_color}; font-weight:700; font-family:'JetBrains Mono',monospace;">{bl.hr_mean:.0f} → {processed.clean_hr:.0f} ({deviation.hr_deviation_pct:+.1f}%)</span></div>
            <div style="display:flex; justify-content:space-between; padding:3px 0;"><span style="color:#7986cb;">SpO₂</span><span style="color:{spo2_color}; font-weight:700; font-family:'JetBrains Mono',monospace;">{bl.spo2_mean:.1f} → {processed.clean_spo2:.1f} ({deviation.spo2_deviation_pct:+.1f}%)</span></div>
        </div>
    </div>
    """)


def _trend(data, invert=False):
    if len(data) < 3:
        return "→ Stable"
    diff = data[-1] - data[-5] if len(data) >= 5 else data[-1] - data[0]
    if invert:
        diff = -diff
    return "↑ Rising" if diff > 1 else "↓ Falling" if diff < -1 else "→ Stable"
