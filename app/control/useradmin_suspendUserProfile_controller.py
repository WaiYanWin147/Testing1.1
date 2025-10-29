"""
User Story:
As a user admin, I want to suspend user profiles so that invalid user profiles are no longer used.
"""
from app import db
from app.entity.user_profile import UserProfile

class UserAdminSuspendUserProfileController:
    def suspend_profile(self, profile_id:int):
        p = UserProfile.query.get(profile_id)
        if not p: raise ValueError("Profile not found.")
        p.isActive = False; db.session.commit(); return p
