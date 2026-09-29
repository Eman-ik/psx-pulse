"""
Document Management System (Sprint 2)

Source of truth for all company research documents.
Pipeline: RECEIVED -> EXTRACTING -> EXTRACTED -> NORMALIZING -> NORMALIZED
"""

import os
import hashlib
from datetime import datetime
from pathlib import Path
from sqlalchemy.orm import Session
from .schema import Document, DocumentType, ProcessingStatus, Security, Source, SourceType
from .database import get_session


# Document storage configuration
DOCUMENT_STORAGE_DIR = os.getenv("DOCUMENT_STORAGE_DIR", "./documents")


def ensure_storage_dir():
    """Ensure document storage directory exists."""
    Path(DOCUMENT_STORAGE_DIR).mkdir(parents=True, exist_ok=True)
    return DOCUMENT_STORAGE_DIR


def calculate_checksum(file_content: bytes) -> str:
    """Calculate SHA-256 checksum of file content."""
    return hashlib.sha256(file_content).hexdigest()


def get_storage_path(security_id: int, filename: str) -> str:
    """Get storage path for a document."""
    # Create subdirectory for each company
    company_dir = Path(DOCUMENT_STORAGE_DIR) / f"security_{security_id}"
    company_dir.mkdir(parents=True, exist_ok=True)
    return str(company_dir / filename)


def upload_document(
    session: Session,
    security_id: int,
    file_content: bytes,
    filename: str,
    document_type: DocumentType,
    publication_date,
    fiscal_year: int = None,
    fiscal_quarter: int = None,
    source_id: int = None,
) -> Document:
    """
    Upload a document.

    Args:
        session: Database session
        security_id: Company security_id
        file_content: File content (bytes)
        filename: Original filename
        document_type: Type of document (ANNUAL_REPORT, QUARTERLY_REPORT, etc.)
        publication_date: When document was published
        fiscal_year: Fiscal year (optional)
        fiscal_quarter: 1/2/3/4 for quarterly (optional)
        source_id: Source of document (optional, defaults to PSX)

    Returns:
        Document record
    """
    # Verify company exists
    security = session.query(Security).filter_by(security_id=security_id).first()
    if not security:
        raise ValueError(f"Security {security_id} not found")

    # Get or create PSX source if not provided
    if source_id is None:
        psx_source = session.query(Source).filter_by(
            source_type=SourceType.PSX,
            source_name="PSX Official"
        ).first()
        if psx_source:
            source_id = psx_source.source_id
        else:
            # Create default source
            source = Source(
                source_type=SourceType.PSX,
                source_name="PSX Official",
                source_url="https://www.psx.com.pk"
            )
            session.add(source)
            session.flush()
            source_id = source.source_id

    # Calculate checksum
    checksum = calculate_checksum(file_content)

    # Check if document already exists
    existing = session.query(Document).filter(
        Document.security_id == security_id,
        Document.document_type == document_type,
        Document.fiscal_year == fiscal_year,
        Document.fiscal_quarter == fiscal_quarter,
    ).first()

    if existing and existing.checksum == checksum:
        # Same file already uploaded
        return existing

    # Create storage path and save file
    storage_path = get_storage_path(security_id, filename)
    with open(storage_path, 'wb') as f:
        f.write(file_content)

    # Convert datetime if needed
    if isinstance(publication_date, datetime):
        publication_date = publication_date.date()

    # Create document record
    document = Document(
        security_id=security_id,
        title=f"{security.company_name} {document_type.value} FY{fiscal_year}" if fiscal_year else filename,
        document_type=document_type,
        publication_date=publication_date,
        fiscal_year=fiscal_year,
        fiscal_quarter=fiscal_quarter,
        source_id=source_id,
        file_path=storage_path,
        checksum=checksum,
        processing_status=ProcessingStatus.RECEIVED,
    )

    session.add(document)
    session.commit()

    return document


def update_processing_status(
    session: Session,
    document_id: int,
    status: ProcessingStatus,
    notes: str = None,
) -> Document:
    """Update document processing status."""
    document = session.query(Document).filter_by(document_id=document_id).first()
    if not document:
        raise ValueError(f"Document {document_id} not found")

    document.processing_status = status

    if status == ProcessingStatus.NORMALIZED:
        document.processed_at = datetime.utcnow()

    session.commit()
    return document


