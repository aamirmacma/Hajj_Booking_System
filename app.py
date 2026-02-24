import streamlit as st
import io
import re
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Image as RLImage, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from io import BytesIO

# --- OCR SETUP FOR PASSPORT SCANNER ---
try:
    import pytesseract
    from PIL import Image
except ImportError:
    pass

# --- HELPER FUNCTION: MODERN YES/NO BOXES ---
def get_yes_no_table(selected_val):
    # Professional Gold Highlight for selections
    y_bg = colors.HexColor("#FFC107") if selected_val == "YES" else colors.white
    n_bg = colors.HexColor("#FFC107") if selected_val == "NO" else colors.white
    
    t = Table([["YES", "NO"]], colWidths=[40, 40], rowHeights=[20])
    t.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor("#002060")),
        ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor("#002060")),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('BACKGROUND', (0,0), (0,0), y_bg),
        ('BACKGROUND', (1,0), (1,0), n_bg),
    ]))
    return t

# --- 1. PREMIUM PDF GENERATION FUNCTION ---
def create_pdf(fd):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=25, leftMargin=25, topMargin=25, bottomMargin=20)
    elements = []
    styles = getSampleStyleSheet()
    
    # Custom Styles for Premium Look
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=26,
        textColor=colors.HexColor("#002060"), # Royal Blue Title
        alignment=TA_CENTER,
        spaceAfter=5
    )
    subtitle_style = ParagraphStyle(
        'CustomSubTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=14,
        textColor=colors.black,
        alignment=TA_CENTER,
        spaceAfter=15
    )
    
    # Photo Box Handling (Clean Dashed look)
    img = Paragraph("<para align='center'><font color='#555555' size='9'><br/><br/><br/><br/><b>AFFIX<br/>PASSPORT SIZE<br/>PHOTO HERE</b></font></para>", styles['Normal'])
    if fd.get('photo'):
        try:
            img_bytes = fd['photo'].getvalue()
            img_io = io.BytesIO(img_bytes)
            img = RLImage(img_io, width=115, height=140)
        except Exception as e:
            pass

    title_p = Paragraph("HAJJ BOOKING FORM", title_style)
    subtitle_p = Paragraph("HAJJ 2026 - 1447 A.H", subtitle_style)
    
    # Combine Title for row 0
    header_content = [title_p, subtitle_p]

    full_name = f"{fd['app_title']}. {fd['given_name']}" if fd['app_title'] else fd['given_name']

    # --- PDF TABLE DATA STRUCTURE ---
    data = [
        [header_content, "", "", img],
        ["HAJJ APPLICANT DETAILS", "", "", ""], 
        ["SURNAME (AS PER PASSPORT)", fd['surname'].upper(), "TITLE & GIVEN NAME", full_name.upper()],
        ["FATHER / HUSBAND NAME\n(AS PER PASSPORT)", fd['guardian'].upper(), "", ""],
        ["CNIC NO / NICOP", fd['cnic'], "BLOOD GROUP", fd['blood']],
        ["DATE OF BIRTH", fd['dob'], "MARITAL STATUS", fd['marital'].upper()],
        ["PASSPORT NO", fd['passport'].upper(), "MOBILE NO", fd['mobile']],
        ["DATE OF ISSUE", fd['doi'], "WHATSAPP NO", fd['whatsapp']],
        ["DATE OF EXPIRY", fd['doe'], "OCCUPATION", fd['job'].upper()],
        ["EMAIL (Optional)", fd['email'], "COUNTRY STAY IN", fd['country'].upper()],
        ["RESIDENT ADDRESS", fd['address'].upper(), "", ""],
        ["PERFORM HAJJ IN LAST FIVE YEARS", get_yes_no_table(fd['hajj_5yr']), "HAJJ-E- BADAL", get_yes_no_table(fd['hajj_badal'])],
        
        ["NOMINEE IN CASE OF EMERGENCY (MUST BE ADULT/RELATIVE)", "", "", ""],
        ["NAME OF NOMINEE", fd['nom_name'].upper(), "NOMINEE RELATION", fd['nom_rel'].upper()],
        ["CNIC (MANDATORY)", fd['nom_cnic'], "MOBILE/WHATSAPP", fd['nom_mobile']],
        ["ADDRESS OF NOMINEE", fd['nom_address'].upper(), "", ""],
        
        ["HAJJ PACKAGE DETAILS", "", "", ""],
        ["HAJJ PACKAGE NO.", fd['pkg_no'], "MAKTAB / CATEGORY", fd['maktab'].upper()],
        ["MAKKAH HOTEL", fd['makkah_hotel'].upper(), "MAKKAH ROOM TYPE", fd['makkah_room_type']], 
        ["MADINAH HOTEL", fd['madinah_hotel'].upper(), "MADINAH ROOM TYPE", fd['madinah_room_type']], 
        ["AZIZIAH ROOM TYPE", fd['aziz_type'], "FLIGHT FROM", fd['flight_from'].upper()],             
        ["QURBANI", fd['qurbani'], "TICKETS", get_yes_no_table(fd['tickets'])],               
        ["FLIGHT DETAILS", fd['flight_details'].upper(), "", ""],
        
        ["FOR OFFICIAL USE ONLY", "", "", ""],
        ["INVOICE NO:", fd['invoice'], "REMARKS", fd['remarks']],
        ["COMPANY NAME", fd['company'].upper(), "", ""],
        ["REFERENCE", fd['reference'].upper(), "", ""]
    ]

    col_widths = [155, 135, 115, 140] 
    table = Table(data, colWidths=col_widths)
    
    # Premium Color Palette
    border_color = colors.HexColor("#002060") # Royal Blue Borders
    header_bg = colors.HexColor("#002060")    # Royal Blue Headers
    label_bg = colors.HexColor("#F0F2F6")     # Soft Modern Grey for labels
    official_bg = colors.HexColor("#D4AF37")  # Premium Gold for Official Use
    
    style = TableStyle([
        # Main Grid Design
        ('GRID', (0,0), (-1,-1), 1, border_color),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING', (0,0), (-1,-1), 7),
        ('BOTTOMPADDING', (0,0), (-1,-1), 7),
        ('LEFTPADDING', (0,0), (-1,-1), 8),
        ('RIGHTPADDING', (0,0), (-1,-1), 8),
        
        # Outer Thick Box for Premium feel
        ('BOX', (0,0), (-1,-1), 2, border_color),
        
        # Title Row Spans
        ('SPAN', (0,0), (2,0)),
        ('ALIGN', (0,0), (2,0), 'CENTER'),
        ('VALIGN', (0,0), (2,0), 'MIDDLE'),
        
        # Photo Spans
        ('SPAN', (3,0), (3,3)), 
        ('ALIGN', (3,0), (3,3), 'CENTER'),
        ('VALIGN', (3,0), (3,3), 'MIDDLE'),
        ('BACKGROUND', (3,0), (3,3), colors.whitesmoke), 

        # Sub-Headers (Applicant, Nominee, Package, Official)
        ('SPAN', (0,1), (2,1)), 
        ('BACKGROUND', (0,1), (2,1), header_bg),
        ('TEXTCOLOR', (0,1), (2,1), colors.white),
        ('ALIGN', (0,1), (2,1), 'CENTER'),
        ('FONTNAME', (0,1), (2,1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,1), (2,1), 10),
        
        ('SPAN', (0,12), (3,12)), 
        ('BACKGROUND', (0,12), (3,12), header_bg),
        ('TEXTCOLOR', (0,12), (3,12), colors.white),
        ('ALIGN', (0,12), (3,12), 'CENTER'),
        ('FONTNAME', (0,12), (3,12), 'Helvetica-Bold'),
        ('FONTSIZE', (0,12), (3,12), 10),

        ('SPAN', (0,16), (3,16)), 
        ('BACKGROUND', (0,16), (3,16), header_bg),
        ('TEXTCOLOR', (0,16), (3,16), colors.white),
        ('ALIGN', (0,16), (3,16), 'CENTER'),
        ('FONTNAME', (0,16), (3,16), 'Helvetica-Bold'),
        ('FONTSIZE', (0,16), (3,16), 10),

        ('SPAN', (0,23), (3,23)), 
        ('BACKGROUND', (0,23), (3,23), header_bg),
        ('TEXTCOLOR', (0,23), (3,23), colors.white),
        ('ALIGN', (0,23), (3,23), 'CENTER'),
        ('FONTNAME', (0,23), (3,23), 'Helvetica-Bold'),
        ('FONTSIZE', (0,23), (3,23), 10),

        # Value Cell Spans
        ('SPAN', (1,3), (3,3)),   # Father Name
        ('SPAN', (1,10), (3,10)), # Address
        ('SPAN', (1,15), (3,15)), # Nominee Address
        ('SPAN', (1,22), (3,22)), # Flight Details
        
        ('SPAN', (3,24), (3,26)), # Remarks Box
        ('SPAN', (1,25), (2,25)), # Company Name
        ('SPAN', (1,26), (2,26)), # Reference

        # Grey Labels Alignment & Formatting
        ('BACKGROUND', (0,2), (0,11), label_bg), 
        ('BACKGROUND', (2,2), (2,2), label_bg),  
        ('BACKGROUND', (2,4), (2,9), label_bg),  
        ('BACKGROUND', (2,11), (2,11), label_bg),
        
        ('BACKGROUND', (0,13), (0,15), label_bg), 
        ('BACKGROUND', (2,13), (2,14), label_bg), 
        
        ('BACKGROUND', (0,17), (0,22), label_bg), 
        ('BACKGROUND', (2,17), (2,21), label_bg), 
        
        ('BACKGROUND', (0,24), (0,26), official_bg), 
        ('BACKGROUND', (2,24), (2,24), official_bg), 
        
        ('FONTNAME', (0,2), (0,11), 'Helvetica-Bold'),
        ('FONTNAME', (2,2), (2,2), 'Helvetica-Bold'), 
        ('FONTNAME', (2,4), (2,11), 'Helvetica-Bold'),
        ('FONTNAME', (0,13), (0,15), 'Helvetica-Bold'),
        ('FONTNAME', (2,13), (2,14), 'Helvetica-Bold'),
        ('FONTNAME', (0,17), (0,22), 'Helvetica-Bold'),
        ('FONTNAME', (2,17), (2,21), 'Helvetica-Bold'),
        
        ('FONTSIZE', (0,11), (0,11), 8), # Specific resize for 'Perform hajj in last 5 years'
    ])
    
    table.setStyle(style)
    elements.append(table)
    
    # --- FOOTER SECTION ---
    elements.append(Spacer(1, 20))
    footer_text = f"<i>Generated securely via Professional Booking Management System on {datetime.now().strftime('%d-%b-%Y')}</i>"
    footer_p = Paragraph(footer_text, ParagraphStyle('Footer', parent=styles['Normal'], alignment=TA_RIGHT, textColor=colors.grey, fontSize=8))
    elements.append(footer_p)

    doc.build(elements)
    return buffer.getvalue()


