"""
Test script for Flask API endpoints
"""
import requests
import json

API_BASE_URL = "http://localhost:5000"

def test_health_check():
    """Test the health check endpoint"""
    print("\n" + "="*80)
    print("Testing Health Check Endpoint")
    print("="*80)
    
    try:
        response = requests.get(f"{API_BASE_URL}/api/health")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_analyze_endpoint():
    """Test the analyze endpoint with sample data"""
    print("\n" + "="*80)
    print("Testing Analyze Endpoint")
    print("="*80)
    
    # Sample request payload
    payload = {
        "research_idea": "Improving text classification using lightweight transformer models",
        "selected_domains": ["Natural Language Processing", "Machine Learning"],
        "paper_data": None
    }
    
    print(f"Sending request with payload:")
    print(json.dumps(payload, indent=2))
    print("\nWaiting for response (this may take a few minutes)...\n")
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/analyze",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=600  # 10 minute timeout for long analysis
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("\n✅ Analysis completed successfully!")
            print(f"\nFinal Report Preview (first 500 chars):")
            print("-" * 80)
            final_report = result.get('data', {}).get('final_report', '')
            print(final_report[:500] + "..." if len(final_report) > 500 else final_report)
            print("-" * 80)
            
            # Print metrics
            metrics = result.get('data', {}).get('metrics', {})
            print(f"\n📊 Metrics:")
            print(f"  - Duration: {metrics.get('total_duration_seconds', 0):.2f}s")
            print(f"  - Papers Retrieved: {metrics.get('total_papers_retrieved', 0)}")
            print(f"  - Total Agents: {metrics.get('total_agents', 0)}")
            
            return True
        else:
            print(f"❌ Error response:")
            print(json.dumps(response.json(), indent=2))
            return False
            
    except requests.Timeout:
        print("❌ Request timed out (analysis took too long)")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_validation():
    """Test input validation"""
    print("\n" + "="*80)
    print("Testing Input Validation")
    print("="*80)
    
    # Test missing research_idea
    print("\n1. Testing missing research_idea...")
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/analyze",
            json={"selected_domains": ["AI"]},
            headers={"Content-Type": "application/json"}
        )
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        assert response.status_code == 400, "Should return 400 for missing research_idea"
        print("✅ Validation working correctly")
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    # Test missing selected_domains
    print("\n2. Testing missing selected_domains...")
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/analyze",
            json={"research_idea": "Test idea"},
            headers={"Content-Type": "application/json"}
        )
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        assert response.status_code == 400, "Should return 400 for missing selected_domains"
        print("✅ Validation working correctly")
    except Exception as e:
        print(f"❌ Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("\n" + "="*80)
    print("🧪 Flask API Test Suite")
    print("="*80)
    print("\nMake sure the Flask server is running on http://localhost:5000")
    print("Run it with: python api_server.py")
    print("="*80)
    
    input("\nPress Enter to start tests...")
    
    # Run tests
    tests = [
        ("Health Check", test_health_check),
        ("Input Validation", test_validation),
        ("Full Analysis", test_analyze_endpoint)
    ]
    
    results = {}
    for test_name, test_func in tests:
        print(f"\n\n{'='*80}")
        print(f"Running: {test_name}")
        print('='*80)
        results[test_name] = test_func()
    
    # Print summary
    print("\n\n" + "="*80)
    print("📊 TEST SUMMARY")
    print("="*80)
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
    print("="*80)
