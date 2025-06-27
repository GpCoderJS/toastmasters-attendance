import streamlit as st
import gspread
from datetime import datetime, timedelta
from google.oauth2.service_account import Credentials
import random
import string
import base64

# Page config with custom styling
st.set_page_config(
    page_title="Koramangala Toastmasters Club", 
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS for professional UI
st.markdown("""
<style>
/* Main theme colors - Modern Dark Blue */
:root {
    --primary-blue: #06B6D4;
    --secondary-blue: #0891B2;
    --light-blue: #E0F7FA;
    --dark-blue: #0F172A;
    --medium-blue: #1E40AF;
    --white: #FFFFFF;
    --light-gray: #F8FAFC;
    --text-dark: #1F2937;
}

/* Body background with dark gradient */
.stApp {
    background: linear-gradient(135deg, #0F172A 0%, #1E40AF 100%);
    min-height: 100vh;
}

/* Hide Streamlit elements */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
.stDeployButton {display: none;}

/* Custom header with logo */
.header-container {
    display: flex;
    justify-content: center;
    align-items: center;
    padding: 1rem 0;
    margin-bottom: 2rem;
}

.logo-title {
    display: flex;
    align-items: center;
    gap: 1rem;
}

.logo-title h1 {
    color: var(--white);
    margin: 0;
    font-size: 1.8rem;
    font-weight: 600;
    text-shadow: 0 2px 4px rgba(0,0,0,0.3);
}

/* Login form styling - REMOVED WHITE BOX */
.login-container {
    background: transparent;
    padding: 2rem;
    border-radius: 0;
    box-shadow: none;
    border: none;
    max-width: 400px;
    margin: 0 auto;
}

.login-header {
    text-align: center;
    margin-bottom: 2rem;
}

.login-header h2 {
    color: var(--white);
    margin-bottom: 0.5rem;
    font-size: 1.5rem;
    text-shadow: 0 2px 4px rgba(0,0,0,0.3);
}

.login-header p {
    color: rgba(255, 255, 255, 0.8);
    font-size: 0.9rem;
}

/* Section headers */
.section-header {
    color: var(--white);
    font-size: 1.2rem;
    font-weight: 600;
    margin: 1.5rem 0 1rem 0;
    text-shadow: 0 2px 4px rgba(0,0,0,0.3);
}

/* Input styling */
.stTextInput > div > div > input {
    border: 2px solid rgba(255, 255, 255, 0.3);
    border-radius: 8px;
    padding: 0.75rem;
    font-size: 1rem;
    transition: border-color 0.3s ease;
    background: rgba(255, 255, 255, 0.9);
    color: var(--text-dark);
}

.stTextInput > div > div > input:focus {
    border-color: var(--primary-blue);
    box-shadow: 0 0 0 3px rgba(6, 182, 212, 0.3);
    background: var(--white);
}

/* Button styling - Updated for new colors */
.stButton > button {
    background: linear-gradient(135deg, var(--primary-blue), var(--secondary-blue));
    color: white;
    border: none;
    border-radius: 8px;
    font-size: 1rem;
    font-weight: 600;
    padding: 0.75rem 2rem;
    width: 100%;
    transition: all 0.3s ease;
    margin-top: 1rem;
}

.stButton > button:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(6, 182, 212, 0.4);
}

/* Login type buttons - side by side - FIXED for mobile */
.login-type-buttons {
    display: flex !important;
    gap: 0.5rem;
    margin-bottom: 1.5rem;
}

.login-type-buttons .stButton {
    flex: 1 !important;
    min-width: 0 !important;
}

.login-type-buttons .stButton > button {
    margin-top: 0;
    padding: 0.6rem 1rem;
    font-size: 0.9rem;
    width: 100% !important;
}

/* Active tab styling - Updated colors */
.active-tab button {
    background: var(--primary-blue) !important;
    color: white !important;
}

.inactive-tab button {
    background: rgba(255, 255, 255, 0.2) !important;
    color: var(--white) !important;
    border: 1px solid rgba(255, 255, 255, 0.3) !important;
}

/* Success/Error messages */
.success-message {
    background: rgba(232, 245, 232, 0.9);
    border: 1px solid #4CAF50;
    color: #2E7D32;
    padding: 1rem;
    border-radius: 8px;
    margin: 1rem 0;
}

.error-message {
    background: rgba(255, 235, 238, 0.9);
    border: 1px solid #F44336;
    color: #C62828;
    padding: 1rem;
    border-radius: 8px;
    margin: 1rem 0;
}

/* Admin panel styling - MOVED TO FOOTER */
.admin-panel {
    background: rgba(255, 255, 255, 0.95);
    padding: 1.5rem;
    border-radius: 12px;
    margin: 2rem auto 1rem auto;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
    backdrop-filter: blur(10px);
    max-width: 500px;
}

/* Footer styling */
.footer {
    text-align: center;
    padding: 2rem 0 1rem 0;
    color: rgba(255, 255, 255, 0.8);
    font-size: 0.9rem;
}

/* Mobile responsive */
@media (max-width: 768px) {
    .header-container {
        flex-direction: column;
        gap: 1rem;
        text-align: center;
    }
    
    .logo-title h1 {
        font-size: 1.5rem;
    }
    
    .login-container {
        margin: 0 1rem;
        padding: 1.5rem;
    }
    
    .login-type-buttons {
        flex-direction: row !important;
        gap: 0.5rem;
    }
    
    .login-type-buttons .stButton {
        flex: 1 !important;
        min-width: 0 !important;
    }
    
    .login-type-buttons .stButton > button {
        font-size: 0.85rem;
        padding: 0.5rem 0.5rem;
        white-space: nowrap;
    }
    
    .admin-panel {
        margin: 2rem 1rem 1rem 1rem;
        padding: 1.25rem;
    }
}

/* Remove default Streamlit container padding */
.block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
}

/* Hide any white background containers */
.stContainer {
    background: transparent !important;
}

/* Ensure forms have proper styling */
.stForm {
    background: transparent;
    border: none;
    padding: 0;
}

/* Input labels styling */
.stTextInput > label {
    color: rgba(255, 255, 255, 0.9) !important;
    font-weight: 500 !important;
}
</style>
""", unsafe_allow_html=True)

# Google Sheets Auth
SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

@st.cache_resource
def get_logo_base64():
    """Convert logo to base64 for embedding"""
    try:
        with open("logo.png", "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except FileNotFoundError:
        return None

@st.cache_resource
def init_google_sheets():
    try:

        
        creds = Credentials.from_service_account_file(st.secrets["google_service_account"], scopes=SCOPE)
        client = gspread.authorize(creds)   
        sheet = client.open("Toastmasters Attendance")
        return sheet
    except Exception as e:
        st.error(f"Failed to connect to Google Sheets: {str(e)}")
        return None

def get_meeting_code(sheet):
    """Get active meeting code"""
    try:
        meetingcode_sheet = sheet.worksheet("MeetingCode")
        code_data = meetingcode_sheet.get_all_records()
        
        if code_data:
            expiry_time = datetime.strptime(code_data[0]["Expiry Timestamp"], "%Y-%m-%d %H:%M:%S")
            if datetime.now() <= expiry_time:
                return code_data[0]["Meeting Code"]
    except Exception:
        pass
    return None

def create_or_update_attendance_member(sheet, name, phone, today):
    """Create or update attendance member record"""
    try:
        matrix_sheet = sheet.worksheet("Attendance_Member")
        matrix_data = matrix_sheet.get_all_values()
        
        # If sheet is empty, create headers
        if not matrix_data:
            matrix_sheet.update("A1:C1", [["Name", "Phone", today]])
            matrix_sheet.update("A2:C2", [[name, phone, "1"]])
            return True
            
        headers = matrix_data[0] if matrix_data else ["Name", "Phone"]
        
        # Add today's date as a new column if not present
        if today not in headers:
            matrix_sheet.update_cell(1, len(headers) + 1, today)
            headers.append(today)
        
        # Look for existing member record
        member_found = False
        for idx, row in enumerate(matrix_data[1:], start=2):
            if len(row) > 1 and row[1] == phone:  # Match by phone number
                # Update existing member
                col_index = headers.index(today) + 1
                matrix_sheet.update_cell(idx, col_index, "1")
                member_found = True
                break
        
        # If member not found, create new record
        if not member_found:
            new_row = [name, phone] + [""] * (len(headers) - 2)
            col_index = headers.index(today)
            new_row[col_index] = "1"
            matrix_sheet.append_row(new_row)
            
        return True
    except Exception as e:
        st.error(f"Error updating attendance member sheet: {str(e)}")
        return False

def generate_meeting_code(sheet):
    """Generate new meeting code"""
    try:
        new_code = "TM" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        expiry = datetime.now() + timedelta(hours=2)
        expiry_str = expiry.strftime("%Y-%m-%d %H:%M:%S")
        
        meetingcode_sheet = sheet.worksheet("MeetingCode")
        meetingcode_sheet.clear()
        meetingcode_sheet.update("A1:B1", [["Meeting Code", "Expiry Timestamp"]])
        meetingcode_sheet.update("A2:B2", [[new_code, expiry_str]])
        
        return new_code, expiry_str
    except Exception as e:
        st.error(f"Error generating meeting code: {str(e)}")
        raise e
    

# Initialize session state
if 'login_type' not in st.session_state:
    st.session_state.login_type = 'member'
if 'show_admin' not in st.session_state:
    st.session_state.show_admin = False
if 'admin_authenticated' not in st.session_state:
    st.session_state.admin_authenticated = False
if 'generated_code' not in st.session_state:
    st.session_state.generated_code = None
if 'code_expiry' not in st.session_state:
    st.session_state.code_expiry = None

# Header with logo (centered)
logo_base64 = get_logo_base64()

if logo_base64:
    logo_html = f'<img src="data:image/png;base64,{logo_base64}" width="50" height="50" style="border-radius: 8px;">'
else:
    # Fallback to TM icon if logo not found
    logo_html = '<div style="width: 50px; height: 50px; background: rgba(255, 255, 255, 0.2); border-radius: 8px; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 1.2rem; backdrop-filter: blur(10px);">TM</div>'

st.markdown(f"""
<div class="header-container">
    <div class="logo-title">
        {logo_html}
        <h1>Koramangala Toastmasters Club</h1>
    </div>
</div>
""", unsafe_allow_html=True)

# Main login interface
sheet = init_google_sheets()
if not sheet:
    st.stop()

MEETING_CODE = get_meeting_code(sheet)

# Login container (now transparent)
st.markdown('<div class="login-container">', unsafe_allow_html=True)

# Login header
st.markdown("""
<div class="login-header">
    <h2>Welcome to the Meeting</h2>
    <p>Please sign in to mark your attendance</p>
</div>
""", unsafe_allow_html=True)

# Login type tabs - side by side
st.markdown('<div class="login-type-buttons">', unsafe_allow_html=True)
col1, col2 = st.columns(2)

with col1:
    member_class = "active-tab" if st.session_state.login_type == 'member' else "inactive-tab"
    st.markdown(f'<div class="{member_class}">', unsafe_allow_html=True)
    if st.button("👥 Member", key="member_tab", use_container_width=True):
        st.session_state.login_type = 'member'
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    guest_class = "active-tab" if st.session_state.login_type == 'guest' else "inactive-tab"
    st.markdown(f'<div class="{guest_class}">', unsafe_allow_html=True)
    if st.button("🎯 Guest", key="guest_tab", use_container_width=True):
        st.session_state.login_type = 'guest'
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# Member Login Form
if st.session_state.login_type == 'member':
    st.markdown('<h3 class="section-header">👥 Member Check-in</h3>', unsafe_allow_html=True)
    
    with st.form("member_form", clear_on_submit=False):
        phone = st.text_input("📱 Phone Number", placeholder="Enter your registered phone number")
        code = st.text_input("🔐 Meeting Code", type="password", placeholder="Enter meeting code")
        submitted = st.form_submit_button("✅ Sign In", use_container_width=True)
        
        if submitted:
            if not MEETING_CODE:
                st.error("🚫 No active meeting code. Please contact the organizer.")
            elif code != MEETING_CODE:
                st.error("❌ Invalid meeting code.")
            elif not phone.strip():
                st.error("❌ Please enter your phone number.")
            else:
                try:
                    members_sheet = sheet.worksheet("Members")
                    member_records = members_sheet.get_all_records()
                    matched = next((m for m in member_records if str(m["Phone Number"]) == str(phone)), None)
                    
                    if matched:
                        name = matched["Name"]
                        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        today = datetime.now().strftime("%Y-%m-%d")
                        
                        # Log in flat Attendance sheet
                        attendance_sheet = sheet.worksheet("Attendance")
                        attendance_sheet.append_row([timestamp, "Member", name, phone, code])
                        
                        # Create or update Attendance_Member matrix
                        if create_or_update_attendance_member(sheet, name, phone, today):
                            st.success(f"✅ Welcome **{name}**! You've been marked present for today's meeting.")
                        else:
                            st.warning("⚠️ Attendance logged but matrix update failed.")
                    else:
                        st.error("❌ Phone number not found in member records.")
                        
                except Exception as e:
                    st.error(f"❌ Error processing attendance: {str(e)}")

# Guest Login Form
else:
    st.markdown('<h3 class="section-header">🎯 Guest Check-in</h3>', unsafe_allow_html=True)
    
    with st.form("guest_form", clear_on_submit=False):
        name = st.text_input("👤 Full Name", placeholder="Enter your full name")
        email = st.text_input("📧 Email Address", placeholder="Enter your email address")
        phone = st.text_input("📱 Phone Number", placeholder="Enter your phone number")
        code = st.text_input("🔐 Meeting Code", type="password", placeholder="Enter meeting code")
        submitted = st.form_submit_button("✅ Sign In", use_container_width=True)
        
        if submitted:
            if not MEETING_CODE:
                st.error("🚫 No active meeting code. Please contact the organizer.")
            elif code != MEETING_CODE:
                st.error("❌ Invalid meeting code.")
            elif not name.strip():
                st.error("❌ Please enter your name.")
            elif not email.strip():
                st.error("❌ Please enter your email address.")
            else:
                try:
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    
                    # Log in Attendance sheet
                    attendance_sheet = sheet.worksheet("Attendance")
                    attendance_sheet.append_row([timestamp, "Guest", name, phone, code])
                    
                    # Log in Guest sheet
                    guest_sheet = sheet.worksheet("Guest")
                    guest_sheet.append_row([timestamp, name, email, phone, code])
                    
                    st.success(f"✅ Welcome **{name}**! Thank you for joining us as a guest today.")
                    
                except Exception as e:
                    st.error(f"❌ Error processing guest registration: {str(e)}")

st.markdown('</div>', unsafe_allow_html=True)

# Admin Panel (MOVED TO FOOTER AREA)
# --- Admin Panel (Always Visible) ---
st.markdown('<div class="admin-panel">', unsafe_allow_html=True)
st.markdown("### 🔐 Admin Controls")

# Admin password input
admin_pass = st.text_input("Enter Admin Password", type="password", key="admin_pass_input")

# Check and store authentication state
if admin_pass == "admin123":
    st.session_state.admin_authenticated = True
elif admin_pass and admin_pass != "admin123":
    st.session_state.admin_authenticated = False
    st.error("❌ Invalid admin password.")

# Show admin actions if authenticated
if st.session_state.get("admin_authenticated", False):
    st.success("✅ Admin authenticated")

    if st.button("Generate New Meeting Code", key="gen_code"):
        new_code, expiry_str = generate_meeting_code(sheet)
        if new_code:
            st.session_state.generated_code = new_code
            st.session_state.code_expiry = expiry_str

    if st.session_state.get("generated_code"):
        st.success(f"✅ **Current Active Code: {st.session_state.generated_code}**")
        st.info(f"📅 Valid until: {st.session_state.code_expiry}")

        if st.button("Clear Code Display", key="clear_code"):
            st.session_state.generated_code = None
            st.session_state.code_expiry = None
            st.rerun()
else:
    st.info("🔐 Enter admin password to access token generation.")

st.markdown('</div>', unsafe_allow_html=True)