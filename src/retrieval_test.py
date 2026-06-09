"""
Milestone 4: Test Retrieval with Evaluation Questions

Tests the 5 questions from planning.md evaluation plan.
"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from embedding import EmbeddingManager, Retriever
from pipeline import main as run_milestone3
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_chunks_from_file(filepath: str = "outputs/chunks.json") -> list:
    """Load chunks from JSON output."""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def print_retrieval_result(query: str, chunks: list, result_number: int = 1):
    """Pretty-print a retrieval result."""
    print(f"\n{'='*80}")
    print(f"TEST {result_number}: '{query}'")
    print(f"{'='*80}")
    
    if not chunks:
        print("❌ NO RESULTS RETRIEVED")
        return
    
    print(f"✓ Retrieved {len(chunks)} chunks:\n")
    
    for i, chunk in enumerate(chunks, 1):
        print(f"--- Result {i} ---")
        print(f"Rank: {i} | Source: {chunk['source']}")
        print(f"Distance: {chunk['distance']:.3f} | Similarity: {chunk['similarity']:.3f}")
        print(f"Chunk ID: {chunk['chunk_id']}")
        print("-" * 40)
        
        # Print first 300 chars of chunk
        preview = chunk['text'][:300]
        if len(chunk['text']) > 300:
            preview += " [...]"
        
        print(preview)
        print()


def evaluate_retrieval(chunks: list, query: str, expected_topics: list) -> dict:
    """
    Evaluate if retrieved chunks match expected topics.
    
    Args:
        chunks: Retrieved chunks
        query: Original query
        expected_topics: List of keywords/topics expected in results
    
    Returns:
        Evaluation report
    """
    report = {
        "query": query,
        "chunks_retrieved": len(chunks),
        "expected_topics": expected_topics,
        "topics_found": [],
        "quality_score": 0,
        "assessment": "UNKNOWN"
    }
    
    if not chunks:
        report["assessment"] = "FAILED - No chunks retrieved"
        return report
    
    # Check if expected topics appear in retrieved text
    all_text = " ".join([c["text"].lower() for c in chunks])
    
    for topic in expected_topics:
        if topic.lower() in all_text:
            report["topics_found"].append(topic)
    
    # Assess quality
    coverage = len(report["topics_found"]) / len(expected_topics) if expected_topics else 0
    
    if coverage >= 0.8:
        report["assessment"] = "EXCELLENT"
        report["quality_score"] = 1.0
    elif coverage >= 0.5:
        report["assessment"] = "GOOD"
        report["quality_score"] = 0.75
    elif coverage >= 0.2:
        report["assessment"] = "PARTIAL"
        report["quality_score"] = 0.5
    else:
        report["assessment"] = "POOR"
        report["quality_score"] = 0.25
    
    return report


def main():
    """Run Milestone 4 retrieval tests."""
    
    print("\n" + "="*80)
    print("MILESTONE 4: EMBED CHUNKS AND TEST RETRIEVAL")
    print("="*80 + "\n")
    
    # Step 1: Load chunks
    print("Step 1: Loading chunks from Milestone 3...")
    print("-" * 40)
    
    chunks = load_chunks_from_file()
    print(f"✓ Loaded {len(chunks)} chunks")
    
    # Step 2: Initialize embedding manager
    print("\n\nStep 2: Initializing Embedding Manager...")
    print("-" * 40)
    
    embedding_manager = EmbeddingManager(persist_dir="chroma_db")
    print("✓ Embedding model loaded: all-MiniLM-L6-v2")
    print("✓ ChromaDB initialized")
    
    # Step 3: Create collection
    print("\n\nStep 3: Creating ChromaDB Collection...")
    print("-" * 40)
    
    embedding_manager.create_collection("unofficial_guide")
    print("✓ Collection created")
    
    # Step 4: Embed chunks
    print("\n\nStep 4: Embedding Chunks...")
    print("-" * 40)
    
    embeddings = embedding_manager.embed_chunks(chunks)
    print(f"✓ Generated {len(embeddings)} embeddings")
    
    # Step 5: Add to collection
    print("\n\nStep 5: Adding Embeddings to ChromaDB...")
    print("-" * 40)
    
    embedding_manager.add_chunks_to_collection(chunks, embeddings)
    
    # Get stats
    stats = embedding_manager.get_collection_stats()
    print(f"\n✓ Collection Statistics:")
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Step 6: Initialize retriever
    print("\n\nStep 6: Initializing Retriever...")
    print("-" * 40)
    
    retriever = Retriever(embedding_manager)
    print("✓ Retriever initialized with top-k=8")
    
    # Step 7: Test retrieval with evaluation questions
    print("\n\n" + "="*80)
    print("RETRIEVAL TESTS: Planning.md Evaluation Questions")
    print("="*80)
    
    # Define test questions from planning.md
    test_questions = [
        {
            "query": "What do students say about the workload in introductory computer science courses?",
            "expected_topics": ["homework", "workload", "hours", "projects", "assignments"],
            "description": "Workload in intro CS courses"
        },
        {
            "query": "Which teaching styles help students understand difficult material best?",
            "expected_topics": ["teaching style", "clear", "examples", "interactive", "lectures", "understanding"],
            "description": "Effective teaching styles"
        },
        {
            "query": "What are common complaints about exam difficulty and grading fairness?",
            "expected_topics": ["exam", "grading", "difficulty", "fair", "harsh", "partial credit"],
            "description": "Exam difficulty and grading"
        },
        {
            "query": "How do students rate professors who are approachable versus those who are difficult to reach?",
            "expected_topics": ["office hours", "approachable", "accessible", "responsive", "emails"],
            "description": "Professor accessibility"
        },
        {
            "query": "What factors make a course review-worthy (positive or negative)?",
            "expected_topics": ["passion", "material", "relevant", "applications", "clarity", "assignments"],
            "description": "Review-worthy factors"
        }
    ]
    
    # Run tests
    all_evaluations = []
    
    for i, test in enumerate(test_questions, 1):
        query = test["query"]
        expected_topics = test["expected_topics"]
        
        # Retrieve
        results = retriever.retrieve(query, top_k=8)
        
        # Print results
        print_retrieval_result(query, results, i)
        
        # Evaluate
        evaluation = evaluate_retrieval(results, query, expected_topics)
        all_evaluations.append(evaluation)
        
        # Print evaluation
        print(f"\nEvaluation:")
        print(f"  Assessment: {evaluation['assessment']}")
        print(f"  Quality Score: {evaluation['quality_score']:.2f}/1.0")
        print(f"  Topics Found: {len(evaluation['topics_found'])}/{len(expected_topics)}")
        if evaluation['topics_found']:
            print(f"  Matched: {', '.join(evaluation['topics_found'][:3])}")
        print()
    
    # Step 8: Summary
    print("\n" + "="*80)
    print("RETRIEVAL TEST SUMMARY")
    print("="*80)
    
    avg_quality = sum(e["quality_score"] for e in all_evaluations) / len(all_evaluations)
    
    print(f"\nTests run: {len(all_evaluations)}")
    print(f"Average quality score: {avg_quality:.2f}/1.0")
    print()
    
    for i, evaluation in enumerate(all_evaluations, 1):
        status = "✓" if evaluation["quality_score"] >= 0.5 else "✗"
        print(
            f"{status} Test {i}: {evaluation['assessment']} "
            f"({evaluation['quality_score']:.2f}) - "
            f"{len(evaluation['topics_found'])}/{len(evaluation['expected_topics'])} topics matched"
        )
    
    # Final assessment
    print("\n" + "="*80)
    if avg_quality >= 0.7:
        print("✓ RETRIEVAL CHECKPOINT PASSED")
        print("Distance scores are reasonable and retrieval is returning relevant chunks.")
        print("Ready for Milestone 5: Generation and Interface")
    elif avg_quality >= 0.5:
        print("⚠️  RETRIEVAL CHECKPOINT PARTIAL")
        print("Some retrieval is working, but consider:")
        print("  - Adjusting chunk size")
        print("  - Checking document cleaning")
        print("  - Verifying metadata attachment")
    else:
        print("❌ RETRIEVAL CHECKPOINT FAILED")
        print("Retrieval is not returning relevant results.")
        print("Debug by checking:")
        print("  1. Chunk quality (run Milestone 3)")
        print("  2. Document cleaning (are chunks readable?)")
        print("  3. Chunk size (too small = no semantic signal)")
    
    print("="*80 + "\n")
    
    # Save results
    results_file = Path("outputs") / "retrieval_test_results.json"
    with open(results_file, 'w', encoding='utf-8') as f:
        json.dump(
            {
                "timestamp": "Milestone 4",
                "total_chunks_embedded": len(chunks),
                "queries_tested": len(all_evaluations),
                "average_quality_score": avg_quality,
                "evaluations": all_evaluations,
            },
            f,
            indent=2,
            ensure_ascii=False
        )
    
    print(f"Results saved to {results_file}")
    
    return {
        "chunks": chunks,
        "embedding_manager": embedding_manager,
        "retriever": retriever,
        "evaluations": all_evaluations,
        "average_quality": avg_quality,
    }


if __name__ == "__main__":
    main()
