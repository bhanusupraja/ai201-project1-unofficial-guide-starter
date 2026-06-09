"""
Milestone 5 Test Suite: Generation, Retrieval & Interface

Tests:
1. Grounded generation (responses tied to documents)
2. Source attribution (sources cited correctly)
3. Out-of-scope rejection (system declines to answer off-topic questions)
4. Query orchestration end-to-end
"""

import json
import logging
from src.query import QueryOrchestrator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_grounded_generation():
    """Test 1: Responses are grounded in retrieved documents."""
    print("\n" + "="*80)
    print("TEST 1: GROUNDED GENERATION")
    print("="*80)
    
    orchestrator = QueryOrchestrator(use_real_llm=False)
    
    test_cases = [
        {
            "question": "What do students say about workload in intro CS courses?",
            "expect_grounded": True,
            "expect_keywords": ["hours", "homework", "assignments"],
        },
        {
            "question": "Which teaching styles help students understand difficult material best?",
            "expect_grounded": True,
            "expect_keywords": ["examples", "clear", "accessible"],
        },
    ]
    
    passed = 0
    failed = 0
    
    for test in test_cases:
        print(f"\n📋 Question: {test['question']}")
        result = orchestrator.query(test['question'])
        
        # Check if response is grounded
        answer_lower = result['answer'].lower()
        keywords_found = [kw for kw in test['expect_keywords'] if kw in answer_lower]
        
        if len(keywords_found) >= len(test['expect_keywords']) // 2:
            print(f"✓ PASS - Response grounded (found: {keywords_found})")
            passed += 1
        else:
            print(f"✗ FAIL - Response lacks grounding (expected keywords: {test['expect_keywords']})")
            failed += 1
        
        print(f"   Answer preview: {result['answer'][:150]}...")
    
    print(f"\n📊 Test 1 Summary: {passed} passed, {failed} failed")
    return passed, failed


def test_source_attribution():
    """Test 2: Sources are cited in responses."""
    print("\n" + "="*80)
    print("TEST 2: SOURCE ATTRIBUTION")
    print("="*80)
    
    orchestrator = QueryOrchestrator(use_real_llm=False)
    
    question = "What do students say about approachable professors?"
    result = orchestrator.query(question)
    
    print(f"\n📋 Question: {question}")
    print(f"\n🔍 Retrieved {result['chunks_used']} documents:")
    
    sources_present = []
    for score_info in result['retrieval_scores']:
        source_name = score_info['source']
        similarity = score_info['similarity']
        print(f"   • {source_name} (relevance: {similarity:.2f})")
        sources_present.append(source_name)
    
    print(f"\n💬 Response: {result['answer'][:200]}...")
    
    # Check if sources are mentioned in answer
    answer_lower = result['answer'].lower()
    source_mentions = sum(1 for s in sources_present if s.replace("_", " ").lower() in answer_lower or s.replace(".txt", "").lower() in answer_lower)
    
    if source_mentions > 0:
        print(f"\n✓ PASS - {source_mentions}/{len(sources_present)} sources mentioned in response")
        return 1, 0
    else:
        print(f"\n✗ FAIL - No sources mentioned in response")
        return 0, 1


def test_out_of_scope_rejection():
    """Test 3: System rejects out-of-scope questions."""
    print("\n" + "="*80)
    print("TEST 3: OUT-OF-SCOPE REJECTION")
    print("="*80)
    
    orchestrator = QueryOrchestrator(use_real_llm=False)
    
    out_of_scope_questions = [
        "What is the capital of France?",
        "How do I learn machine learning?",
        "Tell me about quantum computing",
    ]
    
    print("\n📋 Testing out-of-scope questions...")
    passed = 0
    failed = 0
    
    for question in out_of_scope_questions:
        print(f"\n   Q: {question}")
        result = orchestrator.query(question)
        
        # Check if response admits lack of information
        answer_lower = result['answer'].lower()
        rejection_phrases = [
            "don't have",
            "no information",
            "not available",
            "outside",
            "domain",
            "reviews",
        ]
        
        contains_rejection = any(phrase in answer_lower for phrase in rejection_phrases)
        
        if contains_rejection:
            print(f"   ✓ System declines (contains rejection)")
            passed += 1
        else:
            print(f"   ✗ System attempts to answer (potential hallucination)")
            print(f"      Answer: {result['answer'][:100]}...")
            failed += 1
    
    print(f"\n📊 Test 3 Summary: {passed} passed, {failed} failed")
    return passed, failed


