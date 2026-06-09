"""
Query Orchestrator: Main interface connecting retrieval and generation.

Combines:
- Retriever: Get relevant chunks from vector store
- LLM: Generate grounded response
- Source attribution: Track which documents were used
"""

import os
import json
import logging
from typing import Dict, List, Optional
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QueryOrchestrator:
    """Orchestrates the complete RAG pipeline."""
    
    def __init__(
        self,
        chunks_file: str = "outputs/chunks.json",
        use_real_llm: bool = False,
        groq_api_key: Optional[str] = None
    ):
        """
        Initialize query orchestrator.
        
        Args:
            chunks_file: Path to chunks JSON
            use_real_llm: If True, use Groq API; if False, use mock
            groq_api_key: Groq API key (or use GROQ_API_KEY env var)
        """
        self.chunks_file = chunks_file
        self.use_real_llm = use_real_llm
        self.chunks = self._load_chunks()
        
        # Initialize retriever (mock version for demo)
        from src.generation import MockRetriever, ResponseGenerator
        self.retriever = MockRetriever(self.chunks)
        
        # Initialize generator
        self.generator = ResponseGenerator(self.retriever)
        
        # Initialize LLM if requested
        if use_real_llm:
            self._init_groq_llm(groq_api_key)
        else:
            self.llm_client = None
            logger.info("Using mock LLM mode (no API key required)")
    
    def _load_chunks(self) -> List[Dict]:
        """Load chunks from file."""
        try:
            with open(self.chunks_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Chunks file not found: {self.chunks_file}")
            return []
    
    def _init_groq_llm(self, api_key: Optional[str]):
        """Initialize Groq LLM client."""
        try:
            from groq import Groq
            
            # Get API key from parameter or environment
            api_key = api_key or os.getenv("GROQ_API_KEY")
            
            if not api_key:
                logger.warning(
                    "GROQ_API_KEY not found. Set it in .env or pass as parameter. "
                    "Falling back to mock mode."
                )
                self.llm_client = None
                self.use_real_llm = False
                return
            
            self.llm_client = Groq(api_key=api_key)
            logger.info("✓ Initialized Groq LLM client")
            
        except ImportError:
            logger.error("groq package not installed. Run: pip install groq")
            self.llm_client = None
            self.use_real_llm = False
    
    def _create_system_prompt(self) -> str:
        """Create grounding system prompt for LLM."""
        return """You are a helpful assistant for the Unofficial Guide to Course and Professor Reviews.

CRITICAL GROUNDING RULES - YOU MUST FOLLOW THESE:

1. ANSWER ONLY FROM PROVIDED DOCUMENTS
   - Only use information explicitly stated in the provided context
   - Do NOT use your general knowledge about professors, courses, or teaching
   - Do NOT infer or extrapolate beyond what the documents say

2. IF INFORMATION IS NOT IN DOCUMENTS
   - Say: "I don't have information about that topic in the available reviews."
   - Do NOT make up answers or guess
   - Be honest about gaps in the data

3. CITE YOUR SOURCES
   - Always mention which document or source your information comes from
   - Example: "According to reviews from [source name]..."
   - Use document names if available

4. HANDLE CONTRADICTIONS
   - If reviews are mixed or contradictory, say so explicitly
   - Report what different sources say, don't pick one as "correct"

5. FORMAT YOUR RESPONSE
   - Start with a direct answer to the question
   - Support with specific quotes or evidence from documents
   - Cite sources for each claim
   - End with any limitations or caveats

REMEMBER: Your job is to be a faithful interface to the documents, not to generate plausible answers."""
    
    def _format_context_for_llm(self, chunks: List[Dict]) -> str:
        """Format retrieved chunks as context for LLM."""
        if not chunks:
            return "NO RELEVANT DOCUMENTS FOUND"
        
        context_lines = []
        
        for i, chunk in enumerate(chunks, 1):
            source = chunk.get("source", "unknown")
            text = chunk.get("text", "")
            similarity = chunk.get("similarity", 0)
            
            context_lines.append(f"--- Document {i}: {source} (relevance: {similarity:.2f}) ---")
            context_lines.append(text)
            context_lines.append("")
        
        return "\n".join(context_lines)
    
    def query(
        self,
        question: str,
        top_k: int = 8,
        use_mock: bool = None
    ) -> Dict:
        """
        Execute complete query: retrieve → generate → format.
        
        Args:
            question: User question
            top_k: Number of chunks to retrieve
            use_mock: Override use_real_llm for this query
        
        Returns:
            Complete response dict with answer, sources, metadata
        """
        use_mock = use_mock if use_mock is not None else not self.use_real_llm
        
        logger.info(f"Processing query: {question}")
        
        # Step 1: Retrieve
        retrieved_chunks = self.retriever.retrieve(question, top_k)
        logger.info(f"Retrieved {len(retrieved_chunks)} chunks")
        
        # Step 2: Prepare context
        context = self._format_context_for_llm(retrieved_chunks)
        
        # Step 3: Generate
        if use_mock or not self.llm_client:
            response_text = self._generate_with_mock(question, retrieved_chunks)
        else:
            response_text = self._generate_with_groq(question, context)
        
        # Step 4: Format response with sources
        sources = list(set(chunk.get("source", "unknown") for chunk in retrieved_chunks))
        
        return {
            "question": question,
            "answer": response_text,
            "sources": sources,
            "chunks_used": len(retrieved_chunks),
            "retrieval_scores": [
                {
                    "source": chunk.get("source", "unknown"),
                    "similarity": chunk.get("similarity", 0)
                }
                for chunk in retrieved_chunks
            ],
            "grounded": True,
            "mode": "mock" if use_mock else "groq",
        }
    
    def _generate_with_groq(self, question: str, context: str) -> str:
        """Generate response using Groq LLM."""
        if not self.llm_client:
            logger.warning("Groq client not available, falling back to mock")
            return self._generate_with_mock(question, [])
        
        try:
            system_prompt = self._create_system_prompt()
            
            user_message = f"""Question: {question}

Here are the relevant documents:

{context}

Remember: ONLY answer using information from the documents above. 
If the documents don't contain relevant information, say so explicitly.
Always cite which documents you're drawing from."""
            
            logger.info("Calling Groq API...")
            
            message = self.llm_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.3,  # Lower temp for more grounded responses
                max_tokens=1000,
            )
            
            response_text = message.choices[0].message.content
            logger.info("✓ Groq response received")
            
            return response_text
        
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            return f"Error generating response: {str(e)}"
    
    def _generate_with_mock(self, question: str, chunks: List[Dict]) -> str:
        """Generate mock response (for development/testing)."""
        question_lower = question.lower()
        
        # Simple rule-based responses grounded in keywords
        if any(word in question_lower for word in ["workload", "homework", "hours"]):
            return (
                "Based on student reviews, introductory CS courses typically involve 8-12 hours "
                "of homework per week (source: rate_my_professors_cs_001.txt). Students emphasize "
                "that starting assignments early is crucial for managing the workload. The work "
                "consists primarily of coding assignments and projects."
            )
        
        elif any(word in question_lower for word in ["teaching", "style", "clear", "explain"]):
            return (
                "According to student reviews, effective teaching includes: clear lectures with "
                "real-world examples (source: rate_my_professors_cs_001.txt), interactive learning, "
                "accessible office hours (source: reddit_r_professors_001.txt), and using visual aids. "
                "Students highly value professors who make abstract concepts understandable through "
                "concrete examples."
            )
        
        elif any(word in question_lower for word in ["exam", "grade", "fair", "difficulty"]):
            return (
                "Student reviews mention varied exam experiences (source: rate_my_professors_math_001.txt). "
                "Common concerns include unexpected exam problems not covered in class, harsh grading curves, "
                "and inconsistent partial credit policies. However, fair professors clearly communicate "
                "exam expectations and provide constructive feedback."
            )
        
        elif any(word in question_lower for word in ["access", "office hours", "approachable", "reach"]):
            return (
                "Student reviews highly value professor accessibility (source: rate_my_professors_cs_001.txt, "
                "reddit_r_learnprogramming_001.txt). Positive mentions include: regular office hours, "
                "prompt email responses, one-on-one explanation willingness, and approachable demeanor. "
                "Less accessible professors maintain formal distance and limited availability."
            )
        
        else:
            # For other questions, admit lack of information
            return (
                "I don't have specific information about that topic in the available student reviews. "
                "The Unofficial Guide covers: workload and homework expectations, teaching styles and clarity, "
                "exam difficulty and grading fairness, professor accessibility, and factors that make courses "
                "review-worthy. Please rephrase your question to focus on one of these topics."
            )


def ask(question: str, use_mock: bool = True) -> Dict:
    """
    Convenience function for simple queries.
    
    Args:
        question: User question
        use_mock: Use mock LLM (default True for no API key required)
    
    Returns:
        Response dict
    """
    orchestrator = QueryOrchestrator(use_real_llm=not use_mock)
    return orchestrator.query(question, use_mock=use_mock)


if __name__ == "__main__":
    # Example usage
    orchestrator = QueryOrchestrator(use_real_llm=False)
    
    test_questions = [
        "What do students say about workload in intro CS courses?",
        "Which teaching styles help students learn best?",
        "How do students rate approachable professors?",
    ]
    
    print("\n" + "="*80)
    print("QUERY ORCHESTRATOR TEST")
    print("="*80 + "\n")
    
    for question in test_questions:
        result = orchestrator.query(question)
        
        print(f"Q: {result['question']}")
        print(f"A: {result['answer'][:300]}...")
        print(f"Sources: {', '.join(result['sources'])}")
        print()
