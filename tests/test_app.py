import pytest
from fastapi.testclient import TestClient


class TestGetActivities:
    """Tests for GET /activities endpoint."""
    
    def test_get_activities_returns_all_activities(self, client, reset_activities):
        """ARRANGE: Activities exist in database
           ACT: Make GET request to /activities
           ASSERT: Status 200 and all expected activities are returned
        """
        # ACT
        response = client.get("/activities")
        
        # ASSERT
        assert response.status_code == 200
        activities = response.json()
        assert len(activities) == 9
        assert "Chess Club" in activities
        assert "Programming Class" in activities
        assert "Gym Class" in activities
    
    def test_get_activities_returns_correct_structure(self, client, reset_activities):
        """ARRANGE: Activities exist with expected fields
           ACT: Make GET request to /activities
           ASSERT: Response has correct structure for each activity
        """
        # ACT
        response = client.get("/activities")
        
        # ASSERT
        assert response.status_code == 200
        activities = response.json()
        chess_club = activities["Chess Club"]
        
        assert "description" in chess_club
        assert "schedule" in chess_club
        assert "max_participants" in chess_club
        assert "participants" in chess_club
        assert isinstance(chess_club["participants"], list)
    
    def test_get_activities_includes_participants(self, client, reset_activities):
        """ARRANGE: Chess Club has known participants
           ACT: Make GET request to /activities
           ASSERT: Participants list includes expected emails
        """
        # ACT
        response = client.get("/activities")
        
        # ASSERT
        assert response.status_code == 200
        activities = response.json()
        chess_participants = activities["Chess Club"]["participants"]
        
        assert "michael@mergington.edu" in chess_participants
        assert "daniel@mergington.edu" in chess_participants
        assert len(chess_participants) == 2


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint."""
    
    def test_signup_successful(self, client, reset_activities):
        """ARRANGE: Soccer Club exists and has no participants
           ACT: Sign up a new student for Soccer Club
           ASSERT: Status 200, message confirms signup, participant added
        """
        # ARRANGE
        email = "test@mergington.edu"
        activity = "Soccer Club"
        
        # ACT
        response = client.post(f"/activities/{activity}/signup?email={email}")
        
        # ASSERT
        assert response.status_code == 200
        assert email in response.json()["message"]
        assert "Soccer Club" in response.json()["message"]
    
    def test_signup_adds_participant_to_activity(self, client, reset_activities):
        """ARRANGE: Basketball Club exists
           ACT: Sign up a new student, then fetch activities
           ASSERT: Participant appears in activity's participants list
        """
        # ARRANGE
        email = "newstudent@mergington.edu"
        activity = "Basketball Club"
        
        # ACT
        client.post(f"/activities/{activity}/signup?email={email}")
        response = client.get("/activities")
        
        # ASSERT
        activities = response.json()
        assert email in activities[activity]["participants"]
    
    def test_signup_duplicate_email_rejected(self, client, reset_activities):
        """ARRANGE: michael@mergington.edu is already in Chess Club
           ACT: Try to sign up the same student again
           ASSERT: Status 400, error message about duplicate signup
        """
        # ARRANGE
        email = "michael@mergington.edu"
        activity = "Chess Club"
        
        # ACT
        response = client.post(f"/activities/{activity}/signup?email={email}")
        
        # ASSERT
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"].lower()
    
    def test_signup_nonexistent_activity_fails(self, client, reset_activities):
        """ARRANGE: Nonexistent activity name
           ACT: Try to sign up for non-existent activity
           ASSERT: Status 404, error message about activity not found
        """
        # ARRANGE
        email = "test@mergington.edu"
        activity = "Nonexistent Club"
        
        # ACT
        response = client.post(f"/activities/{activity}/signup?email={email}")
        
        # ASSERT
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestRemoveParticipant:
    """Tests for DELETE /activities/{activity_name}/participants/{email} endpoint."""
    
    def test_remove_participant_successful(self, client, reset_activities):
        """ARRANGE: michael@mergington.edu is in Chess Club
           ACT: Delete the participant
           ASSERT: Status 200, message confirms removal
        """
        # ARRANGE
        email = "michael@mergington.edu"
        activity = "Chess Club"
        
        # ACT
        response = client.delete(f"/activities/{activity}/participants/{email}")
        
        # ASSERT
        assert response.status_code == 200
        assert email in response.json()["message"]
    
    def test_remove_participant_removes_from_list(self, client, reset_activities):
        """ARRANGE: daniel@mergington.edu is in Chess Club
           ACT: Delete the participant, then fetch activities
           ASSERT: Participant no longer in participants list
        """
        # ARRANGE
        email = "daniel@mergington.edu"
        activity = "Chess Club"
        
        # ACT
        client.delete(f"/activities/{activity}/participants/{email}")
        response = client.get("/activities")
        
        # ASSERT
        activities = response.json()
        assert email not in activities[activity]["participants"]
    
    def test_remove_nonexistent_participant_fails(self, client, reset_activities):
        """ARRANGE: nonexistent@email.com is not in any activity
           ACT: Try to delete non-existent participant from Chess Club
           ASSERT: Status 400, error message about not being signed up
        """
        # ARRANGE
        email = "nonexistent@mergington.edu"
        activity = "Chess Club"
        
        # ACT
        response = client.delete(f"/activities/{activity}/participants/{email}")
        
        # ASSERT
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"].lower()
    
    def test_remove_from_nonexistent_activity_fails(self, client, reset_activities):
        """ARRANGE: Nonexistent activity name
           ACT: Try to delete participant from non-existent activity
           ASSERT: Status 404, error message about activity not found
        """
        # ARRANGE
        email = "test@mergington.edu"
        activity = "Nonexistent Club"
        
        # ACT
        response = client.delete(f"/activities/{activity}/participants/{email}")
        
        # ASSERT
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_remove_participant_updates_count(self, client, reset_activities):
        """ARRANGE: Chess Club has 2 participants
           ACT: Remove one participant
           ASSERT: Participant count decreases by 1
        """
        # ARRANGE
        email = "michael@mergington.edu"
        activity = "Chess Club"
        response_before = client.get("/activities")
        count_before = len(response_before.json()[activity]["participants"])
        
        # ACT
        client.delete(f"/activities/{activity}/participants/{email}")
        response_after = client.get("/activities")
        count_after = len(response_after.json()[activity]["participants"])
        
        # ASSERT
        assert count_after == count_before - 1


class TestActivitySignupAndRemovalFlow:
    """Integration tests for signup and removal flows."""
    
    def test_signup_then_remove_participant(self, client, reset_activities):
        """ARRANGE: Soccer Club is empty
           ACT: Sign up a student, then remove them
           ASSERT: Participant added then removed correctly
        """
        # ARRANGE
        email = "flow@mergington.edu"
        activity = "Soccer Club"
        
        # ACT: Sign up
        response_signup = client.post(f"/activities/{activity}/signup?email={email}")
        assert response_signup.status_code == 200
        
        # ACT: Verify they're added
        response_check = client.get("/activities")
        assert email in response_check.json()[activity]["participants"]
        
        # ACT: Remove
        response_remove = client.delete(f"/activities/{activity}/participants/{email}")
        assert response_remove.status_code == 200
        
        # ASSERT: Verify they're removed
        response_final = client.get("/activities")
        assert email not in response_final.json()[activity]["participants"]
    
    def test_multiple_participants_signup_and_removal(self, client, reset_activities):
        """ARRANGE: Drama Club is empty
           ACT: Add multiple participants, remove one
           ASSERT: Correct participants remain
        """
        # ARRANGE
        emails = ["student1@mergington.edu", "student2@mergington.edu", "student3@mergington.edu"]
        activity = "Drama Club"
        
        # ACT: Sign up multiple students
        for email in emails:
            response = client.post(f"/activities/{activity}/signup?email={email}")
            assert response.status_code == 200
        
        # ASSERT: All are added
        response_check = client.get("/activities")
        participants = response_check.json()[activity]["participants"]
        assert len(participants) == 3
        for email in emails:
            assert email in participants
        
        # ACT: Remove one
        client.delete(f"/activities/{activity}/participants/{emails[1]}")
        
        # ASSERT: Correct participant removed
        response_final = client.get("/activities")
        final_participants = response_final.json()[activity]["participants"]
        assert len(final_participants) == 2
        assert emails[0] in final_participants
        assert emails[1] not in final_participants
        assert emails[2] in final_participants
