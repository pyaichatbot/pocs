"""
Script to generate test markdown files with ~100 lines of content each.

Creates multiple markdown files in different subdirectories for testing
parallel indexing functionality.
"""

import os

# Sample content templates
TEMPLATES = [
    """# Introduction to Machine Learning

Machine learning is a subset of artificial intelligence that focuses on teaching computers to learn from data. It enables systems to automatically improve their performance through experience without being explicitly programmed for every task.

## Types of Machine Learning

There are three main types of machine learning: supervised learning, unsupervised learning, and reinforcement learning. Each type has its own characteristics and use cases.

### Supervised Learning

In supervised learning, the algorithm learns from labeled training data. The model makes predictions and is corrected by comparing outputs to known correct answers. Common applications include image classification and spam detection.

### Unsupervised Learning

Unsupervised learning involves finding patterns in data without labeled examples. The algorithm identifies hidden structures or groupings in the data. Clustering and dimensionality reduction are typical examples.

### Reinforcement Learning

Reinforcement learning involves an agent learning to make decisions by interacting with an environment. The agent receives rewards or penalties for actions and learns optimal strategies over time.

## Applications

Machine learning has revolutionized many industries including healthcare, finance, transportation, and entertainment. From medical diagnosis to autonomous vehicles, the impact is profound.

## Challenges

Despite its potential, machine learning faces challenges such as data quality, bias, interpretability, and computational requirements. Addressing these challenges is crucial for responsible AI development.
""",
    """# Web Development Best Practices

Modern web development requires understanding multiple technologies and following best practices to create maintainable, scalable applications.

## Frontend Development

Frontend development involves creating the user interface and experience. HTML, CSS, and JavaScript form the foundation, with modern frameworks like React, Vue, and Angular providing powerful abstractions.

### Responsive Design

Responsive design ensures applications work well across different screen sizes and devices. Using flexible layouts, media queries, and mobile-first approaches is essential.

### Performance Optimization

Performance is critical for user experience. Techniques include code splitting, lazy loading, image optimization, and minimizing JavaScript bundle sizes.

## Backend Development

Backend development handles server-side logic, databases, and API design. Common languages include Python, Node.js, Java, and Go.

### API Design

RESTful APIs follow standard conventions for creating, reading, updating, and deleting resources. GraphQL provides an alternative approach with flexible querying capabilities.

### Database Management

Choosing the right database (SQL vs NoSQL) depends on data structure, scalability needs, and consistency requirements. Understanding normalization and indexing is crucial.
""",
    """# Cloud Computing Fundamentals

Cloud computing delivers computing services over the internet, enabling on-demand access to resources without managing physical infrastructure.

## Service Models

Cloud computing offers three primary service models: Infrastructure as a Service (IaaS), Platform as a Service (PaaS), and Software as a Service (SaaS).

### Infrastructure as a Service

IaaS provides virtualized computing resources over the internet. Users manage operating systems, applications, and data while the provider handles hardware and networking.

### Platform as a Service

PaaS offers a platform for developing, testing, and deploying applications without managing underlying infrastructure. Developers focus on code while the platform handles scaling and maintenance.

### Software as a Service

SaaS delivers complete applications over the internet. Users access software through web browsers without installing or maintaining anything locally.

## Deployment Strategies

Cloud platforms support various deployment strategies including blue-green deployments, canary releases, and rolling updates to minimize downtime during updates.

## Security Considerations

Cloud security involves shared responsibility models, encryption, access controls, and compliance with regulations. Understanding these aspects is essential for secure cloud adoption.
""",
    """# Database Management Systems

Databases are fundamental to storing, organizing, and retrieving data efficiently. Understanding different database types and their characteristics is crucial for system design.

## Relational Databases

Relational databases organize data into tables with relationships defined by foreign keys. ACID properties ensure data consistency and reliability.

### SQL Fundamentals

SQL (Structured Query Language) is the standard language for interacting with relational databases. Understanding SELECT, INSERT, UPDATE, DELETE, and JOIN operations is essential.

### Normalization

Normalization reduces data redundancy and improves data integrity. The process involves organizing data to minimize duplication and ensure dependencies are properly handled.

## NoSQL Databases

NoSQL databases provide alternatives to relational models, offering flexibility for unstructured or semi-structured data.

### Document Databases

Document databases store data in flexible document formats, typically JSON. They excel at handling hierarchical data and are popular for content management systems.

### Key-Value Stores

Key-value stores provide simple data models with fast read/write operations. They're ideal for caching, session management, and real-time applications.

## Performance Optimization

Database performance depends on proper indexing, query optimization, connection pooling, and caching strategies. Monitoring and profiling help identify bottlenecks.
""",
    """# Software Testing Methodologies

Testing is a critical phase in software development that ensures code quality, functionality, and reliability before deployment.

## Testing Types

Various testing types serve different purposes throughout the development lifecycle, from unit tests to end-to-end integration tests.

### Unit Testing

Unit tests verify individual components in isolation. They should be fast, independent, and cover edge cases. Mocking dependencies ensures isolation.

### Integration Testing

Integration tests verify that multiple components work together correctly. They ensure interfaces between modules function as expected.

### End-to-End Testing

End-to-end tests simulate real user scenarios across the entire application. They validate complete workflows and user interactions.

## Test-Driven Development

Test-Driven Development (TDD) involves writing tests before implementation code. This approach leads to better design and higher test coverage.

## Continuous Testing

In CI/CD pipelines, automated tests run on every code change, providing rapid feedback. This helps catch issues early and maintains code quality.
""",
]

