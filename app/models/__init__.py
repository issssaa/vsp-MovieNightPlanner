"""ORM models.

Importing every model here means `Base.metadata.create_all()` sees all three
tables, and SQLAlchemy can resolve the string names used in `relationship()`.
"""

from app.models.media import Media
from app.models.user import User
from app.models.user_media import STATUSES, UserMedia

__all__ = ["User", "Media", "UserMedia", "STATUSES"]
