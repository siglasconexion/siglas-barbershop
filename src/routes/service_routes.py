########## ########## ########## ##########     (RUTA - TABLA SERVICIOS)     ########## ########## ########## ##########

# nuevas rutas


@api.route("/services", methods=["GET"])  # listar todos los servicios
def list_services():
    services = Service.query.all()
    return jsonify({"ok": True, "data": [s.serialize() for s in services]}), 200


@api.route("/services/<int:service_id>", methods=["GET"])
def get_service(service_id):
    service = db.session.get(Service, service_id)
    if not service:
        return jsonify({"ok": False, "message": "Servicio no encontrado"}), 404
    return jsonify({"ok": True, "data": service.serialize()}), 200


# crear servicios solo usuarios admonistradores
@api.route("/services", methods=["POST"])
# @require_roles("admin")
@jwt_required()
def create_service():
    claims = get_jwt()
    is_admin = claims.get("is_admin", False)
    if not is_admin:
        return (
            jsonify(
                {
                    "ok": False,
                    "msg": "Acceso denegado: se requieren permisos de administrador",
                }
            ),
            403,
        )

    data = request.get_json() or {}
    name = data.get("name")
    price = data.get("price")
    duration_minutes = data.get("duration_minutes", 30)
    if not name or price is None:
        return jsonify({"ok": False, "message": "name y price son requeridos"}), 400
    service = Service(name=name, price=price, duration_minutes=int(duration_minutes))
    db.session.add(service)
    db.session.commit()
    return jsonify({"ok": True, "data": service.serialize()}), 201


#######


@api.route("/services/<int:service_id>", methods=["PUT"])
@jwt_required()
def update_service(service_id):
    claims = get_jwt()
    is_admin = claims.get("is_admin", False)

    if not is_admin:
        return (
            jsonify(
                {
                    "ok": False,
                    "msg": "Acceso denegado: se requieren permisos de administrador",
                }
            ),
            403,
        )

    service = db.session.get(Service, service_id)
    if not service:
        return jsonify({"ok": False, "message": "Servicio no encontrado"}), 404

    data = request.get_json() or {}
    service.name = data.get("name", service.name)

    if data.get("price") is not None:
        service.price = data.get("price")

    if data.get("duration_minutes") is not None:
        service.duration_minutes = int(data.get("duration_minutes"))

    db.session.commit()
    return jsonify({"ok": True, "data": service.serialize()}), 200


@api.route("/services/<int:service_id>", methods=["DELETE"])
@jwt_required()
# @require_roles("admin")
def delete_service(service_id):
    claims = get_jwt()
    is_admin = claims.get("is_admin", False)

    if not is_admin:
        return (
            jsonify(
                {
                    "ok": False,
                    "msg": "Acceso denegado: se requieren permisos de administrador",
                }
            ),
            403,
        )

    service = db.session.get(Service, service_id)
    if not service:
        return jsonify({"ok": False, "message": "Servicio no encontrado"}), 404

    db.session.delete(service)
    db.session.commit()
    return jsonify({"ok": True, "message": "Servicio eliminado"}), 200


########## ########## ########## ##########     (FIN - TABLA SERVICIOS)     ########## ########## ########## ##########

######################
