import httpx
import json

BASE_URL = "http://localhost:8000"


def test_allocation():
    # Test token allocation
    token_data = {
        "doctor_id": "some-uuid",  # Need actual doctor ID
        "source": "emergency",
        "patient_name": "Test Patient",
        "patient_contact": "1234567890",
    }

    response = httpx.post(url=f"{BASE_URL}/allocation/tokens", json=token_data)
    print("Allocation Response:", response.json())


if __name__ == "__main__":
    test_allocation()
