'''Event Logger models'''
import uuid
from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class Event(db.Model):  # pylint: disable=too-few-public-methods
    '''Event class to hold event log data'''
    id = db.Column(db.String(36), primary_key=True,
                   default=lambda: str(uuid.uuid4()))
    time = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    user = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    url = db.Column(db.Text, nullable=True)
    platform = db.Column(db.String(100), nullable=True)

    def to_dict(self):
        '''Return sql data as dict'''
        return {
            "id": self.id,
            "time": self.time.isoformat(),
            "user": self.user,
            "message": self.message,
            "url": self.url,
            "platform": self.platform,
        }

    def __repr__(self):
        return f"<User {self.user}><Time {self.time}>"
