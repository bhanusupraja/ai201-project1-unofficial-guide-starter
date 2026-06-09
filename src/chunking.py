"""
Text Chunking: Splits documents into chunks matching the planning.md spec.

Strategy from planning.md:
- Chunk size: 300-400 tokens (~1,200-1,600 characters)
- Overlap: 50 tokens (~200 characters)
- Reason: Review-heavy corpus; preserves individual reviews intact
"""

import logging
import tiktoken
from typing import List, Dict, Tuple
from langchain_text_splitters import RecursiveCharacterTextSplitter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ChunkingStrategy:
    """Implements the chunking strategy from planning.md."""
    
    # From planning.md spec
    CHUNK_SIZE_TOKENS = 350  # Target: 300-400 tokens
    OVERLAP_TOKENS = 50
    
    # Character approximations (tokens ≈ words * 1.3)
    AVG_TOKENS_PER_CHAR = 0.25  # 1 token ≈ 4 characters (conservative)
    CHUNK_SIZE_CHARS = int(CHUNK_SIZE_TOKENS / AVG_TOKENS_PER_CHAR)  # ~1,400 chars
    OVERLAP_CHARS = int(OVERLAP_TOKENS / AVG_TOKENS_PER_CHAR)  # ~200 chars
    
    def __init__(self):
        # Initialize tokenizer for accurate token counting
        self.encoding = tiktoken.get_encoding("cl100k_base")
        
        # Create splitter matching our spec
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.CHUNK_SIZE_CHARS,
            chunk_overlap=self.OVERLAP_CHARS,
            separators=["\n\n", "\n", ". ", " ", ""],  # Respect sentence/paragraph boundaries
            length_function=len,
        )
    
    def chunk_text(self, text: str, metadata: Dict = None) -> List[Dict]:
        """
        Split text into chunks following planning.md spec.
        
        Args:
            text: Document text to chunk
            metadata: Document metadata (source, url, etc.)
        
        Returns:
            List of chunk dicts with text, chunk_id, token_count, metadata
        """
        if not text or len(text.strip()) < 50:
            logger.warning(f"Skipping tiny document: {metadata}")
            return []
        
        # Split text
        chunks_text = self.splitter.split_text(text)
        
        chunks = []
        for i, chunk_text in enumerate(chunks_text):
            # Count tokens in this chunk
            token_count = len(self.encoding.encode(chunk_text))
            
            # Skip empty chunks
            if not chunk_text.strip() or token_count < 5:
                continue
            
            chunk = {
                "chunk_id": f"{metadata.get('source', 'unknown')}_chunk_{i:03d}" if metadata else f"chunk_{i:03d}",
                "text": chunk_text.strip(),
                "token_count": token_count,
                "char_count": len(chunk_text),
                "metadata": metadata or {},
                "sequence": i,
            }
            chunks.append(chunk)
        
        return chunks
    
    def get_chunk_stats(self, chunk: Dict) -> Dict:
        """Get statistics about a chunk."""
        return {
            "token_count": chunk["token_count"],
            "char_count": chunk["char_count"],
            "word_count": len(chunk["text"].split()),
            "sentence_count": len([s for s in chunk["text"].split(".") if s.strip()]),
            "lines": len(chunk["text"].split("\n")),
        }
    
    def validate_chunk_quality(self, chunk: Dict) -> Tuple[bool, str]:
        """
        Validate that a chunk is high quality.
        
        Returns: (is_valid, reason)
        """
        text = chunk["text"]
        token_count = chunk["token_count"]
        
        # Check token count in target range
        if token_count < 50:
            return False, f"Too small ({token_count} tokens)"
        
        if token_count > 600:
            return False, f"Too large ({token_count} tokens, consider smaller overlap)"
        
        # Check for HTML artifacts
        if "<" in text or ">" in text or "&" in text:
            # Quick check - if it looks like HTML
            html_chars = len([c for c in text if c in "<>&"])
            if html_chars / len(text) > 0.01:  # More than 1% HTML chars
                return False, "Contains HTML artifacts"
        
        # Check for mostly whitespace
        if len(text.split()) < 5:
            return False, "Too few words"
        
        # Check for natural language (not a menu/list of links)
        words = text.split()
        avg_word_length = sum(len(w) for w in words) / len(words)
        
        if avg_word_length < 2:  # Average word too short
            return False, "Average word too short (possible navigation text)"
        
        # Check that it starts/ends reasonably
        if text.startswith(("http://", "https://", ">>>", ">>>")):
            return False, "Looks like URL or code artifact"
        
        return True, "Valid"


