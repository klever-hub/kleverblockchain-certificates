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

# Network configuration
NETWORK = os.getenv("NETWORK", "testnet")
if NETWORK == "mainnet":
    NODE_URL = "https://node.klever.org"
    API_URL = "https://api.klever.org"
else:  # Default to testnet
    NODE_URL = "https://node.testnet.klever.org"
    API_URL = "https://api.testnet.klever.org"

# Allow override if specific URLs are provided
NODE_URL = os.getenv("NODE_URL", NODE_URL)
API_URL = os.getenv("API_URL", API_URL)

NFT_TICKER = os.getenv("NFT_TICKER", "KCERT")
NFT_ID = os.getenv("NFT_ID", "KCERT-V2YJ")  # Default NFT ID, can be overridden
PARTICIPANTS_CSV = os.getenv("PARTICIPANTS_CSV", "participants.csv")
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
        "--result-only",
        "-s"  # auto sign
    ]
    
    # Add maxSupply only if it's greater than 0
    if NFT_MAX_SUPPLY > 0:
        cmd.extend(["--maxSupply", str(NFT_MAX_SUPPLY)])
    
    result = run_command(cmd)
    if result:
        try:
            # Parse the JSON response
            response_data = json.loads(result)
            
            # Extract the NFT ID from receipts
            nft_id = None
            for receipt in response_data.get('receipts', []):
                if receipt.get('type') == 1 and receipt.get('typeString') == 'CreateKDA':
                    nft_id = receipt.get('assetId')
                    break
            
            if nft_id:
                print(f"✅ NFT Collection created successfully!")
                print(f"   Ticker: {NFT_TICKER}")
                print(f"   Collection ID: {nft_id}")
                print(f"   Name: {NFT_NAME}")
                print(f"\n🔔 IMPORTANT: Save this Collection ID for next steps: {nft_id}")
                
                # Optionally save to a file for convenience
                with open(f"{NFT_TICKER}_collection_id.txt", "w") as f:
                    f.write(nft_id)
                print(f"   (Also saved to {NFT_TICKER}_collection_id.txt)")
                
                return True
            else:
                print(f"✅ NFT Collection creation transaction sent!")
                print(f"   Ticker: {NFT_TICKER}")
                print(f"   Check transaction hash: {response_data.get('hash', 'N/A')}")
                return True
                
        except json.JSONDecodeError:
            # Fallback if response is not JSON
            print(f"✅ NFT Collection {NFT_TICKER} created successfully!")
            print(f"   Name: {NFT_NAME}")
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
        "--result-only",
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
        "--result-only",
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
        "--result-only",
        "-s"
    ]
    
    result = run_command(cmd)
    if result:
        print(f"✅ Metadata updated for NFT {NFT_TICKER}/{nonce}")
        return True
    return False

