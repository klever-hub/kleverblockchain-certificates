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
import argparse
from dotenv import load_dotenv
import hashlib
import json
from merkle_tree import create_certificate_merkle_tree
from translations import get_translation, get_available_languages
import random
import string

# Load environment variables from .env file if exists
load_dotenv()

def generate_salt(length=16):
    """Generate a user-friendly salt using alphanumeric characters"""
    # Use uppercase letters and numbers for easier reading/typing
    # Avoid confusing characters like 0/O, 1/I/l
    chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
    return ''.join(random.choice(chars) for _ in range(length))

# Set up argument parser
parser = argparse.ArgumentParser(description='Generate NFT certificates for Klever Blockchain courses')
parser.add_argument('--course-name', default=os.getenv('COURSE_NAME', 'Klever Blockchain: Construindo Smart Contracts na Prática'),
                    help='Name of the course')
parser.add_argument('--course-load', default=os.getenv('COURSE_LOAD', '12 horas'),
                    help='Course duration/load')
parser.add_argument('--location', default=os.getenv('LOCATION', 'Universidade de Fortaleza (UNIFOR)'),
                    help='Location where the course was held')
parser.add_argument('--location-date', default=os.getenv('LOCATION_DATE', 'Fortaleza, Julho de 2025'),
                    help='City and date of the course')
parser.add_argument('--professor-name', default=os.getenv('PROFESSOR_NAME', 'Nicollas Gabriel'),
                    help='Name of the instructor')
parser.add_argument('--professor-title', default=os.getenv('PROFESSOR_TITLE', 'Klever Blockchain Leader'),
                    help='Title of the instructor')
parser.add_argument('--certificate-issuer', default=os.getenv('CERTIFICATE_ISSUER', 'Klever Blockchain Academy'),
                    help='Certificate issuing organization')
parser.add_argument('--nft-id', default=os.getenv('NFT_ID', 'KCERT-ABCD'),
                    help='NFT collection ID')
parser.add_argument('--nft-starting-nonce', type=int, default=int(os.getenv('NFT_STARTING_NONCE', '1')),
                    help='Starting nonce for NFT IDs')
parser.add_argument('--participants-csv', default=os.getenv('PARTICIPANTS_CSV', 'participants.csv'),
                    help='Path to CSV file with participant names')
parser.add_argument('--output-dir', default=os.getenv('OUTPUT_DIR', 'certificates'),
                    help='Output directory for certificates')
parser.add_argument('--language', default=os.getenv('LANGUAGE', 'en'),
                    choices=get_available_languages(),
                    help='Language for certificate text (default: en)')
parser.add_argument('--network', default=os.getenv('NETWORK', 'testnet'),
                    choices=['mainnet', 'testnet'],
                    help='Network to use (mainnet/testnet) - default: testnet')

args = parser.parse_args()

# Try to register the Mistrully cursive font
try:
    pdfmetrics.registerFont(TTFont('Mistrully', 'fonts/Mistrully.ttf'))
    SIGNATURE_FONT = 'Mistrully'
    SIGNATURE_FONT_SIZE = 40
except:
    # Fallback to italic Times
    SIGNATURE_FONT = 'Times-Italic'
    SIGNATURE_FONT_SIZE = 24

# Use arguments
COURSE_NAME = args.course_name
COURSE_LOAD = args.course_load
LOCATION = args.location
LOCATION_DATE = args.location_date
PROFESSOR_NAME = args.professor_name
PROFESSOR_TITLE = args.professor_title
CERTIFICATE_ISSUER = args.certificate_issuer
NFT_ID = args.nft_id
NFT_STARTING_NONCE = args.nft_starting_nonce
PARTICIPANTS_CSV = args.participants_csv
OUTPUT_DIR = args.output_dir
LANGUAGE = args.language

# Determine network (testnet or mainnet)
NETWORK = args.network

# Set verify URL based on network
VERIFY_BASE_URL = 'https://verify.stg.kleverhub.io' if NETWORK == 'testnet' else 'https://verify.kleverhub.io'

# Fixed paths for logos and background
UNIFOR_LOGO_PATH = "./images/unifor.png"
KLEVER_LOGO_PATH = "./images/klever.png"
BACKGROUND_PATH = "./images/background.png"