# --- 2. STREAMLIT APP INTERFACE ---
st.set_page_config(page_title="Hajj Booking System", layout="wide", page_icon="🕋")

st.markdown("""
    <div style='background-color: #002060; padding: 15px; border-radius: 10px; margin-bottom: 20px;'>
        <h1 style='text-align: center; color: white; margin: 0;'>🕋 HAJJ BOOKING MANAGEMENT SYSTEM</h1>
    </div>
""", unsafe_allow_html=True)

st.sidebar.header("📂 Manage Records")
form_choice = st.sidebar.selectbox("Select Applicant Data:", ["New Blank Form", "Korsar Rasul", "Imran Sheikh", "Mahira Faiz"])

# --- PASSPORT SCANNER (MRZ) ---
st.markdown("### 🛂 Auto-Fill from Passport (MRZ Scanner)")
st.info("💡 Passport ki clear picture upload karein. System 'Surname', 'Given Name', 'Title', 'CNIC', 'DOB' aur 'Passport No' automatically fill kar dega.")
passport_scan = st.file_uploader("Upload Passport Image (JPG/PNG)", type=["jpg", "jpeg", "png"], key="scanner")

ocr_data = {}
if passport_scan:
    try:
        img_for_ocr = Image.open(passport_scan)
        with st.spinner("🔍 Passport Read ho raha hai... Please wait."):
            text = pytesseract.image_to_string(img_for_ocr)
            lines = text.split('\n')
            
            mrz_lines = [line.strip().replace(" ", "") for line in lines if '<' in line and len(line.strip()) > 20]
            
            if len(mrz_lines) >= 2:
                line1 = mrz_lines[-2]
                line2 = mrz_lines[-1] 
                
                if line1.startswith('P'):
                    parts = line1[5:].split('<<')
                    if len(parts) >= 2:
                        ocr_data['surname'] = parts[0].replace('<', ' ').strip()
                        ocr_data['given_name'] = parts[1].replace('<', ' ').strip()
                
                if len(line2) >= 30:
                    ocr_data['passport'] = line2[0:9].replace('<', '')
                    dob_yy = line2[13:15]
                    dob_mm = line2[15:17]
                    dob_dd = line2[17:19]
                    year_prefix = "19" if dob_yy.isdigit() and int(dob_yy) > 25 else "20"
                    if dob_dd.isdigit() and dob_mm.isdigit():
                        ocr_data['dob'] = f"{dob_dd}/{dob_mm}/{year_prefix}{dob_yy}"
                    
                    gender = line2[20]
                    if gender == 'M': ocr_data['title'] = 'MR'
                    elif gender == 'F': ocr_data['title'] = 'MRS'
                        
                    exp_yy = line2[21:23]
                    exp_mm = line2[23:25]
                    exp_dd = line2[25:27]
                    if exp_dd.isdigit() and exp_mm.isdigit():
                        ocr_data['doe'] = f"{exp_dd}/{exp_mm}/20{exp_yy}"
                        
                    cnic = line2[28:41].replace('<', '')
                    if len(cnic) == 13 and cnic.isdigit():
                        ocr_data['cnic'] = f"{cnic[:5]}-{cnic[5:12]}-{cnic[12]}"
                        
            doi_match = re.search(r'(?:Date of Issue|DateofIssue).*?(\d{2})[\s/-]*([A-Za-z]{3})[\s/-]*(\d{4})', text, re.IGNORECASE)
            if doi_match:
                ocr_data['doi'] = f"{doi_match.group(1)} {doi_match.group(2).upper()} {doi_match.group(3)}"

            if ocr_data: st.success(f"✅ Data 100% Extracted! Welcome {ocr_data.get('title', '')} {ocr_data.get('surname', '')}")
            else: st.warning("⚠️ Passport MRZ clear read nahi hua. Please saaf tasveer upload karein.")
                
    except Exception as e:
        st.error("⚠️ Scanner Error: System OCR ko theek se nahi parh pa raha. Tesseract file missing ho sakti hai.")