def load_participants_data():
    """Load participants data from CSV"""
    participants = []
    if os.path.exists(PARTICIPANTS_CSV):
        with open(PARTICIPANTS_CSV, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                participants.append(row)
    else:
        print(f"⚠️ {PARTICIPANTS_CSV} not found. Please ensure it has columns: name, address")
    return participants

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
    """Mint NFTs for all participants in the CSV"""
    participants = load_participants_data()
    if not participants:
        print("❌ No participants found in CSV")
        return
    
    # Get the current minted value to determine starting nonce
    starting_nonce = get_next_nonce()
    if starting_nonce is None:
        print("❌ Could not fetch collection info. Please check the collection exists.")
        return
    
    print(f"\n🚀 Starting batch mint for {len(participants)} participants...")
    print(f"📊 Current collection state: {starting_nonce - 1} NFTs minted")
    print(f"🔢 Will mint NFTs with nonces: {starting_nonce} to {starting_nonce + len(participants) - 1}")
    
    success_count = 0
    for idx, participant in enumerate(participants):
        nonce = starting_nonce + idx
        participant_name = participant.get('name', 'Unknown')
        
        print(f"\n👤 Minting for {participant_name} (nonce: {nonce})")
        
        if mint_nft(nonce, skip_validation=False):
            success_count += 1
        else:
            print(f"❌ Failed to mint NFT for {participant_name}")
            # If one fails, subsequent ones will likely fail too due to nonce mismatch
            print(f"⚠️  Stopping batch mint. Successfully minted: {success_count}/{len(participants)}")
            break
    
    print(f"\n✅ Batch minting complete: {success_count}/{len(participants)} successful")

def batch_transfer_nfts():
    """Transfer NFTs to recipients based on participants CSV"""
    participants = load_participants_data()
    if not participants:
        print("❌ No participants found in CSV")
        return
    
    # Load metadata to get nonces
    metadata = load_metadata()
    if not metadata:
        print("❌ No metadata found. Please generate certificates and update metadata first.")
        return
    
    print(f"\n🚀 Starting batch transfer for {len(participants)} participants...")
    
    success_count = 0
    for participant in participants:
        participant_name = participant.get('name', 'Unknown')
        participant_address = participant.get('address', '').strip()
        
        if not participant_address or not participant_address.startswith('klv'):
            print(f"\n⚠️  Skipping {participant_name} - no valid address provided")
            continue
        
        # Find the corresponding metadata entry by name
        participant_metadata = None
        for meta in metadata:
            private_data = meta.get('_privateData', {})
            if private_data.get('name') == participant_name:
                participant_metadata = meta
                break
        
        if not participant_metadata:
            print(f"\n⚠️  No metadata found for {participant_name}")
            continue
        
        nonce = participant_metadata.get('nonce')
        nft_id = f"{NFT_ID}/{nonce}"
        
        print(f"\n👤 Transferring NFT for {participant_name}")
        print(f"   📦 NFT: {nft_id}")
        print(f"   📮 To: {participant_address}")
        
        if transfer_nft(nft_id, participant_address):
            success_count += 1
        else:
            print(f"❌ Failed to transfer NFT for {participant_name}")
    
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
        
        # Get participant name for display
        # Try to get from private data first, then fall back to direct field
        private_data = cert.get('_privateData', {})
        participant_name = private_data.get('name', cert.get('name', 'Unknown'))

        if update_metadata(cert['nonce'], metadata):
            success_count += 1
            print(f"  ✓ Updated metadata for {participant_name} (NFT: {cert['nft_id']})")
        else:
            print(f"  ❌ Failed to update metadata for {participant_name} (NFT: {cert['nft_id']})")
    
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

def get_saved_collection_id(ticker):
    """Try to read saved collection ID from file"""
    try:
        with open(f"{ticker}_collection_id.txt", "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return None

def main():
    global WALLET_KEY, NODE_URL, API_URL, NFT_TICKER, NFT_ID, NETWORK
    
    parser = argparse.ArgumentParser(description='Klever NFT Certificate Manager')
    parser.add_argument('action', choices=['status', 'create', 'mint', 'mint-all', 'transfer', 'transfer-all', 'update', 'update-all', 'get-id'],
                        help='Action to perform')
    parser.add_argument('--nonce', type=int, help='NFT nonce (for single mint/update)')
    parser.add_argument('--address', help='Recipient address (for single mint)')
    parser.add_argument('--key-file', default=WALLET_KEY, help='Path to wallet key file')
    parser.add_argument('--network', choices=['mainnet', 'testnet'], default=NETWORK,
                        help='Network to use (mainnet/testnet)')
    parser.add_argument('--node', help='Override Klever node URL')
    parser.add_argument('--api', help='Override Klever API URL')
    parser.add_argument('--ticker', default=NFT_TICKER, help='NFT collection ticker')
    parser.add_argument('--id', default=NFT_ID, help='NFT collection ID')
    
    args = parser.parse_args()
    
    # Update network URLs based on network flag
    if args.network:
        NETWORK = args.network
        if NETWORK == "mainnet":
            NODE_URL = "https://node.klever.org"
            API_URL = "https://api.klever.org"
        else:  # testnet
            NODE_URL = "https://node.testnet.klever.org"
            API_URL = "https://api.testnet.klever.org"

    # allow override with environment variables
    NODE_URL = os.getenv("NODE_URL", NODE_URL)
    API_URL = os.getenv("API_URL", API_URL)

    # Allow override with specific URLs if provided
    if args.node:
        NODE_URL = args.node
    if args.api:
        API_URL = args.api
    
    # Update other global variables
    WALLET_KEY = args.key_file
    NFT_TICKER = args.ticker
    NFT_ID = args.id

    # Show network configuration
    print(f"🌐 Using {NETWORK} network")
    print(f"   Node: {NODE_URL}")
    print(f"   API: {API_URL}")
    print()
    
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
    
    elif args.action == 'get-id':
        # Try to get saved collection ID
        saved_id = get_saved_collection_id(NFT_TICKER)
        if saved_id:
            print(f"📋 Saved Collection ID for {NFT_TICKER}: {saved_id}")
        else:
            print(f"❌ No saved Collection ID found for {NFT_TICKER}")
            print(f"   Run 'python nft_manager.py create --ticker {NFT_TICKER}' first")

if __name__ == "__main__":
    main()