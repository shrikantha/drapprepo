from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_guess_disease():
    # Test with known medications
    response = client.post(
        "/guess_disease",
        json={"medications": ["Insulin", "Metformin"]}
    )
    assert response.status_code == 200
    assert "diseases" in response.json()

    # Test with medications that do not match any disease
    response = client.post(
        "/guess_disease",
        json={"medications": ["UnknownMedicine1", "UnknownMedicine2"]}
    )
    assert response.status_code == 404
    assert response.json() == {"detail": "No matching diseases found"}


def test_get_disease_description():
    # Test with a known disease
    response = client.post(
        "/get_disease_description",
        json={"disease": "Diabetes"}
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"

    # Test with a disease that is not in the database
    response = client.post(
        "/get_disease_description",
        json={"disease": "UnknownDisease"}
    )
    assert response.status_code == 404
    assert response.json() == {"detail": "Disease not found"}
