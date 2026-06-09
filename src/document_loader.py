"""
Document Loader: Ingests documents from files and URLs.

Supports:
- Plain text files (.txt)
- Manual downloads from websites
- Folder-based loading
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Optional
import requests
from bs4 import BeautifulSoup
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Document:
    """Represents a single document with metadata."""
    
    def __init__(
        self,
        text: str,
        source: str,
        source_type: str = "local_file",
        url: Optional[str] = None,
        metadata: Optional[Dict] = None
    ):
        self.text = text
        self.source = source  # e.g., "rate_my_professors_cs_001.txt"
        self.source_type = source_type  # "local_file", "url", "forum_thread", etc.
        self.url = url
        self.metadata = metadata or {}
        self.length = len(text.split())  # word count
    
    def __repr__(self):
        return f"Document(source={self.source}, length={self.length} words, type={self.source_type})"


class DocumentLoader:
    """Loads documents from various sources."""
    
    def __init__(self, documents_dir: str = "documents"):
        self.documents_dir = Path(documents_dir)
        self.documents_dir.mkdir(exist_ok=True)
        self.documents: List[Document] = []
    
    def load_from_directory(self) -> List[Document]:
        """Load all .txt files from documents/ folder."""
        documents = []
        
        txt_files = list(self.documents_dir.glob("*.txt"))
        logger.info(f"Found {len(txt_files)} .txt files in {self.documents_dir}")
        
        for file_path in sorted(txt_files):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    text = f.read().strip()
                
                if text:  # Only add non-empty documents
                    doc = Document(
                        text=text,
                        source=file_path.name,
                        source_type="local_file",
                        metadata={"file_path": str(file_path)}
                    )
                    documents.append(doc)
                    logger.info(f"Loaded {file_path.name}: {doc.length} words")
                else:
                    logger.warning(f"Skipped empty file: {file_path.name}")
            
            except Exception as e:
                logger.error(f"Error loading {file_path.name}: {e}")
        
        self.documents.extend(documents)
        return documents
    
    def load_from_url(self, url: str, source_name: str) -> Optional[Document]:
        """Fetch and load text from a URL."""
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Extract text from HTML
            soup = BeautifulSoup(response.content, "html.parser")
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            text = soup.get_text()
            
            # Basic cleanup
            lines = [line.strip() for line in text.split("\n") if line.strip()]
            text = "\n".join(lines)
            
            if text:
                doc = Document(
                    text=text,
                    source=source_name,
                    source_type="url",
                    url=url,
                    metadata={"original_url": url}
                )
                self.documents.append(doc)
                logger.info(f"Loaded from URL {source_name}: {doc.length} words")
                return doc
        
        except Exception as e:
            logger.error(f"Error loading from {url}: {e}")
        
        return None
    
    def create_sample_documents(self):
        """Create sample documents for testing (since live scraping is tricky)."""
        samples = [
            {
                "name": "rate_my_professors_cs_001.txt",
                "text": """Professor Sarah Chen - Computer Science 101
Rating: 4.5/5 - Clarity: 5 - Difficulty: 4 - Helpfulness: 5
Source: Rate My Professors

Dr. Chen is an exceptional professor who makes computer science concepts incredibly clear. 
Her lectures are well-structured and she uses plenty of real-world examples to illustrate 
abstract ideas. Expect 8-12 hours of homework per week, mostly coding assignments and reading. 
The assignments are challenging but doable if you start early. Office hours are always open 
and she's responsive to emails. Exams are fair and reflect what was taught in class. Her 
grading is generous with partial credit. I'd recommend taking her class—you'll actually 
understand the material instead of just memorizing it. The class size is about 60 students 
but she still manages to be personable.
"""
            },
            {
                "name": "reddit_r_professors_001.txt",
                "text": """Reddit Discussion: r/professors - Teaching CS with Limited Resources
Posted by: comp_sci_ta | 47 upvotes

I just finished my first semester teaching CS to intro students and it was tough. Here's what 
I learned: 1) Don't assume students have touched a computer before - some literally haven't. 
2) Pair programming in labs helps shy students engage. 3) Real projects beat textbook exercises 
every time. 4) Office hours are where you actually fix misconceptions. I had 15 students 
regularly, not counting ones who showed up once. The grading workload is insane - 100+ 
submissions per assignment. Solution: I built a rubric template that speeds things up. 
Also, students appreciate when you explain why concepts matter. Telling them "you'll need 
this for interviews" motivates way more than "it's on the exam." Anyone else struggle with 
time management in their first year?

