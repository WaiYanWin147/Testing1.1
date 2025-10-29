"""
User Story:
As a user admin, I want to activate suspended user profiles so that valid user profiles can be used again.
"""
from app import db
from app.entity.user_profile import UserProfile

class UserAdminActivateUserProfileController:
    def activate_profile(self, profile_id:int):
        p = UserProfile.query.get(profile_id)
        if not p: raise ValueError("Profile not found.")
        p.isActive = True; db.session.commit(); return p
