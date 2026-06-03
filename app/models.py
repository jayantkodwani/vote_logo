"""Database model for the logo vote."""

from datetime import datetime

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Each person may vote for up to this many distinct logos.
MAX_VOTES_PER_USER = 3


class LogoVote(db.Model):
    # New table name: each row is one (voter, logo) pick, so a person can have
    # up to MAX_VOTES_PER_USER rows. (Renamed from the old single-vote table so
    # create_all() builds the new schema cleanly without a migration.)
    __tablename__ = "logo_votes2"

    id = db.Column(db.Integer, primary_key=True)
    # Stable per-person key (the entered name, normalised).
    voter_key = db.Column(db.String(190), nullable=False, index=True)
    voter_name = db.Column(db.String(190))
    concept_id = db.Column(db.String(40), nullable=False, index=True)
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # One row per (person, logo): prevents a double-vote for the same logo.
    __table_args__ = (
        db.UniqueConstraint("voter_key", "concept_id", name="uq_voter_concept"),
    )

    def __repr__(self):
        return f"<LogoVote {self.voter_key} -> {self.concept_id}>"
