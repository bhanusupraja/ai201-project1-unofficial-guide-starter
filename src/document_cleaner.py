"""
Document Cleaner: Preprocesses and cleans documents before chunking.

Removes:
- HTML tags and entities
- Navigation/boilerplate text
- Duplicate whitespace
- Special characters that add noise

Keeps:
- Substantive content (reviews, opinions, facts)
- Structure (paragraph breaks, lists)
"""

import re
import logging
from typing import List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DocumentCleaner:
    """Cleans documents before chunking."""
    
    def __init__(self):
        # Common boilerplate patterns to remove
        self.boilerplate_patterns = [
            r"Read more\s*\n",
            r"Share this.*?\n",
            r"Comment count.*?\n",
            r"Updated.*?ago\n",
            r"Report.*?\n",
            r"Flag.*?\n",
            r"Thanks for reading.*?\n",
        ]
        
        # HTML entities to replace
        self.html_entities = {
            "&nbsp;": " ",
            "&amp;": "&",
            "&lt;": "<",
            "&gt;": ">",
            "&quot;": '"',
            "&apos;": "'",
            "&ldquo;": '"',
            "&rdquo;": '"',
            "&#39;": "'",
            "&#8217;": "'",
        }
    
    def clean(self, text: str) -> str:
        """
        Clean a document following the strategy:
        1. Remove HTML tags and entities
        2. Remove boilerplate/navigation text
        3. Normalize whitespace
        4. Remove trailing/leading whitespace
        """
        if not text:
            return ""
        
        # Step 1: Remove HTML tags
        text = self._remove_html_tags(text)
        
        # Step 2: Decode HTML entities
        text = self._decode_html_entities(text)
        
        # Step 3: Remove boilerplate patterns
        text = self._remove_boilerplate(text)
        
        # Step 4: Normalize whitespace
        text = self._normalize_whitespace(text)
        
        # Step 5: Remove suspicious patterns (ads, tracking, etc.)
        text = self._remove_ads_and_noise(text)
        
        return text.strip()
    
    @staticmethod
    def _remove_html_tags(text: str) -> str:
        """Remove HTML/XML tags."""
        # Remove script and style content
        text = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
        
        # Remove HTML tags
        text = re.sub(r"<[^>]+>", "", text)
        
        return text
    
    def _decode_html_entities(self, text: str) -> str:
        """Decode HTML entities."""
        for entity, char in self.html_entities.items():
            text = text.replace(entity, char)
        
        # Handle numeric entities
        text = re.sub(r"&#\d+;", "", text)
        text = re.sub(r"&#x[0-9a-f]+;", "", text, flags=re.IGNORECASE)
        
        return text
    
    def _remove_boilerplate(self, text: str) -> str:
        """Remove common boilerplate patterns."""
        for pattern in self.boilerplate_patterns:
            text = re.sub(pattern, "", text, flags=re.IGNORECASE)
        
        # Remove common nav phrases
        nav_phrases = [
            "navigation", "menu", "sidebar", "footer", "header",
            "cookie", "advertisement", "ad by", "promoted post"
        ]
        
        for phrase in nav_phrases:
            text = re.sub(rf"^.*?{phrase}.*?$", "", text, flags=re.MULTILINE | re.IGNORECASE)
        
        return text
    
    @staticmethod
    def _normalize_whitespace(text: str) -> str:
        """Normalize spaces, tabs, newlines."""
        # Replace multiple spaces with single space
        text = re.sub(r" +", " ", text)
        
        # Replace multiple newlines with double newline (preserve paragraphs)
        text = re.sub(r"\n\n+", "\n\n", text)
        
        # Remove trailing spaces on each line
        text = "\n".join(line.rstrip() for line in text.split("\n"))
        
        return text
    
    @staticmethod
    def _remove_ads_and_noise(text: str) -> str:
        """Remove ads and tracking noise."""
        # Remove common ad patterns
        text = re.sub(r"(?i)click here.*?(?:\n|$)", "", text)
        text = re.sub(r"(?i)sponsored\s+content.*?(?:\n|$)", "", text)
        text = re.sub(r"(?i)advertisement.*?(?:\n|$)", "", text)
        
        # Remove tracking pixels and beacon URLs
        text = re.sub(r"(?i)(pixel|beacon|tracker).*?(?:\n|$)", "", text)
        
        # Remove lines that are just URLs
        text = re.sub(r"^https?://[^\s]+$", "", text, flags=re.MULTILINE)
        
        return text
    
    @staticmethod
    def _validate_cleaned_text(text: str) -> bool:
        """Check if cleaned text looks reasonable."""
        # Must have some words
        if len(text.split()) < 5:
            return False
        
        # Should not be all caps (likely ads)
        if text.isupper():
            return False
        
        return True


class BatchCleaner:
    """Clean multiple documents efficiently."""
    
    def __init__(self):
        self.cleaner = DocumentCleaner()
        self.stats = {
            "total_documents": 0,
            "cleaned_documents": 0,
            "skipped_documents": 0,
            "avg_reduction_percent": 0,
        }
    
    def clean_documents(self, documents: List) -> List:
        """
        Clean a batch of documents.
        
        Args:
            documents: List of Document objects
        
        Returns:
            List of cleaned Document objects
        """
        cleaned = []
        sizes_before = []
        sizes_after = []
        
        for doc in documents:
            sizes_before.append(len(doc.text))
            
            # Clean the text
            cleaned_text = self.cleaner.clean(doc.text)
            
            sizes_after.append(len(cleaned_text))
            
            # Validate
            if self.cleaner._validate_cleaned_text(cleaned_text):
                doc.text = cleaned_text
                cleaned.append(doc)
                self.stats["cleaned_documents"] += 1
            else:
                logger.warning(f"Skipped {doc.source}: invalid after cleaning")
                self.stats["skipped_documents"] += 1
            
            self.stats["total_documents"] += 1
        
        # Calculate stats
        if sizes_before:
            reduction = [
                (sb - sa) / sb * 100
                for sb, sa in zip(sizes_before, sizes_after)
                if sb > 0
            ]
            self.stats["avg_reduction_percent"] = sum(reduction) / len(reduction)
        
        logger.info(
            f"Cleaned {self.stats['cleaned_documents']}/{self.stats['total_documents']} documents "
            f"(avg {self.stats['avg_reduction_percent']:.1f}% size reduction)"
        )
        
        return cleaned
