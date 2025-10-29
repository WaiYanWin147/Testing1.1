"""
Resets (drops & recreates) the database and seeds demo data for all roles.

Run:
  python seed.py

Then log in with:
  admin@test.com / 1234       (UserAdmin)
  csr@test.com   / 1234       (CSRRep)
  pin@test.com   / 1234       (PersonInNeed)
  pm@test.com    / 1234       (PlatformManager)
"""

from datetime import datetime, timedelta
from app import create_app, db
from app.entity.user_profile import UserProfile
from app.entity.user_account import UserAccount
from app.entity.category import Category
from app.entity.request import Request
from app.entity.shortlist import Shortlist
from app.entity.match_record import MatchRecord
from app.entity.report import Report


def reset_and_seed():
    app = create_app()
    with app.app_context():
        # --- 1) Reset DB ---
        db.drop_all()
        db.create_all()

        # --- 2) Profiles (roles) ---
        p_admin = UserProfile(profileName="UserAdmin", description="Manages users and profiles")
        p_csr = UserProfile(profileName="CSRRep", description="Corporate Social Responsibility representative")
        p_pin = UserProfile(profileName="PersonInNeed", description="Person in Need")
        p_pm = UserProfile(profileName="PlatformManager", description="Manages categories and reports")
        db.session.add_all([p_admin, p_csr, p_pin, p_pm])
        db.session.commit()

        # --- 3) Users (one per role) ---
        u_admin = UserAccount(name="Admin User", email="admin@test.com", profileID=p_admin.profileID)
        u_admin.password = "1234"
        u_csr = UserAccount(name="CSR User", email="csr@test.com", profileID=p_csr.profileID)
        u_csr.password = "1234"
        u_pin = UserAccount(name="PIN User", email="pin@test.com", profileID=p_pin.profileID)
        u_pin.password = "1234"
        u_pm = UserAccount(name="PM User", email="pm@test.com", profileID=p_pm.profileID)
        u_pm.password = "1234"
        db.session.add_all([u_admin, u_csr, u_pin, u_pm])
        db.session.commit()

        # --- 4) Categories ---
        c_transport = Category(categoryName="Transportation", description="Transport assistance", isActive=True)
        c_medical = Category(categoryName="Medical Aid", description="Medical support", isActive=True)
        c_food = Category(categoryName="Food Support", description="Food & groceries", isActive=True)
        db.session.add_all([c_transport, c_medical, c_food])
        db.session.commit()

        # --- 5) PIN Requests ---
        now = datetime.utcnow()

        r1 = Request(
            pinID=u_pin.userID,
            categoryID=c_transport.categoryID,
            title="Wheelchair-friendly transport needed",
            description="Pickup to hospital appointment",
            status="closed",
            viewCount=3,
            shortlistCount=1,
            createdAt=now - timedelta(days=5),
            closedAt=now - timedelta(days=3),
        )

        r2 = Request(
            pinID=u_pin.userID,
            categoryID=c_food.categoryID,
            title="Groceries delivery assistance",
            description="Weekly delivery preferred",
            status="open",
            viewCount=1,
            shortlistCount=0,
            createdAt=now - timedelta(days=2),
        )

        db.session.add_all([r1, r2])
        db.session.commit()

        # --- 6) CSR interactions (shortlist + match) ---
        s1 = Shortlist(csrRepID=u_csr.userID, requestID=r1.requestID)
        db.session.add(s1)

        # Completed match
        m1 = MatchRecord(
            requestID=r1.requestID,
            csrRepID=u_csr.userID,
            pinID=u_pin.userID,
            categoryID=c_transport.categoryID,
            status="completed",
            matchedAt=now - timedelta(days=4),
            completedAt=now - timedelta(days=3),
        )
        db.session.add(m1)
        db.session.commit()

        # --- 7) Example reports (Platform Manager) ---
        rep_daily = Report(
            reportTitle="Daily System Report - Demo",
            reportType="daily",
            generatedBy=u_pm.userID,
            period="2025-10-22",
            reportData='{"summary": {"note":"daily demo data"}}'
        )

        rep_weekly = Report(
            reportTitle="Weekly System Report - Demo",
            reportType="weekly",
            generatedBy=u_pm.userID,
            period="2025-W43",
            reportData='{"summary": {"note":"weekly demo data"}}'
        )

        rep_monthly = Report(
            reportTitle="Monthly System Report - Demo",
            reportType="monthly",
            generatedBy=u_pm.userID,
            period="2025-10",
            reportData='{"summary": {"note":"monthly demo data"}}'
        )

        db.session.add_all([rep_daily, rep_weekly, rep_monthly])
        db.session.commit()

        print("✅ Database reset complete.")
        print("👤 Demo users:")
        print("  - admin@test.com / 1234 (UserAdmin)")
        print("  - csr@test.com   / 1234 (CSRRep)")
        print("  - pin@test.com   / 1234 (PersonInNeed)")
        print("  - pm@test.com    / 1234 (PlatformManager)")
        print("🗂️  Demo categories: Transportation, Medical Aid, Food Support")
        print(f"📌 Requests: #{r1.requestID} (closed), #{r2.requestID} (open)")
        print(f"📊 Reports: {rep_daily.reportType}, {rep_weekly.reportType}, {rep_monthly.reportType}")


if __name__ == "__main__":
    reset_and_seed()
