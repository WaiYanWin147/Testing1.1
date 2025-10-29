"""
User Story:
As a CSR Rep, I want to search and view the history of my completed volunteer services,
filtered by category and date period.
"""
from app.entity.match_record import MatchRecord
from datetime import datetime

class CsrSearchHistoryController:
    def searchHistory(self, userID: int, category_id: int = None, start_date: str = None, end_date: str = None):
        """Returns completed match records for a CSR representative filtered by category and date."""
        q = MatchRecord.query.filter(
            MatchRecord.csrRepID == userID,
            MatchRecord.status == "completed"
        )

        # ✅ Filter by category
        if category_id:
            q = q.filter(MatchRecord.categoryID == category_id)

        # ✅ Filter by date range (using completedAt)
        if start_date:
            try:
                start_dt = datetime.strptime(start_date, "%Y-%m-%d")
                q = q.filter(MatchRecord.completedAt >= start_dt)
            except ValueError:
                pass

        if end_date:
            try:
                end_dt = datetime.strptime(end_date, "%Y-%m-%d")
                q = q.filter(MatchRecord.completedAt <= end_dt)
            except ValueError:
                pass

        return q.order_by(MatchRecord.completedAt.desc()).all()
