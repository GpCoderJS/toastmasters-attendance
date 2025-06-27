import streamlit as st
import gspread
from datetime import datetime, timedelta
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="Koramangala Toastmasters Club", layout="centered")




# ✅ Use full Sheets + Drive access
SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

creds = Credentials.from_service_account_file("client_secret.json", scopes=SCOPE)
client = gspread.authorize(creds)
# # Google Sheets Auth
# SCOPE = ["https://www.googleapis.com/auth/spreadsheets"]
# creds = Credentials.from_service_account_file("client_secret.json", scopes=SCOPE)
# client = gspread.authorize(creds)

# Connect to the sheets
sheet = client.open("Toastmasters Attendance")
members_sheet = sheet.worksheet("Members")
attendance_sheet = sheet.worksheet("Attendance")
guest_sheet = sheet.worksheet("Guest")
meetingcode_sheet = sheet.worksheet("MeetingCode")
# Set your meeting code here
code_data = meetingcode_sheet.get_all_records()
MEETING_CODE = None

if code_data:
    expiry_time = datetime.strptime(code_data[0]["Expiry Timestamp"], "%Y-%m-%d %H:%M:%S")
    if datetime.now() <= expiry_time:
        MEETING_CODE = code_data[0]["Meeting Code"]

st.title("🎤 Koramangala Toastmasters Club Attendance")
st.markdown("Welcome to the weekly meeting check-in system.")

with st.expander("🔐 Admin Controls"):
    admin_pass = st.text_input("Enter Admin Password", type="password")
    if admin_pass == "admin123":  # 🔑 Replace with your secure admin password
        if st.button("Generate New Meeting Code"):
            import random, string

            # Generate code like 'TMX92Q'
            new_code = "TM" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))

            # Set expiry 5 hours from now
            expiry = datetime.now() + timedelta(hours=2)
            expiry_str = expiry.strftime("%Y-%m-%d %H:%M:%S")

            # Clear old code and add new one
            meetingcode_sheet.clear()
            meetingcode_sheet.update("A1:B1", [["Meeting Code", "Expiry Timestamp"]])
            meetingcode_sheet.update("A2:B2", [[new_code, expiry_str]])

            st.success(f"✅ New code generated: {new_code} (valid until {expiry_str})")
    elif admin_pass != "":
        st.error("❌ Invalid admin password.")


user_type = st.radio("Are you a:", ["Member", "Guest"])

if user_type == "Member":
    phone = st.text_input("📱 Enter your phone number")
    code = st.text_input("🔐 Enter meeting code", type="password")
    if code!= MEETING_CODE:
        st.error("🚫 No active meeting code. Please contact the organizer.")
        st.stop()
    if st.button("✅ Submit as Member"):
        member_records = members_sheet.get_all_records()
        matched = next((m for m in member_records if str(m["Phone Number"]) == str(phone)), None)
        
        if matched and code == MEETING_CODE:
            name = matched["Name"]
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            today = datetime.now().strftime("%Y-%m-%d")

            # ✅ Log in flat Attendance sheet
            attendance_sheet.append_row([
                timestamp,
                "Member",
                name,
                phone,
                code
            ])

            # ✅ Log in Attendance_Member matrix sheet
            matrix_sheet = sheet.worksheet("Attendance_Member")
            matrix_data = matrix_sheet.get_all_values()
            headers = matrix_data[0]

            # Add today's date as a new column if not present
            if today not in headers:
                matrix_sheet.update_cell(1, len(headers) + 1, today)
                headers.append(today)

            # Find the member's row and mark 1 under today's date
            for idx, row in enumerate(matrix_data[1:], start=2):  # start=2 because of headers
                if row[1] == phone:
                    col_index = headers.index(today) + 1
                    matrix_sheet.update_cell(idx, col_index, "1")
                    break

            st.success(f"✅ Welcome {matched['Name']} to Koramangala Toastmasters Club! You’ve been marked present.")

        else:
            st.error("❌ Invalid phone number or meeting code.")


elif user_type == "Guest":
    name = st.text_input("👤 Enter your full name")
    email = st.text_input("📧 Enter your email ")
    phone = st.text_input("📧 Enter your Phone Number ")
    code = st.text_input("🔐 Enter meeting code", type="password")
    if code!= MEETING_CODE:
        st.error("🚫 No active meeting code. Please contact the organizer.")
        st.stop()
    if st.button("✅ Submit as Guest"):
        if name.strip() == "":
            st.warning("⚠️ Please enter your name.")
        elif code != MEETING_CODE:
            st.error("❌ Invalid meeting code.")
        else:
            attendance_sheet.append_row([
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Guest",
                name,
                phone,
                code
            ])
            guest_sheet.append_row([
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                name,
                email,
                phone,
                code
            ])
            st.success(f"✅ Welcome {name} to Koramangala Toastmasters Club! Thank you for joining as a guest!")
