"""
CLI Interface for the Unofficial Guide to Course and Professor Reviews.

Run with: python cli.py
Provides interactive query interface in terminal.
"""

import sys
import logging
from src.query import QueryOrchestrator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def print_banner():
    """Print welcome banner."""
    print("\n" + "="*80)
    print("📚 UNOFFICIAL GUIDE: Course and Professor Reviews - Query Interface")
    print("="*80)
    print("\nAsk questions about:")
    print("  • Workload and homework expectations")
    print("  • Teaching styles and clarity")
    print("  • Exam difficulty and grading fairness")
    print("  • Professor accessibility")
    print("  • Factors that make courses review-worthy")
    print("\n💡 Tip: Responses are grounded in actual student reviews.")
    print("   Questions outside the domain will be declined explicitly.\n")
    print("Commands:")
    print("  • Enter a question and press Enter")
    print("  • Type 'examples' to see sample questions")
    print("  • Type 'exit' to quit\n")


def print_examples():
    """Print example questions."""
    examples = [
        "What do students say about workload in intro CS courses?",
        "Which teaching styles help students learn best?",
        "How do students rate approachable professors?",
        "What makes a course worth reviewing?",
        "Tell me about exam difficulty and grading.",
    ]
    
    print("\n📋 Example Questions:")
    for i, q in enumerate(examples, 1):
        print(f"  {i}. {q}")
    print()


def format_response(result: dict) -> str:
    """Format result for display."""
    lines = []
    lines.append("\n" + "="*80)
    lines.append("RESPONSE")
    lines.append("="*80)
    lines.append(f"\nQ: {result['question']}\n")
    lines.append(f"A: {result['answer']}\n")
    
    lines.append("📍 Sources:")
    for score_info in result['retrieval_scores']:
        lines.append(f"   • {score_info['source']} (relevance: {score_info['similarity']:.2f})")
    
    lines.append(f"\n✓ Retrieved {result['chunks_used']} document(s)")
    lines.append(f"✓ Mode: {'Mock LLM' if result['mode'] == 'mock' else 'Groq API'}")
    lines.append("="*80 + "\n")
    
    return "\n".join(lines)


def main():
    """Main CLI loop."""
    print_banner()
    
    # Initialize
    logger.info("Initializing query orchestrator...")
    orchestrator = QueryOrchestrator(use_real_llm=False)
    logger.info("✓ Ready for queries\n")
    
    while True:
        try:
            user_input = input("Enter your question (or 'examples'/'exit'): ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() == 'exit':
                print("\n👋 Goodbye!\n")
                break
            
            if user_input.lower() == 'examples':
                print_examples()
                continue
            
            # Process query
            result = orchestrator.query(user_input)
            print(format_response(result))
        
        except KeyboardInterrupt:
            print("\n\n👋 Interrupted. Goodbye!\n")
            break
        except Exception as e:
            logger.error(f"Error: {e}")
            print(f"Error processing query: {str(e)}\n")


if __name__ == "__main__":
    main()
