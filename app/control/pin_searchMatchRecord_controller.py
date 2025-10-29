"""
User Story:
As a PIN, I want to search and view the history of my completed matches,
filtered by category and date period.
"""
from app.entity.match_record import MatchRecord
from app.entity.category import Category
from datetime import datetime

class PinSearchMatchRecordController:
    def searchMatchRecord(self, pin_id: int, category_name: str = None, start_date: str = None, end_date: str = None):
        """
        Returns a list of completed MatchRecord filtered by category name and optional date range.
        """
        q = (
            MatchRecord.query
            .join(Category)
            .filter(MatchRecord.pinID == pin_id, MatchRecord.status == "completed")
        )

        # ✅ Filter by category name (case-insensitive)
        if category_name:
            q = q.filter(Category.categoryName.ilike(f"%{category_name}%"))

        # ✅ Date range filtering
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
