"""
CLI utilities for conversation history.
"""
import os
import time
import logging
import argparse
from typing import Optional

from ..core.manager import ConversationHistoryManager
from ..exporters.exporter import ConversationExporter

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def export_conversation_history(student_id: str, 
                               conversation_dir: str = "conversation_history/data", 
                               export_format: str = "text"):
    """
    Export conversation history for a student.
    
    Args:
        student_id: ID of the student
        conversation_dir: Directory containing conversation history
        export_format: Format to export (text, json, csv)
    """
    manager = ConversationHistoryManager(conversation_dir)
    exporter = ConversationExporter()
    
    # Get all conversations for the student
    conversation_files = manager.get_conversations_for_student(student_id)
    
    if not conversation_files:
        print(f"No conversation history found for student {student_id}")
        return
    
    print(f"Found {len(conversation_files)} conversation(s) for student {student_id}")
    
    # Create export directory
    export_dir = os.path.join(conversation_dir, "exports", student_id)
    os.makedirs(export_dir, exist_ok=True)
    
    # Export each conversation
    for i, file_path in enumerate(conversation_files):
        try:
            # Load the conversation
            conversation = manager.load_conversation(file_path)
            
            # Generate export filename
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"conversation_{i+1}_{timestamp}"
            
            # Export based on format
            if export_format == "json":
                export_path = os.path.join(export_dir, f"{filename}.json")
                exporter.export_to_json(conversation, export_path)
            elif export_format == "csv":
                export_path = os.path.join(export_dir, f"{filename}.csv")
                exporter.export_to_csv(conversation, export_path)
            else:  # Default to text
                export_path = os.path.join(export_dir, f"{filename}.txt")
                exporter.export_to_text(conversation, export_path)
            
            print(f"Exported conversation {i+1} to {export_path}")
        except Exception as e:
            print(f"Failed to export conversation {i+1}: {e}")
    
    print(f"\nExport complete. Files are available in {export_dir}")


def main():
    """Main function for the CLI."""
    parser = argparse.ArgumentParser(description="Conversation History CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Export command
    export_parser = subparsers.add_parser("export", help="Export conversation history")
    export_parser.add_argument("student_id", help="ID of the student")
    export_parser.add_argument("--dir", default="conversation_history/data", 
                              help="Directory containing conversation history")
    export_parser.add_argument("--format", choices=["text", "json", "csv"], default="text",
                              help="Format to export (text, json, csv)")
    
    # Parse arguments
    args = parser.parse_args()
    
    # Run the appropriate command
    if args.command == "export":
        export_conversation_history(args.student_id, args.dir, args.format)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
