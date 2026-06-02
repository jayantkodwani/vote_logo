"""Database model for the logo vote."""

from datetime import datetime

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class LogoVote(db.Model):
    __tablename__ = "logo_votes"

    id = db.Column(db.Integer, primary_key=True)
    # Stable per-person key (Entra email when Easy Auth is on, else a cookie id).
    # Unique => exactly one (changeable) vote per person.
    voter_key = db.Column(db.String(190), unique=True, nullable=False, index=True)
    voter_name = db.Column(db.String(190))
    concept_id = db.Column(db.String(40), nullable=False, index=True)
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<LogoVote {self.voter_key} -> {self.concept_id}>"
