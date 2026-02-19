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


@bp.get("/<int:item_id>")
def get_item(item_id):
    x = Person.query.get_or_404(item_id)
    return (
        jsonify(
            {
                "person_id": x.person_id,
                "person_type_id": x.person_type_id,
                "name": x.name,
                "address": x.address,
                "createdAt": x.createdAt.isoformat() if x.createdAt else None,
                "updatedAt": x.updatedAt.isoformat() if x.updatedAt else None,
            }
        ),
        200,
    )


@bp.post("/")
def create_item():
    data = request.get_json() or {}
    x = Person(person_type_id=data["person_type_id"])
