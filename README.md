# Klever Blockchain Certificate Generator

## Setup
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Required Images
Place the following images in the `images/` folder:
- `unifor.png` - UNIFOR logo
- `klever.png` - Klever logo  
- `background.png` - Certificate background (optional)
- `signature.png` - Instructor signature (optional)

## Usage
```bash
python main.py
```

Certificates will be generated in the `certificates/` folder.