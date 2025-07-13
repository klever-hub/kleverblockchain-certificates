# Klever Blockchain Certificate Generator

Generate professional NFT certificates for Klever Blockchain courses.

## Features
- 🎨 Professional certificate design with customizable elements
- 🔗 NFT integration with unique IDs (TICKER/NONCE format)
- 📱 QR codes with Klever logo for verification
- 🎯 Batch generation from CSV files
- ⚙️ Flexible configuration via CLI or environment variables
- 🚀 Blockchain integration for NFT creation and minting
- 🔐 Merkle tree proofs for zero-knowledge field verification
- 🛡️ SHA256 hash verification for certificate integrity

## Setup

### 1. Install Dependencies
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env with your values
```

### 3. Prepare Student Data
Create a `students.csv` file:
```csv
name,address
João Silva,klv1xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
Maria Santos,klv1yyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyyy
```

The `address` field is optional. If not provided, NFTs will remain with the owner.

### 4. Add Required Images
Place in `images/` directory:
- `unifor.png` - UNIFOR logo
- `klever.png` - Klever logo
- `kleverlogo.png` - Small Klever logo for QR center
- `background.png` - Certificate background (optional)

## Certificate Generation

### Basic Usage
```bash
python main.py
```

This generates:
- PDF certificates with unique NFT IDs
- `metadata.json` with Merkle tree proofs for zero-knowledge verification
- SHA256 hashes for certificate integrity

The metadata is automatically generated from the certificate data - no need for external IPFS uploads.

### Custom Parameters
```bash
python main.py \
  --course-name "Advanced Smart Contracts" \
  --professor-name "John Doe" \
  --nft-ticker "KLVADV" \
  --location "Klever Labs"
```

### Available Parameters
- `--course-name`: Course title
- `--course-load`: Duration (e.g., "12 horas")
- `--location`: Venue
- `--location-date`: City and date
- `--professor-name`: Instructor name
- `--professor-title`: Instructor title
- `--certificate-issuer`: Organization issuing the certificate
- `--language`: Certificate language (en, pt, es, fr) - default: en
- `--network`: Network to use (mainnet/testnet) - default: testnet
- `--nft-ticker`: NFT collection ID
- `--nft-starting-nonce`: First NFT number
- `--students-csv`: Student data file
- `--output-dir`: Output directory

### Language Support

Certificates can be generated in multiple languages:

```bash
# English (default)
python main.py --language en

# Portuguese
python main.py --language pt

# Spanish
python main.py --language es

# French
python main.py --language fr
```

### Network Configuration

The certificate generator supports both mainnet and testnet:

```bash
# Use testnet (default)
python main.py --network testnet

# Use mainnet
python main.py --network mainnet
```

The network flag determines:
- Which verification URL to use:
  - Testnet: `https://verify.stg.kleverhub.io`
  - Mainnet: `https://verify.kleverhub.io`
- Which blockchain endpoints the NFT manager uses:
  - Testnet: `https://node.testnet.klever.org` and `https://api.testnet.klever.org`
  - Mainnet: `https://node.klever.org` and `https://api.klever.org`

## NFT Management

