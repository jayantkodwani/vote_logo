"""Routes for the logo vote."""

import secrets

from flask import (
    Blueprint, render_template, request, redirect, url_for, flash, abort,
    session, jsonify, current_app,
)

from .models import db, LogoVote, MAX_VOTES_PER_USER
from .concepts import CONCEPTS, CONCEPT_IDS

bp = Blueprint("main", __name__)


# --------------------------------------------------------------------------- #
#  Identity — voters are identified by the name they type in the popup.
# --------------------------------------------------------------------------- #
def _norm(name: str) -> str:
    return " ".join((name or "").split()).lower()


def _user_votes(key):
    """All of this voter's picks (rows)."""
    if not key:
        return []
    return LogoVote.query.filter_by(voter_key=key).all()


# --------------------------------------------------------------------------- #
#  CSRF (lightweight, session-based)
# --------------------------------------------------------------------------- #
def _csrf_token():
    t = session.get("csrf")
    if not t:
        t = secrets.token_hex(16)
        session["csrf"] = t
    return t


@bp.app_context_processor
def inject_csrf():
    return {"csrf_token": _csrf_token}


def _csrf_ok():
    return bool(request.form.get("csrf")) and request.form.get("csrf") == session.get("csrf")


# --------------------------------------------------------------------------- #
#  Tally
# --------------------------------------------------------------------------- #
def tally():
    counts = {c["id"]: 0 for c in CONCEPTS}
    total = 0
    for (cid,) in db.session.query(LogoVote.concept_id).all():
        if cid in counts:
            counts[cid] += 1
            total += 1
    leader = max(counts, key=counts.get) if total else None
    return counts, total, leader


# --------------------------------------------------------------------------- #
#  Vote routes
# --------------------------------------------------------------------------- #
@bp.route("/", methods=["GET"])
def index():
    counts, total, leader = tally()

    my_name = session.get("voter_name") or ""
    my_rows = _user_votes(_norm(my_name)) if my_name else []
    my_votes = [r.concept_id for r in my_rows]
    used = len(my_votes)

    return render_template(
        "vote.html",
        concepts=CONCEPTS,
        counts=counts,
        total=total,
        leader=leader,
        my_name=my_name,
        my_votes=my_votes,
        used=used,
        remaining=max(0, MAX_VOTES_PER_USER - used),
        max_votes=MAX_VOTES_PER_USER,
    )


@bp.route("/cast", methods=["POST"])
def cast():
    if not _csrf_ok():
        abort(400)

    name = (request.form.get("voter_name") or "").strip()
    concept_id = (request.form.get("concept_id") or "").strip()
    comment = (request.form.get("comment") or "").strip() or None

    if not name:
        flash("Please enter your name to vote.", "warning")
        return redirect(url_for("main.index"))
    if concept_id not in CONCEPT_IDS:
        flash("Please choose one of the logo options.", "warning")
        return redirect(url_for("main.index"))

    key = _norm(name)
    session["voter_name"] = name  # remember to highlight their picks

    rows = LogoVote.query.filter_by(voter_key=key).all()
    existing = {r.concept_id: r for r in rows}
    label = next((c["name"] for c in CONCEPTS if c["id"] == concept_id), concept_id)

    if concept_id in existing:
        # already a pick — just update the comment / name
        existing[concept_id].comment = comment
        existing[concept_id].voter_name = name
        db.session.commit()
        flash(f"Your vote for “{label}” is already counted.", "info")
        return redirect(url_for("main.index"))

    if len(rows) >= MAX_VOTES_PER_USER:
        flash(
            f"You can vote for up to {MAX_VOTES_PER_USER} logos. "
            f"Remove one of your picks to choose a different logo.",
            "warning",
        )
        return redirect(url_for("main.index"))

    db.session.add(LogoVote(voter_key=key, voter_name=name,
                            concept_id=concept_id, comment=comment))
    db.session.commit()

    used = len(rows) + 1
    flash(f"Thanks, {name} — vote {used} of {MAX_VOTES_PER_USER} recorded for “{label}”.", "success")
    return redirect(url_for("main.index"))


@bp.route("/remove", methods=["POST"])
def remove():
    if not _csrf_ok():
        abort(400)
    name = session.get("voter_name") or (request.form.get("voter_name") or "").strip()
    concept_id = (request.form.get("concept_id") or "").strip()
    if not name:
        flash("Enter your name and vote first.", "warning")
        return redirect(url_for("main.index"))

    row = LogoVote.query.filter_by(voter_key=_norm(name), concept_id=concept_id).first()
    if row:
        label = next((c["name"] for c in CONCEPTS if c["id"] == concept_id), concept_id)
        db.session.delete(row)
        db.session.commit()
        flash(f"Removed your vote for “{label}”.", "info")
    return redirect(url_for("main.index"))


# --------------------------------------------------------------------------- #
#  Admin (password-protected) — view every vote: name, selection, timestamp
# --------------------------------------------------------------------------- #
@bp.route("/admin", methods=["GET", "POST"])
def admin():
    if request.method == "POST":
        if not _csrf_ok():
            abort(400)
        if (request.form.get("password") or "") == current_app.config["ADMIN_PASSWORD"]:
            session["admin_ok"] = True
            return redirect(url_for("main.admin"))
        flash("Incorrect password.", "warning")
        return redirect(url_for("main.admin"))

    if not session.get("admin_ok"):
        return render_template("admin_login.html")

    names = {c["id"]: c["name"] for c in CONCEPTS}
    votes = LogoVote.query.order_by(LogoVote.updated_at.desc()).all()
    counts, total, leader = tally()
    distinct_voters = db.session.query(LogoVote.voter_key).distinct().count()
    return render_template(
        "admin.html",
        votes=votes,
        names=names,
        counts=counts,
        total=total,
        leader=leader,
        leader_name=(names.get(leader) if leader else None),
        distinct_voters=distinct_voters,
        max_votes=MAX_VOTES_PER_USER,
    )


@bp.route("/admin/logout")
def admin_logout():
    session.pop("admin_ok", None)
    flash("Signed out of admin.", "info")
    return redirect(url_for("main.index"))


@bp.route("/admin/reset", methods=["POST"])
def admin_reset():
    if not session.get("admin_ok"):
        abort(403)
    if not _csrf_ok():
        abort(400)
    LogoVote.query.delete()
    db.session.commit()
    flash("All logo votes have been cleared.", "info")
    return redirect(url_for("main.admin"))


# --------------------------------------------------------------------------- #
#  Utility
# --------------------------------------------------------------------------- #
@bp.route("/api/results", methods=["GET"])
def api_results():
    counts, total, leader = tally()
    return jsonify({"total": total, "leader": leader, "counts": counts})


@bp.route("/healthz", methods=["GET"])
def healthz():
    return "ok", 200
