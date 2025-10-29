from app import db

class Shortlist(db.Model):
    __tablename__ = "shortlists"

    shortlistID = db.Column(db.Integer, primary_key=True)
    csrRepID = db.Column(db.Integer, db.ForeignKey("user_accounts.userID"), nullable=False)
    requestID = db.Column(db.Integer, db.ForeignKey("requests.requestID", ondelete="CASCADE"), nullable=False)

    # ✅ only define one side of relationship
    request = db.relationship("Request", lazy=True)
    