# --- PRESETS & DROPDOWNS ---
presets = {
    "New Blank Form": {k: "" for k in ['surname','given_name','guardian','cnic','blood','dob','marital','passport','mobile','doi','whatsapp','doe','job','email','country','address','hajj_5yr','hajj_badal','nom_name','nom_rel','nom_cnic','nom_mobile','nom_address','pkg_no','maktab','makkah_hotel','makkah_room_type','madinah_hotel','madinah_room_type','flight_from','aziz_type','tickets', 'qurbani', 'flight_details','invoice','remarks','company','reference']},
    "Korsar Rasul": {'surname': "RASUL", 'given_name': "KORSAR", 'guardian': "ABID HUSSAIN", 'cnic': "9140001304292", 'blood': "A+", 'dob': "7/16/1978", 'marital': "Married", 'passport': "AS456321", 'mobile': "03008912129", 'doi': "7/16/2015", 'whatsapp': "03008912129", 'doe': "7/16/2030", 'job': "AHMED", 'email': "", 'country': "United Kingdom", 'address': "23 Malmesbury Road, Birmingham, West Midlands, B10 0JG United Kingdom", 'hajj_5yr': "NO", 'hajj_badal': "NO", 'nom_name': "UMER AYAZ", 'nom_rel': "COUSIN", 'nom_cnic': "8130108651631", 'nom_mobile': "923474374778", 'nom_address': "", 'pkg_no': "Package # 05 (17 DAYS)", 'maktab': "", 'makkah_hotel': "", 'makkah_room_type': "DOUBLE", 'madinah_hotel': "", 'madinah_room_type': "DOUBLE", 'flight_from': "", 'aziz_type': "DOUBLE", 'tickets': "YES", 'qurbani': "INCLUDE", 'flight_details': "", 'invoice': "", 'remarks': "", 'company': "", 'reference': ""},
    "Imran Sheikh": {'surname': "SHEIKH", 'given_name': "IMRAN", 'guardian': "AMEER-UD-DIN SHEIKH", 'cnic': "3520215340823", 'blood': "B+", 'dob': "11/13/1984", 'marital': "Married", 'passport': "AS1234567", 'mobile': "44 7903832425", 'doi': "01/JAN/2014", 'whatsapp': "44 7903832425", 'doe': "01/JAN/2030", 'job': "PRIVATE SERVICE", 'email': "avcfcxcbfcgnfgn@GMAIL.COM", 'country': "United Kingdom", 'address': "24 HOLLINGSWORTH ROAD, CROYDON, CR0 5RP SURREY, UNITED KINGDOM", 'hajj_5yr': "NO", 'hajj_badal': "NO", 'nom_name': "TANYA QADEER", 'nom_rel': "SISTER", 'nom_cnic': "35201-7844030 0", 'nom_mobile': "+44 7737 542493", 'nom_address': "23 HARTLEY DOWN, PURLEY, LONDON, SURREY, CR8 4EF", 'pkg_no': "Package # 05 (17 DAYS)", 'maktab': "", 'makkah_hotel': "", 'makkah_room_type': "DOUBLE", 'madinah_hotel': "", 'madinah_room_type': "DOUBLE", 'flight_from': "", 'aziz_type': "DOUBLE", 'tickets': "YES", 'qurbani': "INCLUDE", 'flight_details': "", 'invoice': "", 'remarks': "", 'company': "", 'reference': ""},
    "Mahira Faiz": {'surname': "FAIZ", 'given_name': "MAHIRA", 'guardian': "SHEHARYAR KHAN", 'cnic': "42201-0522296-8", 'blood': "", 'dob': "30 - AUG - 1992", 'marital': "Married", 'passport': "AE8912963", 'mobile': "00971-504712952", 'doi': "04 - MAY - 2016", 'whatsapp': "00971-504712952", 'doe': "02 - MAY - 2026", 'job': "HOUSE WIFE", 'email': "sheharyark1987@gmail.com", 'country': "United Arab Emirates", 'address': "Flat 201, Villa 33, Shabiya 2, Musaffah, MBZ City Abu Dhabi - UAE", 'hajj_5yr': "NO", 'hajj_badal': "NO", 'nom_name': "", 'nom_rel': "", 'nom_cnic': "", 'nom_mobile': "", 'nom_address': "", 'pkg_no': "", 'maktab': "", 'makkah_hotel': "", 'makkah_room_type': "", 'madinah_hotel': "", 'madinah_room_type': "", 'flight_from': "", 'aziz_type': "", 'tickets': "YES", 'qurbani': "NOT INCLUDE", 'flight_details': "", 'invoice': "", 'remarks': "", 'company': "", 'reference': ""}
}

