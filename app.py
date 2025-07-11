import streamlit as st
import gspread
from datetime import datetime, timedelta
from google.oauth2.service_account import Credentials
import random
import string
import base64
from zoneinfo import ZoneInfo
import pytz

ist = pytz.timezone('Asia/Kolkata')

# Page config with custom styling
st.set_page_config(
    page_title="Koramangala Toastmasters Club", 
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS for professional UI
st.markdown("""
<style>
/* Main theme colors - Based on provided color scheme */
:root {
    --primary-maroon: #772432;
    --loyal-blue: #004165;
    --cool-gray: #A9B2B1;
    --white: #FFFFFF;
    --text-dark: #1F2937;
    --success-green: #10B981;
    --gradient-maroon: linear-gradient(135deg, #772432 0%, #8B2635 100%);
}

/* Body background - WHITE */
.stApp {
    background: var(--white);
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
    padding: 2rem 0;
    margin-bottom: 2rem;
}

.logo-title {
    display: flex;
    align-items: center;
    gap: 1.5rem;
}

.logo-title h1 {
    color: var(--loyal-blue);
    margin: 0;
    font-size: 2.5rem;
    font-weight: 700;
    text-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

/* Step headers */
.step-header {
    text-align: center;
    margin-bottom: 2rem;
}

.step-header h2 {
    color: var(--loyal-blue);
    margin-bottom: 0.5rem;
    font-size: 1.8rem;
    font-weight: 600;
}

.step-header p {
    color: var(--loyal-blue);
    font-size: 1.1rem;
    margin: 0;
    font-weight: 500;
}

/* Input styling */
.stTextInput > label {
    color: var(--loyal-blue) !important;
    font-weight: 500 !important;
    margin-bottom: 0.5rem !important;
}

.stTextInput > div > div > input {
    border: 2px solid var(--cool-gray);
    border-radius: 8px;
    padding: 0.75rem;
    font-size: 1rem;
    transition: all 0.3s ease;
    background: var(--white);
    color: var(--text-dark);
}

.stTextInput > div > div > input:focus {
    border-color: var(--loyal-blue);
    box-shadow: 0 0 0 3px rgba(0, 65, 101, 0.3);
    background: var(--white);
}

.stTextInput > div > div > input::placeholder {
    color: rgba(31, 41, 55, 0.6);
}

/* Enhanced Button Styling - MAROON with WHITE text */
div[data-testid="column"]:first-child button,
div[data-testid="column"]:last-child button {
    background: var(--gradient-maroon) !important;
    border: 2px solid var(--primary-maroon) !important;
    border-radius: 16px !important;
    padding: 2rem 1rem !important;
    height: 140px !important;
    width: 100% !important;
    color: var(--white) !important;
    font-size: 1.1rem !important;
    font-weight: 600 !important;
    line-height: 1.5 !important;
    white-space: pre-line !important;
    text-align: center !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 4px 12px rgba(119, 36, 50, 0.3) !important;
    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3) !important;
}

div[data-testid="column"]:first-child button:hover,
div[data-testid="column"]:last-child button:hover {
    background: linear-gradient(135deg, #8B2635 0%, #772432 100%) !important;
    border-color: var(--primary-maroon) !important;
    border-width: 3px !important;
    transform: translateY(-4px) scale(1.02) !important;
    box-shadow: 0 8px 24px rgba(119, 36, 50, 0.4) !important;
}

/* Submit button styling */
.stButton > button {
    background: var(--gradient-maroon) !important;
    color: var(--white) !important;
    border: none !important;
    border-radius: 12px !important;
    font-size: 1.1rem !important;
    font-weight: 600 !important;
    padding: 1rem 2rem !important;
    width: 100% !important;
    transition: all 0.3s ease !important;
    margin-top: 1.5rem !important;
    box-shadow: 0 4px 12px rgba(119, 36, 50, 0.3) !important;
    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3) !important;
}

.stButton > button:hover {
    transform: translateY(-3px) !important;
    box-shadow: 0 8px 20px rgba(119, 36, 50, 0.4) !important;
    background: linear-gradient(135deg, #8B2635 0%, #772432 100%) !important;
}

/* Success/Error messages */
.success-message {
    background: rgba(16, 185, 129, 0.1);
    border: 1px solid var(--success-green);
    color: var(--loyal-blue);
    padding: 1rem;
    border-radius: 8px;
    margin: 1rem 0;
    text-align: center;
}

.error-message {
    background: rgba(239, 68, 68, 0.1);
    border: 1px solid #EF4444;
    color: #EF4444;
    padding: 1rem;
    border-radius: 8px;
    margin: 1rem 0;
    text-align: center;
}

/* Voting link container */
.voting-link-container {
    margin-top: 2rem;
    text-align: center;
}

.voting-link-button {
    display: inline-block !important;
    background: var(--gradient-maroon) !important;
    color: var(--white) !important;
    padding: 1.2rem 2.5rem !important;
    border-radius: 16px !important;
    text-decoration: none !important;
    font-weight: 600 !important;
    font-size: 1.1rem !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 4px 12px rgba(119, 36, 50, 0.3) !important;
    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3) !important;
}

.voting-link-button:hover {
    transform: translateY(-4px) !important;
    box-shadow: 0 8px 20px rgba(119, 36, 50, 0.4) !important;
    text-decoration: none !important;
    color: var(--white) !important;
}

/* Mobile responsive */
@media (max-width: 768px) {
    .header-container {
        padding: 1rem 0;
        margin-bottom: 1.5rem;
    }
    
    .logo-title {
        flex-direction: column;
        gap: 1rem;
        text-align: center;
    }
    
    .logo-title h1 {
        font-size: 2rem;
    }
    
    /* Force buttons to stay side by side on mobile */
    div[data-testid="column"] {
        flex: 1 !important;
        width: 50% !important;
        min-width: 0 !important;
    }
    
    div[data-testid="column"]:first-child button,
    div[data-testid="column"]:last-child button {
        height: 110px !important;
        padding: 1.2rem 0.5rem !important;
        font-size: 0.95rem !important;
        border-radius: 12px !important;
        line-height: 1.3 !important;
    }
    
    /* Ensure columns container uses flexbox properly */
    div[data-testid="column"]:first-child,
    div[data-testid="column"]:last-child {
        display: flex !important;
        flex-direction: column !important;
    }
    
    /* Force horizontal layout for button container */
    div[data-testid="element-container"] > div[data-testid="column"] {
        display: flex !important;
        flex: 1 !important;
    }
}

/* Remove default Streamlit container padding */
.block-container {
    padding-top: 2rem;
    padding-bottom: 2rem;
}

/* Hide any background containers and forms */
.stContainer {
    background: transparent !important;
}

.stForm {
    background: transparent !important;
    border: none !important;
    padding: 0 !important;
}

/* Hide the specific markdown container that creates unwanted spacing */
div[data-testid="stMarkdownContainer"] .main-container {
    display: none !important;
}

/* Ensure main content container is clean */
.main-content-container {
    background: var(--white);
    border-radius: 16px;
    padding: 2rem;
    max-width: 440px;
    margin: 0 auto;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
    border: 1px solid var(--cool-gray);
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
        creds = Credentials.from_service_account_info(dict(st.secrets["google_service_account"]), scopes=SCOPE)
        client = gspread.authorize(creds)   
        sheet = client.open("Toastmasters Attendance")
        return sheet
    except Exception as e:
        raise e

def get_meeting_code(sheet):
    """Get active meeting code"""
    try:
        meetingcode_sheet = sheet.worksheet("MeetingCode")
        code_data = meetingcode_sheet.get_all_records()
        
        if code_data:
            expiry_time = datetime.strptime(code_data[0]["Expiry Timestamp"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=ZoneInfo("Asia/Kolkata"))
            if datetime.now(ist) <= expiry_time:
                return code_data[0]["Meeting Code"]
    except Exception:
        raise e

def create_or_update_attendance_member(sheet, name, phone, today):
    """Create or update attendance member record"""
    try:
        matrix_sheet = sheet.worksheet("Attendance_Member")
        matrix_data = matrix_sheet.get_all_values()
        
        # If sheet is empty, create headers
        if not matrix_data:
            matrix_sheet.update("A1:C1", [["Name", "Phone", today]])
            matrix_sheet.update("A2:C2", [[name, phone, 1]])
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
                matrix_sheet.update_cell(idx, col_index, 1)
                member_found = True
                break
        
        # If member not found, create new record
        if not member_found:
            new_row = [name, phone] + [""] * (len(headers) - 2)
            col_index = headers.index(today)
            new_row[col_index] = 1
            matrix_sheet.append_row(new_row)
            
        return True
    except Exception as e:
        st.error(f"Error updating attendance member sheet: {str(e)}")
        return False

def generate_meeting_code(sheet):
    """Generate new meeting code"""
    try:
        new_code = "TM" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        expiry = datetime.now(ist) + timedelta(hours=2)
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
if 'step' not in st.session_state:
    st.session_state.step = 'home'
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
if 'user_name' not in st.session_state:
    st.session_state.user_name = None

# Header with logo
logo_base64 = get_logo_base64()

if logo_base64:
    logo_html = f'<img src="data:image/png;base64,{logo_base64}" width="80" height="80" style="border-radius: 8px;">'
else:
    logo_html = '<div style="width: 80px; height: 80px; background: #A9B2B1; border-radius: 8px; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 1.5rem;">TM</div>'

st.markdown(f"""
<div class="header-container">
    <div class="logo-title">
        {logo_html}
        <h1>Koramangala Toastmasters Club</h1>
    </div>
</div>
""", unsafe_allow_html=True)

# Initialize Google Sheets
sheet = init_google_sheets()
if not sheet:
    st.stop()

# # Main content container
# st.markdown('<div class="main-content-container">', unsafe_allow_html=True)

# HOME STEP
if st.session_state.step == 'home':
    st.markdown("""
    <div class="step-header">
        <h2>Welcome to the Meeting</h2>
        <p>Please select your attendance type</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Check for button clicks
    if 'member_clicked' not in st.session_state:
        st.session_state.member_clicked = False
    if 'guest_clicked' not in st.session_state:
        st.session_state.guest_clicked = False
    
    # Handle button clicks
    if st.session_state.member_clicked:
        st.session_state.step = 'member_login'
        st.session_state.login_type = 'member'
        st.session_state.member_clicked = False
        st.rerun()
    
    if st.session_state.guest_clicked:
        st.session_state.step = 'guest_login'
        st.session_state.login_type = 'guest'
        st.session_state.guest_clicked = False
        st.rerun()
    
    # Custom selection buttons
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🧑\n\nMember\n\nRegistered Members", key="member_select", use_container_width=True):
            st.session_state.member_clicked = True
            st.rerun()
    
    with col2:
        if st.button("🙋‍♂️\n\nGuest\n\nVisitors ", key="guest_select", use_container_width=True):
            st.session_state.guest_clicked = True
            st.rerun()

# MEMBER LOGIN STEP
elif st.session_state.step == 'member_login':
    col_back, col_space = st.columns([1, 3])
    with col_back:
        if st.button("← Back", key="back_member"):
            st.session_state.step = 'home'
            st.rerun()
    
    st.markdown("""
    <div class="step-header">
        <h2>🧑 Member Check-in</h2>
        <p>Enter your registered phone number</p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("member_form", clear_on_submit=False):
        phone = st.text_input("Phone Number", placeholder="Enter your registered phone number")
        submitted = st.form_submit_button("Sign In", use_container_width=True)
        
        if submitted:
            if not phone.strip():
                st.markdown('<div class="error-message">❌ Please enter your phone number.</div>', unsafe_allow_html=True)
            else:
                try:
                    members_sheet = sheet.worksheet("Members")
                    member_records = members_sheet.get_all_records()
                    matched = next((m for m in member_records if str(m["Phone Number"]) == str(phone)), None)
                    
                    if matched:
                        name = matched["Name"]
                        timestamp = datetime.now(ist).strftime("%Y-%m-%d %H:%M:%S")
                        today = datetime.now(ist).strftime("%Y-%m-%d")
                        
                        # Log in flat Attendance sheet
                        attendance_sheet = sheet.worksheet("Attendance")
                        attendance_sheet.append_row([timestamp, "Member", name, phone, "0000"])
                        
                        # Create or update Attendance_Member matrix
                        if create_or_update_attendance_member(sheet, name, phone, today):
                            st.session_state.user_name = name
                            st.session_state.step = 'success'
                            st.rerun()
                        else:
                            st.markdown('<div class="error-message">⚠️ Attendance logged but matrix update failed.</div>', unsafe_allow_html=True)
                    else:
                        st.markdown('<div class="error-message">❌ Phone number not found in member records.</div>', unsafe_allow_html=True)
                        
                except Exception as e:
                    st.markdown(f'<div class="error-message">❌ Error processing attendance: {str(e)}</div>', unsafe_allow_html=True)

# GUEST LOGIN STEP
elif st.session_state.step == 'guest_login':
    col_back, col_space = st.columns([1, 3])
    with col_back:
        if st.button("← Back", key="back_guest"):
            st.session_state.step = 'home'
            st.rerun()
    
    st.markdown("""
    <div class="step-header">
        <h2>🙋‍♂️ Guest Check-in</h2>
        <p>Please provide your details</p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("guest_form", clear_on_submit=False):
        name = st.text_input("Full Name", placeholder="Enter your full name")
        phone = st.text_input("Phone Number", placeholder="Enter your phone number")
        submitted = st.form_submit_button("Sign In", use_container_width=True)
        
        if submitted:
            if not name.strip():
                st.markdown('<div class="error-message">❌ Please enter your name.</div>', unsafe_allow_html=True)
            elif not phone.strip():
                st.markdown('<div class="error-message">❌ Please enter your phone number.</div>', unsafe_allow_html=True)
            else:
                try:
                    timestamp = datetime.now(ist).strftime("%Y-%m-%d %H:%M:%S")
                    
                    # Log in Attendance sheet
                    attendance_sheet = sheet.worksheet("Attendance")
                    attendance_sheet.append_row([timestamp, "Guest", name, phone, "0000"])
                    
                    # Log in Guest sheet
                    guest_sheet = sheet.worksheet("Guest")
                    guest_sheet.append_row([timestamp, name, "None", phone, "0000"])
                    
                    st.session_state.user_name = name
                    st.session_state.step = 'success'
                    st.rerun()
                    
                except Exception as e:
                    st.markdown(f'<div class="error-message">❌ Error processing guest registration: {str(e)}</div>', unsafe_allow_html=True)

# SUCCESS STEP
elif st.session_state.step == 'success':
    st.markdown(f"""
    <div class="step-header">
        <h2>✅ Welcome!</h2>
        <p>Thank you for joining us today</p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.user_name:
        st.markdown(f"""
        <div class="success-message">
            <strong>Hello {st.session_state.user_name}!</strong><br>
            You've been successfully marked present for today's meeting.
        </div>
        """, unsafe_allow_html=True)
    
    # Voting link section
    st.markdown("""
    <div class="voting-link-container">
        <a href="https://forms.gle/eEFE3ZdZSMK6Vdf5A" 
           target="_blank" class="voting-link-button"
           style="color: white !important; text-decoration: none !important;">
            🗳️ &nbsp; Vote for Best Speaker
        </a>
    </div>
    """, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)