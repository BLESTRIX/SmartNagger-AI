import streamlit as st
import hashlib
from datetime import datetime, timezone
from utils.supabase_client import SupabaseDB


class AdminAuth:
    def __init__(self):
        self.db = SupabaseDB()

    def hash_password(self, password: str) -> str:
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()

    def verify_admin(self, username: str, password: str):
        """Verify admin credentials from database"""
        try:
            if not self.db.client:
                st.error("Database connection not available")
                return False, None

            password_hash = self.hash_password(password)

            result = (
                self.db.client
                .table('admin_users')
                .select("*")
                .eq('username', username)
                .eq('password_hash', password_hash)
                .eq('is_active', True)
                .execute()
            )

            if result.data:
                admin = result.data[0]

                # Update last_login with a proper ISO timestamp (UTC)
                self.db.client.table('admin_users').update({
                    'last_login': datetime.now(timezone.utc).isoformat()
                }).eq('id', admin['id']).execute()

                return True, admin

            return False, None

        except Exception as e:
            st.error(f"Authentication error: {str(e)}")
            return False, None

    def login(self, username: str, password: str) -> bool:
        """Admin login — stores admin info in session state"""
        success, admin_data = self.verify_admin(username, password)

        if success and admin_data:
            st.session_state['admin_logged_in'] = True
            st.session_state['admin_username']  = username
            st.session_state['admin_id']        = admin_data['id']
            st.session_state['admin_role']      = admin_data.get('role', 'admin')
            st.session_state['admin_name']      = admin_data.get('full_name', username)
            st.session_state['admin_email']     = admin_data.get('email', '')

            self._log_activity(
                admin_data['id'], 'login', None,
                f"Admin '{username}' logged in"
            )
            return True

        return False

    def logout(self):
        """Admin logout"""
        if self.is_logged_in():
            self._log_activity(
                st.session_state.get('admin_id'),
                'logout', None,
                f"Admin '{st.session_state.get('admin_username')}' logged out"
            )

        for key in ['admin_logged_in', 'admin_username', 'admin_id',
                    'admin_role', 'admin_name', 'admin_email']:
            st.session_state[key] = None
        st.session_state['admin_logged_in'] = False

    def is_logged_in(self) -> bool:
        """Check if an admin is currently logged in"""
        return bool(st.session_state.get('admin_logged_in', False))

    def get_current_admin(self) -> dict | None:
        """
        Return a dict with the current admin's details.
        Named get_current_admin() — admin.py must call this method.
        """
        if self.is_logged_in():
            return {
                'username': st.session_state.get('admin_username'),
                'id':       st.session_state.get('admin_id'),
                'role':     st.session_state.get('admin_role'),
                'name':     st.session_state.get('admin_name'),
                'email':    st.session_state.get('admin_email'),
            }
        return None

    # Alias so that any legacy code calling get_current_user() still works
    def get_current_user(self) -> dict | None:
        return self.get_current_admin()

    def _log_activity(self, admin_id, action_type: str, tracking_id, description: str):
        """Silently log admin activity — never raises"""
        try:
            if self.db.client and admin_id:
                self.db.client.table('admin_activity_log').insert({
                    'admin_id':    admin_id,
                    'action_type': action_type,
                    'tracking_id': tracking_id,
                    'description': description,
                }).execute()
        except Exception as e:
            print(f"[activity log error] {e}")

    def log_complaint_action(self, tracking_id: str, action_type: str, description: str):
        """Log a complaint-related admin action"""
        if self.is_logged_in():
            self._log_activity(
                st.session_state.get('admin_id'),
                action_type, tracking_id, description
            )


# ─────────────────────────────────────────────────────────────────────────────

def require_admin_auth() -> AdminAuth:
    """
    Gate for admin pages.
    If not logged in, render the login form and stop execution.
    Returns the AdminAuth instance when authenticated.
    """
    auth = AdminAuth()

    if not auth.is_logged_in():
        st.markdown("""
        <div style="text-align:center; padding:2rem;">
            <h1>🔐 Admin Login</h1>
            <p>SmartNaggar AI — Administration Panel</p>
        </div>
        """, unsafe_allow_html=True)

        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("### Login to Continue")

            username = st.text_input("Username", placeholder="Enter admin username")
            password = st.text_input("Password", type="password", placeholder="Enter password")

            col_a, col_b = st.columns(2)

            with col_a:
                if st.button("🔓 Login", use_container_width=True, type="primary"):
                    if username and password:
                        if auth.login(username, password):
                            st.success("✅ Login successful!")
                            st.rerun()
                        else:
                            st.error("❌ Invalid credentials")
                    else:
                        st.warning("⚠️ Please enter username and password")

            with col_b:
                if st.button("🏠 Back to App", use_container_width=True):
                    st.switch_page("app.py")

            st.markdown("---")
            st.info("""
            **Default Admin Accounts:**
            - Username: `admin` / Password: `admin123`
            - Username: `supervisor` / Password: `super123`
            - Username: `manager` / Password: `manager123`
            """)

        st.stop()

    return auth