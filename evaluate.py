import requests
import json

API_URL = "http://127.0.0.1:8000"

test_cases = [
    {"question": "What malfunctioned during the deployment?", "expected_keyword": "Server X"},
    {"question": "What caused the payment processing service degradation on March 15?", "expected_keyword": "memory leaks"},
    {"question": "What changes were applied by the DevOps team at 02:00 AM?", "expected_keyword": "gateway router"},
    {"question": "What happened to server Y?", "expected_keyword": "insufficient"}, # Unanswerable test case
]

def run_evaluation():
    print(" Starting Automated Evaluation Suite...")
    passed = 0
    total = len(test_cases)
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n[Test {i}/{total}] Query: '{test['question']}'")
        try:
            res = requests.post(f"{API_URL}/ask", json={"question": test["question"]})
            if res.status_code == 200:
                data = res.json()
                answer = data["answer"].lower()
                sources = " ".join(data["sources"]).lower()
                
                if test["expected_keyword"].lower() in answer or test["expected_keyword"].lower() in sources:
                    print(f"PASSED - Retrieved correct context/answer.")
                    passed += 1
                else:
                    print(f"FAILED - Expected keyword '{test['expected_keyword']}' not found in response.")
                    print(f"Got Answer: {data['answer']}")
            else:
                print(f"ERROR - API returned status {res.status_code}")
        except Exception as e:
            print(f"CONNECTION ERROR: {e}")
            
    print(f"\n--- EVALUATION SUMMARY ---")
    print(f"Total Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Success Rate: {(passed/total)*100}%")

if __name__ == "__main__":
    run_evaluation()