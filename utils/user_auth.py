import streamlit as st
import hashlib
from datetime import datetime
from utils.supabase_client import SupabaseDB

class UserAuth:
    def __init__(self):
        self.db = SupabaseDB()
    
    def hash_password(self, password):
        """Hash password using SHA-256"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def register_user(self, email, password, phone="", name=""):
        """Register new user"""
        try:
            # Check if user exists
            existing = self.db.client.table('users').select("*").eq('email', email).execute()
            
            if existing.data:
                return False, "User already exists"
            
            # Create user
            user_data = {
                'email': email,
                'password_hash': self.hash_password(password),
                'phone': phone,
                'name': name,
                'created_at': datetime.now().isoformat()
            }
            
            result = self.db.client.table('users').insert(user_data).execute()
            
            if result.data:
                return True, "Registration successful"
            else:
                return False, "Registration failed"
                
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def login_user(self, email, password):
        """Login user"""
        try:
            password_hash = self.hash_password(password)
            
            result = self.db.client.table('users').select("*").eq('email', email).eq('password_hash', password_hash).execute()
            
            if result.data:
                user = result.data[0]
                st.session_state['logged_in'] = True
                st.session_state['user_email'] = user['email']
                st.session_state['user_id'] = user['id']
                st.session_state['user_name'] = user.get('name', email)
                return True, "Login successful"
            else:
                return False, "Invalid email or password"
                
        except Exception as e:
            return False, f"Error: {str(e)}"
    
    def logout_user(self):
        """Logout user"""
        st.session_state['logged_in'] = False
        st.session_state['user_email'] = None
        st.session_state['user_id'] = None
        st.session_state['user_name'] = None
    
    def is_logged_in(self):
        """Check if user is logged in"""
        return st.session_state.get('logged_in', False)
    
    def get_current_user(self):
        """Get current user info"""
        if self.is_logged_in():
            return {
                'email': st.session_state.get('user_email'),
                'id': st.session_state.get('user_id'),
                'name': st.session_state.get('user_name')
            }
        return None
    
    def get_user_complaints(self):
        """Get complaints for current user"""
        if not self.is_logged_in():
            return []
        
        user_email = st.session_state.get('user_email')
        
        try:
            result = self.db.client.table('complaints').select("*").eq('email', user_email).order('created_at', desc=True).execute()
            return result.data if result.data else []
        except:
            return []

def show_auth_page():
    """Show login/register page"""
    auth = UserAuth()
    
    st.markdown("""
    <div style="text-align: center; padding: 2rem;">
        <h1>🧠 SmartNaggar AI</h1>
        <p>Please login or register to continue</p>
    </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["🔐 Login", "📝 Register"])
    
    with tab1:
        st.subheader("Login to Your Account")
        
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            if st.button("Login", use_container_width=True):
                if email and password:
                    success, message = auth.login_user(email, password)
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
                else:
                    st.warning("Please enter email and password")
        
        with col2:
            if st.button("Continue as Guest", use_container_width=True):
                st.session_state['logged_in'] = True
                st.session_state['user_email'] = f"guest_{datetime.now().timestamp()}@guest.com"
                st.session_state['user_id'] = None
                st.session_state['user_name'] = "Guest User"
                st.rerun()
    
    with tab2:
        st.subheader("Create New Account")
        
        name = st.text_input("Full Name", key="reg_name")
        email = st.text_input("Email", key="reg_email")
        phone = st.text_input("Phone (Optional)", key="reg_phone")
        password = st.text_input("Password", type="password", key="reg_password")
        password2 = st.text_input("Confirm Password", type="password", key="reg_password2")
        
        if st.button("Register", use_container_width=True):
            if not all([name, email, password, password2]):
                st.warning("Please fill all required fields")
            elif password != password2:
                st.error("Passwords do not match")
            elif len(password) < 6:
                st.error("Password must be at least 6 characters")
            else:
                success, message = auth.register_user(email, password, phone, name)
                if success:
                    st.success(message)
                    st.info("Please login with your credentials")
                else:
                    st.error(message)

def require_auth():
    """Decorator to require authentication"""
    auth = UserAuth()
    if not auth.is_logged_in():
        show_auth_page()
        st.stop()
    return auth