#!/bin/bash
# Script to move original conversation history and assessment files to a legacy folder

# Exit on error
set -e

echo "Moving original files to legacy folders..."

# Create legacy directories
mkdir -p legacy/conversation_history
mkdir -p legacy/assessment_conversations
mkdir -p legacy/question_cache
mkdir -p legacy/student_models

# Move conversation history files
echo "Moving conversation history files..."
if [ -d "conversation_history" ]; then
    cp -r conversation_history/* legacy/conversation_history/
    echo "Conversation history files moved to legacy/conversation_history/"
else
    echo "Conversation history directory not found, skipping"
fi

# Move assessment conversation files
echo "Moving assessment conversation files..."
if [ -d "assessment_conversations" ]; then
    cp -r assessment_conversations/* legacy/assessment_conversations/
    echo "Assessment conversation files moved to legacy/assessment_conversations/"
else
    echo "Assessment conversations directory not found, skipping"
fi

# Move question cache files
echo "Moving question cache files..."
if [ -d "question_cache" ]; then
    cp -r question_cache/* legacy/question_cache/
    echo "Question cache files moved to legacy/question_cache/"
else
    echo "Question cache directory not found, skipping"
fi

# Move student model files
echo "Moving student model files..."
if [ -d "student_models" ]; then
    cp -r student_models/* legacy/student_models/
    echo "Student model files moved to legacy/student_models/"
else
    echo "Student models directory not found, skipping"
fi

# Move KG quizzing assessment conversations
echo "Moving KG quizzing assessment conversations..."
if [ -d "kg_quizzing/scripts/assessment_conversations" ]; then
    mkdir -p legacy/kg_quizzing/scripts/assessment_conversations
    cp -r kg_quizzing/scripts/assessment_conversations/* legacy/kg_quizzing/scripts/assessment_conversations/
    echo "KG quizzing assessment conversations moved to legacy/kg_quizzing/scripts/assessment_conversations/"
else
    echo "KG quizzing assessment conversations directory not found, skipping"
fi

# Move KG quizzing conversation history
echo "Moving KG quizzing conversation history..."
if [ -d "kg_quizzing/scripts/conversation_history" ]; then
    mkdir -p legacy/kg_quizzing/scripts/conversation_history
    cp -r kg_quizzing/scripts/conversation_history/* legacy/kg_quizzing/scripts/conversation_history/
    echo "KG quizzing conversation history moved to legacy/kg_quizzing/scripts/conversation_history/"
else
    echo "KG quizzing conversation history directory not found, skipping"
fi

echo "All files have been moved to legacy folders."
echo "Original files are still in place. You can safely delete them after verifying the database is working correctly."
echo "To delete original files, run:"
echo "  rm -rf conversation_history assessment_conversations question_cache student_models kg_quizzing/scripts/assessment_conversations kg_quizzing/scripts/conversation_history"
