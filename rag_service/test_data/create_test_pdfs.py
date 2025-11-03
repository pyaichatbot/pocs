"""
Script to generate test PDF files with meaningful content.

Creates multiple PDF files in different subdirectories for testing
PDF indexing functionality alongside markdown files.
"""

import os

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.units import inch
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    print("Warning: reportlab not available. Install with: pip install reportlab")
    print("Will create simple text-based PDFs using alternative method.")


# Sample content for PDFs
PDF_CONTENT = [
    {
        "title": "Introduction to Python Programming",
        "content": """Python is a high-level, interpreted programming language known for its simplicity and readability. It was created by Guido van Rossum and first released in 1991.

Python's design philosophy emphasizes code readability with its notable use of significant whitespace. Its language constructs and object-oriented approach aim to help programmers write clear, logical code for small and large-scale projects.

Key Features:
- Simple and easy to learn syntax
- High-level language with dynamic typing
- Extensive standard library
- Cross-platform compatibility
- Large ecosystem of third-party packages

Python is widely used in web development, data science, artificial intelligence, machine learning, automation, and scientific computing. Its versatility makes it one of the most popular programming languages today.""",
    },
    {
        "title": "Docker Containerization Guide",
        "content": """Docker is a platform that uses containerization technology to package applications and their dependencies into portable containers. This enables applications to run consistently across different environments.

Container Benefits:
- Isolation: Each container runs independently
- Portability: Containers work the same on any Docker-enabled system
- Efficiency: Containers share the host OS kernel
- Scalability: Easy to scale applications up or down
- Consistency: Same behavior in development, testing, and production

Docker Basics:
- Dockerfile defines the container image
- Images are templates for containers
- Containers are running instances of images
- Docker Compose manages multi-container applications

Common Commands:
docker build creates an image from a Dockerfile
docker run starts a container from an image
docker ps lists running containers
docker stop terminates a running container""",
    },
    {
        "title": "Microservices Architecture",
        "content": """Microservices architecture is a method of developing software systems that structures an application as a collection of loosely coupled services. Each service is independently deployable and organized around business capabilities.

Architecture Principles:
- Single Responsibility: Each service does one thing well
- Decentralized Governance: Teams choose appropriate technologies
- Fault Isolation: Failure in one service doesn't bring down others
- Independent Deployment: Services can be updated independently
- Technology Diversity: Different services can use different stacks

Benefits:
- Scalability: Scale individual services as needed
- Flexibility: Different teams can work independently
- Resilience: System continues working if one service fails
- Faster Development: Smaller codebases are easier to maintain

Challenges:
- Distributed System Complexity
- Network Latency
- Data Consistency
- Service Discovery
- Testing Complexity""",
    },
]


def create_pdf_with_reportlab(file_path: str, title: str, content: str) -> None:
    """Create a PDF file using reportlab."""
    doc = SimpleDocTemplate(file_path, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    # Add title
    title_style = styles['Heading1']
    story.append(Paragraph(title, title_style))
    story.append(Spacer(1, 0.3 * inch))

    # Add content
    body_style = styles['BodyText']
    paragraphs = content.split('\n\n')
    for para in paragraphs:
        if para.strip():
            story.append(Paragraph(para.strip().replace('\n', '<br/>'), body_style))
            story.append(Spacer(1, 0.2 * inch))

    doc.build(story)


def create_pdf_with_fpdf(file_path: str, title: str, content: str) -> None:
    """Create a PDF file using fpdf (fallback if reportlab not available)."""
    try:
        from fpdf import FPDF
    except ImportError:
        print(f"Error: fpdf not available. Cannot create {file_path}")
        return

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, title, ln=1)
    pdf.ln(5)
    pdf.set_font("Arial", size=12)

    paragraphs = content.split('\n\n')
    for para in paragraphs:
        if para.strip():
            # Replace newlines within paragraphs
            para_text = para.strip().replace('\n', ' ')
            pdf.multi_cell(0, 8, para_text, align='L')
            pdf.ln(3)

    pdf.output(file_path)


def create_simple_text_pdf(file_path: str, title: str, content: str) -> None:
    """Create a simple text-based PDF-like file (last resort)."""
    # This creates a text file that can be converted to PDF
    # For actual testing, we need a real PDF, so we'll use reportlab or fpdf
    with open(file_path.replace('.pdf', '.txt'), 'w', encoding='utf-8') as f:
        f.write(f"{title}\n\n")
        f.write("=" * len(title) + "\n\n")
        f.write(content)
    print(f"Note: Created text file instead of PDF: {file_path.replace('.pdf', '.txt')}")


def create_test_pdfs():
    """Create test PDF files in the test_data/docs directory structure."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    docs_dir = os.path.join(base_dir, "docs")

    # Ensure directories exist
    os.makedirs(docs_dir, exist_ok=True)
    os.makedirs(os.path.join(docs_dir, "subfolder1"), exist_ok=True)
    os.makedirs(os.path.join(docs_dir, "subfolder2"), exist_ok=True)

    pdfs_created = 0

    # Create PDFs in root docs directory
    for i, pdf_data in enumerate(PDF_CONTENT, 1):
        file_path = os.path.join(docs_dir, f"document_pdf_{i}.pdf")
        try:
            if REPORTLAB_AVAILABLE:
                create_pdf_with_reportlab(file_path, pdf_data["title"], pdf_data["content"])
                print(f"Created: {file_path}")
                pdfs_created += 1
            else:
                # Try fpdf
                try:
                    create_pdf_with_fpdf(file_path, pdf_data["title"], pdf_data["content"])
                    print(f"Created: {file_path}")
                    pdfs_created += 1
                except Exception as e:
                    print(f"Error creating {file_path} with fpdf: {e}")
                    create_simple_text_pdf(file_path, pdf_data["title"], pdf_data["content"])
        except Exception as e:
            print(f"Error creating {file_path}: {e}")

    # Create a PDF in subfolder1
    if pdfs_created > 0:
        subfolder1_pdf = {
            "title": "API Design Best Practices",
            "content": """RESTful API design follows standard conventions to create intuitive and maintainable interfaces. 

Design Principles:
- Use nouns for resources, not verbs
- Use HTTP methods appropriately (GET, POST, PUT, DELETE)
- Return appropriate HTTP status codes
- Version your APIs
- Provide clear error messages
- Use consistent naming conventions

Common Patterns:
- Resource-based URLs (/users, /orders)
- Query parameters for filtering
- Pagination for large datasets
- Rate limiting for API protection
- Authentication via tokens or API keys""",
        }
        file_path = os.path.join(docs_dir, "subfolder1", "api_guide.pdf")
        try:
            if REPORTLAB_AVAILABLE:
                create_pdf_with_reportlab(file_path, subfolder1_pdf["title"], subfolder1_pdf["content"])
                print(f"Created: {file_path}")
                pdfs_created += 1
            else:
                create_pdf_with_fpdf(file_path, subfolder1_pdf["title"], subfolder1_pdf["content"])
                print(f"Created: {file_path}")
                pdfs_created += 1
        except Exception as e:
            print(f"Error creating {file_path}: {e}")

    print(f"\nCreated {pdfs_created} test PDF files in {docs_dir}")
    if pdfs_created == 0:
        print("\nWARNING: No PDFs were created. Please install reportlab:")
        print("  pip install reportlab")
        print("\nOr install fpdf:")
        print("  pip install fpdf2")


if __name__ == "__main__":
    create_test_pdfs()

