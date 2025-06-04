"""
CLI entrypoint for The Grey Tutor adaptive quizzing system.
Handles argument parsing, session startup, and user interaction loop.
"""
import argparse
import os
from quiz_orchestrator import QuizOrchestrator

def main():
    parser = argparse.ArgumentParser(
        description="The Grey Tutor: A Journey Through Middle-earth's Knowledge"
    )
    parser.add_argument("--student", type=str, required=True, help="Student ID")
    parser.add_argument("--name", type=str, required=False, help="Student name")
    parser.add_argument("--strategy", type=str, default="adaptive", choices=["adaptive", "depth_first", "breadth_first", "spiral"], help="Question selection strategy")
    parser.add_argument("--tier", type=str, default=None, choices=["basic", "intermediate", "advanced"], 
                      help="Question tier (basic: concise questions, intermediate: moderate detail, advanced: rich narrative)")
    parser.add_argument("--llm", action="store_true", help="Enable LLM-based question generation and assessment")
    parser.add_argument("--conversation-dir", type=str, default="conversation_history", help="Directory for conversation history")
    parser.add_argument("--fussiness", type=int, default=3, help="Gandalf's fussiness (1=very lenient, 10=very strict, default=3)")
    parser.add_argument("--theme", type=str, default=None, help="Broad theme or topic for the quiz session (e.g., Elves, Rings, Battles)")
    args = parser.parse_args()

    orchestrator = QuizOrchestrator(
        student_id=args.student,
        student_name=args.name,
        strategy=args.strategy,
        use_llm=args.llm,
        conversation_dir=args.conversation_dir,
        tier=args.tier,
        fussiness=args.fussiness,
        theme=args.theme
    )

    student_name = args.name or input("And by what name shall I address you, traveler of Middle-earth? ")
    print("\nPreparing the ancient scrolls of wisdom... Gandalf the Grey shall be your guide.")

    orchestrator.start_session(args.student, student_name, args.strategy, theme=args.theme)
    orchestrator.run_interactive_session()

if __name__ == "__main__":
    main()
