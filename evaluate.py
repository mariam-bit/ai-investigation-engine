import requests
import json

API_URL = "http://127.0.0.1:8000"

test_cases = [
    {"question": "What malfunctioned during the deployment?", "expected_keyword": "Server X"},
    {"question": "What caused the payment processing service degradation on March 15?", "expected_keyword": "memory leaks"},
    {"question": "What changes were applied by the DevOps team at 02:00 AM?", "expected_keyword": "gateway router"},
    {"question": "Which server experienced an unexpected kernel panic?", "expected_keyword": "Server X"},
    {"question": "Who authorized the emergency patch deployment?", "expected_keyword": "DevOps"},
    {"question": "What was the primary root cause of the database timeout?", "expected_keyword": "connection pool"},
    {"question": "Which region was most affected by the latency spike?", "expected_keyword": "us-east-1"},
    {"question": "What backup protocol was initiated during the outage?", "expected_keyword": "failover"},
    {"question": "How long did the total network partition last?", "expected_keyword": "minutes"},
    {"question": "What error code was returned by the API gateway?", "expected_keyword": "504"},

    {"question": "What was the peak CPU utilization recorded during the incident?", "expected_keyword": "%"},
    {"question": "Which microservice showed the highest memory consumption?", "expected_keyword": "payment"},
    {"question": "What threshold triggered the automated alert system?", "expected_keyword": "threshold"},
    {"question": "How many requests per second were dropped during peak traffic?", "expected_keyword": "requests"},
    {"question": "What was the recovery time objective (RTO) achieved?", "expected_keyword": "minutes"},
    {"question": "Which caching layer failed to invalidate properly?", "expected_keyword": "Redis"},
    {"question": "What load balancer configuration was modified?", "expected_keyword": "Nginx"},
    {"question": "Were SSL certificate expirations related to the failure?", "expected_keyword": "certificate"},
    {"question": "What disk partition filled up completely?", "expected_keyword": "var/log"},
    {"question": "What throughput was measured after the hotfix?", "expected_keyword": "mbps"},

    {"question": "What IP address initiated the unauthorized scan?", "expected_keyword": "192.168"},
    {"question": "Which user account had elevated privileges compromised?", "expected_keyword": "admin"},
    {"question": "What authentication token type was revoked?", "expected_keyword": "JWT"},
    {"question": "What firewall rule was updated in response to the anomaly?", "expected_keyword": "port"},
    {"question": "Were any database credentials exposed in the logs?", "expected_keyword": "credentials"},
    {"question": "What VPN gateway reported connection drops?", "expected_keyword": "VPN"},
    {"question": "What SSH key fingerprint was flagged?", "expected_keyword": "RSA"},
    {"question": "What audit log level was active during the event?", "expected_keyword": "INFO"},
    {"question": "Did the intrusion detection system trigger an alarm?", "expected_keyword": "IDS"},
    {"question": "What session timeout policy was enforced?", "expected_keyword": "timeout"},

    {"question": "What happened to server Y?", "expected_keyword": "insufficient"}, 
    {"question": "Who was the CEO of the company in 1995?", "expected_keyword": "insufficient"},
    {"question": "What was the exact weather in Tokyo during the server crash?", "expected_keyword": "insufficient"},
    {"question": "Which quantum computer was used for data processing?", "expected_keyword": "insufficient"},
    {"question": "What recipe was ordered for the team lunch?", "expected_keyword": "insufficient"},
    {"question": "How many satellites were launched on March 20?", "expected_keyword": "insufficient"},
    {"question": "What stock price did the company reach on Wall Street?", "expected_keyword": "insufficient"},
    {"question": "What airline ticket was booked for the CTO?", "expected_keyword": "insufficient"},
    {"question": "What electric vehicle model did the engineering lead drive?", "expected_keyword": "insufficient"},
    {"question": "What championship did the office soccer team win?", "expected_keyword": "insufficient"},
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