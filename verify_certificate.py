#!/usr/bin/env python3
import json
import argparse
from merkle_tree import verify_certificate_field
import sys

def list_certificates(metadata_file: str):
    """List all certificates in the metadata file"""
    try:
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
    except FileNotFoundError:
        print(f"❌ Metadata file not found: {metadata_file}")
        return
    except json.JSONDecodeError:
        print(f"❌ Invalid JSON in metadata file")
        return
    
    print(f"📋 Found {len(metadata)} certificate(s) in metadata:\n")
    
    for cert in metadata:
        nft_id = cert.get('nft_id', 'Unknown')
        private_data = cert.get('_privateData', {})
        name = private_data.get('name', 'Unknown')
        course = private_data.get('course', 'Unknown')
        
        print(f"NFT ID: {nft_id}")
        print(f"  Holder: {name}")
        print(f"  Course: {course}")
        print(f"  Root Hash: {cert.get('rootHash', 'Unknown')[:16]}...")
        print(f"  Salt: {cert.get('salt', 'None')}")
        print()

def verify_field(metadata_file: str, field_name: str, field_value: str, nonce: int = None, nft_id: str = None):
    """Verify a specific field in a certificate using Merkle proof"""
    
    # Load metadata
    try:
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
    except FileNotFoundError:
        print(f"❌ Metadata file not found: {metadata_file}")
        return False
    except json.JSONDecodeError:
        print(f"❌ Invalid JSON in metadata file")
        return False
    
    # Find the certificate by nonce or NFT ID if provided
    if nonce is not None or nft_id is not None:
        cert = None
        for c in metadata:
            if nonce is not None and c.get('nonce') == nonce:
                cert = c
                break
            elif nft_id is not None and c.get('nft_id') == nft_id:
                cert = c
                break
        if not cert:
            identifier = f"nonce {nonce}" if nonce is not None else f"NFT ID {nft_id}"
            print(f"❌ Certificate with {identifier} not found")
            return False
        certificates = [cert]
        print(f"🔍 Verifying field '{field_name}' for certificate {cert.get('nft_id')}")
    else:
        # When no specific certificate is requested, find ALL certificates that claim to have this field value
        print(f"🔍 Searching for certificates with {field_name}='{field_value}'...")
        matching_certs = []
        
        for cert in metadata:
            # Check if this certificate has the required proofs
            root_hash = cert.get('rootHash')
            proof_key = f"{field_name}Proof"
            proof = cert.get(proof_key)
            
            if not root_hash or not proof:
                continue
            
            # Get salt from certificate metadata
            salt = cert.get('salt')
            
            # Verify if this certificate actually has this field value
            is_valid = verify_certificate_field(field_name, field_value, root_hash, proof, salt)
            if is_valid:
                matching_certs.append(cert)
        
        if not matching_certs:
            print(f"❌ No certificates found with {field_name}='{field_value}'")
            return False
        
        certificates = matching_certs
        print(f"📋 Found {len(certificates)} certificate(s) with matching field value")
    
    # Verify the field for selected certificates
    verified_count = 0
    for cert in certificates:
        root_hash = cert.get('rootHash')
        proof_key = f"{field_name}Proof"
        proof = cert.get(proof_key)
        
        if not root_hash:
            print(f"⚠️  No rootHash found for certificate {cert.get('nft_id')}")
            continue
        
        if not proof:
            print(f"⚠️  No proof found for field '{field_name}' in certificate {cert.get('nft_id')}")
            continue
        
        # Get salt from certificate metadata
        salt = cert.get('salt')
        
        # Verify using Merkle proof
        is_valid = verify_certificate_field(field_name, field_value, root_hash, proof, salt)
        
        if is_valid:
            verified_count += 1
            print(f"✅ Field '{field_name}' verified for NFT {cert.get('nft_id')}")
            # Show other certificate details if available
            private_data = cert.get('_privateData', {})
            if private_data and field_name != 'name':
                name = private_data.get('name', 'Unknown')
                print(f"   Certificate holder: {name}")
        else:
            print(f"❌ Field '{field_name}' verification failed for NFT {cert.get('nft_id')}")
    
    print(f"\n📊 Verification complete: {verified_count}/{len(certificates)} certificates verified")
    return verified_count > 0

def main():
    parser = argparse.ArgumentParser(description='Verify certificate fields using Merkle proofs')
    parser.add_argument('--metadata', default='certificates/metadata.json', 
                        help='Path to metadata JSON file')
    parser.add_argument('--list', action='store_true',
                        help='List all certificates in the metadata')
    parser.add_argument('--field',
                        choices=['name', 'course', 'course_load', 'location', 'date', 'instructor', 'instructor_title', 'issuer', 'nft_id'],
                        help='Field to verify (note: pdf_hash is not part of Merkle tree)')
    parser.add_argument('--value',
                        help='Expected value of the field')
    parser.add_argument('--nonce', type=int,
                        help='Specific certificate nonce to verify (optional)')
    parser.add_argument('--nft-id', dest='nft_id',
                        help='Specific NFT ID to verify (e.g., KCERT-V2YJ/1)')
    
    args = parser.parse_args()
    
    # List certificates if requested
    if args.list:
        list_certificates(args.metadata)
        sys.exit(0)
    
    # Otherwise, verify a field
    if not args.field or not args.value:
        parser.error("--field and --value are required for verification")
    
    # Verify the field
    result = verify_field(args.metadata, args.field, args.value, args.nonce, args.nft_id)
    
    if result:
        print(f"\n✅ Verification successful!")
        sys.exit(0)
    else:
        print(f"\n❌ Verification failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()