d = presets[form_choice]

blood_list = ["", "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"]
country_list = [
    "", "Afghanistan", "Albania", "Algeria", "Andorra", "Angola", "Argentina", "Armenia", "Australia", 
    "Austria", "Azerbaijan", "Bahrain", "Bangladesh", "Belgium", "Brazil", "Canada", "China", "Denmark", 
    "Egypt", "Finland", "France", "Germany", "Greece", "India", "Indonesia", "Iran", "Iraq", "Ireland", 
    "Italy", "Japan", "Jordan", "Kuwait", "Lebanon", "Malaysia", "Maldives", "Morocco", "Netherlands", 
    "New Zealand", "Norway", "Oman", "Pakistan", "Palestine", "Qatar", "Russia", "Saudi Arabia", 
    "Singapore", "South Africa", "Spain", "Sri Lanka", "Sweden", "Switzerland", "Syria", "Turkey", 
    "United Arab Emirates", "United Kingdom", "USA", "Yemen", "Other"
]
marital_list = ["Single", "Married", "Widowed", "Divorced"]
package_list = ["", "Package # 01 (10/11 Days)", "Package # 02 (13/14 Days)", "Package # 03 (13/14 DAYS)", "Package # 04 (17/18 DAYS)", "Package # 05 (17 DAYS)", "Package # 06 (22 DAYS)", "Package # 07 (14 DAYS)", "Package # 08 (14 DAYS)"]
title_list = ["MR", "MRS", "MS", "CHILD", "INF"]
room_types_list = ["DOUBLE", "TRIPLE", "QUAD", "SHARING", "N/A", ""]

