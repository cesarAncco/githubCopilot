"""
Tests for the Mergington High School API
Following AAA (Arrange-Act-Assert) testing pattern
"""

import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import pytest
from fastapi.testclient import TestClient
from app import app, activities

# Create a test client
client = TestClient(app)


class TestGetActivities:
    """Tests for GET /activities endpoint"""
    
    def test_get_activities_returns_all_activities(self):
        """Test that GET /activities returns all activities"""
        # Arrange
        expected_activity_count = 9
        
        # Act
        response = client.get("/activities")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == expected_activity_count
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Basketball Team" in data
    
    def test_get_activities_structure(self):
        """Test that activities have correct structure"""
        # Arrange
        required_keys = ["description", "schedule", "max_participants", "participants"]
        
        # Act
        response = client.get("/activities")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        activity = data["Chess Club"]
        
        for key in required_keys:
            assert key in activity
        assert isinstance(activity["participants"], list)


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def setup_method(self):
        """Reset activities before each test"""
        # Reset participants to initial state
        activities["Chess Club"]["participants"] = ["michael@mergington.edu", "daniel@mergington.edu"]
        activities["Basketball Team"]["participants"] = []
    
    def test_signup_successful(self):
        """Test successful signup for an activity"""
        # Arrange
        email = "newstudent@mergington.edu"
        activity_name = "Basketball Team"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "Signed up" in data["message"]
        assert email in data["message"]
        assert email in activities[activity_name]["participants"]
    
    def test_signup_activity_not_found(self):
        """Test signup for non-existent activity"""
        # Arrange
        email = "student@mergington.edu"
        invalid_activity = "Non Existent Club"
        
        # Act
        response = client.post(
            f"/activities/{invalid_activity}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_signup_already_registered(self):
        """Test signup when student is already registered"""
        # Arrange
        email = "michael@mergington.edu"
        activity_name = "Chess Club"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"].lower()
    
    def test_signup_multiple_students(self):
        """Test multiple students can sign up"""
        # Arrange
        emails = ["student1@mergington.edu", "student2@mergington.edu"]
        activity_name = "Art Club"
        
        # Act
        for email in emails:
            client.post(
                f"/activities/{activity_name}/signup",
                params={"email": email}
            )
        
        # Assert
        assert len(activities[activity_name]["participants"]) == 2
        for email in emails:
            assert email in activities[activity_name]["participants"]


class TestUnregisterFromActivity:
    """Tests for DELETE /activities/{activity_name}/signup endpoint"""
    
    def setup_method(self):
        """Reset activities before each test"""
        activities["Chess Club"]["participants"] = ["michael@mergington.edu", "daniel@mergington.edu"]
        activities["Basketball Team"]["participants"] = ["john@mergington.edu"]
    
    def test_unregister_successful(self):
        """Test successful unregister from an activity"""
        # Arrange
        email = "michael@mergington.edu"
        activity_name = "Chess Club"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered" in data["message"]
        assert email not in activities[activity_name]["participants"]
    
    def test_unregister_activity_not_found(self):
        """Test unregister from non-existent activity"""
        # Arrange
        email = "student@mergington.edu"
        invalid_activity = "Fake Club"
        
        # Act
        response = client.delete(
            f"/activities/{invalid_activity}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_unregister_not_signed_up(self):
        """Test unregister when student is not signed up"""
        # Arrange
        email = "notregistered@mergington.edu"
        activity_name = "Basketball Team"
        
        # Act
        response = client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"].lower()
    
    def test_unregister_removes_from_participants(self):
        """Test that unregister properly removes student from list"""
        # Arrange
        email = "john@mergington.edu"
        activity_name = "Basketball Team"
        
        # Act
        # Verify student is initially signed up
        assert email in activities[activity_name]["participants"]
        
        client.delete(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert email not in activities[activity_name]["participants"]


class TestRootRedirect:
    """Tests for root endpoint"""
    
    def test_root_redirects_to_static(self):
        """Test that root endpoint redirects to static files"""
        # Arrange
        expected_location = "/static/index.html"
        
        # Act
        response = client.get("/", follow_redirects=False)
        
        # Assert
        assert response.status_code == 307
        assert response.headers["location"] == expected_location