from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.utils import ImageReader
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os

# Try to register the Mistrully cursive font
try:
    pdfmetrics.registerFont(TTFont('Mistrully', 'fonts/Mistrully.ttf'))
    SIGNATURE_FONT = 'Mistrully'
    SIGNATURE_FONT_SIZE = 40
except:
    # Fallback to italic Times
    SIGNATURE_FONT = 'Times-Italic'
    SIGNATURE_FONT_SIZE = 24

# Certificate details
COURSE_NAME = "Klever Blockchain: Construindo Smart Contracts na Prática"
COURSE_LOAD = "12 horas"
LOCATION = "Universidade de Fortaleza (UNIFOR)"
PROFESSOR_NAME = "Nicollas Gabriel"
PROFESSOR_TITLE = "Klever Blockchain Leader"
UNIFOR_LOGO_PATH = "./images/unifor.png"
KLEVER_LOGO_PATH = "./images/klever.png"
BACKGROUND_PATH = "./images/background.png"

# Load student names (replace this list or load from a CSV)
students = ["Fernando Sobreira", "João Beroni"]

# Output directory
os.makedirs("certificates", exist_ok=True)

# Generate certificates
for student in students:
    output_file = f"certificates/{student.replace(' ', '_')}_certificate.pdf"
    c = canvas.Canvas(output_file, pagesize=landscape(A4))
    width, height = landscape(A4)
    
    # Background image (if exists)
    if os.path.exists(BACKGROUND_PATH):
        c.drawImage(BACKGROUND_PATH, 0, 0, width=width, height=height)
    
    # Title
    c.setFont("Helvetica-Bold", 36)
    c.drawCentredString(width / 2, height - 120, "CERTIFICADO DE PARTICIPAÇÃO")
    
    # Main content with inline text
    text_y = height / 2 + 80
    
    # First line: "Certificamos que"
    c.setFont("Helvetica", 20)
    c.drawCentredString(width / 2, text_y, "Certificamos que")
    
    # Student name inline with larger font
    c.setFont("Helvetica-Bold", 28)
    c.drawCentredString(width / 2, text_y - 40, student.upper())
    
    # Course participation text
    c.setFont("Helvetica", 18)
    c.drawCentredString(width / 2, text_y - 80, f"participou do curso {COURSE_NAME}")
    
    # Event details
    c.setFont("Helvetica", 16)
    c.drawCentredString(width / 2, text_y - 115, f"realizado na {LOCATION}, com carga horária total de {COURSE_LOAD},")
    c.drawCentredString(width / 2, text_y - 140, "em Julho de 2025.")
    
    # Signature section
    signature_y = 180
    
    # Signature line
    line_start_x = width / 2 - 150
    line_end_x = width / 2 + 150
    c.line(line_start_x, signature_y, line_end_x, signature_y)
    
    # Draw signature using font
    c.setFont(SIGNATURE_FONT, SIGNATURE_FONT_SIZE)
    c.setFillColor(HexColor('#000080'))  # Navy blue
    c.drawCentredString(width / 2, signature_y + 5, PROFESSOR_NAME)
    
    # Reset color to black for name and title
    c.setFillColor(HexColor('#000000'))
    
    # Instructor name and title below line
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width / 2, signature_y - 25, PROFESSOR_NAME)
    c.setFont("Helvetica", 12)
    c.drawCentredString(width / 2, signature_y - 40, PROFESSOR_TITLE)
    
    # Logos at bottom - side by side, centered
    logo_y = 50
    logo_size = 80
    logo_spacing = 250
    
    # Calculate center positions for logos
    left_logo_x = width / 2 - logo_spacing / 2 - logo_size / 2
    right_logo_x = width / 2 + logo_spacing / 2 - logo_size / 2
    
    if os.path.exists(UNIFOR_LOGO_PATH):
        c.drawImage(UNIFOR_LOGO_PATH, left_logo_x, logo_y, width=logo_size, height=logo_size, preserveAspectRatio=True, mask='auto')
    
    if os.path.exists(KLEVER_LOGO_PATH):
        c.drawImage(KLEVER_LOGO_PATH, right_logo_x, logo_y, width=logo_size + 10, height=logo_size + 10, preserveAspectRatio=True, mask='auto')
    
    # Date at the very bottom
    c.setFont("Helvetica", 12)
    c.drawCentredString(width / 2, 25, "Fortaleza, Julho de 2025")
    
    c.save()
    print(f"Certificate generated for {student}: {output_file}")