blood_index = blood_list.index(d.get('blood', '')) if d.get('blood', '') in blood_list else 0
m_status = d.get('marital', 'Single').capitalize()
marital_index = marital_list.index(m_status) if m_status in marital_list else 0
c_status = d.get('country', '')
if c_status not in country_list and c_status != "": country_list.append(c_status)
country_index = country_list.index(c_status) if c_status in country_list else 0
pkg_index = next((i for i, pkg in enumerate(package_list) if d.get('pkg_no', '') in pkg), 0) if d.get('pkg_no', '') else 0

st.markdown("---")

with st.form("hajj_form"):
    c_photo1, c_photo2 = st.columns([3, 1])
    with c_photo1:
        st.subheader("1. Applicant Details")
    with c_photo2:
        st.markdown("**📸 Photo Upload (Form Header)**")
        uploaded_photo = st.file_uploader("Upload Image", type=["jpg", "jpeg", "png"], label_visibility="collapsed")
        if uploaded_photo: st.image(uploaded_photo, width=110, caption="Preview")

    c1, c2 = st.columns(2)
    with c1:
        col_t, col_s = st.columns([1, 2])
        with col_t:
            title_val = ocr_data.get('title', 'MR')
            t_idx = title_list.index(title_val) if title_val in title_list else 0
            app_title = st.selectbox("Title", title_list, index=t_idx)
        with col_s:
            surname = st.text_input("Surname", ocr_data.get('surname', d.get('surname', '')))
            
        given_name = st.text_input("Given Name", ocr_data.get('given_name', d.get('given_name', '')))
        guardian = st.text_input("Father/Husband", d.get('guardian', ''))
        cnic = st.text_input("CNIC / NICOP", ocr_data.get('cnic', d.get('cnic', '')))
        dob = st.text_input("Date of Birth", ocr_data.get('dob', d.get('dob', '')))
        passport = st.text_input("Passport No", ocr_data.get('passport', d.get('passport', '')))
        doi = st.text_input("Date of Issue", ocr_data.get('doi', d.get('doi', '')))
        doe = st.text_input("Date of Expiry", ocr_data.get('doe', d.get('doe', '')))
        email = st.text_input("Email", d.get('email', ''))
    with c2:
        blood = st.selectbox("Blood Group", blood_list, index=blood_index)
        marital = st.selectbox("Marital Status", marital_list, index=marital_index)
        country = st.selectbox("Country Stay In", country_list, index=country_index)
        mobile = st.text_input("Mobile No", d.get('mobile', ''))
        whatsapp = st.text_input("WhatsApp No", d.get('whatsapp', ''))
        job = st.text_input("Occupation", d.get('job', ''))
        
    address = st.text_area("Resident Address", d.get('address', ''))
    
    col_h1, col_h2 = st.columns(2)
    with col_h1:
        hajj_5yr = st.radio("Hajj in Last 5 Years?", ["YES", "NO"], index=0 if d.get('hajj_5yr')=="YES" else 1, horizontal=True)
    with col_h2:
        hajj_badal = st.radio("Hajj-e-Badal?", ["YES", "NO"], index=0 if d.get('hajj_badal')=="YES" else 1, horizontal=True)

    st.markdown("---")
    st.subheader("2. Nominee Details")
    n1, n2 = st.columns(2)
    with n1:
        nom_name = st.text_input("Nominee Name", d.get('nom_name', ''))
        nom_cnic = st.text_input("Nominee CNIC", d.get('nom_cnic', ''))
    with n2:
        nom_rel = st.text_input("Relation", d.get('nom_rel', ''))
        nom_mobile = st.text_input("Nominee Mobile", d.get('nom_mobile', ''))
    nom_address = st.text_input("Nominee Address", d.get('nom_address', ''))

    st.markdown("---")
    st.subheader("3. Package Details")
    
    p1, p2 = st.columns(2)
    with p1:
        pkg_no = st.selectbox("Package No", package_list, index=pkg_index)
        makkah_hotel = st.text_input("Makkah Hotel", d.get('makkah_hotel', ''))
        madinah_hotel = st.text_input("Madinah Hotel", d.get('madinah_hotel', ''))
        
        aziz_idx = room_types_list.index(d.get('aziz_type', '')) if d.get('aziz_type', '') in room_types_list else 0
        aziz_type = st.selectbox("Aziziah Room Type", room_types_list, index=aziz_idx)
        
        qurbani = st.radio("Qurbani Included?", ["INCLUDE", "NOT INCLUDE"], index=0 if d.get('qurbani')=="INCLUDE" else 1, horizontal=True)
        
    with p2:
        maktab = st.text_input("Maktab / Category", d.get('maktab', ''))
        
        mak_room_idx = room_types_list.index(d.get('makkah_room_type', '')) if d.get('makkah_room_type', '') in room_types_list else 0
        makkah_room_type = st.selectbox("Makkah Room Type", room_types_list, index=mak_room_idx)
        
        mad_room_idx = room_types_list.index(d.get('madinah_room_type', '')) if d.get('madinah_room_type', '') in room_types_list else 0
        madinah_room_type = st.selectbox("Madinah Room Type", room_types_list, index=mad_room_idx)
        
        flight_from = st.text_input("Flight From", d.get('flight_from', ''))
        tickets = st.radio("Tickets Included?", ["YES", "NO"], index=0 if d.get('tickets')=="YES" else 1, horizontal=True)
    
    flight_details = st.text_area("Flight Details", d.get('flight_details', ''))

    st.markdown("---")
    st.subheader("4. Official Use")
    o1, o2 = st.columns(2)
    with o1:
        invoice = st.text_input("Invoice No", d.get('invoice', ''))
        company = st.text_input("Company Name", d.get('company', ''))
        reference = st.text_input("Reference", d.get('reference', ''))
    with o2:
        remarks = st.text_area("Remarks", d.get('remarks', ''))

    st.markdown("---")
    
    # 🔴 BARA SUBMIT BUTTON
    submitted = st.form_submit_button("📄 GENERATE PREMIUM PDF", use_container_width=True)

