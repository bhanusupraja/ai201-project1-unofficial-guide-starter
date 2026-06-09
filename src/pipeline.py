"""
Main Pipeline: Orchestrates document ingestion, cleaning, and chunking.

Milestone 3: Build the Document Pipeline
- Load documents from documents/ folder
- Clean and preprocess
- Chunk according to planning.md spec
- Validate and inspect chunks
- Save for next milestone
"""

import sys
import json
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from document_loader import DocumentLoader, Document
from document_cleaner import BatchCleaner
from chunking import BatchChunker
from validation import ChunkInspector

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def main():
    """Run the complete pipeline."""
    
    print("\n" + "=" * 80)
    print("MILESTONE 3: DOCUMENT PIPELINE")
    print("Ingestion → Cleaning → Chunking → Validation")
    print("=" * 80 + "\n")
    
    # Step 1: Load documents
    print("Step 1: Loading Documents...")
    print("-" * 40)
    
    loader = DocumentLoader(documents_dir="documents")
    
    # Create sample documents if none exist
    txt_files = list(loader.documents_dir.glob("*.txt"))
    if len(txt_files) == 0:
        logger.info("No .txt files found. Creating sample documents...")
        documents = loader.create_sample_documents()
    else:
        documents = loader.load_from_directory()
    
    # Print load stats
    stats = loader.get_stats()
    print(f"\n✓ Loaded {stats['total_documents']} documents")
    print(f"  Total words: {stats['total_words']:,}")
    print(f"  Average per document: {stats['avg_words_per_doc']:.0f} words")
    
    for doc_info in stats['documents'][:5]:  # Show first 5
        print(f"    - {doc_info['source']}: {doc_info['words']} words")
    
    if len(stats['documents']) > 5:
        print(f"    ... and {len(stats['documents']) - 5} more")
    
    # Step 2: Clean documents
    print("\n\nStep 2: Cleaning Documents...")
    print("-" * 40)
    
    cleaner = BatchCleaner()
    cleaned_docs = cleaner.clean_documents(documents)
    
    print(f"\n✓ Cleaned {cleaner.stats['cleaned_documents']} documents")
    print(f"  Skipped: {cleaner.stats['skipped_documents']} documents")
    print(f"  Average size reduction: {cleaner.stats['avg_reduction_percent']:.1f}%")
    
    # Spot check: print first cleaned document
    if cleaned_docs:
        print(f"\n  Spot check - First document after cleaning:")
        print(f"  Source: {cleaned_docs[0].source}")
        print(f"  Preview: {cleaned_docs[0].text[:200]}...")
    
    # Step 3: Chunk documents
    print("\n\nStep 3: Chunking Documents...")
    print("-" * 40)
    
    chunker = BatchChunker()
    chunks = chunker.chunk_documents(cleaned_docs)
    
    print(f"\n✓ Created {chunker.stats['total_chunks']} chunks")
    print(f"  Average tokens per chunk: {chunker.stats['avg_tokens_per_chunk']:.0f}")
    print(f"  Token range: {chunker.stats['min_tokens']}-{chunker.stats['max_tokens']}")
    print(f"  Chunks in target range (300-400 tokens): {chunker.stats['chunks_in_target_range']} ({chunker.stats['chunks_in_target_range']/chunker.stats['total_chunks']*100:.1f}%)")
    
    # Step 4: Quality validation
    print("\n\nStep 4: Quality Validation...")
    print("-" * 40)
    
    quality_report = chunker.get_quality_report(chunks)
    print(f"\n✓ Quality Report:")
    print(f"  Valid chunks: {quality_report['valid_chunks']}/{quality_report['total_chunks']} ({quality_report['quality_score_percent']:.1f}%)")
    
    if quality_report['issues']:
        print(f"  Issues found: {len(quality_report['issues'])}")
        for issue in quality_report['issues'][:3]:
            print(f"    - {issue['chunk_id']}: {issue['reason']}")
    
    # Step 5: Inspect samples
    print("\n\nStep 5: Sample Inspection...")
    print("-" * 40)
    
    inspector = ChunkInspector()
    samples = inspector.print_sample_chunks(chunks, num_samples=5)
    
    # Step 6: Detailed quality summary
    print("\nStep 6: Detailed Quality Summary...")
    print("-" * 40)
    
    inspector.print_quality_summary(chunks)
    
    # Step 7: Save results
    print("Step 7: Saving Results...")
    print("-" * 40)
    
    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)
    
    # Save chunks as JSON
    chunks_output = output_dir / "chunks.json"
    inspector.export_chunks_to_json(chunks, str(chunks_output))
    print(f"✓ Chunks saved to {chunks_output}")
    
    # Save metadata
    metadata = {
        "pipeline_stats": {
            "total_documents_loaded": stats['total_documents'],
            "documents_cleaned": cleaner.stats['cleaned_documents'],
            "total_chunks": chunker.stats['total_chunks'],
            "avg_tokens_per_chunk": chunker.stats['avg_tokens_per_chunk'],
            "quality_score_percent": quality_report['quality_score_percent'],
        },
        "chunking_spec": {
            "chunk_size_tokens_target": "300-400",
            "overlap_tokens": 50,
            "strategy": "RecursiveCharacterTextSplitter with sentence boundaries"
        },
        "sample_chunks": [
            {
                "chunk_id": s["chunk_id"],
                "tokens": s["token_count"],
                "words": len(s["text"].split()),
                "preview": s["text"][:100] + "..."
            }
            for s in samples
        ]
    }
    
    metadata_output = output_dir / "pipeline_metadata.json"
    with open(metadata_output, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    print(f"✓ Metadata saved to {metadata_output}")
    
    # Final summary
    print("\n" + "=" * 80)
    print("MILESTONE 3 COMPLETE")
    print("=" * 80)
    print(f"""
Summary:
  ✓ Documents loaded: {stats['total_documents']}
  ✓ Documents cleaned: {cleaner.stats['cleaned_documents']}
  ✓ Total chunks created: {chunker.stats['total_chunks']}
  ✓ Average chunk size: {chunker.stats['avg_tokens_per_chunk']:.0f} tokens
  ✓ Quality score: {quality_report['quality_score_percent']:.1f}%
  ✓ In target range (300-400 tokens): {chunker.stats['chunks_in_target_range']} ({chunker.stats['chunks_in_target_range']/chunker.stats['total_chunks']*100:.1f}%)

Next: Milestone 4 - Embedding and Retrieval
  - Use {len(chunks)} chunks for embedding
  - Initialize ChromaDB vector store
  - Test retrieval on planning.md test questions
    """)
    
    print("=" * 80 + "\n")
    
    return {
        "documents": cleaned_docs,
        "chunks": chunks,
        "stats": {
            "total_documents": stats['total_documents'],
            "total_chunks": chunker.stats['total_chunks'],
            "quality_score": quality_report['quality_score_percent'],
        }
    }


if __name__ == "__main__":
    result = main()
