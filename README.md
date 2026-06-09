# The Unofficial Guide — Project 1

> **How to use this template:**
> Complete each section *after* you've built and tested the corresponding part of your system.
> Do not write placeholder text — if a section isn't done yet, leave it blank and come back.
> Every section below is required for submission. One-liners will not receive full credit.

---

## Domain

**Course and Professor Reviews: Crowdsourced Insights on Teaching Quality and Course Structure**

This system aggregates student experiences with specific professors and courses to help future students make informed enrollment decisions. While official university course catalogs list requirements and credits, they rarely capture teaching style, workload expectations, grading fairness, or real student outcomes. This knowledge is scattered across Rate My Professors, subreddit discussions, forum threads, and student reviews—making it difficult for students to find comprehensive, recent perspectives without manually visiting multiple platforms. Our Unofficial Guide brings this wisdom together in one searchable, AI-powered interface.

---

## Document Sources

<!-- List every source you collected documents from.
     Be specific: include URLs, subreddit names, forum thread titles, or file names.
     Aim for variety — sources that together cover different subtopics or perspectives. -->

| # | Source | Type | URL or file path |
|---|--------|------|-----------------|
| 1 | Rate My Professors - Computer Science | Web (Reviews) | https://www.ratemyprofessors.com/search/teachers?query=computer+science |
| 2 | Reddit r/professors | Web (Forum/Discussion) | https://www.reddit.com/r/professors/ |
| 3 | Reddit r/learnprogramming - Course Recommendations | Web (Forum/Discussion) | https://www.reddit.com/r/learnprogramming/ |
| 4 | Course Evaluations Database | Web (Aggregated Reviews) | https://www.courseevaluations.org/ |
| 5 | Rate My Professors - Mathematics | Web (Reviews) | https://www.ratemyprofessors.com/search/teachers?query=mathematics |
| 6 | Reddit r/csMajors - Course/Professor Threads | Web (Forum/Discussion) | https://www.reddit.com/r/csMajors/ |
| 7 | Rate My Professors - Business/Economics | Web (Reviews) | https://www.ratemyprofessors.com/search/teachers?query=business |
| 8 | Glassdoor University Teaching Quality Reviews | Web (Alumni Reviews) | https://www.glassdoor.com/Reviews/Companies/Education-c1_c100.htm |
| 9 | Reddit r/university - General Course/Professor Posts | Web (Forum/Discussion) | https://www.reddit.com/r/university/ |
| 10 | Rate My Professors - Biology/STEM | Web (Reviews) | https://www.ratemyprofessors.com/search/teachers?query=biology |
| 11 | Stack Overflow - Learning Resource Recommendations | Web (Community Forum) | https://stackoverflow.com/questions/tagged/learning-resources |
| 12 | The Student Room - Academic Discussion Forum | Web (Forum/Discussion) | https://www.thestudentroom.co.uk/ |

---

## Chunking Strategy

<!-- Describe your chunking approach with enough specificity that someone else could reproduce it.
     Include:
     - Chunk size (characters or tokens) and why that size fits your documents
     - Overlap size and why (or why not) you used overlap
     - Any preprocessing you did before chunking (e.g., stripping HTML, removing headers)
     - What your final chunk count was across all documents -->

**Chunk size:**

**Overlap:**

**Why these choices fit your documents:**

**Final chunk count:**

---

## Embedding Model

<!-- Name the embedding model you used and explain your choice.
     Then answer: if you were deploying this system for real users and cost wasn't a constraint,
     what tradeoffs would you weigh in choosing a different model?
     Consider: context length limits, multilingual support, accuracy on domain-specific text,
     latency, and local vs. API-hosted. -->

**Model used:**

**Production tradeoff reflection:**

---

## Grounded Generation

<!-- Explain how your system enforces grounding — how does it prevent the LLM from answering
     beyond the retrieved documents?
     Describe both your system prompt (what instruction you gave the model) and any structural
     choices (e.g., how you formatted the context, whether you filtered low-relevance chunks).
     Do not just say "I told it to use the documents" — show the actual instruction or explain
     the mechanism. -->

**System prompt grounding instruction:**

**How source attribution is surfaced in the response:**

---

## Evaluation Report

<!-- Run your 5 test questions from planning.md through your system and record the results.
     Be honest — a partially accurate or inaccurate result that you explain well is more
     valuable than a suspiciously perfect result. -->

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |
| 4 | | | | | |
| 5 | | | | | |

**Retrieval quality:** Relevant / Partially relevant / Off-target  
**Response accuracy:** Accurate / Partially accurate / Inaccurate

---

## Failure Case Analysis

<!-- Identify at least one question where retrieval or generation did not work as expected.
     Write a specific explanation of *why* it failed, tied to a part of the pipeline.

     "The answer was wrong" is not an explanation.

     "The relevant information was split across a chunk boundary, so retrieval returned
     only half the context — the model didn't have enough to answer correctly" is an explanation.

     "The embedding model treated the professor's nickname as out-of-vocabulary and returned
     results from an unrelated review" is an explanation. -->

**Question that failed:**

**What the system returned:**

**Root cause (tied to a specific pipeline stage):**

**What you would change to fix it:**

---

## Spec Reflection

<!-- Reflect on how planning.md shaped your implementation.
     Answer both questions with at least 2–3 sentences each. -->

**One way the spec helped you during implementation:**

**One way your implementation diverged from the spec, and why:**

---

## AI Usage

<!-- Describe at least 2 specific instances where you used an AI tool during this project.
     For each: what did you give the AI as input, what did it produce, and what did you
     change, override, or direct differently?

     "I used Claude to help me code" is not sufficient.
     "I gave Claude my Chunking Strategy section from planning.md and asked it to implement
     chunk_text(). It returned a function using a fixed character split. I overrode the
     chunk size from 500 to 200 because my documents are short reviews, not long guides." -->

**Instance 1**

- *What I gave the AI:*
- *What it produced:*
- *What I changed or overrode:*

**Instance 2**

- *What I gave the AI:*
- *What it produced:*
- *What I changed or overrode:*
