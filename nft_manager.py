#!/usr/bin/env python3
import json
import os
import subprocess
import argparse
import sys
from dotenv import load_dotenv
import csv
import requests

# Load environment variables
load_dotenv()

# Configuration
KOPERATOR_PATH = os.path.expanduser("~/klever-sdk/koperator")
WALLET_KEY = os.getenv("WALLET_KEY_FILE", "./walletKey.pem")
NODE_URL = os.getenv("NODE_URL", "https://node.testnet.klever.org")
API_URL = os.getenv("API_URL", "https://api.testnet.klever.org")
NFT_TICKER = os.getenv("NFT_TICKER", "KCERT")
NFT_ID = os.getenv("NFT_ID", "KCERT-V2YJ")  # Default NFT ID, can be overridden
STUDENTS_CSV = os.getenv("STUDENTS_CSV", "students.csv")
CERTIFICATES_DIR = os.getenv("OUTPUT_DIR", "certificates")

# NFT Metadata
NFT_NAME = os.getenv("NFT_NAME", "KleverBlockchainCertificate")
NFT_LOGO = os.getenv("NFT_LOGO", "https://raw.githubusercontent.com/klever-hub/kleverblockchain-certificates/refs/heads/main/images/nftc.png")
NFT_MAX_SUPPLY = int(os.getenv("NFT_MAX_SUPPLY", "0"))

