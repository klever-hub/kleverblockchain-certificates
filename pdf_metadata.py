#!/usr/bin/env python3
"""
PDF Metadata handling for certificate verification
"""

import PyPDF2
import json
import argparse
import sys

def parse_certificate_data(cert_data_string):
    """
    Parse the delimited certificate data string
    
    Args:
        cert_data_string: String in format "field1|value1||field2|value2||..."
        
    Returns:
        Dictionary with parsed certificate data
    """
    certificate_data = {}
    if cert_data_string:
        pairs = cert_data_string.split('||')
        for pair in pairs:
            if '|' in pair:
                field, value = pair.split('|', 1)
                # Unescape pipe characters
                value = value.replace('\\|', '|')
                certificate_data[field] = value
    return certificate_data

def create_certificate_data_string(certificate_data):
    """
    Create a delimited string from certificate data dictionary
    
    Args:
        certificate_data: Dictionary with certificate fields
        
    Returns:
        Delimited string in format "field1|value1||field2|value2||..."
    """
    field_order = ['name', 'course', 'course_load', 'location', 'date', 
                  'instructor', 'instructor_title', 'issuer']
    
    cert_data_parts = []
    for field in field_order:
        value = certificate_data.get(field, '')
        # Escape pipe characters in the value if any
        value = str(value).replace('|', '\\|')
        cert_data_parts.append(f"{field}|{value}")
    
    return '||'.join(cert_data_parts)