class BatchChunker:
    """Chunk multiple documents efficiently."""
    
    def __init__(self):
        self.strategy = ChunkingStrategy()
        self.stats = {
            "total_documents": 0,
            "total_chunks": 0,
            "avg_tokens_per_chunk": 0,
            "min_tokens": float('inf'),
            "max_tokens": 0,
            "chunks_in_target_range": 0,  # 300-400 tokens
        }
    
    def chunk_documents(self, documents: List) -> List[Dict]:
        """
        Chunk a batch of documents.
        
        Args:
            documents: List of Document objects with .text and .source attributes
        
        Returns:
            List of chunks
        """
        all_chunks = []
        token_counts = []
        
        for doc in documents:
            metadata = {
                "source": doc.source,
                "source_type": doc.source_type,
                **doc.metadata,
            }
            
            # Chunk this document
            chunks = self.strategy.chunk_text(doc.text, metadata)
            all_chunks.extend(chunks)
            
            # Track stats
            for chunk in chunks:
                token_counts.append(chunk["token_count"])
                
                # Check if in target range (300-400 tokens)
                if 300 <= chunk["token_count"] <= 400:
                    self.stats["chunks_in_target_range"] += 1
                
                self.stats["min_tokens"] = min(self.stats["min_tokens"], chunk["token_count"])
                self.stats["max_tokens"] = max(self.stats["max_tokens"], chunk["token_count"])
            
            self.stats["total_documents"] += 1
        
        # Calculate aggregate stats
        if token_counts:
            self.stats["total_chunks"] = len(all_chunks)
            self.stats["avg_tokens_per_chunk"] = sum(token_counts) / len(token_counts)
        
        logger.info(
            f"Created {self.stats['total_chunks']} chunks from {self.stats['total_documents']} documents. "
            f"Avg: {self.stats['avg_tokens_per_chunk']:.0f} tokens, "
            f"Range: {self.stats['min_tokens']}-{self.stats['max_tokens']} tokens. "
            f"{self.stats['chunks_in_target_range']} chunks in target range (300-400 tokens)."
        )
        
        return all_chunks
    
    def get_quality_report(self, chunks: List[Dict]) -> Dict:
        """Generate a quality report for chunks."""
        valid_chunks = []
        invalid_chunks = []
        
        for chunk in chunks:
            is_valid, reason = self.strategy.validate_chunk_quality(chunk)
            
            if is_valid:
                valid_chunks.append(chunk)
            else:
                invalid_chunks.append({
                    "chunk_id": chunk["chunk_id"],
                    "reason": reason,
                    "tokens": chunk["token_count"],
                })
        
        quality_score = len(valid_chunks) / len(chunks) * 100 if chunks else 0
        
        report = {
            "total_chunks": len(chunks),
            "valid_chunks": len(valid_chunks),
            "invalid_chunks": len(invalid_chunks),
            "quality_score_percent": quality_score,
            "issues": invalid_chunks[:10],  # First 10 issues
        }
        
        logger.info(f"Chunk quality: {quality_score:.1f}% valid ({len(valid_chunks)}/{len(chunks)})")
        
        if invalid_chunks:
            logger.warning(f"Found {len(invalid_chunks)} low-quality chunks:")
            for issue in invalid_chunks[:5]:
                logger.warning(f"  - {issue['chunk_id']}: {issue['reason']}")
        
        return report