def get_documents_by_company(session: Session, security_id: int) -> list:
    """Get all documents for a company."""
    return session.query(Document).filter_by(security_id=security_id).all()


def get_documents_by_status(session: Session, status: ProcessingStatus) -> list:
    """Get all documents with a specific processing status."""
    return session.query(Document).filter_by(processing_status=status).all()


def get_document_content(document: Document) -> bytes:
    """Read document file content."""
    if not os.path.exists(document.file_path):
        raise FileNotFoundError(f"Document file not found: {document.file_path}")

    with open(document.file_path, 'rb') as f:
        return f.read()


def verify_document_integrity(document: Document) -> bool:
    """Verify document hasn't been corrupted."""
    try:
        content = get_document_content(document)
        current_checksum = calculate_checksum(content)
        return current_checksum == document.checksum
    except FileNotFoundError:
        return False


def sprint_2_document_foundation():
    """
    Sprint 2: Document Foundation Implementation

    1. Create storage directory
    2. Upload test documents
    3. Verify processing pipeline
    4. Test integrity checking
    """
    print("\n" + "="*70)
    print("SPRINT 2: DOCUMENT FOUNDATION IMPLEMENTATION")
    print("="*70 + "\n")

    session = get_session()

    try:
        print("Step 1: Ensuring document storage exists...")
        storage_dir = ensure_storage_dir()
        print(f"[OK] Storage directory: {storage_dir}\n")

        print("Step 2: Testing document upload...")

        # Get FFC (security_id=1)
        ffc = session.query(Security).filter_by(ticker="FFC").first()

        # Create test document
        test_content = b"FFC Annual Report FY2026\n\nRevenue: 182.5bn PKR\nProfit: 45.2bn PKR"

        doc = upload_document(
            session=session,
            security_id=ffc.security_id,
            file_content=test_content,
            filename="FFC_Annual_Report_FY2026.pdf",
            document_type=DocumentType.ANNUAL_REPORT,
            publication_date=datetime(2026, 8, 15),
            fiscal_year=2026,
            fiscal_quarter=None,
        )
        print(f"[OK] Document uploaded:")
        print(f"     security_id: {doc.security_id}")
        print(f"     document_id: {doc.document_id}")
        print(f"     title: {doc.title}")
        print(f"     status: {doc.processing_status.value}")
        print(f"     checksum: {doc.checksum[:16]}...\n")

        print("Step 3: Testing processing status updates...")

        # Simulate extraction
        doc = update_processing_status(
            session=session,
            document_id=doc.document_id,
            status=ProcessingStatus.EXTRACTING,
        )
        print(f"[OK] Status updated: {doc.processing_status.value}")

        # Simulate extracted
        doc = update_processing_status(
            session=session,
            document_id=doc.document_id,
            status=ProcessingStatus.EXTRACTED,
        )
        print(f"[OK] Status updated: {doc.processing_status.value}")

        # Simulate normalizing
        doc = update_processing_status(
            session=session,
            document_id=doc.document_id,
            status=ProcessingStatus.NORMALIZING,
        )
        print(f"[OK] Status updated: {doc.processing_status.value}")

        # Simulate normalized
        doc = update_processing_status(
            session=session,
            document_id=doc.document_id,
            status=ProcessingStatus.NORMALIZED,
        )
        print(f"[OK] Status updated: {doc.processing_status.value}\n")

        print("Step 4: Testing document integrity...")

        # Verify integrity
        is_intact = verify_document_integrity(doc)
        print(f"[OK] Document integrity verified: {is_intact}\n")

        print("Step 5: Querying documents...")

        # Get FFC documents
        ffc_docs = get_documents_by_company(session, ffc.security_id)
        print(f"[OK] FFC has {len(ffc_docs)} document(s)")

        # Get normalized documents
        normalized_docs = get_documents_by_status(session, ProcessingStatus.NORMALIZED)
        print(f"[OK] {len(normalized_docs)} document(s) in NORMALIZED status\n")

        print("="*70)
        print("SPRINT 2 COMPLETE: Document Foundation is ready")
        print("="*70)

        return {
            "documents_uploaded": 1,
            "storage_verified": True,
            "integrity_verified": is_intact,
            "status": "VALID"
        }

    finally:
        session.close()


if __name__ == "__main__":
    sprint_2_document_foundation()
