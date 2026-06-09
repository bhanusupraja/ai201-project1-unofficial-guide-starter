"""
Chunk Inspector: Displays and validates chunks for quality.

Milestone 3 checkpoint: Print 5 random chunks and verify they're:
- Readable and substantive
- Self-contained (answerable without context)
- Free of HTML/artifacts
"""

import random
import logging
from typing import List, Dict
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ChunkInspector:
    """Inspect and validate chunks for quality."""
    
    def __init__(self):
        self.inspection_results = []
    
    def print_sample_chunks(self, chunks: List[Dict], num_samples: int = 5) -> List[Dict]:
        """
        Print random sample of chunks for inspection.
        
        Args:
            chunks: List of chunk dicts
            num_samples: Number of chunks to display
        
        Returns:
            List of sampled chunks
        """
        if not chunks:
            logger.error("No chunks to inspect!")
            return []
        
        samples = random.sample(chunks, min(num_samples, len(chunks)))
        
        print("\n" + "=" * 80)
        print(f"MILESTONE 3 CHECKPOINT: {num_samples} Random Chunk Samples")
        print("=" * 80 + "\n")
        
        for i, chunk in enumerate(samples, 1):
            self._print_chunk(chunk, i)
        
        return samples
    
    def _print_chunk(self, chunk: Dict, index: int):
        """Print a single chunk with metadata."""
        print(f"--- CHUNK {index} ---")
        print(f"ID: {chunk['chunk_id']}")
        print(f"Source: {chunk['metadata'].get('source', 'unknown')}")
        print(f"Tokens: {chunk['token_count']} | Words: {len(chunk['text'].split())}")
        print(f"Characters: {chunk['char_count']}")
        print("-" * 40)
        print(chunk["text"][:500])  # First 500 chars
        
        if len(chunk["text"]) > 500:
            print("[... truncated for display ...]")
        
        print("-" * 40)
        
        # Quality check
        is_valid, reason = self._quick_quality_check(chunk)
        status = "✓ GOOD" if is_valid else "✗ ISSUE"
        print(f"Quality: {status} - {reason}")
        print()
    
    @staticmethod
    def _quick_quality_check(chunk: Dict) -> tuple:
        """Quick quality check on a chunk."""
        text = chunk["text"]
        token_count = chunk["token_count"]
        
        # Checks
        if token_count < 50:
            return False, f"Too small ({token_count} tokens)"
        
        if token_count > 600:
            return False, f"Too large ({token_count} tokens)"
        
        if len(text.split()) < 5:
            return False, "Too few words"
        
        if "<" in text or ">" in text:
            html_ratio = sum(1 for c in text if c in "<>") / len(text)
            if html_ratio > 0.01:
                return False, "HTML artifacts detected"
        
        if not text[0].isalpha() and text[0] not in ['"', "'"]:
            return False, "Doesn't start with letter (possible artifact)"
        
        return True, f"Valid ({token_count} tokens, {len(chunk['text'].split())} words)"
    
    def generate_quality_summary(self, chunks: List[Dict]) -> Dict:
        """Generate detailed quality summary."""
        summary = {
            "total_chunks": len(chunks),
            "statistics": {
                "avg_tokens": 0,
                "min_tokens": 0,
                "max_tokens": 0,
                "median_tokens": 0,
                "avg_words": 0,
                "chunks_in_target_range": 0,  # 300-400 tokens
            },
            "quality_checks": {
                "valid": 0,
                "too_small": 0,
                "too_large": 0,
                "has_html": 0,
                "too_few_words": 0,
                "other": 0,
            },
            "issues": [],
        }
        
        if not chunks:
            return summary
        
        # Calculate statistics
        token_counts = [c["token_count"] for c in chunks]
        word_counts = [len(c["text"].split()) for c in chunks]
        
        summary["statistics"]["avg_tokens"] = sum(token_counts) / len(token_counts)
        summary["statistics"]["min_tokens"] = min(token_counts)
        summary["statistics"]["max_tokens"] = max(token_counts)
        summary["statistics"]["avg_words"] = sum(word_counts) / len(word_counts)
        
        # Calculate median
        sorted_tokens = sorted(token_counts)
        if len(sorted_tokens) % 2 == 0:
            summary["statistics"]["median_tokens"] = (
                sorted_tokens[len(sorted_tokens) // 2 - 1] +
                sorted_tokens[len(sorted_tokens) // 2]
            ) / 2
        else:
            summary["statistics"]["median_tokens"] = sorted_tokens[len(sorted_tokens) // 2]
        
        # Count chunks in target range
        summary["statistics"]["chunks_in_target_range"] = sum(
            1 for c in chunks if 300 <= c["token_count"] <= 400
        )
        
        # Quality checks
        for chunk in chunks:
            is_valid, reason = self._quick_quality_check(chunk)
            
            if is_valid:
                summary["quality_checks"]["valid"] += 1
            elif "Too small" in reason:
                summary["quality_checks"]["too_small"] += 1
                if len(summary["issues"]) < 5:
                    summary["issues"].append({
                        "chunk_id": chunk["chunk_id"],
                        "issue": reason,
                        "tokens": chunk["token_count"]
                    })
            elif "Too large" in reason:
                summary["quality_checks"]["too_large"] += 1
                if len(summary["issues"]) < 5:
                    summary["issues"].append({
                        "chunk_id": chunk["chunk_id"],
                        "issue": reason,
                        "tokens": chunk["token_count"]
                    })
            elif "HTML" in reason:
                summary["quality_checks"]["has_html"] += 1
            elif "Too few" in reason:
                summary["quality_checks"]["too_few_words"] += 1
            else:
                summary["quality_checks"]["other"] += 1
        
        return summary
    
    def print_quality_summary(self, chunks: List[Dict]):
        """Print formatted quality summary."""
        summary = self.generate_quality_summary(chunks)
        
        print("\n" + "=" * 80)
        print("CHUNK QUALITY SUMMARY")
        print("=" * 80)
        
        print(f"\nTotal chunks: {summary['total_chunks']}")
        
        print("\nToken Statistics:")
        stats = summary["statistics"]
        print(f"  Average: {stats['avg_tokens']:.0f} tokens")
        print(f"  Median: {stats['median_tokens']:.0f} tokens")
        print(f"  Range: {stats['min_tokens']}-{stats['max_tokens']} tokens")
        print(f"  Target range (300-400): {stats['chunks_in_target_range']} chunks ({stats['chunks_in_target_range']/summary['total_chunks']*100:.1f}%)")
        
        print("\nWord Statistics:")
        print(f"  Average words per chunk: {stats['avg_words']:.0f}")
        
        print("\nQuality Breakdown:")
        quality = summary["quality_checks"]
        total_checked = sum(quality.values())
        if total_checked > 0:
            print(f"  ✓ Valid: {quality['valid']} ({quality['valid']/total_checked*100:.1f}%)")
            if quality['too_small'] > 0:
                print(f"  ✗ Too small: {quality['too_small']} ({quality['too_small']/total_checked*100:.1f}%)")
            if quality['too_large'] > 0:
                print(f"  ✗ Too large: {quality['too_large']} ({quality['too_large']/total_checked*100:.1f}%)")
            if quality['has_html'] > 0:
                print(f"  ✗ HTML artifacts: {quality['has_html']}")
            if quality['too_few_words'] > 0:
                print(f"  ✗ Too few words: {quality['too_few_words']}")
        
        if summary["issues"]:
            print("\nSample Issues (first 5):")
            for issue in summary["issues"]:
                print(f"  - {issue['chunk_id']}: {issue['issue']}")
        
        print("\n" + "=" * 80 + "\n")
        
        # Recommendations
        if stats['chunks_in_target_range'] / summary['total_chunks'] < 0.6:
            print("⚠️  RECOMMENDATION: Less than 60% of chunks in target range (300-400 tokens).")
            if stats['avg_tokens'] > 450:
                print("    Your chunks are too large. Consider reducing chunk_size or increasing overlap.")
            elif stats['avg_tokens'] < 200:
                print("    Your chunks are too small. Consider increasing chunk_size or decreasing overlap.")
        else:
            print("✓ Chunk distribution looks good!")
        
        print()
    
    def export_chunks_to_json(self, chunks: List[Dict], output_path: str):
        """Export chunks to JSON for debugging."""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(chunks, f, indent=2, ensure_ascii=False)
        logger.info(f"Exported {len(chunks)} chunks to {output_path}")
