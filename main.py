from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.utils import ImageReader
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os
import csv
from datetime import datetime

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
LOCATION_DATE = "Fortaleza, Julho de 2025"
PROFESSOR_NAME = "Nicollas Gabriel"
PROFESSOR_TITLE = "Klever Blockchain Leader"
UNIFOR_LOGO_PATH = "./images/unifor.png"
KLEVER_LOGO_PATH = "./images/klever.png"
BACKGROUND_PATH = "./images/background.png"

# Load student names
def load_students():
    """Load students from CSV file if exists, otherwise use default list"""
    csv_file = "students.csv"
    if os.path.exists(csv_file):
        students = []
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader, None)  # Skip header if exists
            for row in reader:
                if row:  # Check if row is not empty
                    students.append(row[0])
        return students
    else:
        # throw error loading students
        print(f"⚠️ Warning: {csv_file} not found! Using default student list.")
        return []

students = load_students()

# Output directory
os.makedirs("certificates", exist_ok=True)

# Certificate ID counter
certificate_id = 1000

# Generate certificates
for idx, student in enumerate(students):
    output_file = f"certificates/{student.replace(' ', '_')}_certificate.pdf"
    c = canvas.Canvas(output_file, pagesize=landscape(A4))
    width, height = landscape(A4)
    
    # Background image (if exists)
    if os.path.exists(BACKGROUND_PATH):
        c.drawImage(BACKGROUND_PATH, 0, 0, width=width, height=height)
    
    # Add border frame
    c.setStrokeColor(HexColor('#cccccc'))
    c.setLineWidth(2)
    c.rect(30, 30, width - 60, height - 60, stroke=1, fill=0)
    
    # Title with better spacing
    c.setFont("Helvetica-Bold", 42)
    c.setFillColor(HexColor('#1a237e'))  # Dark blue for title
    c.drawCentredString(width / 2, height - 100, "CERTIFICADO DE PARTICIPAÇÃO")
    
    # Reset to black for body text
    c.setFillColor(HexColor('#000000'))
    
    # Main content with inline text
    text_y = height / 2 + 80
    
    # First line: "Certificamos que"
    c.setFont("Helvetica", 20)
    c.drawCentredString(width / 2, text_y, "Certificamos que")
    
    # Student name with emphasis
    c.setFont("Helvetica-Bold", 32)
    c.setFillColor(HexColor('#1a237e'))  # Highlight student name
    c.drawCentredString(width / 2, text_y - 45, student.upper())
    
    # Reset to black
    c.setFillColor(HexColor('#000000'))
    
    # Course participation text
    c.setFont("Helvetica", 18)
    c.drawCentredString(width / 2, text_y - 85, "participou do curso")
    
    # Course name with emphasis
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(width / 2, text_y - 115, COURSE_NAME)
    
    # Event details
    c.setFont("Helvetica", 16)
    c.drawCentredString(width / 2, text_y - 150, f"realizado na {LOCATION}, com carga horária total de {COURSE_LOAD},")
    c.drawCentredString(width / 2, text_y - 175, "em Julho de 2025.")
    
    # Signature section
    signature_y = 150
    
    # Signature line
    line_start_x = width / 2 - 150
    line_end_x = width / 2 + 150
    c.setLineWidth(1)
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
    
    # Certificate ID and verification
    c.setFont("Helvetica", 10)
    c.setFillColor(HexColor('#666666'))
    cert_number = f"ID: KLC-{certificate_id + idx}"
    c.drawString(40, 45, cert_number)
    c.drawRightString(width - 40, 45, f"Verificação: klever.org/verify/{cert_number}")
    
    # Logos at bottom - side by side, centered
    logo_y = 45
    logo_size = 70
    logo_spacing = 220
    
    # Calculate center positions for logos
    left_logo_x = width / 2 - logo_spacing / 2 - logo_size / 2
    right_logo_x = width / 2 + logo_spacing / 2 - logo_size / 2
    
    if os.path.exists(UNIFOR_LOGO_PATH):
        c.drawImage(UNIFOR_LOGO_PATH, left_logo_x, logo_y, width=logo_size, height=logo_size, preserveAspectRatio=True, mask='auto')
    
    if os.path.exists(KLEVER_LOGO_PATH):
        c.drawImage(KLEVER_LOGO_PATH, right_logo_x, logo_y, width=logo_size, height=logo_size, preserveAspectRatio=True, mask='auto')
    
    # Date at the very bottom
    c.setFont("Helvetica", 12)
    c.setFillColor(HexColor('#000000'))
    c.drawCentredString(width / 2, 40, LOCATION_DATE)
    
    c.save()
    print(f"✓ Certificate generated for {student}: {output_file} (ID: KLC-{certificate_id + idx})")

# Create sample students.csv if it doesn't exist
if not os.path.exists("students.csv"):
    with open("students.csv", "w", encoding='utf-8') as f:
        f.write("name\n")
        f.write("Fernando Sobreira\n")
        f.write("João Beroni\n")
    print("\n📝 Created students.csv - Add more students to this file and run again!")

print(f"\n✅ Generated {len(students)} certificates successfully!")