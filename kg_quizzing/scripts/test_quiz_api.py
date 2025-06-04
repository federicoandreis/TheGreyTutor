import requests

BASE = "http://localhost:8000"

# 1. Start a session with all parameters
session_params = {
    "student_id": "test123",
    "student_name": "Frodo Baggins",
    "strategy": "spiral",
    "tier": "advanced",
    "use_llm": True,
    "conversation_dir": "test_convo_dir",
    "fussiness": 7,
    "theme": "Elves"
}
resp = requests.post(f"{BASE}/session", json=session_params)
assert resp.status_code == 200, f"Failed to start session: {resp.text}"
session = resp.json()
print("Session started:", session)

# Assert all parameters are reflected in the response
for k in ["student_id", "student_name", "strategy", "tier", "use_llm", "fussiness", "theme", "conversation_dir"]:
    assert session.get(k) == session_params.get(k), f"Mismatch for {k}: expected {session_params.get(k)}, got {session.get(k)}"

# 1b. Start a session with minimal parameters (edge case)
minimal_params = {
    "student_id": "test_minimal",
    "student_name": "Samwise"
}
resp = requests.post(f"{BASE}/session", json=minimal_params)
assert resp.status_code == 200, f"Failed to start minimal session: {resp.text}"
minimal_session = resp.json()
print("Minimal session started:", minimal_session)
assert minimal_session["student_id"] == minimal_params["student_id"]
assert minimal_session["student_name"] == minimal_params["student_name"]

# 1c. Start a session with use_llm False, fussiness edge, and custom theme
custom_params = {
    "student_id": "test_no_llm",
    "student_name": "Gimli",
    "use_llm": False,
    "fussiness": 1,
    "theme": "Dwarves"
}
resp = requests.post(f"{BASE}/session", json=custom_params)
assert resp.status_code == 200, f"Failed to start custom session: {resp.text}"
custom_session = resp.json()
print("Custom session started:", custom_session)
assert custom_session["use_llm"] == False
assert custom_session["fussiness"] == 1
assert custom_session["theme"] == "Dwarves"

# Use the first session for the rest of the test
session_id = session["session_id"]

# 2. Get a question
resp = requests.get(f"{BASE}/session/{session_id}/question")
assert resp.status_code == 200, f"Failed to get question: {resp.text}"
question = resp.json()
print("First question:", question)

# 3. Submit an answer (dummy answer)
resp = requests.post(
    f"{BASE}/session/{session['session_id']}/answer",
    json={"answer": "The Shire"}
)
assert resp.status_code == 200, f"Failed to submit answer: {resp.text}"
answer_result = resp.json()
print("Answer result:", answer_result)

# 4. Get session state
resp = requests.get(f"{BASE}/session/{session['session_id']}")
assert resp.status_code == 200, f"Failed to get session state: {resp.text}"
state = resp.json()
print("Session state:", state)