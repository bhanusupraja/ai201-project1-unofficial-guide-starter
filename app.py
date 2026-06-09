"""
Gradio Web Interface for the Unofficial Guide to Course and Professor Reviews.

Run with: python app.py
Access at: http://localhost:7860
"""

import gradio as gr
import logging
from src.query import QueryOrchestrator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize orchestrator
orchestrator = QueryOrchestrator(use_real_llm=False)  # Set to True if GROQ_API_KEY in .env

def handle_query(question: str, use_groq: bool = False) -> tuple:
    """Handle user query and return formatted response."""
    if not question.strip():
        return ("Please enter a question", "")
    
    try:
        # Use Groq if checkbox is checked AND API key is available
        use_mock = not use_groq
        result = orchestrator.query(question, use_mock=use_mock)
        
        # Format answer
        answer = result["answer"]
        
        # Format sources
        sources_list = []
        sources_list.append(f"📊 Retrieved {result['chunks_used']} relevant document(s):\n")
        for score_info in result['retrieval_scores']:
            sources_list.append(
                f"• {score_info['source']} (relevance: {score_info['similarity']:.2f})"
            )
        sources_text = "\n".join(sources_list)
        
        return (answer, sources_text)
    
    except Exception as e:
        logger.error(f"Query error: {e}")
        return (f"Error processing query: {str(e)}", "")


# Build Gradio interface
with gr.Blocks(title="Unofficial Guide - Q&A Interface") as demo:
    gr.Markdown("""
    # 📚 Unofficial Guide: Course and Professor Reviews
    
    Ask questions about course workload, teaching styles, professor accessibility, grading practices, 
    and other factors that make courses worth reviewing.
    
    **Key Feature**: Responses are grounded in actual student reviews — if information isn't available, 
    the system will say so rather than making something up.
    """)
    
    # Input section
    with gr.Group(label="Ask a Question"):
        question_input = gr.Textbox(
            label="Your Question",
            placeholder="e.g., What do students say about workload in intro CS courses?",
            lines=2,
        )
        
        use_groq_checkbox = gr.Checkbox(
            label="Use Groq LLM (requires GROQ_API_KEY in .env; uncheck for mock mode)",
            value=False,
        )
        
        submit_btn = gr.Button("Ask", size="lg", variant="primary")
    
    # Output section
    gr.Markdown("---")
    
    with gr.Group(label="Response"):
        answer_output = gr.Textbox(
            label="Answer",
            lines=8,
            interactive=False,
        )
        
        sources_output = gr.Textbox(
            label="Retrieved From",
            lines=4,
            interactive=False,
        )
    
    # Info section
    gr.Markdown("""
    ---
    
    ### 💡 Tips
    - Questions should focus on: **workload**, **teaching style**, **exam/grading**, 
      **professor accessibility**, or **review-worthy factors**
    - Try asking: "What makes a course worth reviewing?" or "How important is professor accessibility?"
    - The system will decline to answer questions outside the scope of available reviews
    
    ### ✅ Grounding Guarantee
    - ✓ Responses cite which documents they come from
    - ✓ Answers drawn exclusively from student reviews (no general knowledge)
    - ✓ Requests for unavailable information are rejected explicitly
    """)
    
    # Connect button and input
    submit_btn.click(
        handle_query,
        inputs=[question_input, use_groq_checkbox],
        outputs=[answer_output, sources_output],
    )
    
    # Also submit on Enter key
    question_input.submit(
        handle_query,
        inputs=[question_input, use_groq_checkbox],
        outputs=[answer_output, sources_output],
    )
    
    # Example questions
    gr.Examples(
        examples=[
            ["What do students say about workload in intro CS courses?"],
            ["Which teaching styles help students learn best?"],
            ["How do students rate approachable professors?"],
            ["What factors make a course worth reviewing?"],
        ],
        inputs=question_input,
        label="Example Questions",
    )


if __name__ == "__main__":
    logger.info("🚀 Starting Gradio interface at http://localhost:7860")
    demo.launch(share=False)
