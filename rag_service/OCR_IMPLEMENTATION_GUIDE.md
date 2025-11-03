# OCR Implementation Guide for Scanned PDFs

This guide explains what's required to add OCR (Optical Character Recognition) support for processing scanned PDFs with tables, images, and complex layouts.

## Current State

The RAG service currently uses **pdfplumber** which only extracts text from PDFs that have a **text layer**. This means:
- ✅ **Works**: Digital PDFs with selectable text
- ❌ **Doesn't Work**: Scanned PDFs (image-only), PDFs with only images/tables without text layers

## What OCR Adds

OCR enables the service to:
- Extract text from scanned documents (images)
- Recognize text in tables and preserve structure
- Process image-heavy PDFs
- Handle handwritten text (with advanced models)
- Extract text from charts and diagrams

## Recommended Open-Source OCR Solutions

### 1. **Tesseract OCR** (Most Popular)
- **Language**: C++ with Python bindings (pytesseract)
- **License**: Apache 2.0
- **Strengths**: 
  - Supports 100+ languages
  - Mature and well-documented
  - Good accuracy for standard text
  - Lightweight
- **Weaknesses**:
  - Struggles with complex layouts
  - Limited table extraction
  - May need preprocessing for best results
- **Installation**:
  ```bash
  # System dependency
  sudo apt-get install tesseract-ocr  # Ubuntu/Debian
  brew install tesseract  # macOS
  
  # Python package
  pip install pytesseract pillow
  ```

### 2. **PaddleOCR** (Best for Tables & Images)
- **Language**: Python
- **License**: Apache 2.0
- **Strengths**:
  - Excellent table extraction
  - Good image handling
  - Strong multilingual support (especially Chinese)
  - Preserves layout structure
  - Active development
- **Weaknesses**:
  - Larger model size (~100MB+)
  - More memory intensive
- **Installation**:
  ```bash
  pip install paddlepaddle paddleocr
  ```

### 3. **olmOCR** (Structure-Preserving)
- **Language**: Python
- **License**: Open Source (check specific license)
- **Strengths**:
  - Preserves document structure (sections, tables, lists)
  - Handles equations and formulas
  - Good for academic/research papers
  - Vision language model based
- **Weaknesses**:
  - Newer project, less mature
  - May require more setup
- **Installation**:
  ```bash
  # Check GitHub for latest installation instructions
  pip install olmocr  # (if available on PyPI)
  ```

### 4. **OCRmyPDF** (PDF-Focused)
- **Language**: Python
- **License**: MPL 2.0
- **Strengths**:
  - Specifically designed for PDFs
  - Adds OCR layer to existing PDFs
  - Preserves PDF metadata and structure
  - Batch processing support
- **Weaknesses**:
  - Uses Tesseract under the hood
  - Limited table extraction
- **Installation**:
  ```bash
  pip install ocrmypdf
  # Also requires Tesseract OCR
  ```

### 5. **PdfTable** (Table-Specialized)
- **Language**: Python
- **License**: Open Source
- **Strengths**:
  - Specialized for table extraction
  - Handles complex table layouts
  - Supports both digital and scanned PDFs
  - Multiple model integration
- **Weaknesses**:
  - Focused on tables, not general OCR
- **Installation**:
  ```bash
  # Check GitHub repository for installation
  ```

### 6. **docTR (Document Text Recognition)**
- **Language**: Python (TensorFlow/PyTorch)
- **License**: Apache 2.0
- **Strengths**:
  - End-to-end OCR pipeline
  - Good for complex layouts
  - Deep learning based
  - High accuracy
- **Weaknesses**:
  - Requires GPU for best performance
  - Larger dependencies
- **Installation**:
  ```bash
  pip install python-doctr[torch]  # or [tf]
  ```

## Implementation Approach

### Option 1: Hybrid Approach (Recommended)
Use **pdfplumber** first, fallback to **OCR** if no text extracted:

```python
def extract_text_from_pdf(pdf_path: str, use_ocr: bool = True) -> str:
    # Try pdfplumber first (fast, no OCR needed)
    text = pdfplumber.extract_text(pdf_path)
    
    # If no text found, use OCR
    if not text and use_ocr:
        text = ocr_extract_text(pdf_path)
    
    return text
```

### Option 2: Detect Scanned PDFs
Detect if PDF is scanned, then choose extraction method:

```python
def is_scanned_pdf(pdf_path: str) -> bool:
    """Check if PDF is image-based (scanned)"""
    with pdfplumber.open(pdf_path) as pdf:
        # Check if text layer exists
        first_page = pdf.pages[0]
        text = first_page.extract_text()
        return text is None or len(text.strip()) < 50
```

### Option 3: Always Use OCR
Process all PDFs with OCR (slower but most comprehensive).

## Recommended Solution: PaddleOCR + pdfplumber Hybrid

**Why PaddleOCR?**
- Best balance of accuracy and features
- Excellent table extraction
- Good image handling
- Active community
- Production-ready

## Implementation Requirements

### Dependencies

```bash
# Core OCR
pip install paddlepaddle paddleocr

# Image processing (if needed)
pip install pillow opencv-python

# PDF handling (already have)
pip install pdfplumber
```

### System Requirements

