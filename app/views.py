"""Routes for the logo vote."""

import secrets

from flask import (
    Blueprint, render_template, request, redirect, url_for, flash, abort,
    session, jsonify, current_app,
)

from .models import db, LogoVote
from .concepts import CONCEPTS, CONCEPT_IDS

bp = Blueprint("main", __name__)


# --------------------------------------------------------------------------- #
#  Identity — voters are identified by the name they type in the popup.
#  The name (normalised) is the unique key, so each person has one changeable
#  vote regardless of device.
# --------------------------------------------------------------------------- #
def _norm(name: str) -> str:
    return " ".join((name or "").split()).lower()


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
    mine = None
    if my_name:
        mine = LogoVote.query.filter_by(voter_key=_norm(my_name)).first()

    return render_template(
        "vote.html",
        concepts=CONCEPTS,
        counts=counts,
        total=total,
        leader=leader,
        my_vote=(mine.concept_id if mine else None),
        my_comment=(mine.comment if mine else ""),
        my_name=my_name,
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
    vote = LogoVote.query.filter_by(voter_key=key).first()
    if vote is None:
        vote = LogoVote(voter_key=key, voter_name=name)
        db.session.add(vote)
    vote.voter_name = name
    vote.concept_id = concept_id
    if comment is not None:
        vote.comment = comment
    db.session.commit()

    session["voter_name"] = name  # remember so we can highlight their pick

    label = next((c["name"] for c in CONCEPTS if c["id"] == concept_id), concept_id)
    flash(f"Thanks, {name} — your vote for “{label}” has been recorded.", "success")
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
    return render_template(
        "admin.html",
        votes=votes,
        names=names,
        counts=counts,
        total=total,
        leader=leader,
        leader_name=(names.get(leader) if leader else None),
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
