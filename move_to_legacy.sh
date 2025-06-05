#!/bin/bash

# Script to move original conversation history files to legacy folders

# Exit on error
set -e

echo "Moving original conversation history files to legacy folders..."

# Create legacy directories
mkdir -p legacy/conversation_history
mkdir -p legacy/assessment_conversations
mkdir -p legacy/kg_quizzing/scripts/assessment_conversations

# Move conversation history files
if [ -d "conversation_history" ]; then
    echo "Moving conversation_history to legacy folder..."
    cp -r conversation_history/* legacy/conversation_history/
    echo "Conversation history files copied to legacy folder."
fi

# Move assessment conversations files
if [ -d "assessment_conversations" ]; then
    echo "Moving assessment_conversations to legacy folder..."
    cp -r assessment_conversations/* legacy/assessment_conversations/
    echo "Assessment conversations files copied to legacy folder."
fi

# Move KG quizzing assessment conversations files
if [ -d "kg_quizzing/scripts/assessment_conversations" ]; then
    echo "Moving kg_quizzing/scripts/assessment_conversations to legacy folder..."
    cp -r kg_quizzing/scripts/assessment_conversations/* legacy/kg_quizzing/scripts/assessment_conversations/
    echo "KG quizzing assessment conversations files copied to legacy folder."
fi

echo "All files have been copied to legacy folders."
echo "You can now safely remove the original files if the database import was successful."
echo "To remove original files, run:"
echo "  rm -rf conversation_history"
echo "  rm -rf assessment_conversations"
echo "  rm -rf kg_quizzing/scripts/assessment_conversations"