# Load participant names
def load_participants():
    """Load participants from CSV file if exists, otherwise use default list"""
    if os.path.exists(PARTICIPANTS_CSV):
        participants = []
        with open(PARTICIPANTS_CSV, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader, None)  # Skip header if exists
            for row in reader:
                if row:  # Check if row is not empty
                    participants.append(row[0])
        return participants
    else:
        print(f"⚠️ Warning: {PARTICIPANTS_CSV} not found!")
        print("Please create a CSV file with participant names or specify a different file with --participants-csv")
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

def hash_file(file_path):
    """Calculate SHA256 hash of a file"""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            # Read and update hash in chunks of 4K
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        print(f"⚠️ File not found: {file_path}")
        return None
    except Exception as e:
        print(f"❌ Error hashing file {file_path}: {str(e)}")
        return None

def calculate_font_size(text, base_font_size, max_width, c, font_name="Helvetica"):
    """Calculate optimal font size to fit text within max_width"""
    font_size = base_font_size
    min_font_size = 12  # Minimum readable font size
    
    # Try different font sizes until text fits
    while font_size >= min_font_size:
        c.setFont(font_name, font_size)
        text_width = c.stringWidth(text, font_name, font_size)
        if text_width <= max_width:
            return font_size
        font_size -= 1
    
    return min_font_size

def get_text_metrics(c, text, font_name, font_size):
    """Get the width of text with given font and size"""
    return c.stringWidth(text, font_name, font_size)

def wrap_text(text, max_width, c, font_name, font_size):
    """Wrap text to fit within max_width, returning list of lines"""
    words = text.split()
    lines = []
    current_line = []
    
    c.setFont(font_name, font_size)
    
    for word in words:
        test_line = ' '.join(current_line + [word])
        if c.stringWidth(test_line, font_name, font_size) <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
                current_line = [word]
            else:
                # Word is too long, add it anyway
                lines.append(word)
    
    if current_line:
        lines.append(' '.join(current_line))
    
    return lines

def draw_centered_multiline_text(c, x, y, lines, font_name, font_size, line_spacing=1.2):
    """Draw multiple lines of text centered at x, starting from y"""
    c.setFont(font_name, font_size)
    line_height = font_size * line_spacing
    
    # Adjust starting y to center the block vertically
    total_height = len(lines) * line_height
    current_y = y + (total_height / 2) - line_height
    
    for line in lines:
        c.drawCentredString(x, current_y, line)
        current_y -= line_height

participants = load_participants()

if not participants:
    print("\n❌ No participants found. Exiting.")
    exit(1)

# Output directory
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Metadata list to store certificate info
metadata_list = []

