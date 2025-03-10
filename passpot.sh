sudo apt-get update && sudo apt-get install -y \
    libmagic1 \
    libmupdf-dev \
    tesseract-ocr \
    tesseract-ocr-eng \
    clamav \
    clamav-daemon \
    poppler-utils \
    python3-dev \
    libjpeg-dev \
    zlib1g-dev

    # Create virtual environment
python -m venv pdfenv
source pdfenv/bin/activate  # Linux/Mac
# pdfenv\Scripts\activate  # Windows

# Install with exact versions
pip install --upgrade pip wheel setuptools
pip install \
    streamlit==1.32.0 \
    pymupdf==1.24.0 \
    pdfplumber==0.10.3 \
    python-docx==1.1.0 \
    pillow==10.3.0 \
    python-magic==0.4.27 \
    pyclamd==1.0.1 \
    pytesseract==0.3.10 \
    pikepdf==8.13.0 \
    python-magic-bin==0.4.14  # Windows only

    sudo ln -s /usr/lib/x86_64-linux-gnu/libmagic.so.1 /usr/lib/x86_64-linux-gnu/libmagic.so
# In your code, add fallback
try:
    cd = clamd.ClamdAgnostic()
except:
    cd = None
    st.warning("Virus scanning disabled")

git add requirements.txt .gitignore app.py
git commit -m "Fix dependency issues"
git push origin main