if submitted:
    form_data = {
        'photo': uploaded_photo, 
        'app_title': app_title, 
        'surname': surname, 'given_name': given_name, 'guardian': guardian, 'cnic': cnic, 'blood': blood,
        'dob': dob, 'marital': marital, 'passport': passport, 'mobile': mobile,
        'doi': doi, 'whatsapp': whatsapp, 'doe': doe, 'job': job,
        'email': email, 'country': country, 'address': address,
        'hajj_5yr': hajj_5yr, 'hajj_badal': hajj_badal,
        'nom_name': nom_name, 'nom_rel': nom_rel, 'nom_cnic': nom_cnic,
        'nom_mobile': nom_mobile, 'nom_address': nom_address,
        'pkg_no': pkg_no, 'maktab': maktab, 
        'makkah_hotel': makkah_hotel, 'makkah_room_type': makkah_room_type,
        'madinah_hotel': madinah_hotel, 'madinah_room_type': madinah_room_type, 
        'flight_from': flight_from, 'aziz_type': aziz_type, 'tickets': tickets,
        'qurbani': qurbani, 
        'flight_details': flight_details,
        'invoice': invoice, 'company': company, 'reference': reference, 'remarks': remarks
    }
    
    with st.spinner('Preparing Professional PDF...'):
        pdf_bytes = create_pdf(form_data)
        
    st.success("🎉 PDF is ready! Click below to download your premium formatted document.")
    
    # Clean Download Button
    st.download_button(
        label="📥 DOWNLOAD PDF NOW",
        data=pdf_bytes,
        file_name=f"Hajj_Booking_{surname}_{given_name}.pdf",
        mime="application/pdf",
        use_container_width=True
    )