# Generate certificates
for idx, name in enumerate(participants):
    output_file = f"{OUTPUT_DIR}/{name.replace(' ', '_')}_certificate.pdf"
    c = canvas.Canvas(output_file, pagesize=landscape(A4))
    width, height = landscape(A4)
    
    # Calculate NFT ID and generate salt
    nft_nonce = NFT_STARTING_NONCE + idx
    nft_id = f"{NFT_ID}/{nft_nonce}"
    salt = generate_salt()
    verify_url = f"{VERIFY_BASE_URL}/{nft_id}?salt={salt}"
    
    # Set PDF metadata
    c.setTitle(f"{get_translation(LANGUAGE, 'title')} - {name}")
    c.setAuthor(CERTIFICATE_ISSUER)
    c.setSubject(COURSE_NAME)
    c.setCreator("Klever Blockchain Certificate Generator")
    c.setProducer("Klever Blockchain Certificate System")
    c.setKeywords(f"NFT,{nft_id},certificate,blockchain,klever")
    
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
    c.drawCentredString(width / 2, height - 100, get_translation(LANGUAGE, 'title'))
    
    # Reset to black for body text
    c.setFillColor(HexColor('#000000'))
    
    # Main content with inline text
    text_y = height / 2 + 90
    
    # Define margins and usable width
    left_margin = 80
    right_margin = 80
    usable_width = width - left_margin - right_margin
    
    # First line: "We certify that"
    c.setFont("Helvetica", 20)
    c.drawCentredString(width / 2, text_y, get_translation(LANGUAGE, 'certify_that'))
    
    # Participant name with emphasis - dynamic font size
    name_upper = name.upper()
    name_font_size = calculate_font_size(name_upper, 32, usable_width * 0.9, c, "Helvetica-Bold")
    
    c.setFont("Helvetica-Bold", name_font_size)
    c.setFillColor(HexColor('#1a237e'))  # Highlight participant name
    c.drawCentredString(width / 2, text_y - 45, name_upper)
    
    # Reset to black
    c.setFillColor(HexColor('#000000'))
    
    # Course participation text
    c.setFont("Helvetica", 18)
    c.drawCentredString(width / 2, text_y - 80, get_translation(LANGUAGE, 'participated_in'))
    
    # Course name with emphasis - use wrapping for long names
    c.setFont("Helvetica-Bold", 20)
    course_lines = wrap_text(COURSE_NAME, usable_width * 0.85, c, "Helvetica-Bold", 20)
    course_y = text_y - 110
    if len(course_lines) == 1:
        c.drawCentredString(width / 2, course_y, COURSE_NAME)
    else:
        draw_centered_multiline_text(c, width / 2, course_y, course_lines, "Helvetica-Bold", 20, line_spacing=1.1)
        # Adjust next element position if multiple lines
        course_y -= (len(course_lines) - 1) * 20 * 1.1
    
    # Event details - use wrapping for long location
    held_at = get_translation(LANGUAGE, 'held_at')
    with_duration = get_translation(LANGUAGE, 'with_duration')
    location_line = f"{held_at} {LOCATION}, {with_duration} {COURSE_LOAD},"
    c.setFont("Helvetica", 16)
    location_lines = wrap_text(location_line, usable_width * 0.9, c, "Helvetica", 16)
    location_y = course_y - 25
    if len(location_lines) == 1:
        c.drawCentredString(width / 2, location_y, location_line)
    else:
        draw_centered_multiline_text(c, width / 2, location_y, location_lines, "Helvetica", 16)
        # Adjust next element position if multiple lines
        location_y -= (len(location_lines) - 1) * 16 * 1.2
    
    # Date line
    date_text = get_translation(LANGUAGE, 'date_format').replace('{date}', LOCATION_DATE)
    date_line = f"{date_text}."
    c.setFont("Helvetica", 16)
    c.drawCentredString(width / 2, location_y - 25, date_line)
    
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
    
    # Verification info next to QR code
    info_x = qr_x + qr_size + 5
    
    # NFT ID
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(HexColor('#000000'))
    nft_label = get_translation(LANGUAGE, 'nft_id')
    c.drawString(info_x, qr_y + qr_size - 15, f"{nft_label} {nft_id}")
    
    # Security Code - formatted in groups of 4
    salt_label = get_translation(LANGUAGE, 'salt')
    formatted_salt = '-'.join([salt[i:i+4] for i in range(0, len(salt), 4)])
    c.drawString(info_x, qr_y + qr_size - 30, salt_label)
    c.drawString(info_x, qr_y + qr_size - 45, formatted_salt)
    
    # Verification URL - aligned to bottom of QR code
    c.setFont("Helvetica", 8)
    c.setFillColor(HexColor('#666666'))  # Gray for label
    verification_label = get_translation(LANGUAGE, 'verification')
    c.drawString(info_x, qr_y + 15, verification_label)  # Near bottom of QR
    c.setFont("Helvetica", 7)
    c.setFillColor(HexColor('#444444'))  # Darker gray for URL
    base_url = verify_url.split('?')[0]  # Show only base URL
    c.drawString(info_x, qr_y + 5, base_url)  # At bottom of QR
    
    # Certificate Issuer - bottom center
    c.setFont("Helvetica", 10)
    c.setFillColor(HexColor('#1a237e'))  # Dark blue for issuer
    issued_by = get_translation(LANGUAGE, 'issued_by')
    c.drawCentredString(width / 2, 55, issued_by)
    c.setFont("Helvetica-Bold", 11)
    c.drawCentredString(width / 2, 40, CERTIFICATE_ISSUER)
    
    # Date at the bottom right
    c.setFont("Helvetica", 10)
    c.setFillColor(HexColor('#666666'))  # Gray for date
    c.drawRightString(width - 40, 40, LOCATION_DATE)
    
    c.save()
    
    # Prepare certificate data WITHOUT the PDF hash for Merkle tree
    # We'll add the final PDF hash after metadata embedding
    cert_data = {
        "nonce": nft_nonce,
        "nft_id": nft_id,
        "salt": salt,  # Include salt in the data to be hashed
        "name": name,
        # Note: pdf_hash is excluded from Merkle tree
        "course": COURSE_NAME,
        "course_load": COURSE_LOAD,
        "location": LOCATION,
        "date": LOCATION_DATE,
        "instructor": PROFESSOR_NAME,
        "instructor_title": PROFESSOR_TITLE,
        "issuer": CERTIFICATE_ISSUER,
        "verify_url": verify_url
    }
    
    # Create Merkle tree and get root hash and proofs
    root_hash, proofs = create_certificate_merkle_tree(cert_data)
    
    # Prepare metadata for embedding (without PDF hash)
    cert_metadata_for_embedding = {
        "nonce": nft_nonce,
        "nft_id": nft_id,
        "salt": salt,  # Include salt for verification
        "rootHash": root_hash,  # Merkle tree root
        "verify_url": verify_url,
        # Include all proofs for ZKP
        **proofs,
        # Include the actual values
        "_privateData": {
            "name": name,
            "course": COURSE_NAME,
            "course_load": COURSE_LOAD,
            "location": LOCATION,
            "date": LOCATION_DATE,
            "instructor": PROFESSOR_NAME,
            "instructor_title": PROFESSOR_TITLE,
            "issuer": CERTIFICATE_ISSUER,
        }
    }
    
    # Try to embed metadata into PDF
    metadata_embedded = False
    try:
        from pdf_metadata import embed_verification_data
        if embed_verification_data(output_file, cert_metadata_for_embedding):
            metadata_embedded = True
    except ImportError:
        pass  # PyPDF2 not installed, skip embedding
    
    # NOW calculate the FINAL hash of the PDF file (after metadata embedding)
    final_pdf_hash = hash_file(output_file)
    
    if final_pdf_hash:
        # Create the complete metadata with the final PDF hash
        cert_metadata = {
            "nonce": nft_nonce,
            "nft_id": nft_id,
            "salt": salt,  # Include salt for verification
            "hash": final_pdf_hash,  # Final PDF hash (after metadata embedding)
            "rootHash": root_hash,  # Merkle tree root
            "verify_url": verify_url,
            # Include all proofs for ZKP
            **proofs,
            # Include the actual values
            "_privateData": {
                "name": name,
                "course": COURSE_NAME,
                "course_load": COURSE_LOAD,
                "location": LOCATION,
                "date": LOCATION_DATE,
                "instructor": PROFESSOR_NAME,
                "instructor_title": PROFESSOR_TITLE,
                "issuer": CERTIFICATE_ISSUER,
            }
        }
        
        metadata_list.append(cert_metadata)
        print(f"✓ Certificate generated for {name}: {output_file} (NFT: {nft_id})")
        print(f"  📄 SHA256: {final_pdf_hash}")
        print(f"  🌳 Merkle Root: {root_hash[:16]}...")
        print(f"  🔐 Salt: {salt}")
        if metadata_embedded:
            print(f"  📎 Embedded verification data in PDF")

