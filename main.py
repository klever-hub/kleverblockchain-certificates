from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib.utils import ImageReader
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os
import csv
import qrcode
from io import BytesIO

# Try to register the Mistrully cursive font
try:
    pdfmetrics.registerFont(TTFont('Mistrully', 'fonts/Mistrully.ttf'))
    SIGNATURE_FONT = 'Mistrully'
    SIGNATURE_FONT_SIZE = 40
except:
    # Fallback to italic Times
    SIGNATURE_FONT = 'Times-Italic'
    SIGNATURE_FONT_SIZE = 24

# NFT Configuration
NFT_TICKER = "KLVCERT-ABC"  # NFT Collection ticker
NFT_STARTING_NONCE = 1  # Starting nonce for NFT IDs

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

def generate_qr_code(data):
    """Generate QR code with logo in center and return as image data"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,  # High error correction for logo
        box_size=10,
        border=1,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white").convert('RGB')
    
    # Add logo to center if exists
    logo_path = "./images/kleverlogo.png"
    if os.path.exists(logo_path):
        from PIL import Image, ImageDraw
        logo = Image.open(logo_path)
        
        # Calculate logo size (about 1/5 of QR code)
        qr_width, qr_height = img.size
        logo_size = min(qr_width, qr_height) // 5
        
        # Resize logo
        logo = logo.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
        
        # Convert logo to RGBA if not already
        if logo.mode != 'RGBA':
            logo = logo.convert('RGBA')
        
        # Create a circular white background
        circle_size = logo_size + 20
        circle_img = Image.new('RGBA', (circle_size, circle_size), (255, 255, 255, 0))
        
        # Create circular mask for the entire circle
        mask_full = Image.new('L', (circle_size, circle_size), 0)
        draw_mask = ImageDraw.Draw(mask_full)
        draw_mask.ellipse((0, 0, circle_size - 1, circle_size - 1), fill=255)
        
        # Draw white circle
        draw_circle = ImageDraw.Draw(circle_img)
        draw_circle.ellipse((0, 0, circle_size - 1, circle_size - 1), fill='white')
        
        # Create mask for logo
        logo_mask = Image.new('L', (logo_size, logo_size), 0)
        draw_logo_mask = ImageDraw.Draw(logo_mask)
        draw_logo_mask.ellipse((0, 0, logo_size - 1, logo_size - 1), fill=255)
        
        # Apply mask to logo
        logo_circular = Image.new('RGBA', (logo_size, logo_size), (255, 255, 255, 0))
        logo_circular.paste(logo, (0, 0), logo_mask)
        
        # Paste logo onto circle
        logo_offset = (circle_size - logo_size) // 2
        circle_img.paste(logo_circular, (logo_offset, logo_offset), logo_circular)
        
        # Apply the full circle mask
        final_logo = Image.new('RGBA', (circle_size, circle_size), (255, 255, 255, 0))
        final_logo.paste(circle_img, (0, 0), mask_full)
        
        # Convert to RGB for QR code
        final_logo_rgb = Image.new('RGB', (circle_size, circle_size), 'white')
        final_logo_rgb.paste(final_logo, (0, 0), final_logo)
        
        # Paste onto QR code
        logo_pos = ((qr_width - circle_size) // 2, (qr_height - circle_size) // 2)
        img.paste(final_logo_rgb, logo_pos)
    
    # Convert to bytes
    img_bytes = BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    
    return img_bytes

students = load_students()

# Output directory
os.makedirs("certificates", exist_ok=True)

# Generate certificates
for idx, student in enumerate(students):
    output_file = f"certificates/{student.replace(' ', '_')}_certificate.pdf"
    c = canvas.Canvas(output_file, pagesize=landscape(A4))
    width, height = landscape(A4)
    
    # Calculate NFT ID
    nft_nonce = NFT_STARTING_NONCE + idx
    nft_id = f"{NFT_TICKER}/{nft_nonce}"
    verify_url = f"https://verify.klever.org/{nft_id}"
    
    # Background image (if exists)
    if os.path.exists(BACKGROUND_PATH):
        c.drawImage(BACKGROUND_PATH, 0, 0, width=width, height=height)
    
    # Add border frame
    c.setStrokeColor(HexColor('#cccccc'))
    c.setLineWidth(2)
    c.rect(30, 30, width - 60, height - 60, stroke=1, fill=0)
    
    # Logos at top - more centered
    logo_size = 80
    logo_y = height - 200
    logo_spacing = 300  # Space between logos
    
    # Calculate positions to center the logos as a group
    left_logo_x = width / 2 - logo_spacing / 2 - logo_size / 2
    right_logo_x = width / 2 + logo_spacing / 2 - logo_size / 2
    
    if os.path.exists(UNIFOR_LOGO_PATH):
        c.drawImage(UNIFOR_LOGO_PATH, left_logo_x, logo_y, width=logo_size, height=logo_size, preserveAspectRatio=True, mask='auto')
    
    if os.path.exists(KLEVER_LOGO_PATH):
        c.drawImage(KLEVER_LOGO_PATH, right_logo_x, logo_y, width=logo_size + 10, height=logo_size + 10, preserveAspectRatio=True, mask='auto')
    
    # Title with better spacing
    c.setFont("Helvetica-Bold", 42)
    c.setFillColor(HexColor('#1a237e'))  # Dark blue for title
    c.drawCentredString(width / 2, height - 100, "CERTIFICADO DE PARTICIPAÇÃO")
    
    # Reset to black for body text
    c.setFillColor(HexColor('#000000'))
    
    # Main content with inline text
    text_y = height / 2 + 90
    
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
    c.drawCentredString(width / 2, text_y - 80, "participou do curso")
    
    # Course name with emphasis
    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(width / 2, text_y - 110, COURSE_NAME)
    
    # Event details
    c.setFont("Helvetica", 16)
    c.drawCentredString(width / 2, text_y - 135, f"realizado na {LOCATION}, com carga horária total de {COURSE_LOAD},")
    c.drawCentredString(width / 2, text_y - 160, "em Julho de 2025.")
    
    # Signature section
    signature_y = 155
    
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
    
    # NFT ID and QR Code section
    # Position QR code on the left
    qr_size = 80
    qr_x = 40
    qr_y = 40
    
    # Generate and add QR code
    qr_img = generate_qr_code(verify_url)
    c.drawImage(ImageReader(qr_img), qr_x, qr_y, width=qr_size, height=qr_size)
    
    # NFT ID text next to QR code
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(HexColor('#000000'))
    c.drawString(qr_x + qr_size + 10, qr_y + qr_size - 25, f"NFT ID: {nft_id}")
    
    c.setFont("Helvetica", 9)
    c.setFillColor(HexColor('#666666'))
    c.drawString(qr_x + qr_size + 10, qr_y + qr_size - 45, "Verificação:")
    c.drawString(qr_x + qr_size + 10, qr_y + qr_size - 60, verify_url)
    
    # Date at the bottom right
    c.setFont("Helvetica", 11)
    c.setFillColor(HexColor('#000000'))
    c.drawRightString(width - 40, 45, LOCATION_DATE)
    
    c.save()
    print(f"✓ Certificate generated for {student}: {output_file} (NFT: {nft_id})")

# Create sample students.csv if it doesn't exist
if not os.path.exists("students.csv"):
    with open("students.csv", "w", encoding='utf-8') as f:
        f.write("name\n")
        f.write("Fernando Sobreira\n")
        f.write("João Beroni\n")
    print("\n📝 Created students.csv - Add more students to this file and run again!")

print(f"\n✅ Generated {len(students)} certificates successfully!")
print(f"📦 NFT Collection: {NFT_TICKER}")
print(f"🔢 NFT Range: {NFT_TICKER}/{NFT_STARTING_NONCE} to {NFT_TICKER}/{NFT_STARTING_NONCE + len(students) - 1}")