"""
Test script for Doc Assembler API.

Tests all endpoints to ensure proper functionality.
"""

import json
import requests
from pathlib import Path


# Configuration
BASE_URL = "http://localhost:8002"
API_V1 = f"{BASE_URL}/api/v1"


def test_health():
    """Test health check endpoint."""
    print("\n🔍 Testing /health endpoint...")
    response = requests.get(f"{BASE_URL}/health")

    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    print("✅ Health check passed")


def test_list_templates():
    """Test template listing endpoint."""
    print("\n🔍 Testing GET /api/v1/templates...")
    response = requests.get(f"{API_V1}/templates")

    print(f"Status Code: {response.status_code}")
    data = response.json()
    print(f"Templates found: {data['count']}")

    if data['templates']:
        print("\nAvailable templates:")
        for template in data['templates']:
            print(f"  - {template['id']}: {template['name']} ({template['size_bytes']} bytes)")

    assert response.status_code == 200
    print("✅ Template listing passed")
    return data['templates']


def test_template_detail(template_id: str):
    """Test template detail endpoint."""
    print(f"\n🔍 Testing GET /api/v1/templates/{template_id}...")
    response = requests.get(f"{API_V1}/templates/{template_id}")

    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"Template: {data['template']['name']}")
        print(f"Variables ({data['variable_count']}):")
        for var in data['variables']:
            print(f"  - {var}")
        print("✅ Template detail passed")
        return data
    else:
        print(f"⚠️  Template not found: {template_id}")
        return None


def test_validate():
    """Test data validation endpoint."""
    print("\n🔍 Testing POST /api/v1/validate...")

    payload = {
        "template_path": "example.docx",
        "data": {
            "nome": "João da Silva",
            "cpf": "12345678901"
        }
    }

    response = requests.post(
        f"{API_V1}/validate",
        json=payload
    )

    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"Valid: {data['result']['valid']}")
        print(f"Missing fields: {data['result']['missing']}")
        print(f"Extra fields: {data['result']['extra']}")
        if data['result']['warnings']:
            print("Warnings:")
            for warning in data['result']['warnings']:
                print(f"  - {warning}")
        print("✅ Validation test passed")
    else:
        print(f"⚠️  Validation failed (expected for missing template)")


def test_preview():
    """Test document preview endpoint."""
    print("\n🔍 Testing POST /api/v1/preview...")

    payload = {
        "template_path": "example.docx",
        "data": {
            "nome": "João da Silva",
            "cpf": "12345678901",
            "endereco": "Rua das Flores, 123"
        },
        "auto_normalize": True
    }

    response = requests.post(
        f"{API_V1}/preview",
        json=payload
    )

    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"Paragraphs: {data['paragraph_count']}")
        print(f"Tables: {data['table_count']}")
        print("\nPreview text (first 500 chars):")
        print(data['full_text'][:500])
        print("✅ Preview test passed")
    else:
        print(f"⚠️  Preview failed (expected for missing template)")


def test_assemble():
    """Test document assembly endpoint."""
    print("\n🔍 Testing POST /api/v1/assemble...")

    payload = {
        "template_path": "example.docx",
        "data": {
            "nome": "João da Silva",
            "cpf": "123.456.789-01",
            "endereco": "Rua das Flores, 123, São Paulo - SP"
        },
        "output_filename": "test_output.docx",
        "field_types": {
            "nome": "name",
            "cpf": "cpf",
            "endereco": "address"
        },
        "auto_normalize": True
    }

    response = requests.post(
        f"{API_V1}/assemble",
        json=payload
    )

    print(f"Status Code: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"Success: {data['success']}")
        print(f"Output file: {data['filename']}")
        print(f"Download URL: {data['download_url']}")
        print(f"Message: {data['message']}")
        print("✅ Assembly test passed")
    else:
        print(f"⚠️  Assembly failed (expected for missing template)")
        print(f"Error: {response.json()}")


def test_error_handling():
    """Test error handling with invalid requests."""
    print("\n🔍 Testing error handling...")

    # Test 1: Invalid template path (missing .docx)
    print("\n  Test 1: Invalid template path")
    payload = {
        "template_path": "invalid_template",
        "data": {"test": "data"}
    }
    response = requests.post(f"{API_V1}/assemble", json=payload)
    print(f"  Status Code: {response.status_code}")
    assert response.status_code == 422  # Validation error
    print("  ✅ Validation error handled correctly")

    # Test 2: Non-existent template
    print("\n  Test 2: Non-existent template")
    payload = {
        "template_path": "nonexistent.docx",
        "data": {"test": "data"}
    }
    response = requests.post(f"{API_V1}/assemble", json=payload)
    print(f"  Status Code: {response.status_code}")
    assert response.status_code == 404  # Not found
    print("  ✅ File not found error handled correctly")

    print("\n✅ Error handling tests passed")


def main():
    """Run all tests."""
    print("=" * 60)
    print("Doc Assembler API Test Suite")
    print("=" * 60)

    try:
        # Basic endpoints
        test_health()
        templates = test_list_templates()

        # Test template detail if templates exist
        if templates:
            test_template_detail(templates[0]['id'])

        # Data operations (will fail gracefully if no templates)
        test_validate()
        test_preview()
        test_assemble()

        # Error handling
        test_error_handling()

        print("\n" + "=" * 60)
        print("✅ All tests completed!")
        print("=" * 60)

    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Cannot connect to API at", BASE_URL)
        print("Make sure the service is running:")
        print("  docker-compose up doc-assembler")
        print("  or")
        print("  uvicorn api.main:app --host 0.0.0.0 --port 8002")

    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        raise


if __name__ == "__main__":
    main()