- **CPU**: Multi-core recommended (OCR is CPU-intensive)
- **RAM**: 4GB+ recommended (PaddleOCR models are ~100-200MB)
- **Disk**: Additional ~500MB for models
- **GPU**: Optional but recommended for production (10x faster)

### Docker Considerations

```dockerfile
# Add to Dockerfile
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# PaddleOCR will download models on first use
# Consider pre-downloading in image for faster startup
```

## Code Structure

### Proposed Implementation

```
rag_service/utils/
├── pdf_parser.py          # Current: pdfplumber only
├── ocr_parser.py          # New: OCR-based extraction
└── pdf_extractor.py       # New: Unified interface
```

### Configuration

Add to `config.py`:

```python
# OCR Configuration
ocr_enabled: bool = os.environ.get("OCR_ENABLED", "false").lower() == "true"
ocr_engine: str = os.environ.get("OCR_ENGINE", "paddleocr")  # paddleocr, tesseract, etc.
ocr_fallback: bool = os.environ.get("OCR_FALLBACK", "true").lower() == "true"  # Use OCR if pdfplumber fails
```

## Performance Considerations

### Processing Time
- **pdfplumber**: ~0.1-0.5 seconds per page
- **Tesseract OCR**: ~1-3 seconds per page
- **PaddleOCR**: ~2-5 seconds per page (CPU), ~0.5-1 second (GPU)

### Resource Usage
- **Memory**: OCR models load into RAM (100-500MB per model)
- **CPU**: High CPU usage during OCR processing
- **Parallel Processing**: Can process multiple PDFs in parallel

### Optimization Strategies
1. **Caching**: Cache OCR results for unchanged PDFs
2. **Lazy Loading**: Load OCR models only when needed
3. **Batch Processing**: Process multiple pages in parallel
4. **Model Selection**: Use lighter models for simple documents

## Cost vs. Benefit Analysis

### Benefits
- ✅ Process scanned documents (huge use case expansion)
- ✅ Extract text from tables and images
- ✅ Better document coverage
- ✅ Handles legacy/archived documents

### Costs
- ❌ 10-50x slower processing
- ❌ Higher memory usage
- ❌ Additional dependencies and complexity
- ❌ Requires more system resources

## Migration Path

### Phase 1: Add OCR Support (Optional)
- Implement OCR as optional feature
- Use environment variable to enable/disable
- Keep pdfplumber as default (fast path)

### Phase 2: Hybrid Approach
- Automatically detect scanned PDFs
- Use OCR only when needed
- Fallback gracefully

### Phase 3: Advanced Features
- Table structure extraction
- Image caption extraction
- Layout analysis

## Example Implementation

### Basic OCR Integration

```python
# utils/ocr_parser.py
from typing import Optional
import logging

logger = logging.getLogger(__name__)

try:
    from paddleocr import PaddleOCR
    PADDLEOCR_AVAILABLE = True
except ImportError:
    PADDLEOCR_AVAILABLE = False
    PaddleOCR = None

_ocr_engine = None

def get_ocr_engine():
    """Lazy load OCR engine"""
    global _ocr_engine
    if _ocr_engine is None and PADDLEOCR_AVAILABLE:
        _ocr_engine = PaddleOCR(use_angle_cls=True, lang='en')
    return _ocr_engine

def extract_text_with_ocr(pdf_path: str) -> Optional[str]:
    """Extract text from PDF using OCR"""
    if not PADDLEOCR_AVAILABLE:
        logger.warning("OCR not available. Install with: pip install paddleocr")
        return None
    
    try:
        ocr = get_ocr_engine()
        # Convert PDF pages to images
        images = pdf_to_images(pdf_path)
        
        text_parts = []
        for img in images:
            result = ocr.ocr(img, cls=True)
            page_text = extract_text_from_ocr_result(result)
            if page_text:
                text_parts.append(page_text)
        
        return "\n\n".join(text_parts) if text_parts else None
    except Exception as e:
        logger.error(f"OCR extraction failed: {e}")
        return None
```

## Testing Strategy

1. **Unit Tests**: Test OCR extraction with sample scanned PDFs
2. **Performance Tests**: Measure processing time vs. pdfplumber
3. **Accuracy Tests**: Compare OCR results with ground truth
4. **Integration Tests**: Test hybrid approach (pdfplumber → OCR fallback)

## Recommendations

### For Your Organization

**Start with**: PaddleOCR + pdfplumber hybrid
- Best balance of features and performance
- Good table extraction (important for your use case)
- Active development and community support
- Apache 2.0 license (safe for enterprise)

**Consider**: 
- Tesseract if you need maximum language support (100+ languages)
- OCRmyPDF if you want to add OCR layer to PDFs (archival)
- docTR if you have GPU resources and need highest accuracy

**Avoid initially**:
- olmOCR (too new, may have stability issues)
- PdfTable (too specialized, only for tables)

## Next Steps

1. **Evaluate**: Test PaddleOCR on sample scanned PDFs from your organization
2. **Prototype**: Implement basic OCR support as optional feature
3. **Measure**: Collect performance metrics (speed, accuracy, resource usage)
4. **Decide**: Based on results, decide on full implementation or alternatives

## Resources

- [PaddleOCR Documentation](https://github.com/PaddlePaddle/PaddleOCR)
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract)
- [OCRmyPDF](https://github.com/ocrmypdf/OCRmyPDF)
- [docTR Documentation](https://github.com/mindee/doctr)