### Prerequisites
- Install [Klever SDK](https://github.com/klever-io/klever-sdk)
- Have a wallet key file (`walletKey.pem`)
- Sufficient KLV for transactions

### 1. Check Collection Status
```bash
python nft_manager.py status
```

This shows:
- Current minted NFTs count
- Next available nonce
- Collection properties and limits

### 2. Create NFT Collection
```bash
python nft_manager.py create
```

### 3. Mint NFTs

#### Single NFT
```bash
python nft_manager.py mint --nonce 1
```

All NFTs are minted to the owner address first.

#### Batch Mint (from CSV)
```bash
python nft_manager.py mint-all
```

**Note**: The system automatically validates that nonces are sequential. If the collection has 5 NFTs minted, the next mint must be nonce 6.

### 4. Update Metadata

The metadata now includes:
- `hash`: PDF file SHA256 hash
- `rootHash`: Merkle tree root for field verification
- `proofs`: Zero-knowledge proofs for each field
- NFT ID and verification URL

#### Update All NFTs from metadata.json
```bash
python nft_manager.py update-all
```

This reads the generated `metadata.json` and updates each NFT with its cryptographic proofs.

### 5. Transfer NFTs

#### Single Transfer
```bash
python nft_manager.py transfer --nonce 1 --address klv1xxxxxxxx
```

#### Batch Transfer (from CSV)
```bash
python nft_manager.py transfer-all
```

This reads the `students.csv` file and transfers NFTs to addresses specified in the CSV. Only students with valid Klever addresses will receive transfers.

**Important**: Transfers should only be done AFTER metadata has been updated.

### NFT Manager Options
- `--key-file`: Path to wallet key (default: `./walletKey.pem`)
- `--network`: Network to use (mainnet/testnet) - default: testnet
- `--ticker`: NFT collection ticker
- `--id`: NFT collection ID
- `--node`: Override node URL (optional)
- `--api`: Override API URL (optional)

## Workflow Example

1. **Generate Certificates**
   ```bash
   python main.py --nft-id "KCERT-2025"
   ```

2. **Create NFT Collection**
   ```bash
   python nft_manager.py create
   ```

3. **Mint NFTs to Owner**
   ```bash
   python nft_manager.py mint-all
   ```

4. **Update NFT Metadata**
   ```bash
   python nft_manager.py update-all
   ```

5. **Transfer NFTs to Recipients**
   ```bash
   python nft_manager.py transfer-all
   ```

**Important**: Always follow this order. Transfers should only be done after metadata is updated.

## Certificate Verification

The system uses Merkle tree proofs for zero-knowledge verification of certificate fields.

### PDF Metadata

Certificates include embedded metadata in the PDF properties:
- **Standard Metadata**: Title, Author (Issuer), Subject (Course), Creator, Keywords
- **Verification Metadata**: NFT ID, Root Hash, Verification URL
- **Certificate Data**: All certificate fields stored as a delimited string for easy parsing

**Important Note on PDF Hash**: The certificate hash stored in `metadata.json` refers to the FINAL PDF file (after metadata embedding). To avoid circular dependency:
1. The PDF hash is NOT included in the Merkle tree
2. The Merkle tree contains only the certificate data fields
3. After embedding metadata, the final PDF hash is calculated and stored

The workflow is:
1. Generate PDF → Create Merkle tree (without PDF hash) → Embed metadata (including Merkle root) → Calculate final PDF hash → Store in metadata.json

The certificate data is stored in a single field using a delimiter format:
- Format: `field1|value1||field2|value2||field3|value3||...`
- Field separator: `|` (pipe)
- Record separator: `||` (double pipe)
- Escaped pipes in values: `\|`

This format makes it easy to extract and validate certificate data in any programming language.

#### Extract Metadata from PDF
```bash
# Extract all verification data from a PDF
python pdf_metadata.py extract certificates/Fernando_Sobreira_certificate.pdf

# Embed metadata into existing PDF
python pdf_metadata.py embed certificates/Fernando_Sobreira_certificate.pdf --metadata-file certificates/metadata.json
```

#### Frontend Verification
With the embedded metadata, frontend applications can:
1. Extract certificate data directly from the PDF
2. Display certificate information without external files
3. Verify the NFT ID and hash
4. Access the verification URL

Example extracted data:
```json
{
  "nft_id": "KCERT-V2YJ/1",
  "rootHash": "749644030a2d78e098f524ea2060256d542a401b8afa37fc950bf87d4dc54835",
  "verify_url": "https://verify.kleverhub.io/KCERT-V2YJ/1",
  "hash": "88807f995618fcb4252fe7c68d810263fc2a6a0a8045f39b224b241a9c564a3d",
  "certificate_data_raw": "name|Fernando Sobreira||course|Klever Blockchain: Construindo Smart Contracts na Prática||course_load|12 horas||location|Universidade de Fortaleza (UNIFOR)||date|Fortaleza, Julho de 2025||instructor|Nicollas Gabriel||instructor_title|Klever Blockchain Leader||issuer|Klever Blockchain Academy",
  "certificate_data": {
    "name": "Fernando Sobreira",
    "course": "Klever Blockchain: Construindo Smart Contracts na Prática",
    "course_load": "12 horas",
    "location": "Universidade de Fortaleza (UNIFOR)",
    "date": "Fortaleza, Julho de 2025",
    "instructor": "Nicollas Gabriel",
    "instructor_title": "Klever Blockchain Leader",
    "issuer": "Klever Blockchain Academy"
  }
}
```

The `certificate_data_raw` field contains the delimited string that can be easily parsed in any language.

Note: PDF metadata embedding happens automatically during certificate generation if PyPDF2 is installed.

### List All Certificates
```bash
python verify_certificate.py --list
```

### Verify Specific Field
```bash
# Find all certificates with a specific course name
python verify_certificate.py --field course --value "Klever Blockchain: Construindo Smart Contracts na Prática"

# Verify a specific person's name
python verify_certificate.py --field name --value "Fernando Sobreira"

# Verify for a specific NFT ID
python verify_certificate.py --field name --value "Fernando Sobreira" --nft-id "KCERT-V2YJ/1"

# Verify by nonce
python verify_certificate.py --field course_load --value "12 horas" --nonce 1
```

### Available Fields for Verification
- `name`: Certificate holder's name
- `course`: Course name
- `course_load`: Course duration
- `location`: Venue
- `date`: Event date
- `instructor`: Instructor name
- `instructor_title`: Instructor title
- `issuer`: Certificate issuer
- `nft_id`: NFT identifier

Note: The PDF hash is stored in metadata.json but is NOT part of the Merkle tree to avoid circular dependency.

## Environment Variables

See `.env.example` for all available options:
- Course configuration
- NFT parameters
- Blockchain settings
- File paths

## Security Notes
- Never commit `walletKey.pem` or `.env` files
- Keep private keys secure
- Test on testnet first

## License
MIT