def run_command(cmd):
    """Execute a command and return the output"""
    print(f"📟 Executing: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"✅ Success")
        if result.stdout:
            print(result.stdout)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        if e.stderr:
            print(f"Error details: {e.stderr}")
        return None

def get_owner_address():
    """Get the wallet owner address using koperator"""
    cmd = [
        KOPERATOR_PATH, "account", "address",
        "--key-file", WALLET_KEY
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        if result.stdout:
            # Parse the output to find the address
            # Look for line starting with "Wallet address:" or containing "klv1"
            for line in result.stdout.strip().split('\n'):
                if "Wallet address:" in line:
                    # Extract address after "Wallet address:"
                    address = line.split("Wallet address:")[-1].strip()
                    if address.startswith("klv1"):
                        return address
                elif line.strip().startswith("klv1"):
                    # Sometimes the address might be on its own line
                    return line.strip()
            
            # Fallback: look for any klv1 address in the output
            import re
            klv_pattern = r'klv1[a-z0-9]{58}'
            matches = re.findall(klv_pattern, result.stdout)
            if matches:
                return matches[-1]  # Return the last match (likely the wallet address)
        
        return None
    except subprocess.CalledProcessError as e:
        print(f"❌ Error getting owner address: {e}")
        if e.stderr:
            print(f"Error details: {e.stderr}")
        return None

def get_collection_info():
    """Get NFT collection information from Klever API"""
    api_url = f"{API_URL}/assets/{NFT_ID}"
    
    try:
        response = requests.get(api_url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("code") == "successful":
                return data.get("data", {}).get("asset", {})
            else:
                print(f"❌ API Error: {data.get('error', 'Unknown error')}")
                return None
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {str(e)}")
        return None

def get_next_nonce():
    """Get the next available nonce for minting"""
    asset_info = get_collection_info()
    if asset_info:
        minted_value = asset_info.get("mintedValue", 0)
        # Next nonce is mintedValue + 1
        return minted_value + 1
    return None

def create_nft_collection():
    """Create the NFT collection"""
    print(f"\n🎨 Creating NFT Collection: {NFT_TICKER}")
    
    cmd = [
        KOPERATOR_PATH, "kda", "create", "1",  # 1 for NFT
        "--ticker", NFT_TICKER,
        "--name", NFT_NAME,
        "--logo", NFT_LOGO,
        "--canMint",
        "--canChangeOwner",
        "--canAddRoles",
        "--key-file", WALLET_KEY,
        "--node", NODE_URL,
        "--await",
        "-s"  # auto sign
    ]
    
    # Add maxSupply only if it's greater than 0
    if NFT_MAX_SUPPLY > 0:
        cmd.extend(["--maxSupply", str(NFT_MAX_SUPPLY)])
    
    result = run_command(cmd)
    if result:
        print(f"✅ NFT Collection {NFT_TICKER} created successfully!")
        return True
    return False

def mint_nft(nonce, skip_validation=False):
    """Mint a single NFT to the owner address"""
    print(f"\n🪙 Minting NFT {NFT_ID}/{nonce}")
    
    # Validate nonce unless explicitly skipped
    if not skip_validation:
        expected_nonce = get_next_nonce()
        if expected_nonce is None:
            print(f"⚠️  Could not fetch collection info. Proceeding with caution...")
        elif nonce != expected_nonce:
            print(f"❌ Nonce mismatch! Expected: {expected_nonce}, Got: {nonce}")
            print(f"   The collection has {expected_nonce - 1} NFTs minted.")
            print(f"   Next NFT should have nonce {expected_nonce}")
            return False
    
    # Get owner address
    owner_address = get_owner_address()
    if not owner_address:
        print(f"❌ Could not determine owner address")
        return False
    
    print(f"📤 Minting to owner address: {owner_address}")
    
    cmd = [
        KOPERATOR_PATH, "kda", "trigger", "0",  # 0 for mint
        "--kdaID", NFT_ID,
        "--amount", "1",
        "--receiver", owner_address,
        "--key-file", WALLET_KEY,
        "--node", NODE_URL,
        "--await",
        "-s"
    ]
    result = run_command(cmd)
    if result:
        print(f"✅ NFT {NFT_TICKER}/{nonce} minted successfully to {owner_address}!")
        return True
    return False

def transfer_nft(nft_id, to_address):
    """Transfer an NFT to a recipient"""
    print(f"\n📤 Transferring NFT {nft_id} to {to_address}")
    
    cmd = [
        KOPERATOR_PATH, "send", 
        "--kda", nft_id,
        "--kdaAmount", "1",
        "--to", to_address,
        "--key-file", WALLET_KEY,
        "--node", NODE_URL,
        "--await",
        "-s"
    ]
    
    result = run_command(cmd)
    if result:
        print(f"✅ NFT {nft_id} transferred successfully to {to_address}!")
        return True
    return False

def update_metadata(nonce, metadata):
    """Update metadata for a specific NFT"""
    print(f"\n📝 Updating metadata for NFT {NFT_ID}/{nonce}")

    # Get owner address
    owner_address = get_owner_address()
    if not owner_address:
        print(f"❌ Could not determine owner address")
        return False

    cmd = [
        KOPERATOR_PATH, "kda", "trigger", "8",  # 8 for updateMetadata
        "--kdaID", f"{NFT_ID}/{nonce}",
        "--receiver", owner_address,
        "--message", metadata,
        "--key-file", WALLET_KEY,
        "--node", NODE_URL,
        "--await",
        "-s"
    ]
    
    result = run_command(cmd)
    if result:
        print(f"✅ Metadata updated for NFT {NFT_TICKER}/{nonce}")
        return True
    return False

def load_students_data():
    """Load students data from CSV"""
    students = []
    if os.path.exists(STUDENTS_CSV):
        with open(STUDENTS_CSV, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                students.append(row)
    else:
        print(f"⚠️ {STUDENTS_CSV} not found. Please ensure it has columns: name, address")
    return students

def load_metadata():
    """Load certificate metadata from JSON file"""
    metadata_file = f"{CERTIFICATES_DIR}/metadata.json"
    if os.path.exists(metadata_file):
        with open(metadata_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        print(f"⚠️ {metadata_file} not found. Please generate certificates first.")
        return []

def batch_mint_nfts():
    """Mint NFTs for all students in the CSV"""
    students = load_students_data()
    if not students:
        print("❌ No students found in CSV")
        return
    
    # Get the current minted value to determine starting nonce
    starting_nonce = get_next_nonce()
    if starting_nonce is None:
        print("❌ Could not fetch collection info. Please check the collection exists.")
        return
    
    print(f"\n🚀 Starting batch mint for {len(students)} students...")
    print(f"📊 Current collection state: {starting_nonce - 1} NFTs minted")
    print(f"🔢 Will mint NFTs with nonces: {starting_nonce} to {starting_nonce + len(students) - 1}")
    
    success_count = 0
    for idx, student in enumerate(students):
        nonce = starting_nonce + idx
        student_name = student.get('name', 'Unknown')
        
        print(f"\n👤 Minting for {student_name} (nonce: {nonce})")
        
        if mint_nft(nonce, skip_validation=False):
            success_count += 1
        else:
            print(f"❌ Failed to mint NFT for {student_name}")
            # If one fails, subsequent ones will likely fail too due to nonce mismatch
            print(f"⚠️  Stopping batch mint. Successfully minted: {success_count}/{len(students)}")
            break
    
    print(f"\n✅ Batch minting complete: {success_count}/{len(students)} successful")

def batch_transfer_nfts():
    """Transfer NFTs to recipients based on students CSV"""
    students = load_students_data()
    if not students:
        print("❌ No students found in CSV")
        return
    
    # Load metadata to get nonces
    metadata = load_metadata()
    if not metadata:
        print("❌ No metadata found. Please generate certificates and update metadata first.")
        return
    
    print(f"\n🚀 Starting batch transfer for {len(students)} students...")
    
    success_count = 0
    for student in students:
        student_name = student.get('name', 'Unknown')
        student_address = student.get('address', '').strip()
        
        if not student_address or not student_address.startswith('klv'):
            print(f"\n⚠️  Skipping {student_name} - no valid address provided")
            continue
        
        # Find the corresponding metadata entry by name
        student_metadata = None
        for meta in metadata:
            private_data = meta.get('_privateData', {})
            if private_data.get('name') == student_name:
                student_metadata = meta
                break
        
        if not student_metadata:
            print(f"\n⚠️  No metadata found for {student_name}")
            continue
        
        nonce = student_metadata.get('nonce')
        nft_id = f"{NFT_ID}/{nonce}"
        
        print(f"\n👤 Transferring NFT for {student_name}")
        print(f"   📦 NFT: {nft_id}")
        print(f"   📮 To: {student_address}")
        
        if transfer_nft(nft_id, student_address):
            success_count += 1
        else:
            print(f"❌ Failed to transfer NFT for {student_name}")
    
    print(f"\n✅ Batch transfer complete: {success_count} NFTs transferred")

def batch_update_metadata():
    """Update metadata for all existing NFTs"""
    # Load metadata from JSON file
    certificates_metadata = load_metadata()
    if not certificates_metadata:
        print("❌ No certificate metadata found")
        return
    
    print(f"\n🔄 Starting batch metadata update for {len(certificates_metadata)} NFTs...")
    
    success_count = 0
    for cert in certificates_metadata:
        # Build metadata structure for on-chain storage
        # We only store the hashes and proofs, not the actual data
        json_metadata = {
            "hash": cert.get('hash', cert.get('pdf_hash', '')),  # Support both field names
            "rootHash": cert.get('rootHash', ''),  # Merkle tree root
            "nft_id": cert['nft_id'],
            "verify_url": cert['verify_url'],
            # Include all the proofs for ZKP verification
            "proofs": {
                "nameProof": cert.get('nameProof', []),
                "courseProof": cert.get('courseProof', []),
                "course_loadProof": cert.get('course_loadProof', []),
                "locationProof": cert.get('locationProof', []),
                "dateProof": cert.get('dateProof', []),
                "instructorProof": cert.get('instructorProof', []),
                "instructor_titleProof": cert.get('instructor_titleProof', []),
                "issuerProof": cert.get('issuerProof', []),
                "nft_idProof": cert.get('nft_idProof', [])
            }
        }
        metadata = json.dumps(json_metadata)
        
        # Get student name for display
        # Try to get from private data first, then fall back to direct field
        private_data = cert.get('_privateData', {})
        student_name = private_data.get('name', cert.get('name', 'Unknown'))

        if update_metadata(cert['nonce'], metadata):
            success_count += 1
            print(f"  ✓ Updated metadata for {student_name} (NFT: {cert['nft_id']})")
        else:
            print(f"  ❌ Failed to update metadata for {student_name} (NFT: {cert['nft_id']})")
    
    print(f"\n✅ Batch update complete: {success_count}/{len(certificates_metadata)} successful")

def check_collection_status():
    """Check and display collection status"""
    print(f"\n🔍 Checking collection: {NFT_ID}")
    
    asset_info = get_collection_info()
    if not asset_info:
        print(f"❌ Collection {NFT_ID} not found or API error")
        return
    
    print(f"\n📊 Collection Status:")
    print(f"   Name: {asset_info.get('name', 'N/A')}")
    print(f"   Ticker: {asset_info.get('ticker', 'N/A')}")
    print(f"   Type: {asset_info.get('assetType', 'N/A')}")
    print(f"   Minted NFTs: {asset_info.get('mintedValue', 0)}")
    print(f"   Max Supply: {asset_info.get('maxSupply', 'Unlimited')}")
    print(f"   Can Mint: {asset_info.get('properties', {}).get('canMint', False)}")
    print(f"   Owner: {asset_info.get('ownerAddress', 'N/A')}")
    
    next_nonce = get_next_nonce()
    if next_nonce:
        print(f"\n✅ Next available nonce: {next_nonce}")

def main():
    global WALLET_KEY, NODE_URL, API_URL, NFT_TICKER, NFT_ID
    
    parser = argparse.ArgumentParser(description='Klever NFT Certificate Manager')
    parser.add_argument('action', choices=['status', 'create', 'mint', 'mint-all', 'transfer', 'transfer-all', 'update', 'update-all'],
                        help='Action to perform')
    parser.add_argument('--nonce', type=int, help='NFT nonce (for single mint/update)')
    parser.add_argument('--address', help='Recipient address (for single mint)')
    parser.add_argument('--key-file', default=WALLET_KEY, help='Path to wallet key file')
    parser.add_argument('--node', default=NODE_URL, help='Klever node URL')
    parser.add_argument('--api', default=API_URL, help='Klever API URL')
    parser.add_argument('--ticker', default=NFT_TICKER, help='NFT collection ticker')
    parser.add_argument('--id', default=NFT_ID, help='NFT collection ID')
    
    args = parser.parse_args()
    
    # Update global variables if provided
    WALLET_KEY = args.key_file
    NODE_URL = args.node
    API_URL = args.api
    NFT_TICKER = args.ticker
    NFT_ID = args.id

    # Check if koperator exists
    if not os.path.exists(KOPERATOR_PATH):
        print(f"❌ Koperator not found at {KOPERATOR_PATH}")
        print("Please ensure Klever SDK is installed at ~/klever-sdk/")
        sys.exit(1)
    
    # Check if wallet key exists
    if not os.path.exists(WALLET_KEY):
        print(f"❌ Wallet key not found at {WALLET_KEY}")
        print("Please provide a valid wallet key file with --key-file")
        sys.exit(1)
    
    # Execute action
    if args.action == 'status':
        check_collection_status()
    
    elif args.action == 'create':
        create_nft_collection()
    
    elif args.action == 'mint':
        if not args.nonce:
            print("❌ --nonce is required for single mint")
            sys.exit(1)
        mint_nft(args.nonce)
    
    elif args.action == 'mint-all':
        batch_mint_nfts()
    
    elif args.action == 'transfer':
        if not args.nonce or not args.address:
            print("❌ --nonce and --address are required for transfer")
            sys.exit(1)
        nft_id = f"{NFT_ID}/{args.nonce}"
        transfer_nft(nft_id, args.address)
    
    elif args.action == 'transfer-all':
        batch_transfer_nfts()
    
    elif args.action == 'update':
        if not args.nonce:
            print("❌ --nonce is required for single update")
            sys.exit(1)
        # For single update, you would need to provide metadata manually
        print("❌ Single update requires manual metadata. Use 'update-all' to update from metadata.json")
        sys.exit(1)
    
    elif args.action == 'update-all':
        batch_update_metadata()

if __name__ == "__main__":
    main()