# Create sample participants.csv if it doesn't exist
if not os.path.exists(PARTICIPANTS_CSV):
    with open(PARTICIPANTS_CSV, "w", encoding='utf-8') as f:
        f.write("name\n")
        f.write("Fernando Sobreira\n")
        f.write("João Beroni\n")
    print(f"\n📝 Created {PARTICIPANTS_CSV} - Add more participants to this file and run again!")

print(f"\n✅ Generated {len(participants)} certificates successfully!")
print(f"📦 NFT Collection: {NFT_ID}")
print(f"🔢 NFT Range: {NFT_ID}/{NFT_STARTING_NONCE} to {NFT_ID}/{NFT_STARTING_NONCE + len(participants) - 1}")

# Save metadata to JSON file
metadata_file = f"{OUTPUT_DIR}/metadata.json"
with open(metadata_file, 'w', encoding='utf-8') as f:
    json.dump(metadata_list, f, indent=2, ensure_ascii=False)
print(f"\n📋 Metadata saved to: {metadata_file}")

# Show current configuration
print("\n📋 Configuration used:")
print(f"   Course: {COURSE_NAME}")
print(f"   Duration: {COURSE_LOAD}")
print(f"   Location: {LOCATION}")
print(f"   Date: {LOCATION_DATE}")
print(f"   Instructor: {PROFESSOR_NAME} ({PROFESSOR_TITLE})")
print(f"   Issuer: {CERTIFICATE_ISSUER}")
print(f"   Language: {LANGUAGE}")
print(f"   Network: {NETWORK}")
print(f"   Verify URL: {VERIFY_BASE_URL}")
print(f"   NFT ID: {NFT_ID}")
print(f"   Participants CSV: {PARTICIPANTS_CSV}")
print(f"   Output: {OUTPUT_DIR}/")