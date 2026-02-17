from flask import Blueprint, request, jsonify
from src.extensions import db
from src.models.person import Person

bp = Blueprint("person", __name__)


@bp.route("/")
def list_person():
    items = Person.query.all()
    return (
        jsonify(
            [
                {
                    "person_id": x.person_id,
                    "person_type_id": x.person_type_id,
                    "name": x.name,
                    "address": x.address,
                    "createdAt": x.createdAt.isoformat() if x.createdAt else None,
                    "updatedAt": x.updatedAt.isoformat() if x.updatedAt else None,
                }
                for x in items
            ]
        ),
        200,
    )
