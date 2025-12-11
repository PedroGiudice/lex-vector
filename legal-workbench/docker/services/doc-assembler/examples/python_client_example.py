"""
Example Python client for Doc Assembler API.

Demonstrates how to interact with the API programmatically.
"""

import requests
import json
from typing import Dict, Any, Optional, List


class DocAssemblerClient:
    """Client for interacting with Doc Assembler API."""

    def __init__(self, base_url: str = "http://localhost:8002"):
        """
        Initialize client.

        Args:
            base_url: Base URL of the API service
        """
        self.base_url = base_url
        self.api_v1 = f"{base_url}/api/v1"

    def health_check(self) -> Dict[str, Any]:
        """
        Check service health.

        Returns:
            Health status and version info
        """
        response = requests.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()

    def list_templates(self) -> List[Dict[str, Any]]:
        """
        List all available templates.

        Returns:
            List of template information objects
        """
        response = requests.get(f"{self.api_v1}/templates")
        response.raise_for_status()
        data = response.json()
        return data["templates"]

    def get_template_detail(self, template_id: str) -> Dict[str, Any]:
        """
        Get details about a specific template.

        Args:
            template_id: Template identifier

        Returns:
            Template details including required variables
        """
        response = requests.get(f"{self.api_v1}/templates/{template_id}")
        response.raise_for_status()
        return response.json()

    def validate_data(
        self,
        template_path: str,
        data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate data against template requirements.

        Args:
            template_path: Path to template file
            data: Data dictionary to validate

        Returns:
            Validation results
        """
        payload = {
            "template_path": template_path,
            "data": data
        }
        response = requests.post(f"{self.api_v1}/validate", json=payload)
        response.raise_for_status()
        return response.json()

    def preview_document(
        self,
        template_path: str,
        data: Dict[str, Any],
        field_types: Optional[Dict[str, str]] = None,
        auto_normalize: bool = True
    ) -> Dict[str, Any]:
        """
        Generate text preview of document.

        Args:
            template_path: Path to template file
            data: Data dictionary
            field_types: Optional field type mapping
            auto_normalize: Enable automatic normalization

        Returns:
            Preview data with rendered text
        """
        payload = {
            "template_path": template_path,
            "data": data,
            "auto_normalize": auto_normalize
        }
        if field_types:
            payload["field_types"] = field_types

        response = requests.post(f"{self.api_v1}/preview", json=payload)
        response.raise_for_status()
        return response.json()

    def assemble_document(
        self,
        template_path: str,
        data: Dict[str, Any],
        output_filename: Optional[str] = None,
        field_types: Optional[Dict[str, str]] = None,
        auto_normalize: bool = True
    ) -> Dict[str, Any]:
        """
        Assemble a document from template and data.

        Args:
            template_path: Path to template file
            data: Data dictionary
            output_filename: Optional custom output filename
            field_types: Optional field type mapping
            auto_normalize: Enable automatic normalization

        Returns:
            Assembly result with download URL
        """
        payload = {
            "template_path": template_path,
            "data": data,
            "auto_normalize": auto_normalize
        }
        if output_filename:
            payload["output_filename"] = output_filename
        if field_types:
            payload["field_types"] = field_types

        response = requests.post(f"{self.api_v1}/assemble", json=payload)
        response.raise_for_status()
        return response.json()


# ============================================================================
# Example Usage
# ============================================================================

def main():
    """Demonstrate API usage."""
    print("=" * 60)
    print("Doc Assembler API - Python Client Example")
    print("=" * 60)

    # Initialize client
    client = DocAssemblerClient()

    # 1. Health Check
    print("\n1️⃣  Checking service health...")
    try:
        health = client.health_check()
        print(f"✅ Service is {health['status']}")
        print(f"   API Version: {health['version']}")
        print(f"   Engine Version: {health['engine_version']}")
    except Exception as e:
        print(f"❌ Service unavailable: {e}")
        return

    # 2. List Templates
    print("\n2️⃣  Listing available templates...")
    try:
        templates = client.list_templates()
        print(f"✅ Found {len(templates)} template(s)")
        for template in templates:
            print(f"   - {template['name']}")
    except Exception as e:
        print(f"❌ Failed to list templates: {e}")

    # 3. Get Template Details
    if templates:
        print(f"\n3️⃣  Getting details for '{templates[0]['id']}'...")
        try:
            detail = client.get_template_detail(templates[0]['id'])
            print(f"✅ Template requires {detail['variable_count']} variables:")
            for var in detail['variables'][:5]:  # Show first 5
                print(f"   - {var}")
        except Exception as e:
            print(f"❌ Failed to get template details: {e}")

    # 4. Example: Assemble a Document
    print("\n4️⃣  Example: Assembling a document...")

    # Sample data
    document_data = {
        "nome": "João da Silva",
        "cpf": "123.456.789-01",
        "endereco": "Rua das Flores, 123, São Paulo - SP",
        "email": "joao.silva@example.com",
        "telefone": "(11) 98765-4321"
    }

    # Field type mapping
    field_types = {
        "nome": "name",
        "cpf": "cpf",
        "endereco": "address"
    }

    # First, validate the data
    print("\n   a) Validating data...")
    try:
        validation = client.validate_data(
            template_path="example.docx",
            data=document_data
        )
        if validation['result']['valid']:
            print("   ✅ Data is valid")
        else:
            print("   ⚠️  Data validation warnings:")
            for warning in validation['result']['warnings']:
                print(f"      - {warning}")
    except Exception as e:
        print(f"   ⚠️  Validation skipped: {e}")

    # Preview the document
    print("\n   b) Generating preview...")
    try:
        preview = client.preview_document(
            template_path="example.docx",
            data=document_data,
            field_types=field_types
        )
        print(f"   ✅ Preview generated")
        print(f"      Paragraphs: {preview['paragraph_count']}")
        print(f"      Tables: {preview['table_count']}")
        print(f"\n   Preview (first 200 chars):")
        print(f"   {preview['full_text'][:200]}...")
    except Exception as e:
        print(f"   ⚠️  Preview skipped: {e}")

    # Assemble the final document
    print("\n   c) Assembling final document...")
    try:
        result = client.assemble_document(
            template_path="example.docx",
            data=document_data,
            output_filename="joão_silva.docx",
            field_types=field_types
        )
        print(f"   ✅ {result['message']}")
        print(f"      Output: {result['filename']}")
        print(f"      Download: {result['download_url']}")
    except Exception as e:
        print(f"   ⚠️  Assembly skipped: {e}")

    print("\n" + "=" * 60)
    print("✅ Example completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
