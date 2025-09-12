import streamlit as st
from database import DatabaseManager

def show_login_page():
    """Display simple and clean login page"""
    
    # Set page config
    st.set_page_config(
        page_title="Login - Social Listening Tool",
        page_icon="🔍",
        layout="centered"
    )
    
    # Simple CSS for clean design
    st.markdown("""
    <style>
    .main .block-container {
        padding: 2rem;
        max-width: 800px;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)
    
    # Simple header
    st.markdown("""
    <div style="text-align: center; margin-bottom: 3rem;">
        <h1 style="color: #20B2AA; font-size: 2.5rem; margin-bottom: 0.5rem;">🔍 Social Listening Tool</h1>
        <p style="color: #666; font-size: 1.1rem;">Monitor and analyze social media content</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Create tabs for login and registration
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        st.markdown("### Login to your account")
        
        # Simple login form
        with st.form("login_form", clear_on_submit=True):
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            
            col1, col2 = st.columns([1, 1])
            with col1:
                remember_me = st.checkbox("Remember me")
            with col2:
                st.markdown("")
                st.markdown("[Forgot Password?](#)")
            
            login_button = st.form_submit_button("Login", type="primary", use_container_width=True)
            
            if login_button:
                if username and password:
                    db = DatabaseManager()
                    login_result = db.check_login(username, password)
                    if login_result['success']:
                        st.session_state.logged_in = True
                        st.session_state.username = username
                        st.session_state.user_id = login_result['user_id']
                        st.session_state.user_role = login_result['role']
                        st.success("✅ Login successful!")
                        st.rerun()
                    else:
                        st.error(f"❌ {login_result['message']}!")
                else:
                    st.warning("⚠️ Please enter both username and password!")
    
    with tab2:
        st.markdown("### Create a new account")
        
        # Simple registration form
        with st.form("register_form", clear_on_submit=True):
            new_username = st.text_input("Username", placeholder="Choose a username")
            new_password = st.text_input("Password", type="password", placeholder="Choose a password")
            confirm_password = st.text_input("Confirm Password", type="password", placeholder="Confirm your password")
            email = st.text_input("Email (optional)", placeholder="Enter your email")
            
            register_button = st.form_submit_button("Register", type="primary", use_container_width=True)
            
            if register_button:
                if new_username and new_password and confirm_password:
                    if new_password == confirm_password:
                        db = DatabaseManager()
                        if db.user_exists(new_username):
                            st.error("❌ Username already exists!")
                        else:
                            if db.create_user(new_username, new_password, email):
                                st.success("✅ Registration successful! You can now login.")
                            else:
                                st.error("❌ Registration failed! Please try again.")
                    else:
                        st.error("❌ Passwords do not match!")
                else:
                    st.warning("⚠️ Please fill in all required fields!")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; font-size: 0.9rem;">
        <p>AI-powered translation and summarization for content</p>
    </div>
    """, unsafe_allow_html=True)

def check_login_status():
    """Check if user is logged in"""
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    
    if not st.session_state.logged_in:
        show_login_page()
        return False
    else:
        return True

def show_logout():
    """Show logout button in sidebar with beautiful styling"""
    if st.session_state.logged_in:
        # User info with beautiful styling
        st.sidebar.markdown(f"""
        <div class="user-info">
            <div style="display: flex; align-items: center; margin-bottom: 10px;">
                <span style="font-size: 24px; margin-right: 8px;">👤</span>
                <span style="font-weight: bold; font-size: 16px;">{st.session_state.username}</span>
            </div>
            <div style="font-size: 12px; opacity: 0.9;">Logged in successfully</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Logout button with beautiful styling
        if st.sidebar.button("🚪 Logout", key="logout_btn"):
            st.session_state.logged_in = False
            st.session_state.username = None
            st.rerun()

def main():
    """Main function to test login UI"""
    st.set_page_config(page_title="Login Test", layout="wide")
    
    if check_login_status():
        st.success("🎉 You are logged in!")
        show_logout()
        st.write("This is the main application area.")

if __name__ == "__main__":
    main() 