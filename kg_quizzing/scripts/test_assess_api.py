import requests
import os
import pytest
from kg_quizzing.scripts.conversation_history import ConversationHistoryManager, ConversationExporter

BASE = "http://localhost:8000"

@pytest.fixture(scope="module")
def history_manager():
    return ConversationHistoryManager("assessment_conversations")

@pytest.fixture(scope="function")
def test_question():
    return {
        "question": "What is the name of Frodo's sword?",
        "text": "What is the name of Frodo's sword?",
        "type": "factual",
        "difficulty": 2,
        "answer": "Sting",
        "correct_answer": "Sting"
    }

def export_and_check(history_manager, keyword, answer):
    files = history_manager.get_conversations_for_student("test_user")
    assert files, "No conversation files found for test_user!"
    latest_json = files[0]
    latest_txt = latest_json.replace(".json", ".txt")
    conversation = history_manager.load_conversation(latest_json)
    ConversationExporter.export_to_text(conversation, latest_txt)
    assert os.path.exists(latest_txt), f"Text export file not found: {latest_txt}"
    with open(latest_txt, "r", encoding="utf-8") as f:
        exported_content = f.read()
    assert "What is the name of Frodo's sword?" in exported_content
    assert keyword in exported_content
    assert answer in exported_content


def test_assess_correct_answer(history_manager, test_question):
    resp = requests.post(f"{BASE}/assess", json={
        "question": test_question,
        "answer": "Sting",
        "user_id": "test_user"
    })
    assert resp.status_code == 200, f"Failed to assess answer: {resp.text}"
    assessment = resp.json()
    assert assessment["correct"] is True
    assert assessment["feedback"] is not None
    export_and_check(history_manager, "Sting", "Sting")

def test_assess_incorrect_answer(history_manager, test_question):
    resp = requests.post(f"{BASE}/assess", json={
        "question": test_question,
        "answer": "Glamdring",
        "user_id": "test_user"
    })
    assert resp.status_code == 200, f"Failed to assess answer: {resp.text}"
    assessment = resp.json()
    assert assessment["correct"] is False
    assert assessment["feedback"] is not None
    export_and_check(history_manager, "Glamdring", "Glamdring")

def test_assess_custom_conversation_id(history_manager, test_question):
    resp = requests.post(f"{BASE}/assess", json={
        "question": test_question,
        "answer": "Orcrist",
        "user_id": "test_user",
        "conversation_id": "custom_conv_123"
    })
    assert resp.status_code == 200, f"Failed to assess answer: {resp.text}"
    assessment = resp.json()
    assert assessment["conversation_id"] == "custom_conv_123"
    export_and_check(history_manager, "Orcrist", "Orcrist")
