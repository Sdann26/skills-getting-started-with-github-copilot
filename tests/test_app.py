"""
Tests for the High School Management System API
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app, activities


@pytest.fixture
def client():
    """Create a test client"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities data before each test"""
    # Store original state
    original_participants = {
        name: activity["participants"].copy()
        for name, activity in activities.items()
    }
    
    yield
    
    # Restore original state after test
    for name, activity in activities.items():
        activity["participants"] = original_participants[name].copy()


def test_root_redirect(client):
    """Test that root redirects to static index.html"""
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities(client):
    """Test getting all activities"""
    response = client.get("/activities")
    assert response.status_code == 200
    data = response.json()
    
    # Check that we have activities
    assert len(data) > 0
    assert "Chess Club" in data
    assert "Programming Class" in data
    
    # Check structure of an activity
    chess_club = data["Chess Club"]
    assert "description" in chess_club
    assert "schedule" in chess_club
    assert "max_participants" in chess_club
    assert "participants" in chess_club


def test_signup_for_activity_success(client):
    """Test successful signup for an activity"""
    response = client.post(
        "/activities/Chess%20Club/signup?email=test@mergington.edu"
    )
    assert response.status_code == 200
    data = response.json()
    assert "Signed up test@mergington.edu for Chess Club" in data["message"]
    
    # Verify participant was added
    activities_response = client.get("/activities")
    activities_data = activities_response.json()
    assert "test@mergington.edu" in activities_data["Chess Club"]["participants"]


def test_signup_for_nonexistent_activity(client):
    """Test signup for an activity that doesn't exist"""
    response = client.post(
        "/activities/Nonexistent%20Club/signup?email=test@mergington.edu"
    )
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Activity not found"


def test_signup_duplicate_participant(client):
    """Test that a student cannot sign up twice for the same activity"""
    email = "duplicate@mergington.edu"
    
    # First signup should succeed
    response1 = client.post(
        f"/activities/Chess%20Club/signup?email={email}"
    )
    assert response1.status_code == 200
    
    # Second signup should fail
    response2 = client.post(
        f"/activities/Chess%20Club/signup?email={email}"
    )
    assert response2.status_code == 400
    data = response2.json()
    assert "already signed up" in data["detail"]


def test_unregister_from_activity_success(client):
    """Test successful unregistration from an activity"""
    # First sign up
    email = "unregister@mergington.edu"
    client.post(f"/activities/Chess%20Club/signup?email={email}")
    
    # Then unregister
    response = client.delete(
        f"/activities/Chess%20Club/unregister?email={email}"
    )
    assert response.status_code == 200
    data = response.json()
    assert f"Unregistered {email} from Chess Club" in data["message"]
    
    # Verify participant was removed
    activities_response = client.get("/activities")
    activities_data = activities_response.json()
    assert email not in activities_data["Chess Club"]["participants"]


def test_unregister_from_nonexistent_activity(client):
    """Test unregistration from an activity that doesn't exist"""
    response = client.delete(
        "/activities/Nonexistent%20Club/unregister?email=test@mergington.edu"
    )
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Activity not found"


def test_unregister_not_registered_participant(client):
    """Test unregistration of a participant who isn't registered"""
    response = client.delete(
        "/activities/Chess%20Club/unregister?email=notregistered@mergington.edu"
    )
    assert response.status_code == 400
    data = response.json()
    assert "not registered" in data["detail"]


def test_multiple_activities_signup(client):
    """Test that a student can sign up for multiple activities"""
    email = "multi@mergington.edu"
    
    # Sign up for Chess Club
    response1 = client.post(
        f"/activities/Chess%20Club/signup?email={email}"
    )
    assert response1.status_code == 200
    
    # Sign up for Programming Class
    response2 = client.post(
        f"/activities/Programming%20Class/signup?email={email}"
    )
    assert response2.status_code == 200
    
    # Verify participant is in both activities
    activities_response = client.get("/activities")
    activities_data = activities_response.json()
    assert email in activities_data["Chess Club"]["participants"]
    assert email in activities_data["Programming Class"]["participants"]


def test_activity_participant_count(client):
    """Test that participant count is accurate"""
    response = client.get("/activities")
    data = response.json()
    
    for activity_name, activity_data in data.items():
        participant_count = len(activity_data["participants"])
        max_participants = activity_data["max_participants"]
        assert participant_count <= max_participants
        assert isinstance(activity_data["participants"], list)
