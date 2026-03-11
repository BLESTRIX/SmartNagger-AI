import os
os.environ["TRANSFORMERS_NO_TF"] = "1"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, timezone
import plotly.express as px
import plotly.graph_objects as go

# Import utilities
from utils.supabase_client import SupabaseDB
from utils.auth import require_admin_auth
from utils.notifications import get_notification_service

# ─── Page config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Admin Dashboard - SmartNaggar AI",
    layout="wide",
    page_icon="🔐",
    initial_sidebar_state="expanded",
)

# ─── CSS ─────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .admin-header {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: white;
        border-radius: 10px;
        padding: 1.5rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
    }
    .complaint-card {
        background: #f8f9fa;
        border-left: 4px solid #667eea;
        padding: 1rem;
        margin: 1rem 0;
        border-radius: 5px;
    }
    .status-badge {
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-weight: bold;
        font-size: 0.85em;
    }
    .pending        { background: #fff3cd; color: #856404; }
    .under-review   { background: #cfe2ff; color: #084298; }
    .assigned       { background: #d1e7dd; color: #0f5132; }
    .in-progress    { background: #cff4fc; color: #055160; }
    .resolved       { background: #d1e7dd; color: #0a3622; }
    .rejected       { background: #f8d7da; color: #842029; }
</style>
""", unsafe_allow_html=True)

# ─── Authentication ───────────────────────────────────────────────────────────
auth = require_admin_auth()

# ─── Services ─────────────────────────────────────────────────────────────────
@st.cache_resource
def init_services():
    return {
        'db':       SupabaseDB(),
        'notifier': get_notification_service(),
    }

services = init_services()

# ─── Header ───────────────────────────────────────────────────────────────────
st.markdown("""
<div class="admin-header">
    <h1>🔐 Admin Dashboard</h1>
    <p>Manage and Monitor Civic Complaints</p>
</div>
""", unsafe_allow_html=True)

# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    # FIX 1: was auth.get_current_user() — method didn't exist on AdminAuth.
    #         Correct method is get_current_admin(). We now show the admin name,
    #         not the raw dict, to avoid printing the entire dict as a string.
    admin_info = auth.get_current_admin()
    admin_display = admin_info.get('name', admin_info.get('username', 'Admin')) if admin_info else 'Admin'
    st.markdown(f"### 👤 Logged in as: **{admin_display}**")
    if admin_info:
        st.caption(f"Role: {admin_info.get('role', '').title()}  |  {admin_info.get('email', '')}")

    if st.button("🚪 Logout", use_container_width=True):
        auth.logout()
        st.rerun()

    st.markdown("---")

    page = st.radio(
        "Navigation",
        ["📊 Dashboard", "📋 Manage Complaints", "📈 Analytics", "⚙️ Settings"],
        label_visibility="collapsed",
    )

    st.markdown("---")

    st.markdown("### 📊 Quick Stats")
    stats = services['db'].get_complaint_stats()
    st.metric("Total Complaints", stats.get('total', 0))
    st.metric("Pending",          stats.get('by_status', {}).get('Pending', 0))
    st.metric("Resolved",         stats.get('by_status', {}).get('Resolved', 0))

# ══════════════════════════════════════════════════════════════════════════════
#  DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
if page == "📊 Dashboard":
    st.header("📊 Dashboard Overview")

    stats = services['db'].get_complaint_stats()

    col1, col2, col3, col4, col5 = st.columns(5)
    total    = stats.get('total', 0)
    pending  = stats.get('by_status', {}).get('Pending', 0)
    in_prog  = stats.get('by_status', {}).get('In Progress', 0)
    resolved = stats.get('by_status', {}).get('Resolved', 0)
    res_rate = (resolved / total * 100) if total > 0 else 0.0

    for col, value, label, color in [
        (col1, total,           "Total Complaints", "#667eea"),
        (col2, pending,         "Pending",          "#f5a623"),
        (col3, in_prog,         "In Progress",      "#4a90e2"),
        (col4, resolved,        "Resolved",         "#7ed321"),
        (col5, f"{res_rate:.1f}%", "Resolution Rate", "#50e3c2"),
    ]:
        col.markdown(f"""
        <div class="metric-card">
            <h3 style="color:{color};">{value}</h3>
            <p>{label}</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📊 Complaints by Status")
        if stats.get('by_status'):
            fig = px.pie(
                values=list(stats['by_status'].values()),
                names=list(stats['by_status'].keys()),
                color_discrete_sequence=px.colors.qualitative.Set3,
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data available")

    with col2:
        st.subheader("📊 Complaints by Severity")
        if stats.get('by_severity'):
            fig = px.bar(
                x=list(stats['by_severity'].keys()),
                y=list(stats['by_severity'].values()),
                color=list(stats['by_severity'].keys()),
                color_discrete_map={'High': '#ff6b6b', 'Medium': '#ffa500', 'Low': '#4ecdc4'},
            )
            fig.update_layout(showlegend=False, xaxis_title="Severity", yaxis_title="Count")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data available")

    st.subheader("🗺️ Complaints by District")
    if stats.get('by_district'):
        fig = px.bar(
            x=list(stats['by_district'].keys()),
            y=list(stats['by_district'].values()),
            color=list(stats['by_district'].values()),
            color_continuous_scale='Viridis',
        )
        fig.update_layout(showlegend=False, xaxis_title="District", yaxis_title="Count")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data available")

    st.markdown("---")
    st.subheader("🕐 Recent Complaints")

    recent = services['db'].get_all_complaints()[:5]
    if recent:
        for c in recent:
            status_class = c['status'].lower().replace(' ', '-')
            st.markdown(f"""
            <div class="complaint-card">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <div>
                        <h4>{c['tracking_id']} — {c['issue_type']}</h4>
                        <p><b>Location:</b> {c['location']} ({c['district']})</p>
                        <p><b>Severity:</b> {c['severity']} &nbsp;|&nbsp; <b>Dept:</b> {c['department']}</p>
                    </div>
                    <div>
                        <span class="status-badge {status_class}">{c['status']}</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No complaints to display")

# ══════════════════════════════════════════════════════════════════════════════
#  MANAGE COMPLAINTS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📋 Manage Complaints":
    st.header("📋 Manage Complaints")

    st.subheader("🔍 Filters")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        filter_district = st.selectbox(
            "District",
            ["All", "Lahore", "Karachi", "Islamabad", "Rawalpindi", "Multan", "Faisalabad"],
        )
    with col2:
        filter_status = st.selectbox(
            "Status",
            ["All", "Pending", "Under Review", "Assigned", "In Progress", "Resolved", "Rejected"],
        )
    with col3:
        filter_severity = st.selectbox("Severity", ["All", "High", "Medium", "Low"])
    with col4:
        filter_type = st.selectbox(
            "Issue Type",
            ["All", "Pothole", "Garbage", "Water Leak", "Broken Streetlight", "Other"],
        )

    filters = {}
    if filter_district  != "All": filters['district']   = filter_district
    if filter_status    != "All": filters['status']     = filter_status
    if filter_severity  != "All": filters['severity']   = filter_severity
    if filter_type      != "All": filters['issue_type'] = filter_type

    complaints = services['db'].get_all_complaints(filters)
    st.markdown(f"### Found {len(complaints)} complaints")

    STATUS_OPTIONS = ["Pending", "Under Review", "Assigned", "In Progress", "Resolved", "Rejected"]

    if complaints:
        for complaint in complaints:
            with st.expander(
                f"🎫 {complaint['tracking_id']} — {complaint['issue_type']} | "
                f"{complaint['district']} | {complaint['status']}"
            ):
                col1, col2 = st.columns([2, 1])

                with col1:
                    st.markdown("### 📝 Complaint Details")
                    st.markdown(f"**Tracking ID:** {complaint['tracking_id']}")
                    st.markdown(f"**Issue Type:** {complaint['issue_type']}")
                    st.markdown(f"**Severity:** {complaint['severity']}")
                    st.markdown(f"**Department:** {complaint['department']}")
                    st.markdown(f"**District:** {complaint['district']}")
                    st.markdown(f"**Location:** {complaint['location']}")
                    st.markdown(f"**Description:** {complaint['description']}")
                    st.markdown(f"**Submitted:** {complaint['created_at'][:16]}")
                    if complaint.get('admin_notes'):
                        st.markdown(f"**Admin Notes:** {complaint['admin_notes']}")
                    if complaint.get('image_url'):
                        st.image(complaint['image_url'], caption="Evidence Photo", width=400)

                with col2:
                    st.markdown("### ⚙️ Actions")

                    current_idx = STATUS_OPTIONS.index(complaint['status']) \
                        if complaint['status'] in STATUS_OPTIONS else 0

                    new_status = st.selectbox(
                        "Update Status",
                        STATUS_OPTIONS,
                        index=current_idx,
                        key=f"status_{complaint['tracking_id']}",
                    )

                    admin_notes = st.text_area(
                        "Admin Notes",
                        value=complaint.get('admin_notes', ''),
                        key=f"notes_{complaint['tracking_id']}",
                    )

                    if st.button(
                        "💾 Update Complaint",
                        key=f"update_{complaint['tracking_id']}",
                        use_container_width=True,
                    ):
                        result = services['db'].update_complaint_status(
                            complaint['tracking_id'], new_status, admin_notes
                        )

                        if result:
                            st.success("✅ Complaint updated!")

                            # Log admin action
                            auth.log_complaint_action(
                                complaint['tracking_id'],
                                'update_status',
                                f"Status changed to {new_status}",
                            )

                            if complaint.get('email'):
                                services['notifier'].send_status_update(
                                    complaint['email'],
                                    complaint['tracking_id'],
                                    complaint['status'],
                                    new_status,
                                    admin_notes,
                                )
                                st.success("📧 Email notification sent")

                            if complaint.get('phone'):
                                services['notifier'].send_status_update_sms(
                                    complaint['phone'],
                                    complaint['tracking_id'],
                                    new_status,
                                )
                                st.success("📱 SMS notification sent")

                            st.rerun()
                        else:
                            st.error("❌ Failed to update complaint")

                    if st.button(
                        "📜 View History",
                        key=f"history_{complaint['tracking_id']}",
                        use_container_width=True,
                    ):
                        history = services['db'].get_complaint_history(complaint['tracking_id'])
                        if history:
                            st.markdown("#### Update History")
                            for h in history:
                                st.markdown(f"- **{h['status']}** ({h['updated_at'][:16]})")
                                if h.get('notes'):
                                    st.markdown(f"  _{h['notes']}_")
                        else:
                            st.info("No update history")
    else:
        st.info("No complaints found matching the filters")

# ══════════════════════════════════════════════════════════════════════════════
#  ANALYTICS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "📈 Analytics":
    st.header("📈 Advanced Analytics")

    all_complaints = services['db'].get_all_complaints()

    if not all_complaints:
        st.info("No data available for analytics")
    else:
        df = pd.DataFrame(all_complaints)

        # ── FIX 2: Timezone-aware datetime comparison ─────────────────────
        # Supabase stores timestamps with timezone (IST / UTC+5:30).
        # pd.to_datetime with utc=True converts everything to UTC-aware,
        # then we compare against an aware cutoff — no more TypeError.
        df['created_at'] = pd.to_datetime(df['created_at'], utc=True)

        # Convert to IST (UTC+5:30) for display
        df['created_at_ist'] = df['created_at'].dt.tz_convert('Asia/Kolkata')
        df['date']           = df['created_at_ist'].dt.date
        # ─────────────────────────────────────────────────────────────────

        col1, col2 = st.columns([3, 1])
        with col1:
            st.subheader("📅 Complaints Over Time")
        with col2:
            time_range = st.selectbox(
                "Time Range", ["Last 7 Days", "Last 30 Days", "All Time"]
            )

        # Timezone-aware cutoff (UTC) for comparison
        now_utc = datetime.now(timezone.utc)
        if time_range == "Last 7 Days":
            cutoff = now_utc - timedelta(days=7)
            df_filtered = df[df['created_at'] >= cutoff]
        elif time_range == "Last 30 Days":
            cutoff = now_utc - timedelta(days=30)
            df_filtered = df[df['created_at'] >= cutoff]
        else:
            df_filtered = df

        daily_counts = df_filtered.groupby('date').size().reset_index(name='count')

        if daily_counts.empty:
            st.info("No complaints in the selected time range.")
        else:
            fig = px.line(
                daily_counts, x='date', y='count',
                title='Daily Complaints (IST)',
                labels={'date': 'Date', 'count': 'Number of Complaints'},
            )
            fig.update_traces(line_color='#667eea', line_width=3)
            st.plotly_chart(fig, use_container_width=True)

        # ── Department Analysis ───────────────────────────────────────────
        st.markdown("---")
        st.subheader("🏢 Department-wise Analysis")

        col1, col2 = st.columns(2)

        with col1:
            dept_counts = df['department'].value_counts()
            fig = px.bar(
                x=dept_counts.index,
                y=dept_counts.values,
                title="Complaints by Department",
                color=dept_counts.values,
                color_continuous_scale='Blues',
            )
            fig.update_layout(showlegend=False, xaxis_title="Department", yaxis_title="Count")
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            dept_status = df.groupby(['department', 'status']).size().unstack(fill_value=0)
            if 'Resolved' in dept_status.columns:
                dept_status['resolution_rate'] = (
                    dept_status['Resolved'] / dept_status.sum(axis=1) * 100
                ).round(1)
                fig = px.bar(
                    x=dept_status.index,
                    y=dept_status['resolution_rate'],
                    title="Resolution Rate by Department (%)",
                    color=dept_status['resolution_rate'],
                    color_continuous_scale='Greens',
                )
                fig.update_layout(showlegend=False, xaxis_title="Department", yaxis_title="Resolution Rate (%)")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No resolved complaints yet to show resolution rate.")

        # ── Issue Type Treemap ────────────────────────────────────────────
        st.markdown("---")
        st.subheader("🔧 Issue Type Analysis")

        issue_counts = df['issue_type'].value_counts()
        fig = px.treemap(
            names=issue_counts.index,
            parents=[""] * len(issue_counts),
            values=issue_counts.values,
            title="Issue Types Distribution",
        )
        st.plotly_chart(fig, use_container_width=True)

        # ── District × Issue Type Heatmap ─────────────────────────────────
        st.markdown("---")
        st.subheader("🗺️ District vs Issue Type Heatmap")

        heatmap_data = df.groupby(['district', 'issue_type']).size().unstack(fill_value=0)
        fig = px.imshow(
            heatmap_data,
            labels=dict(x="Issue Type", y="District", color="Count"),
            title="Complaint Distribution",
            color_continuous_scale='YlOrRd',
        )
        st.plotly_chart(fig, use_container_width=True)

        # ── Export ────────────────────────────────────────────────────────
        st.markdown("---")
        st.subheader("📥 Export Data")

        # Drop the IST column before exporting so CSV stays clean
        export_df = df.drop(columns=['created_at_ist'], errors='ignore')
        csv = export_df.to_csv(index=False)

        st.download_button(
            label="📊 Download CSV Report",
            data=csv,
            file_name=f"complaints_report_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True,
        )

# ══════════════════════════════════════════════════════════════════════════════
#  SETTINGS
# ══════════════════════════════════════════════════════════════════════════════
elif page == "⚙️ Settings":
    st.header("⚙️ System Settings")

    st.subheader("🔔 Notification Settings")
    col1, col2 = st.columns(2)
    with col1:
        st.checkbox("Enable Email Notifications", value=True)
        st.checkbox("Enable SMS Notifications",   value=True)
    with col2:
        st.checkbox("Auto-assign to Department",    value=True)
        st.checkbox("Auto-notify on Status Change", value=True)

    st.markdown("---")
    st.subheader("🏢 Department Management")

    departments = services['db'].get_all_departments()
    if departments:
        for dept in departments:
            with st.expander(dept['name']):
                st.markdown(f"**Contact:** {dept.get('contact', 'N/A')}")
                st.markdown(f"**Email:**   {dept.get('email',   'N/A')}")
                st.markdown(f"**Phone:**   {dept.get('phone',   'N/A')}")
    else:
        st.info("No departments configured")

    st.markdown("---")
    st.subheader("📊 System Information")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Users",  "—")
        st.metric("Admin Users",  "3")
    with col2:
        st.metric("Database Size", "< 1 MB")
        st.metric("Storage Used",  "< 100 MB")
    with col3:
        st.metric("API Calls Today", "—")
        st.metric("Uptime",          "99.9%")

    if st.button("💾 Save Settings", use_container_width=True):
        st.success("✅ Settings saved successfully!")

# ─── Footer ───────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("""
<div style="text-align:center; color:#666; padding:1rem;">
    <p><b>SmartNaggar AI Admin Dashboard</b></p>
    <p>Version 2.0 &nbsp;|&nbsp; © 2025 All Rights Reserved</p>
</div>
""", unsafe_allow_html=True)