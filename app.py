import streamlit as st
from PyPDF2 import PdfReader, PdfWriter
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from PIL import Image
import io
import tempfile
import os

st.set_page_config(
    page_title="Bewirti - Der Bewirtungsbeleg Buddy",
    page_icon="🧾",
    layout="centered",
    initial_sidebar_state="collapsed",
    menu_items={
        'Get Help': 'https://yannik.swokiz.com/contact',
        'Report a bug': "https://yannik.swokiz.com/contact",
        'About': "# This is a header. This is an *extremely* cool app!"
    }
)

st.title("🧾 Bewirti - Der Bewirtungsbeleg Buddy")
st.logo("res/logo.png", size="large")

col1, col2 = st.columns([0.3, 0.7])
with col1:
    st.image("res/logo_square.png")
with col2:
    st.markdown("""
    Dieses Tool hilft dir dabei, schnell und unkompliziert einen professionellen Bewirtungsbeleg zu erstellen.  
    Du kannst folgende Angaben machen:

    - Anlass und Datum der Bewirtung  
    - Die bewirteten Personen  
    - Betrag, Trinkgeld und Gesamtbetrag  
    - Ein Foto machen oder ein bereits vorhandenes Belegdokument hochladen  
    - Der generierte PDF-Beleg enthält außerdem ein Feld für die Unterschrift

    Klicke unten auf **"Generiere Beleg"**, um die PDF-Datei zu erstellen und herunterzuladen.
    """)

reason = st.text_input("Anlass der Bewirtung")
date = st.date_input("Tag der Bewirtung")

persons_str = st.text_area("Bewirtete Personen")
persons = [p.strip() for p in persons_str.split("\n") if p.strip()]

amount = st.number_input("Betrag", min_value=0.1, format="%.2f")
tip = st.number_input("Trinkgeld", min_value=0.0, format="%.2f")
total_amount = amount + tip

add_logo = st.checkbox("Logo hinzufügen", value=True)
upload_existing_file = st.checkbox("Bestehenden Beleg hochladen", value=True)
took_picture = None
uploaded_file = None

if upload_existing_file:
    uploaded_file = st.file_uploader("Beleg", disabled=not upload_existing_file)
else:
    took_picture = st.camera_input("Take a picture", disabled=upload_existing_file)

btn_generate_pdf = st.button("Generiere Beleg", type="primary")

if btn_generate_pdf:
    errors = []

    if not reason.strip():
        errors.append("Bitte gib den Anlass der Bewirtung an.")
    if len(persons) < 2:
        errors.append("Bitte gib mindestens zwei bewirtete Personen an.")
    if not (took_picture or uploaded_file):
        errors.append("Bitte lade einen Beleg hoch oder nimm ein Foto auf.")

    if errors:
        for error in errors:
            st.error(error)
        st.stop()

    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    if add_logo:
        logo_path = "res/bewirti_logo.png"

        try:
            logo = Image.open(logo_path)
            logo_width_original, logo_height_original = logo.size

            # Set a desired display width
            display_width = 150  # in points
            aspect_ratio = logo_height_original / logo_width_original
            display_height = display_width * aspect_ratio

            c.drawImage(
                logo_path,
                A4[0] - display_width - 50,       # x position
                A4[1] - display_height - 30,      # y position
                width=display_width,
                height=display_height,
                mask='auto'
            )

        except Exception as e:
            st.warning(f"Logo konnte nicht geladen werden: {e}")

    # Title & general info
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, "Bewirtungsbeleg")

    c.setFont("Helvetica-Bold", 11)
    y = height - 80
    line_spacing = 18

    c.drawString(50, y, "Anlass der Bewirtung:")
    c.setFont("Helvetica", 11)
    c.drawString(180, y, reason)

    y -= line_spacing
    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, y, "Tag der Bewirtung:")
    c.setFont("Helvetica", 11)
    c.drawString(180, y, date.strftime('%d.%m.%Y'))

    y -= line_spacing
    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, y, "Betrag:")
    c.setFont("Helvetica", 11)
    c.drawString(180, y, f"{amount:.2f} €")

    y -= line_spacing
    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, y, "Trinkgeld:")
    c.setFont("Helvetica", 11)
    c.drawString(180, y, f"{tip:.2f} €")

    y -= line_spacing
    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, y, "Gesamtbetrag:")
    c.setFont("Helvetica", 11)
    c.drawString(180, y, f"{total_amount:.2f} €")

    y -= line_spacing * 2
    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, y, "Bewirtete Personen:")

    y -= line_spacing
    c.setFont("Helvetica", 11)
    for person in persons:
        c.drawString(70, y, f"- {person}")
        y -= line_spacing

    # Signature line
    signature_y = 100
    c.line(50, signature_y, 250, signature_y)
    c.drawString(50, signature_y - 15, "Unterschrift")

    # Footer note
    footer_text = "Dieser Beleg wurde erstellt mit Bewirti – Der Bewirtungsbeleg Buddy - bewirti.swokiz.com"
    c.setFont("Helvetica-Oblique", 8)
    c.drawCentredString(width / 2, 30, footer_text)

    c.showPage()

    # Handle uploaded or camera image
    img_bytes = None

    if took_picture:
        img_bytes = took_picture.getvalue()
    elif uploaded_file:
        uploaded_bytes = uploaded_file.read()
        if uploaded_file.name.lower().endswith(".pdf"):
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
            temp_file.write(uploaded_bytes)
            temp_file.close()
            pdf_path = temp_file.name
            c.save()
            buffer.seek(0)

            output = PdfWriter()
            output.append(PdfReader(buffer))
            output.append(PdfReader(pdf_path))

            final_pdf = io.BytesIO()
            output.write(final_pdf)
            final_pdf.seek(0)

            st.download_button("Download Beleg-PDF", final_pdf, file_name="bewirtungsbeleg.pdf")
            os.remove(pdf_path)
            st.success("Beleg erstellt mit hochgeladenem PDF.")
            st.stop()
        else:
            img_bytes = uploaded_bytes

    if img_bytes:
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        img_temp = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
        img.save(img_temp.name, format="JPEG")

        # Add image to a new page
        img_width, img_height = img.size
        aspect_ratio = img_height / img_width
        max_width = width - 100
        scaled_height = max_width * aspect_ratio

        c.drawImage(img_temp.name, 50, height - scaled_height - 50,
                    width=max_width, height=scaled_height)
        c.showPage()

        os.remove(img_temp.name)

    c.save()
    buffer.seek(0)

    st.download_button("Download Beleg-PDF", buffer, file_name="bewirtungsbeleg.pdf")
    st.success("Beleg erfolgreich erstellt.")

# Add footer with Impressum link
st.markdown("""
---
Bitte beachten Sie, dass dieser Service keine steuerliche oder rechtliche Beratung ersetzt.  
**Unter Ausschluss jeglicher Gewährleistung!**  
📄 [Impressum](https://yannik.swokiz.com/impressum/)
📄 [GitHub](https://github.com/ykorzikowski/belegi)
""", unsafe_allow_html=True)