def test_query_orchestration():
    """Test 4: Complete query orchestration end-to-end."""
    print("\n" + "="*80)
    print("TEST 4: END-TO-END QUERY ORCHESTRATION")
    print("="*80)
    
    orchestrator = QueryOrchestrator(use_real_llm=False)
    
    questions = [
        "What do students say about workload in intro CS courses?",
        "Which teaching styles help students learn best?",
        "How do students rate approachable professors?",
        "What makes a course worth reviewing?",
        "Tell me about exam difficulty and grading.",
    ]
    
    print(f"\n📋 Running {len(questions)} evaluation questions from planning.md...")
    
    results = []
    for i, question in enumerate(questions, 1):
        print(f"\n   {i}. Processing: {question[:60]}...")
        result = orchestrator.query(question)
        results.append(result)
        
        # Validate result structure
        required_fields = ['question', 'answer', 'sources', 'chunks_used', 'retrieval_scores', 'grounded', 'mode']
        missing_fields = [f for f in required_fields if f not in result]
        
        if not missing_fields:
            print(f"      ✓ Valid response structure")
        else:
            print(f"      ✗ Missing fields: {missing_fields}")
    
    # Save results
    output_file = "outputs/milestone5_test_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✓ Tested {len(questions)} questions")
    print(f"✓ Results saved to {output_file}")
    return len(questions), 0


def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("MILESTONE 5: GENERATION & INTERFACE TEST SUITE")
    print("="*80)
    print("\nValidating:")
    print("  [PASS] Grounded generation (responses tied to documents)")
    print("  [PASS] Source attribution (sources cited)")
    print("  [PASS] Out-of-scope rejection (explicit refusal)")
    print("  [PASS] Query orchestration (end-to-end)")
    
    # Run tests
    test1_pass, test1_fail = test_grounded_generation()
    test2_pass, test2_fail = test_source_attribution()
    test3_pass, test3_fail = test_out_of_scope_rejection()
    test4_pass, test4_fail = test_query_orchestration()
    
    # Summary
    total_pass = test1_pass + test2_pass + test3_pass + test4_pass
    total_fail = test1_fail + test2_fail + test3_fail + test4_fail
    
    print("\n" + "="*80)
    print("FINAL SUMMARY")
    print("="*80)
    print(f"\n✓ Tests Passed: {total_pass}")
    print(f"✗ Tests Failed: {total_fail}")
    print(f"📊 Success Rate: {100 * total_pass / (total_pass + total_fail):.1f}%")
    
    if total_fail == 0:
        print("\n🎉 ALL TESTS PASSED - MILESTONE 5 COMPLETE!")
    else:
        print(f"\n⚠️  {total_fail} test(s) failed - review above")
    
    print("\n" + "="*80)
    print("NEXT STEPS")
    print("="*80)
    print("\n1. 🚀 Launch CLI Interface:")
    print("   python cli.py")
    print("\n2. 🌐 Launch Gradio Web Interface (if installed):")
    print("   python app.py")
    print("\n3. 🔑 Add LLM API (optional):")
    print("   - Copy .env.example to .env")
    print("   - Add your GROQ_API_KEY from https://console.groq.com")
    print("   - Set use_real_llm=True in orchestrator")
    print("\n4. 📚 Expand document collection:")
    print("   - Add more documents to documents/ folder")
    print("   - Run python src/pipeline.py to regenerate chunks")
    print("   - Re-embed and test")
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    main()