# Additional shorter content for variety
SHORTER_CONTENT = [
    """# API Documentation

RESTful APIs follow standard HTTP methods. GET retrieves data, POST creates resources, PUT updates existing resources, and DELETE removes resources.

## Authentication

API authentication typically uses tokens or API keys. OAuth 2.0 provides a secure authorization framework for third-party access.

## Rate Limiting

Rate limiting prevents abuse by restricting the number of requests per time period. This protects servers and ensures fair resource usage.

## Error Handling

Proper error handling returns meaningful status codes and error messages. Common status codes include 400 for bad requests, 401 for unauthorized, and 500 for server errors.
""",
    """# Version Control with Git

Git is a distributed version control system that tracks changes in files and enables collaboration across teams.

## Basic Commands

`git init` creates a new repository. `git add` stages changes. `git commit` saves changes with a message. `git push` uploads to remote repositories.

## Branching Strategy

Branching allows parallel development. Feature branches isolate new work. Main branch maintains production-ready code. Merge requests facilitate code review.

## Collaboration

Git enables multiple developers to work simultaneously. Pull requests provide mechanisms for reviewing and discussing changes before merging.
""",
]


def create_test_files():
    """Create test markdown files in the test_data/docs directory structure."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    docs_dir = os.path.join(base_dir, "docs")
    
    # Create directories
    os.makedirs(os.path.join(docs_dir, "subfolder1"), exist_ok=True)
    os.makedirs(os.path.join(docs_dir, "subfolder2"), exist_ok=True)
    os.makedirs(os.path.join(docs_dir, "nested", "deep"), exist_ok=True)
    
    # Create files in root
    for i, content in enumerate(TEMPLATES, 1):
        file_path = os.path.join(docs_dir, f"document_{i}.md")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Created: {file_path}")
    
    # Create files in subfolder1
    for i, content in enumerate(SHORTER_CONTENT[:2], 1):
        file_path = os.path.join(docs_dir, "subfolder1", f"api_doc_{i}.md")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Created: {file_path}")
    
    # Create files in subfolder2
    for i, content in enumerate(TEMPLATES[:2], 1):
        file_path = os.path.join(docs_dir, "subfolder2", f"guide_{i}.md")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Created: {file_path}")
    
    # Create files in nested/deep
    for i, content in enumerate(SHORTER_CONTENT, 1):
        file_path = os.path.join(docs_dir, "nested", "deep", f"deep_doc_{i}.md")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Created: {file_path}")
    
    # Add a few more files with different content
    additional_content = """# Container Orchestration

Container orchestration platforms like Kubernetes manage containerized applications at scale.

## Pods and Services

Pods are the smallest deployable units. Services provide stable network endpoints for pod access. Load balancing distributes traffic across instances.

## Deployments

Deployments manage replica sets and enable rolling updates. They ensure desired state matches actual state through reconciliation loops.

## Scaling

Horizontal scaling adds more pod instances. Vertical scaling increases resource allocation. Auto-scaling adjusts based on metrics automatically.
"""
    
    for i in range(3):
        file_path = os.path.join(docs_dir, f"container_{i+1}.md")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(additional_content)
        print(f"Created: {file_path}")
    
    total_files = len(TEMPLATES) + 2 + 2 + len(SHORTER_CONTENT) + 3
    print(f"\nCreated {total_files} test markdown files in {docs_dir}")
    print(f"Folder structure:")
    print(f"  docs/")
    print(f"    document_*.md (5 files)")
    print(f"    container_*.md (3 files)")
    print(f"    subfolder1/")
    print(f"      api_doc_*.md (2 files)")
    print(f"    subfolder2/")
    print(f"      guide_*.md (2 files)")
    print(f"    nested/deep/")
    print(f"      deep_doc_*.md (2 files)")


if __name__ == "__main__":
    create_test_files()

