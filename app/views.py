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
#  Identity
# --------------------------------------------------------------------------- #
def voter_identity():
    """Return (key, display_name).

    Prefers the user authenticated by Azure App Service Authentication
    ("Easy Auth" / Microsoft Entra). When that is enabled, the platform sets
    the X-MS-CLIENT-PRINCIPAL-* headers, giving us one vote per employee with
    zero auth code. Otherwise we fall back to a signed per-browser cookie id.
    """
    email = request.headers.get("X-MS-CLIENT-PRINCIPAL-NAME")
    name = request.headers.get("X-MS-CLIENT-PRINCIPAL-NAME")
    if email:
        return email.strip().lower(), name.strip()

    vid = session.get("vid")
    if not vid:
        vid = "anon-" + secrets.token_hex(8)
        session["vid"] = vid
    return vid, "Guest voter"


def is_admin(key: str) -> bool:
    return key in current_app.config.get("ADMIN_EMAILS", [])


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
#  Routes
# --------------------------------------------------------------------------- #
@bp.route("/", methods=["GET"])
def index():
    key, _ = voter_identity()
    counts, total, leader = tally()
    mine = LogoVote.query.filter_by(voter_key=key).first()
    return render_template(
        "vote.html",
        concepts=CONCEPTS,
        counts=counts,
        total=total,
        leader=leader,
        my_vote=(mine.concept_id if mine else None),
        my_comment=(mine.comment if mine else ""),
        is_admin=is_admin(key),
    )


@bp.route("/cast", methods=["POST"])
def cast():
    if not _csrf_ok():
        abort(400)

    concept_id = (request.form.get("concept_id") or "").strip()
    comment = (request.form.get("comment") or "").strip() or None
    if concept_id not in CONCEPT_IDS:
        flash("Please choose one of the logo options.", "warning")
        return redirect(url_for("main.index"))

    key, name = voter_identity()
    vote = LogoVote.query.filter_by(voter_key=key).first()
    if vote is None:
        vote = LogoVote(voter_key=key, voter_name=name)
        db.session.add(vote)
    vote.voter_name = name
    vote.concept_id = concept_id
    if comment is not None:
        vote.comment = comment
    db.session.commit()

    flash("Thanks — your vote has been recorded.", "success")
    return redirect(url_for("main.index"))


@bp.route("/reset", methods=["POST"])
def reset():
    key, _ = voter_identity()
    if not is_admin(key):
        abort(403)
    if not _csrf_ok():
        abort(400)
    LogoVote.query.delete()
    db.session.commit()
    flash("All logo votes have been cleared.", "info")
    return redirect(url_for("main.index"))


@bp.route("/api/results", methods=["GET"])
def api_results():
    counts, total, leader = tally()
    return jsonify({"total": total, "leader": leader, "counts": counts})


@bp.route("/healthz", methods=["GET"])
def healthz():
    return "ok", 200
