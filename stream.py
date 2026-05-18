import cv2
import streamlit as st
from ultralytics import YOLO
import numpy as np
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO
import sqlite3
import pandas as pd
import re

# ================== CONFIG ==================
st.set_page_config(
    page_title="TB Portal",
    page_icon="🩺",
    layout="wide"
)
import os
MODEL_PATH = os.path.join(os.path.dirname(__file__), "best.pt")
DB_PATH = "tb_portal.db"

# ================== DATABASE ==================
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# ---------- USERS TABLE ----------
c.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cnic TEXT,
    email TEXT,
    username TEXT UNIQUE,
    password TEXT
)
""")

# ---------- PREDICTIONS TABLE ----------
c.execute("""
CREATE TABLE IF NOT EXISTS predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    image_name TEXT,
    prediction TEXT,
    confidence REAL
)
""")

conn.commit()
conn.close()

# ================== SESSION ==================
if "page" not in st.session_state:
    st.session_state.page = "login"

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "current_user" not in st.session_state:
    st.session_state.current_user = ""

# ================== STYLE ==================
st.markdown("""
<style>

.stApp {
    background: linear-gradient(135deg,#eaf4ff,#f8fbff,#dbeafe,#ffffff);
    font-family:'Segoe UI',sans-serif;
}

/* INPUT */
.stTextInput input {
    background:#eaf4ff !important;
    border:2px solid #bfdbfe !important;
    border-radius:10px !important;
}

/* INPUT FOCUS */
.stTextInput input:focus {
    border:2px solid #2563eb !important;
}

/* BUTTONS */
.stButton>button{
    background:linear-gradient(90deg,#0f4c81,#2563eb);
    color:white;
    border-radius:10px;
    font-weight:600;
    border:none;
}

/* SIDEBAR */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg,#0f4c81,#1e3a8a) !important;
}

section[data-testid="stSidebar"] * {
    color:white !important;
}

/* CARD BOX */
.box{
    background:white;
    padding:30px;
    border-radius:18px;
    box-shadow:0 8px 25px rgba(0,0,0,0.12);
}

/* HEADINGS */
h1,h2,h3{
    color:#0f4c81 !important;
}

/* FILE UPLOADER */
[data-testid="stFileUploader"] {
    background: #eaf4ff !important;
    border: 2px dashed #2563eb !important;
    border-radius: 15px !important;
    padding: 20px !important;
}

</style>
""", unsafe_allow_html=True)

# ================== SIDEBAR ==================
def show_sidebar():

    with st.sidebar:

        st.success(f"Logged In: {st.session_state.current_user}")

        menu = st.radio(
            "Navigation",
            ["Home", "Prediction", "Dashboard", "History"]
        )

        st.markdown("<br><br>", unsafe_allow_html=True)

        if st.button("LOGOUT"):

            st.session_state.logged_in = False
            st.session_state.page = "login"
            st.session_state.current_user = ""

            st.rerun()

    return menu

# ================== LOGIN PAGE ==================
def login_page():

    st.markdown(
        "<h1 style='text-align:center;'> Login</h1>",
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns([1,2,1])

    with col2:

        username = st.text_input(
            "Username",
            autocomplete="new-password",
            key="login_user"
        )

        password = st.text_input(
            "Password",
            type="password",
            autocomplete="new-password",
            key="login_pass"
        )

        st.write("")

        colA, colB = st.columns(2)

        # ---------- LOGIN BUTTON ----------
        with colA:

            if st.button("Login"):
                if username == "" or password == "":
                    st.error("Please enter username and password")
                    return


                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()

                c.execute(
                    "SELECT * FROM users WHERE username=? AND password=?",
                    (username, password)
                )

                user = c.fetchone()

                conn.close()

                if user:

                    st.session_state.logged_in = True
                    st.session_state.current_user = username
                    st.session_state.page = "home"

                    st.success("Login Successful")

                    st.rerun()

                else:
                    st.error("Invalid Username or Password")

        # ---------- SIGNUP BUTTON ----------
        with colB:

            if st.button("Go to Signup"):

                st.session_state.page = "signup"
                st.rerun()

       # st.markdown("</div>", unsafe_allow_html=True)

# ================== SIGNUP PAGE ==================
def signup_page():

    st.markdown(
        "<h1 style='text-align:center;'>Create Account</h1>",
        unsafe_allow_html=True
    )

    col1, col2, col3 = st.columns([1,2,1])

    with col2:


        cnic = st.text_input("CNIC")

        email = st.text_input("Email")

        username = st.text_input(
            "Username",
            autocomplete="new-password"
        )

        password = st.text_input(
            "Password",
            type="password",
            autocomplete="new-password"
        )

        st.write("")

        colA, colB = st.columns(2)

        # ---------- SIGNUP ----------
        with colA:

            if st.button("Signup"):

                # USERNAME LIMIT
                if len(username) < 4 or len(username) > 10:
                    st.error("Username must be 4 to 10 characters")
                    return

                # PASSWORD LIMIT
                if len(password) < 4 or len(password) > 10:
                    st.error("Password must be 4 to 10 characters")
                    return

                # CNIC VALIDATION
                cnic_pattern = r"^\d{5}-\d{7}-\d{1}$"

                if not re.match(cnic_pattern, cnic):
                    st.error("Invalid CNIC Format")
                    return

                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()

                try:

                    c.execute("""
                    INSERT INTO users (
                        cnic,
                        email,
                        username,
                        password
                    )
                    VALUES (?,?,?,?)
                    """, (
                        cnic,
                        email,
                        username,
                        password
                    ))

                    conn.commit()
                    conn.close()

                    st.success("Account Created Successfully")

                except sqlite3.IntegrityError:

                    st.error("Username already exists")

        # ---------- BACK ----------
        with colB:

            if st.button("Back to Login"):

                st.session_state.page = "login"
                st.rerun()

       # st.markdown("</div>", unsafe_allow_html=True)

# ================== HOME PAGE ==================
def home_page():
    st.markdown("""
                <h1>Welcome to Home page</h1>
                """, unsafe_allow_html=True)
    st.write("")
    if st.button("Introduction"):
        st.markdown("""
    <div class='box'>

    <h2>AI TB Screening System</h2>

    <p>
    AI-powered tuberculosis detection system using chest X-ray images.
    </p>

    <ul>
        <li>Detect Active TB</li>
        <li>Detect Latent TB</li>
        <li>Healthy Detection</li>
        <li>YOLO AI Model</li>
    </ul>

    </div>
    """, unsafe_allow_html=True)

# ================== PDF REPORT ==================
def generate_pdf(report_type):

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter
    )

    styles = getSampleStyleSheet()

    content = []

    title = Paragraph(
        "TB Analysis Report",
        styles['Title']
    )

    content.append(title)

    content.append(Spacer(1,12))

    # ---------- ACTIVE TB ----------
    if report_type == "active_tb":

        data = [
            ["Condition","Active Tuberculosis"],
            ["Status","High Risk"],
            ["Medication","Isoniazid, Rifampicin"],
            ["Precautions","Hospital Treatment"]
        ]

    # ---------- LATENT TB ----------
    elif report_type == "latent_tb":

        data = [
            ["Condition","Latent Tuberculosis"],
            ["Status","Low Risk"],
            ["Medication","Preventive Therapy"]
        ]

    # ---------- HEALTHY ----------
    else:

        data = [
            ["Status","Healthy"],
            ["Note","No TB detected"]
        ]

    table = Table(data)

    table.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),colors.lightblue),
        ('GRID',(0,0),(-1,-1),1,colors.black),
        ('BACKGROUND',(0,1),(-1,-1),colors.whitesmoke),
    ]))

    content.append(table)

    doc.build(content)

    buffer.seek(0)

    return buffer
# ================== PREDICTION PAGE ==================
def project_page():
    
    st.title("Prediction")

    uploaded_file = st.file_uploader(
        "Upload Chest X-ray",
        type=["jpg","jpeg","png"]
    )

    if uploaded_file:

        file_bytes = np.asarray(
            bytearray(uploaded_file.read()),
            dtype=np.uint8
        )

        frame = cv2.imdecode(
            file_bytes,
            cv2.IMREAD_COLOR
        )

        # ---------- LOAD MODEL ----------
        model = YOLO(MODEL_PATH)

        # ---------- PREDICT ----------
        results = model.predict(
            frame,
            conf=0.25,
            verbose=False
        )

        class_name = "healthy"
        confidence = 0.0

        # ---------- DETECTION ----------
        if len(results[0].boxes) > 0:

            box = results[0].boxes[0]

            cls_id = int(box.cls[0])

            confidence = float(box.conf[0])

            class_name = model.names[cls_id]

            x1, y1, x2, y2 = map(
                int,
                box.xyxy[0]
            )

            # ---------- DRAW BOX ----------
            cv2.rectangle(
                frame,
                (x1,y1),
                (x2,y2),
                (0,255,0),
                2
            )

            # ---------- LABEL ----------
            label = f"{class_name} {confidence*100:.1f}%"

            cv2.putText(
                frame,
                label,
                (x1,y1-10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255,0,0),
                2
            )

        # ---------- SAVE PREDICTION ----------
        if st.session_state.get("last_saved") != uploaded_file.name:
            st.session_state.last_saved = uploaded_file.name
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("""
            INSERT INTO predictions (
                username,
                image_name,
                prediction,
                confidence
            )
            VALUES (?,?,?,?)
            """, (
                st.session_state.current_user,
                uploaded_file.name,
                class_name,
                round(confidence*100,2)
            ))
            conn.commit()
            conn.close()
        

        # ---------- DISPLAY ----------
        col1, col2 = st.columns(2)

        # IMAGE
        with col1:

            st.image(
                cv2.cvtColor(frame, cv2.COLOR_BGR2RGB),
                width='stretch'
            )

        # RESULT BOX
        with col2:

            st.markdown("### Analysis Result")

            st.markdown(
                f"<p style='font-size:15px;'><b>Prediction:</b> {class_name}</p>",
                unsafe_allow_html=True
            )

            st.markdown(
                f"<p style='font-size:15px;'><b>Confidence:</b> {confidence*100:.2f}%</p>",
                unsafe_allow_html=True
            )

            if class_name == "healthy":

                st.success("No TB Detected")

            else:

                st.warning("TB Detected")

            # ================= PDF REPORT =================
            if st.button("Generate PDF Report"):

                buffer = BytesIO()

                doc = SimpleDocTemplate(
                    buffer,
                    pagesize=letter
                )

                styles = getSampleStyleSheet()

                content = []

                title = Paragraph(
                    "<font size=20 color='blue'><b>TB MEDICAL REPORT</b></font>",
                    styles['Title']
                )

                content.append(title)

                content.append(Spacer(1,20))

                # ================= TABLE =================
                table_data = [
                    ["Field", "Result"],
                    ["Prediction", class_name],
                    ["Confidence", f"{confidence*100:.2f}%"],
                    ["Date", str(pd.Timestamp.now().date())]
                ]

                table = Table(
                    table_data,
                    colWidths=[200,250]
                )

                table.setStyle(TableStyle([
                    ('BACKGROUND',(0,0),(-1,0),colors.HexColor("#2563eb")),
                    ('TEXTCOLOR',(0,0),(-1,0),colors.white),
                    ('GRID',(0,0),(-1,-1),2,colors.HexColor("#2563eb")),
                    ('FONTNAME',(0,0),(-1,0),'Helvetica-Bold'),
                    ('BACKGROUND',(0,1),(-1,-1),colors.whitesmoke),
                    ('BOTTOMPADDING',(0,0),(-1,0),12),
                ]))

                content.append(table)

                content.append(Spacer(1,25))

                # ================= ACTIVE TB =================
                if class_name.lower() == "active_tb":

                    active_text = """

                    <b><font color='blue'>Prevention Methods</font></b><br/><br/>

                    • Wear mask to prevent spread of TB bacteria.<br/><br/>
                    • Complete full medication course properly.<br/><br/>
                    • Healthy diet improves immunity and recovery.<br/><br/>
                    • Regular doctor monitoring is important.<br/><br/>

                    <b><font color='blue'>Main Reasons</font></b><br/><br/>

                    • Weak Immunity — 40%<br/><br/>
                    • Smoking — 25%<br/><br/>
                    • Close Contact — 20%<br/><br/>
                    • Malnutrition — 15%

                    """

                    para = Paragraph(
                        active_text,
                        styles['BodyText']
                    )

                    content.append(para)

                # ================= LATENT TB =================
                elif class_name.lower() == "latent_tb":

                    latent_text = """

                    <b><font color='blue'>Prevention Methods</font></b><br/><br/>

                    • Regular screening and medical checkups.<br/><br/>
                    • Avoid close contact with infected patients.<br/><br/>
                    • Maintain proper ventilation in rooms.<br/><br/>
                    • Healthy lifestyle and strong immunity.<br/><br/>

                    <b><font color='blue'>Main Reasons</font></b><br/><br/>

                    • Previous TB Exposure — 35%<br/><br/>
                    • Weak Immune System — 30%<br/><br/>
                    • Poor Ventilation — 20%<br/><br/>
                    • Malnutrition — 15%

                    """

                    para = Paragraph(
                        latent_text,
                        styles['BodyText']
                    )

                    content.append(para)

                # ================= HEALTHY =================
                else:

                    healthy_text = """

                    <b><font color='green'>Healthy Result</font></b><br/><br/>

                    No Tuberculosis detected in the uploaded X-ray image.<br/><br/>

                    Continue healthy habits, hygiene, and regular checkups.

                    """

                    para = Paragraph(
                        healthy_text,
                        styles['BodyText']
                    )

                    content.append(para)

                # ---------- BUILD PDF ----------
                doc.build(content)

                buffer.seek(0)

                st.download_button(
                    "Download Report",
                    buffer,
                    file_name="TB_Report.pdf",
                    mime="application/pdf"
                )

# ================== DASHBOARD ==================
def dashboard_page():

    st.title("Dashboard")

    conn = sqlite3.connect(DB_PATH)

    query = """
    SELECT prediction, COUNT(*)
    FROM predictions
    WHERE username=?
    GROUP BY prediction
    """

    df = pd.read_sql_query(
        query,
        conn,
        params=(st.session_state.current_user,)
    )

    conn.close()

    active = 0
    latent = 0
    healthy = 0

    # ---------- COUNTS ----------
    for _, row in df.iterrows():

        pred = row["prediction"]

        count = row["COUNT(*)"]

        if pred == "active_tb":
            active = count

        elif pred == "latent_tb":
            latent = count

        elif pred == "healthy":
            healthy = count

    # ---------- METRICS ----------
    c1, c2, c3 = st.columns(3)

    c1.metric("Active TB", active)

    c2.metric("Latent TB", latent)

    c3.metric("Healthy", healthy)

    st.write("")

    colA, colB = st.columns(2)

    # ================= PIE CHART =================
    with colA:

        st.subheader("Prediction Distribution")

        sizes = [active, latent, healthy]

        labels = [
            "Active TB",
            "Latent TB",
            "Healthy"
        ]

        fig1, ax1 = plt.subplots(figsize=(4,4))

        if sum(sizes) == 0:

            ax1.text(
                0.5,
                0.5,
                "No Data",
                ha='center'
            )

            ax1.axis("off")

        else:

            ax1.pie(
                sizes,
                labels=labels,
                autopct='%1.1f%%'
            )

        st.pyplot(fig1)

    # ================= BAR CHART =================
    with colB:

        st.subheader("Model Performance")

        labels = [
            "P",
            "R",
            "mAP50",
            "mAP50-95"
        ]

        values = [
            98.4,
            95.6,
            95.5,
            79.9
        ]

        fig2, ax2 = plt.subplots(figsize=(4,4))

        bars = ax2.bar(labels, values)

        ax2.set_ylim(0,120)

        for bar in bars:

            h = bar.get_height()

            ax2.text(
                bar.get_x()+bar.get_width()/2,
                h+1,
                f"{h}%",
                ha='center'
            )

        st.pyplot(fig2)

# ================== HISTORY PAGE ==================
def history_page():

    st.title("Prediction History")

    conn = sqlite3.connect(DB_PATH)

    query = """
    SELECT 
        image_name AS 'Image Name',
        prediction AS 'Prediction',
        confidence AS 'Confidence (%)'
    FROM predictions
    WHERE username=?
    ORDER BY id DESC
    """

    df = pd.read_sql_query(
        query,
        conn,
        params=(st.session_state.current_user,)
    )

    conn.close()

    if len(df) == 0:

        st.info("No prediction history found.")

    else:

        st.dataframe(
            df,
            use_container_width=True
        )

# ================== ROUTING ==================
if st.session_state.page in ["login","signup"]:

    if st.session_state.page == "login":

        login_page()

    else:

        signup_page()

else:

    menu = show_sidebar()

    if menu == "Home":

        home_page()

    elif menu == "Prediction":

        project_page()

    elif menu == "Dashboard":

        dashboard_page()

    elif menu == "History":

        history_page()






