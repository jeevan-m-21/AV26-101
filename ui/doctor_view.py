"""
Medisynth Live – Doctor Dashboard View
Advanced clinical: metrics → chart → AI + predictions → timeline → export.
"""

import streamlit as st
from ui.components import (
    render_health_gauge,
    create_vitals_chart, render_confidence_badge, render_ai_reasoning,
    render_detection_card, render_score_breakdown, render_risk_prediction,
    render_event_timeline, render_anomaly_score, create_score_history_chart,
    render_session_info, render_data_source_label,
    render_emergency_notification, render_medisynth_panel,
)


def render_doctor_view(state: dict):
    """Render the Doctor dashboard."""
    score_result = state.get("score_result")
    ai_result = state.get("ai_result")
    processed = state.get("processed")
    emergency = state.get("emergency_system")
    analytics = state.get("analytics")
    synthetic = state.get("synthetic_engine")
    location = state.get("location")
    hr_history = state.get("hr_history", [])
    spo2_history = state.get("spo2_history", [])
    hr_raw = state.get("hr_raw_history", [])
    spo2_raw = state.get("spo2_raw_history", [])
    bp_sys_history = state.get("bp_sys_history", [])
    rr_history = state.get("rr_history", [])
    temp_history = state.get("temp_history", [])
    mode = state.get("mode", "normal")

    if analytics:
        render_session_info(analytics.session_id, analytics.get_elapsed_str(), analytics.total_readings)
    render_data_source_label(mode)

    # Emergency at top
    if emergency and emergency.active_alert:
        render_emergency_notification(emergency.active_alert, emergency.contacts, location)
        if st.button("✕ Dismiss", key="doc_dismiss"):
            emergency.dismiss_alert()
            st.rerun()

    # Metrics row
    if processed:
        m1, m2, m3, m4, m5, m6 = st.columns(6)
        with m1:
            _metric("Heart Rate", f"{processed.clean_hr:.0f} bpm", _delta(hr_history), "#00d4aa")
        with m2:
            _metric("SpO₂", f"{processed.clean_spo2:.1f}%", _delta(spo2_history), "#a78bfa")
        with m3:
            _metric("BP", f"{processed.clean_bp_sys:.0f}/{processed.clean_bp_dia:.0f}", _delta(bp_sys_history), "#f472b6")
        with m4:
            _metric("Resp Rate", f"{processed.clean_rr:.0f} br/min", _delta(rr_history), "#38bdf8")
        with m5:
            _metric("Temp", f"{processed.clean_temp:.1f}°C", _delta(temp_history, ".1f"), "#fbbf24")
        with m6:
            sv = f"{score_result.score:.0f}" if score_result else "—"
            _metric("Score", sv, score_result.status_label if score_result else "", score_result.status_color if score_result else "#7986cb")

    # Chart + Gauge
    col_chart, col_gauge = st.columns([2.5, 1])
    with col_chart:
        show_raw = st.toggle("Show Raw vs Processed", key="doc_raw", value=False)
        if hr_history and spo2_history:
            fig = create_vitals_chart([], hr_history, spo2_history, hr_raw=hr_raw, spo2_raw=spo2_raw, show_raw=show_raw)
            st.plotly_chart(fig, use_container_width=True, key="doc_chart")
    with col_gauge:
        if score_result:
            render_health_gauge(score_result.score, score_result.status_label, score_result.status_color, score_result.status_emoji)
        if analytics and len(analytics.score_all) > 3:
            fig = create_score_history_chart(analytics.score_all[-60:])
            st.plotly_chart(fig, use_container_width=True, key="doc_score")

    # Analysis + Timeline
    col_left, col_right = st.columns([1.5, 1.5])
    with col_left:
        if ai_result:
            render_ai_reasoning(ai_result.thinking_steps)
        if ai_result and ai_result.detections:
            for det in ai_result.detections:
                render_detection_card(det)
        if score_result:
            render_score_breakdown(score_result.breakdown)
    with col_right:
        if ai_result and ai_result.risk_prediction:
            render_risk_prediction(ai_result.risk_prediction)
        if ai_result:
            render_anomaly_score(ai_result.anomaly_score)
        if analytics:
            render_event_timeline(analytics.timeline, max_events=8)
        if processed:
            render_confidence_badge(processed.confidence, processed.noise_level)
        if synthetic and analytics:
            render_medisynth_panel(synthetic, analytics, mode)

    # Export
    if analytics:
        st.html('<div class="section-header" style="margin-top:12px;">💾 DATA EXPORT</div>')
        e1, e2 = st.columns(2)
        with e1:
            st.download_button("📥 CSV", data=analytics.generate_csv(),
                file_name=f"medisynth_{analytics.session_id}.csv", mime="text/csv", key="doc_csv")
        with e2:
            st.download_button("📋 Report", data=analytics.generate_html_report(),
                file_name=f"report_{analytics.session_id}.html", mime="text/html", key="doc_html")


def _metric(label, value, delta="", color="#00d4aa"):
    d = f'<div style="color:{color}; font-size:0.7rem; margin-top:2px;">{delta}</div>' if delta else ""
    st.html(f"""
    <div style="background:rgba(15,20,40,0.5); border:1px solid rgba(255,255,255,0.06);
        border-radius:10px; padding:10px; text-align:center;">
        <div style="color:#7986cb; font-size:0.6rem; font-weight:600; text-transform:uppercase; letter-spacing:1px;">{label}</div>
        <div style="color:#e8eaf6; font-size:1.2rem; font-weight:800; font-family:'JetBrains Mono',monospace;">{value}</div>
        {d}
    </div>
    """)


def _delta(history, fmt=".1f"):
    if len(history) < 2:
        return ""
    d = history[-1] - history[-2]
    arrow = "↑" if d > 0 else "↓" if d < 0 else "→"
    return f"{arrow} {d:{fmt}}"