Comments:
- "Office hours changed my teaching. I now hold 4 hours per week." (23 likes)
- "Real projects absolutely. My pass rate went up 20% when I switched from problem sets." (18 likes)
"""
            },
            {
                "name": "rate_my_professors_math_001.txt",
                "text": """Professor James Rodriguez - Calculus II
Rating: 3.8/5 - Clarity: 3 - Difficulty: 5 - Helpfulness: 4
Source: Rate My Professors

Dr. Rodriguez is a tough but fair instructor. His lectures move quickly and assume you 
know single-variable calculus inside and out. If you're struggling, go to office hours 
early—he becomes much warmer one-on-one than in class. The exams are hard and often 
include problems he's never shown in class, so you need to understand the fundamentals, 
not just the procedures. Homework is brutal (2-3 hours per assignment, 2x weekly). Grading 
is harsh—he takes points off for every small mistake. That said, this class actually prepared 
me for upper-level math better than any other. If you want an easy A, take someone else. 
If you want to actually learn Calculus, he's your guy. Study group saved my grade. Definitely 
form one early.
"""
            },
            {
                "name": "reddit_r_learnprogramming_001.txt",
                "text": """Reddit: r/learnprogramming - Best Professors for Learning Python
Posted by: aspiring_dev | 2.1k upvotes

Thread: "I want to learn programming. Should I look for a professor or use online courses?"

Top comment by: coding_mentor (1.2k upvotes):
"It depends on your learning style. I went the professor route and here's what I found:
- Best professors explain the 'why', not just the 'how'
- They force you to write code instead of copy-pasting tutorials
- They give real feedback on your code (not just 'correct' or 'wrong')
- They're accessible—you can ask random questions in office hours

Bad professors just read slides and don't engage. I had one who said 'let me Google this' 
during office hours. Don't take a class with someone who isn't passionate about teaching.

Key warning: Big intro classes (200+ students) are hit or miss. You need a professor who 
actually uses active learning, not lectures to a dark auditorium.

Specific recommendation: Look for professors who maintain GitHub repos, write their own 
assignments, and respond quickly to emails. Those are signs they actually care about teaching."

Replies:
- "This. I learned more from a bad online course than a bad professor." (850 likes)
- "How do you find which professors are good before registering?" 
  - Response: "RateMyProfessors has reviews. Also ask in your university subreddit." (420 likes)
"""
            },
            {
                "name": "course_evaluations_001.txt",
                "text": """Anonymous Course Evaluation - Introduction to Algorithms
Professor: Dr. Michael Park
Semester: Fall 2024
Response Rate: 62% (44/71 students)

Q: How clearly did the instructor communicate course content?
Average: 4.1/5
Comments: "Very clear lectures with good examples" (15 mentions)
          "Sometimes moved too fast" (8 mentions)
          "Used whiteboard well for complex topics" (12 mentions)

Q: How much did you learn in this course?
Average: 4.4/5
Comments: "Definitely prepared for technical interviews" (18 mentions)
          "Challenging but fair" (10 mentions)
          "Would have liked more implementation details" (6 mentions)

Q: How fairly were you graded?
Average: 3.9/5
Comments: "Grading rubric could be clearer" (12 mentions)
          "Generous with partial credit" (8 mentions)
          "Some assignment expectations were vague" (5 mentions)

Q: How would you rate this professor's accessibility?
Average: 4.2/5
Comments: "Office hours very helpful, open twice weekly" (14 mentions)
          "Responds to emails within 24 hours" (9 mentions)
          "Could offer more one-on-one help" (3 mentions)

Overall Rating: 4.2/5
Would Recommend: 91% (40/44 responses)
"""
            }
        ]
        
        # Save sample documents
        for sample in samples:
            file_path = self.documents_dir / sample["name"]
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(sample["text"])
            logger.info(f"Created sample document: {sample['name']}")
        
        # Load them
        return self.load_from_directory()
    
    def get_stats(self) -> Dict:
        """Get statistics about loaded documents."""
        return {
            "total_documents": len(self.documents),
            "total_words": sum(doc.length for doc in self.documents),
            "avg_words_per_doc": (
                sum(doc.length for doc in self.documents) / len(self.documents)
                if self.documents else 0
            ),
            "documents": [
                {
                    "source": doc.source,
                    "words": doc.length,
                    "type": doc.source_type
                }
                for doc in self.documents
            ]
        }
