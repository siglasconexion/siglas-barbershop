########## ########## ########## ##########     (RUTA - TABLA APPOINTMENTS)     ########## ########## ########## ##########

# crear una cita solo clientes creo


@api.route("/appointments", methods=["POST"])
@jwt_required()
def create_appointment():
    user = get_current_user()
    if not user:
        return jsonify({"ok": False, "message": "Token inválido"}), 401

    if user.role != "cliente":
        return (
            jsonify({"ok": False, "message": "Solo clientes pueden crear citas"}),
            403,
        )

    data = request.get_json() or {}
    barber_id = data.get("barber_id")
    service_id = data.get("service_id")
    date_str = data.get("appointment_date")

    if not barber_id or not service_id or not date_str:
        return (
            jsonify(
                {
                    "ok": False,
                    "message": "barber_id, service_id, appointment_date son requeridos",
                }
            ),
            400,
        )

    barber = db.session.get(Usuario, int(barber_id))
    if not barber or barber.role not in ("barbero", "admin"):
        return jsonify({"ok": False, "message": "Barbero inválido"}), 400

    service = db.session.get(Service, int(service_id))
    if not service:
        return jsonify({"ok": False, "message": "Servicio inválido"}), 400

    try:
        dt = parser.isoparse(date_str)
    except Exception:
        return (
            jsonify(
                {"ok": False, "message": "appointment_date debe ser ISO8601 válido"}
            ),
            400,
        )

    appt = Appointment(
        client_id=user.user_id,
        barber_id=barber.user_id,
        service_id=service.service_id,
        appointment_date=dt,
        status="pendiente",
    )
    db.session.add(appt)
    db.session.commit()

    return jsonify({"ok": True, "data": appt.serialize()}), 201


# ver las citas cliente ve las suyas barberos las de ellos y aqui deberia el admin verlas todas
@api.route("/appointments/mine", methods=["GET"])
@jwt_required()
# hay que cambiar aqui el nuevo esquema de admin is_admin
def my_appointments():
    user = get_current_user()
    if not user:
        return jsonify({"ok": False, "message": "Token inválido"}), 401

    if user.role == "cliente":
        appts = (
            Appointment.query.filter_by(client_id=user.user_id)
            .order_by(Appointment.appointment_date.desc())
            .all()
        )
    elif user.role in ("barbero", "admin"):
        appts = (
            Appointment.query.filter_by(barber_id=user.user_id)
            .order_by(Appointment.appointment_date.desc())
            .all()
        )
    else:
        return jsonify({"ok": False, "message": "Rol no soportado"}), 400

    return jsonify({"ok": True, "data": [a.serialize() for a in appts]}), 200


# administrar citas, admin todas, barbero las de el, cliente solo las de el
@api.route("/appointments/<int:appointment_id>/modificar", methods=["PUT"])
@jwt_required()
def update_appointment_status(appointment_id):
    user = get_current_user()
    if not user:
        return jsonify({"ok": False, "message": "Token inválido", "data": "none"}), 401

    appt = db.session.get(Appointment, appointment_id)
    if not appt:
        return jsonify({"ok": False, "message": "Cita no existe", "data": "none"}), 404

    data = request.get_json() or {}
    new_status = data.get("status")

    if new_status not in ("pendiente", "confirmada", "cancelada", "completada"):
        return jsonify({"ok": False, "message": "status inválido"}), 400

    if user.role == "admin":
        pass
    elif user.role == "barbero":
        if appt.barber_id != user.user_id:
            return jsonify({"ok": False, "message": "No autorizado"}), 403
    elif user.role == "cliente":
        if appt.client_id != user.user_id:
            return jsonify({"ok": False, "message": "No autorizado"}), 403
        if new_status != "cancelada":
            return (
                jsonify({"ok": False, "message": "El cliente solo puede cancelar"}),
                403,
            )
    else:
        return jsonify({"ok": False, "message": "No autorizado"}), 403

    appt.status = new_status
    db.session.commit()
    return jsonify({"ok": True, "data": appt.serialize()}), 200


@api.route("/appointments/<int:appointment_id>/delete", methods=["DELETE"])
@jwt_required()
def delete_appointments(appointment_id):
    if not appointment_id:
        return (
            jsonify(
                {
                    "message": "Falta ID para procesar verifique",
                    "ok": False,
                    "data": "none",
                }
            ),
            400,
        )
    try:
        appointments_a_eliminar = Appointment.query.get_or_404(
            appointment_id
        )  # Busca por ID
        db.session.delete(appointments_a_eliminar)  # Marca para eliminar
        db.session.commit()  # Confirma la eliminación
        return (
            jsonify(
                {"message": "Appointments eliminada", "ok": True, "details": "none"}
            ),
            200,
        )
    except SQLAlchemyError as e:
        db.session.rollback()
        return (
            jsonify(
                {
                    "message": "Error, en la base de datos",
                    "details": str(e),
                    "ok": False,
                    "data": "none",
                }
            ),
            500,
        )
    except Exception as e:
        return (
            jsonify(
                {
                    "message": "Error, en el servidor",
                    "details": str(e),
                    "ok": False,
                    "data": "none",
                }
            ),
            500,
        )


########## ########## ########## ##########     (FIN - TABLA APPOINTMENTS)     ########## ########## ########## ##########

######################