def embed_verification_data(pdf_path, metadata):
    """
    Embed verification metadata into PDF as custom properties
    
    Args:
        pdf_path: Path to the PDF file
        metadata: Dictionary containing verification data (rootHash, proofs, etc.)
    """
    try:
        # Read the original PDF
        with open(pdf_path, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            pdf_writer = PyPDF2.PdfWriter()
            
            # Copy all pages
            for page in pdf_reader.pages:
                pdf_writer.add_page(page)
            
            # First, copy existing metadata if present
            if pdf_reader.metadata:
                pdf_writer.add_metadata(pdf_reader.metadata)
            
            # Get private data
            private_data = metadata.get('_privateData', {})
            
            # Create a delimited string with all certificate data
            # Format: field1|value1||field2|value2||...
            cert_data_parts = []
            field_order = ['name', 'course', 'course_load', 'location', 'date', 
                          'instructor', 'instructor_title', 'issuer']
            
            for field in field_order:
                value = private_data.get(field, '')
                # Escape pipe characters in the value if any
                value = value.replace('|', '\\|')
                cert_data_parts.append(f"{field}|{value}")
            
            certificate_data_string = '||'.join(cert_data_parts)
            
            # Create custom metadata (will be merged with existing)
            custom_metadata = {
                '/NFT_ID': metadata.get('nft_id', ''),
                '/RootHash': metadata.get('rootHash', ''),
                '/VerifyURL': metadata.get('verify_url', ''),
                # Note: We CANNOT include the certificate hash here as it would change the PDF
                # and invalidate the hash. The hash must be computed after all metadata is added.
                # Store all certificate data as a single delimited string
                '/CertificateData': certificate_data_string,
            }
            
            # Add custom metadata (this will merge with existing metadata)
            pdf_writer.add_metadata(custom_metadata)
            
            # Write to temporary file first
            temp_path = pdf_path + '.tmp'
            with open(temp_path, 'wb') as f:
                pdf_writer.write(f)
            
            # Replace original file
            import os
            os.replace(temp_path, pdf_path)
            
            return True
            
    except Exception as e:
        print(f"❌ Error embedding metadata: {str(e)}")
        return False

def verify_from_pdf(pdf_path, field_name, field_value):
    """
    Verify a certificate field directly from PDF metadata
    
    Args:
        pdf_path: Path to the PDF file
        field_name: Field to verify (name, course, etc.)
        field_value: Expected value
        
    Returns:
        Tuple (is_valid, extracted_data)
    """
    try:
        data = extract_verification_data(pdf_path)
        if not data:
            return False, None
        
        certificate_data = data.get('certificate_data', {})
        
        # Check if the field matches
        if field_name in certificate_data:
            is_valid = certificate_data[field_name] == field_value
            return is_valid, data
        else:
            return False, data
            
    except Exception as e:
        print(f"❌ Error verifying from PDF: {str(e)}")
        return False, None

def extract_verification_data(pdf_path):
    """
    Extract verification metadata from PDF
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Dictionary containing verification data or None if not found
    """
    try:
        with open(pdf_path, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            
            # Get metadata
            metadata = pdf_reader.metadata
            
            if metadata:
                verification_data = {
                    'nft_id': metadata.get('/NFT_ID', ''),
                    'rootHash': metadata.get('/RootHash', ''),
                    'verify_url': metadata.get('/VerifyURL', ''),
                    # Note: hash is not stored in PDF metadata as it would create a circular dependency
                }
                
                # Extract certificate data from delimited string
                cert_data_string = metadata.get('/CertificateData', '')
                if cert_data_string:
                    certificate_data = parse_certificate_data(cert_data_string)
                    verification_data['certificate_data'] = certificate_data
                    # Also include the raw delimited string for easy processing
                    verification_data['certificate_data_raw'] = cert_data_string
                
                # Basic PDF properties
                verification_data['pdf_properties'] = {
                    'title': metadata.get('/Title', ''),
                    'author': metadata.get('/Author', ''),
                    'subject': metadata.get('/Subject', ''),
                    'creator': metadata.get('/Creator', ''),
                    'keywords': metadata.get('/Keywords', ''),
                }
                
                return verification_data
            else:
                return None
                
    except Exception as e:
        print(f"❌ Error reading PDF metadata: {str(e)}")
        return None

def main():
    parser = argparse.ArgumentParser(description='Handle PDF metadata for certificate verification')
    parser.add_argument('action', choices=['embed', 'extract'],
                        help='Action to perform')
    parser.add_argument('pdf_file',
                        help='Path to PDF file')
    parser.add_argument('--metadata-file',
                        help='Path to metadata JSON file (for embed action)')
    parser.add_argument('--nft-id',
                        help='NFT ID to find in metadata (for embed action)')
    
    args = parser.parse_args()
    
    if args.action == 'embed':
        if not args.metadata_file:
            parser.error("--metadata-file is required for embed action")
        
        # Load metadata
        try:
            with open(args.metadata_file, 'r', encoding='utf-8') as f:
                all_metadata = json.load(f)
        except Exception as e:
            print(f"❌ Error loading metadata: {str(e)}")
            sys.exit(1)
        
        # Find specific certificate metadata
        cert_metadata = None
        if args.nft_id:
            for cert in all_metadata:
                if cert.get('nft_id') == args.nft_id:
                    cert_metadata = cert
                    break
            if not cert_metadata:
                print(f"❌ NFT ID {args.nft_id} not found in metadata")
                sys.exit(1)
        else:
            # Try to match by filename
            import os
            pdf_name = os.path.basename(args.pdf_file)
            for cert in all_metadata:
                private_data = cert.get('_privateData', {})
                name = private_data.get('name', '')
                expected_name = f"{name.replace(' ', '_')}_certificate.pdf"
                if pdf_name == expected_name:
                    cert_metadata = cert
                    break
            
            if not cert_metadata:
                print(f"❌ Could not find matching metadata for {pdf_name}")
                sys.exit(1)
        
        # Embed metadata
        if embed_verification_data(args.pdf_file, cert_metadata):
            print(f"✅ Successfully embedded verification data into {args.pdf_file}")
        else:
            sys.exit(1)
    
    elif args.action == 'extract':
        data = extract_verification_data(args.pdf_file)
        if data:
            print(f"📋 Verification data from {args.pdf_file}:\n")
            print(json.dumps(data, indent=2))
        else:
            print(f"❌ No verification data found in {args.pdf_file}")
            sys.exit(1)

if __name__ == "__main__":
    main()