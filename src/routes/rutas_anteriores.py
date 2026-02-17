"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""

from flask import Flask, request, jsonify, url_for, Blueprint
from api.models import db, User, Usuario, Service, Appointment, Payment
from api.utils import generate_sitemap, APIException
from flask_cors import CORS
from sqlalchemy.exc import SQLAlchemyError
from api.auth import get_current_user, require_roles

# importaciones nuevas
from flask_bcrypt import Bcrypt
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    jwt_required,
    get_jwt_identity,
    get_jwt,
    verify_jwt_in_request,
)

from datetime import timedelta, timezone, datetime
from dateutil import parser

from sqlalchemy import or_

# ==========
# Stripe config
# ==========
import os
import stripe

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")

# ==========
# Helpers
# ==========


def _to_cents(amount):
    # amount viene como Decimal/float/str; Stripe usa centavos
    return int(round(float(amount) * 100))


api = Blueprint("api", __name__)

# Allow CORS requests to this API
CORS(api)


# nuevas instancias necesarias
jwt = JWTManager()
bcrypt = Bcrypt()


# def validate_required(data, required_fields):
#    """Valida campos requeridos en un JSON y retorna lista de faltantes."""
#    missing = [field for field in required_fields if not data.get(field)]
#    return missing


def validate_required(data, required_fields):
    """Valida que los campos existan en el JSON (aunque estén vacíos)."""
    missing = [field for field in required_fields if field not in data]
    return missing


@api.route("/user", methods=["POST"])  # borrar esta ruta
def add_user():
    data = request.get_json()
    if not data:
        return jsonify({"message": "No hay datos Verifique"}), 400
    required_fields = ["name", "password", "is_active", "email"]
    missing = validate_required(data, required_fields)
    if missing:
        return (
            jsonify({"message": "faltan campos requeridos", "missing_fields": missing}),
            400,
        )

    clean_data = {field: data[field] for field in required_fields if field in data}
    print(clean_data)

    for field in required_fields:
        if not data.get(field):
            return jsonify({"message": f"El campo '{field}' es requerido"}), 400

    try:
        existente = data.get("email")
        pw = data.get("password")
        print(pw)
        print("arriba pasword")
        user = User.query.filter_by(email=existente).first()
        if user:
            return (
                jsonify(
                    {
                        "data": user.serialize(),
                        "ok": False,
                        "message": f"Usuario {existente} ya esta Registrado Verifique...",
                        "details": "none",
                    }
                ),
                404,
            )
        password_hash = bcrypt.generate_password_hash(pw).decode("utf-8")
        print("clean_data", clean_data, "password", password_hash)
        clean_data["password"] = password_hash
        new_user = User(**clean_data)
        db.session.add(new_user)
        db.session.commit()
        return (
            jsonify(
                {
                    "data": new_user.serialize(),
                    "ok": True,
                    "message": "Usuario Creado Sastifactoriamente",
                    "details": "none",
                }
            ),
            201,
        )
    except SQLAlchemyError as e:
        db.session.rollback()
        return (
            jsonify(
                {
                    "message": "Error en la base de datos",
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
                    "message": "Error en el servidor",
                    "details": str(e),
                    "ok": False,
                    "data": "none",
                }
            ),
            500,
        )


@api.route("/user", methods=["GET"])  # porborrar esta ruta
def all_user():
    data = User.query.all()
    return (
        jsonify(
            {
                "data": [user.serialize() for user in data],
                "message": "mensage",
                "ok": True,
                "details": "none",
            }
        ),
        200,
    )


@api.route("/userdelete", methods=["POST"])  # por eliminar
def delete_user():
    data = request.get_json()
    id = data.get("id")
    print("id", id)
    usuario_a_eliminar = User.query.get_or_404(id)  # Busca por ID
    print("usuario_a_eliminar", usuario_a_eliminar)
    db.session.delete(usuario_a_eliminar)  # Marca para eliminar
    db.session.commit()  # Confirma la eliminació
    return jsonify({"message": "mensage", "ok": True, "details": "none"}), 200


@api.route("/users")  # por eliminar
@jwt_required()  # decorador para requerir autenticacion con jwt
def show_user():
    print("chequar el jwt", get_jwt_identity())
    claims = get_jwt()
    role = claims.get("role")  # Accede al rol directamente del token
    print("role", role)
    current_user_id = get_jwt_identity()  # obtiene la id del usuario del token
    if current_user_id:
        users = Usuario.query.all()
        user_list = []
        for user in users:
            user_dict = {
                "user_id": user.user_id,
                "email": user.email,
                "name": user.name,
            }
            user_list.append(user_dict)
        return jsonify({"users": user_list, "ok": True}), 200
    else:
        return jsonify({"message": "token invalido, o no proporcionado"}), 401


@api.route("/login", methods=["POST"])
def login():
    try:
        email = request.json.get("email")
        password = request.json.get("password")
        if not email or not password:
            return jsonify({"message": "Email and password are required."}), 400
        login_user = Usuario.query.filter_by(email=email).first()
        if not login_user:
            return jsonify({"message": "Invalid email"}), 404
        password_from_db = login_user.password
        resultado = bcrypt.check_password_hash(password_from_db, password)
        if resultado:
            # pueden ser "hours", "minutes", "days", "seconds"
            expires = timedelta(days=1)
            user_id = login_user.user_id
            user_role = login_user.role
            access_token = create_access_token(
                identity=str(user_id),
                # Agrega el rol como claim personalizado
                additional_claims={
                    "role": user_role,
                    "is_admin": bool(login_user.is_admin),
                },
                expires_delta=expires,
            )
            return (
                jsonify(
                    {
                        "access_token": access_token,
                        "ok": True,
                        "user": login_user.serialize(),
                    }
                ),
                200,
            )
        else:
            return jsonify({"message": "invalid password/email", "ok": False}), 404
    except Exception as e:
        return jsonify({"message": "se registro un error", "details": str(e)}), 500


########## ########## ########## ##########     (RUTAS - TABLA USUARIO)     ########## ########## ########## ##########
@api.route("/usuarios", methods=["GET"])
def all_usuarios():
    data = Usuario.query.all()
    return (
        jsonify(
            {
                "data": [user.serialize() for user in data],
                "message": "mensage",
                "ok": True,
                "details": "none",
            }
        ),
        200,
    )


@api.route("/usuario/cliente", methods=["POST"])  # cliente creado por cliente
def add_usuario_cliente():
    data = request.get_json()
    if not data:
        return jsonify({"message": "No hay datos Verifique", "ok": False}), 400
    required_fields = ["name", "email", "phone", "address", "password"]
    missing = validate_required(data, required_fields)
    if missing:
        return (
            jsonify(
                {
                    "message": "faltan campos requeridos",
                    "missing_fiends": missing,
                    "ok": False,
                }
            ),
            400,
        )
    clean_data = {field: data[field] for field in required_fields if field in data}
    for field in required_fields:
        if not data.get(field):
            return jsonify({"message": f"El campo '{field}' es requerido"}), 400

    try:
        existente = data.get("email")
        pw = data.get("password")
        user = Usuario.query.filter_by(email=existente).first()
        if user:
            return (
                jsonify(
                    {
                        "data": Usuario.serialize(),
                        "ok": False,
                        "message": f"Usuario {existente} ya esta Registrado Verifique...",
                        "details": "none",
                    }
                ),
                404,
            )
        password_hash = bcrypt.generate_password_hash(pw).decode("utf-8")
        clean_data["password"] = password_hash
        new_user = Usuario(**clean_data)
        db.session.add(new_user)
        db.session.commit()
        return (
            jsonify(
                {
                    "data": new_user.serialize(),
                    "ok": True,
                    "message": "Usuario Creado Sastifactoriamente",
                    "details": "none",
                }
            ),
            201,
        )
    except SQLAlchemyError as e:
        db.session.rollback()
        return (
            jsonify(
                {
                    "message": "Error en la base de datos",
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
                    "message": "Error en el servidor",
                    "details": str(e),
                    "ok": False,
                    "data": "none",
                }
            ),
            500,
        )


@api.route("/usuario/admin", methods=["POST"])  # admin crea usuarios
@require_roles()
def add_usuario_barber_admin():
    data = request.get_json()
    print("data", data)
    if not data:
        return jsonify({"message": "No hay datos Verifique", "ok": False}), 400
    required_fields = [
        "name",
        "email",
        "phone",
        "address",
        "password",
        "bio",
        "specialties",
        "photo_url",
        "role",
    ]
    missing = validate_required(data, required_fields)
    if missing:
        return (
            jsonify(
                {
                    "message": "faltan campos requeridos",
                    "missing_fiends": missing,
                    "ok": False,
                }
            ),
            400,
        )
    clean_data = {field: data[field] for field in required_fields if field in data}
    for field in required_fields:
        if field not in clean_data:
            return jsonify({"message": f"El campo '{field}' es requerido"}), 400
    try:
        existente = data.get("email")
        pw = data.get("password")
        user = Usuario.query.filter_by(email=existente).first()
        if user:
            return (
                jsonify(
                    {
                        "data": Usuario.serialize(),
                        "ok": False,
                        "message": f"Usuario {existente} ya esta Registrado Verifique...",
                        "details": "none",
                    }
                ),
                404,
            )
        password_hash = bcrypt.generate_password_hash(pw).decode("utf-8")
        clean_data["password"] = password_hash
        new_user = Usuario(**clean_data)
        db.session.add(new_user)
        db.session.commit()
        return (
            jsonify(
                {
                    "data": new_user.serialize(),
                    "ok": True,
                    "message": "Usuario Creado Sastifactoriamente",
                    "details": "none",
                }
            ),
            201,
        )
    except SQLAlchemyError as e:
        db.session.rollback()
        return (
            jsonify(
                {
                    "message": "Error en la base de datos",
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
                    "message": "Error en el servidor",
                    "details": str(e),
                    "ok": False,
                    "data": "none",
                }
            ),
            500,
        )


@api.route("/admin/users", methods=["POST"])  # pendiente por eliminar
@require_roles()
def admin_create_user():
    data = request.get_json() or {}

    # Campos básicos
    name = data.get("name")
    email = data.get("email")
    password = data.get("password")
    role = data.get("role", "cliente")  # default cliente

    phone = data.get("phone")
    address = data.get("address")

    # Validaciones
    if not name or not email or not password:
        return (
            jsonify(
                {
                    "ok": False,
                    "message": "name, email y password son requeridos",
                    "data": None,
                }
            ),
            400,
        )

    if role not in ("cliente", "barbero", "admin"):
        return (
            jsonify(
                {
                    "ok": False,
                    "message": "role inválido (cliente, barbero, admin)",
                    "data": None,
                }
            ),
            400,
        )

    # Email único
    exists = Usuario.query.filter_by(email=email).first()
    if exists:
        return (
            jsonify(
                {
                    "ok": False,
                    "message": f"Ya existe un usuario con email: {email}",
                    "data": None,
                }
            ),
            409,
        )

    # Hash del password
    password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    new_user = Usuario(
        name=name,
        email=email,
        password=password_hash,
        role=role,
        phone=phone,
        address=address,
        is_active=True,
    )

    try:
        db.session.add(new_user)
        db.session.commit()
        return (
            jsonify(
                {
                    "ok": True,
                    "message": "Usuario creado correctamente",
                    "data": new_user.serialize(),
                }
            ),
            201,
        )

    except Exception as e:
        db.session.rollback()
        return (
            jsonify(
                {
                    "ok": False,
                    "message": "Error creando usuario",
                    "details": str(e),
                    "data": None,
                }
            ),
            500,
        )


@api.route("/admin/users", methods=["GET"])  # admin lista usuarios
@require_roles()
def admin_list_users():
    users = Usuario.query.order_by(Usuario.user_id.desc()).all()
    return jsonify({"ok": True, "data": [u.serialize() for u in users]}), 200


@api.route("/admin/usuario/<int:user_id>", methods=["PUT"])
@require_roles()
def update_usuario(user_id):
    usuario = Usuario.query.get(user_id)
    if not usuario:
        return jsonify({"ok": False, "message": "Usuario no encontrado"}), 404

    data = request.get_json()

    usuario.name = data.get("name", usuario.name)
    usuario.email = data.get("email", usuario.email)
    usuario.role = data.get("role", usuario.role)
    usuario.is_admin = data.get("is_admin", usuario.is_admin)
    usuario.phone = data.get("phone")
    usuario.address = data.get("address")
    usuario.photo_url = data.get("photo_url")
    usuario.bio = data.get("bio")
    usuario.specialties = data.get("specialties")

    if data.get("password"):
        usuario.password = bcrypt.generate_password_hash(
            data["password"].decode("utf-8")
        )

    db.session.commit()

    return jsonify({"ok": True, "result": usuario.serialize()}), 200


@api.route("/usuario/<int:user_id>", methods=["GET"])
def get_usuario(user_id):
    usuario = Usuario.query.get(user_id)
    if not usuario:
        return jsonify({"ok": False, "message": "Usuario no encontrado"}), 404

    return jsonify({"ok": True, "result": usuario.serialize()}), 200


@api.route("/admin/user/<int:id>", methods=["DELETE"])
# @require_roles("admin")
@jwt_required()
def admin_delete_user(id):
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
    user = db.session.get(Usuario, id)
    if not user:
        return jsonify({"ok": False, "message": "Usuario no encontrado"}), 404

    db.session.delete(user)
    db.session.commit()
    return jsonify({"ok": True, "message": "Usuario eliminado"}), 200


########## ########## ########## ##########     (FIN  - TABLA USUARIO)     ########## ########## ########## ##########

######################

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

########## ########## ########## ##########     (RUTA - TABLA BARBEROS)     ########## ########## ########## ##########


@api.route("/barbers", methods=["GET"])  # listar barberos
# @jwt_required()
def list_barbers():
    barbers = Usuario.query.filter(
        # modificar porque cambie is_admin
        Usuario.role.in_(["barbero", "admin"])
    ).all()
    return jsonify({"ok": True, "data": [b.serialize() for b in barbers]}), 200


########## ########## ########## ##########     (FINAL - TABLA BARBEROS)     ########## ########## ########## ##########

######################

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

########## ########## ########## ##########     (RUTAS PERFILES)     ########## ########## ########## ##########


@api.route("/miperfil/cliente", methods=["GET"])
@jwt_required()
def get_me():
    user = get_current_user()
    try:
        user = db.session.get(Usuario, user.user_id)
        if not user:
            return jsonify(
                {"message": "Usuario no encontrado", "ok": False, "data": "none"}
            )
        return (
            jsonify(
                {
                    "ok": True,
                    "user": {
                        "user_id": user.user_id,
                        "name": user.name,
                        "email": user.email,
                        "phone": user.phone,
                        "address": user.address,
                        # "is_active": user.is_active,
                        # "role": user.role,
                        # "is_admin": user.is_admin,
                        # "photo_url": user.photo_url,
                        # "bio": user.bio,
                        # "specialties": user.specialties,
                        # "created_at": user.created_at.isoformat() if user.created_at else None
                    },
                }
            ),
            200,
        )
    except SQLAlchemyError as e:
        db.session.rollback()
        return (
            jsonify(
                {
                    "message": "Error en la base de datos",
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
                    "message": "Error en el servidor",
                    "details": str(e),
                    "ok": False,
                    "data": "none",
                }
            ),
            500,
        )


@api.route("/miperfil/<int:userId>/modify", methods=["PUT"])
@jwt_required()
def update_miperfilcliente(userId):
    if not userId:
        return (
            jsonify({"message": "Error, no llego dato", "ok": False, "data": "None"}),
            400,
        )
    try:
        user = db.session.get(Usuario, userId)

        data = request.get_json(silent=True) or {}
        if not data:
            pass

        # Campos permitidos para auto-edición
        allowed_fields = {"name", "phone", "address", "email"}

        # Actualiza solo lo permitido
        for key, value in data.items():
            if key not in allowed_fields:
                # Ignoramos extra campos para no romper
                continue

            # Reglas extra: specialties solo si es barbero (o admin-barbero)
            if key == "specialties":
                if user.role != "barbero":
                    continue  # cliente no debe cambiar specialties

            setattr(user, key, value)

        # Validaciones mínimas
        if user.name is None or str(user.name).strip() == "":
            return jsonify({"ok": False, "message": "El nombre es obligatorio"}), 400

        db.session.commit()

        return (
            jsonify(
                {
                    "ok": True,
                    "message": "Perfil actualizado",
                    "user": {
                        "user_id": user.user_id,
                        "name": user.name,
                        "email": user.email,
                        "phone": user.phone,
                        "address": user.address,
                    },
                }
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
                    "data": "mone",
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


########## ########## ########## ##########     (FIN RUTAS PERFILES)   ########## ########## ########## ##########


# rutas adicionales
@api.route("/admin/appointments", methods=["GET"])
@require_roles("barbero")
def admin_list_appointments():
    # filtros opcionales: ?status=pendiente&date=2026-01-11
    status = request.args.get("status")
    date_str = request.args.get("date")  # YYYY-MM-DD

    q = Appointment.query

    if status:
        q = q.filter(Appointment.status == status)

    if date_str:
        # filtra por día (UTC); si trabajas local, lo ajustamos después
        try:
            day = parser.isoparse(date_str).date()
            start = datetime(day.year, day.month, day.day, tzinfo=timezone.utc)
            end = start.replace(hour=23, minute=59, second=59)
            q = q.filter(
                Appointment.appointment_date >= start,
                Appointment.appointment_date <= end,
            )
        except Exception:
            return (
                jsonify({"ok": False, "message": "date inválida (usa YYYY-MM-DD)"}),
                400,
            )

    appts = q.order_by(Appointment.appointment_date.desc()).all()
    return jsonify({"ok": True, "data": [a.serialize() for a in appts]}), 200


@api.route("/admin/users/<int:user_id>", methods=["PUT"])
@require_roles("admin")
def admin_update_user(user_id):
    user = db.session.get(Usuario, user_id)
    if not user:
        return jsonify({"ok": False, "message": "Usuario no encontrado"}), 404

    data = request.get_json() or {}

    # campos editables por admin
    user.name = data.get("name", user.name)
    user.email = data.get("email", user.email)
    user.phone = data.get("phone", user.phone)
    user.address = data.get("address", user.address)
    user.photo_url = data.get("photo_url", user.photo_url)
    user.bio = data.get("bio", user.bio)
    user.specialties = data.get("specialties", user.specialties)

    if data.get("role") in ("cliente", "barbero", "admin"):
        user.role = data.get("role")

    if data.get("is_admin") is not None:
        user.is_admin = bool(data.get("is_admin"))

    if data.get("is_active") is not None:
        user.is_active = bool(data.get("is_active"))

    if data.get("password"):
        user.password = bcrypt.generate_password_hash(data["password"]).decode("utf-8")

    db.session.commit()
    return jsonify({"ok": True, "data": user.serialize()}), 200


@api.route("/payments", methods=["POST"])
@jwt_required()
def create_payment():
    user = get_current_user()
    if not user:
        return jsonify({"ok": False, "message": "Token inválido"}), 401

    if user.role not in ("barbero", "admin") and not bool(user.is_admin):
        return jsonify({"ok": False, "message": "No autorizado"}), 403

    data = request.get_json() or {}
    appointment_id = data.get("appointment_id")
    method = data.get("method", "efectivo")
    status = data.get("status", "pagado")
    notes = data.get("notes")

    if not appointment_id:
        return jsonify({"ok": False, "message": "appointment_id requerido"}), 400

    appt = db.session.get(Appointment, int(appointment_id))
    if not appt:
        return jsonify({"ok": False, "message": "Cita no existe"}), 404

    # Barbero solo puede cobrar citas suyas
    if user.role == "barbero" and appt.barber_id != user.user_id:
        return jsonify({"ok": False, "message": "No autorizado para esta cita"}), 403

    # monto por defecto: precio del servicio
    amount = data.get("amount")
    if amount is None:
        amount = float(appt.service.price)

    payment = Payment(
        appointment_id=appt.appointment_id,
        amount=amount,
        method=method,
        status=status,
        created_by_user_id=user.user_id,
        notes=notes,
    )

    db.session.add(payment)
    db.session.commit()

    return jsonify({"ok": True, "data": payment.serialize()}), 201


@api.route("/admin/payments", methods=["GET"])
# @require_roles("admin")
def admin_list_payments():
    payments = Payment.query.order_by(Payment.paid_at.desc()).all()
    return jsonify({"ok": True, "data": [p.serialize() for p in payments]}), 200


@api.route("/admin/payments/recent", methods=["GET"])
@require_roles("admin")
def admin_recent_payments():
    limit = int(request.args.get("limit", 10))
    payments = Payment.query.order_by(Payment.paid_at.desc()).limit(limit).all()
    return jsonify({"ok": True, "data": [p.serialize() for p in payments]}), 200


@api.route("/admin/sales/today", methods=["GET"])
@require_roles("admin")
def admin_sales_today():
    # hoy en UTC
    """now = datetime.now(timezone.utc)
    start = datetime(now.year, now.month, now.day, tzinfo=timezone.utc)
    end = start.replace(hour=23, minute=59, second=59)"""

    """    paid = Payment.query.filter(
        Payment.status == "pagado",
        Payment.paid_at >= start,
        Payment.paid_at <= end
    ).all() """

    paid = Payment.query.filter().all()

    total = sum([float(p.amount) for p in paid])

    return (
        jsonify(
            {
                "ok": True,
                "data": {
                    # "date": start.date().isoformat(),
                    "count": len(paid),
                    "total": float(total),
                    "payments": [p.serialize() for p in paid],
                },
            }
        ),
        200,
    )


# rutas para pagos stripe
# ==========================================================
# 1) Crear Checkout para una CITA (Payment ligado a appointment)
# POST /api/stripe/checkout/appointment/<appointment_id>
# ==========================================================
@api.route("/stripe/checkout/appointment/<int:appointment_id>", methods=["POST"])
def stripe_checkout_appointment(appointment_id):
    appt = Appointment.query.get(appointment_id)
    if not appt:
        return jsonify({"ok": False, "message": "Cita no encontrada"}), 404

    service = appt.service  # por tu relationship
    if not service:
        return jsonify({"ok": False, "message": "Servicio no encontrado"}), 404

    amount_cents = _to_cents(service.price)

    try:
        session = stripe.checkout.Session.create(
            mode="payment",
            line_items=[
                {
                    "price_data": {
                        "currency": "usd",
                        "product_data": {
                            "name": f"{service.name} - Cita #{appt.appointment_id}"
                        },
                        "unit_amount": amount_cents,
                    },
                    "quantity": 1,
                }
            ],
            # IMPORTANTE: {CHECKOUT_SESSION_ID} literal
            success_url=f"{FRONTEND_URL}/pago-exitoso?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{FRONTEND_URL}/pago-cancelado",
            metadata={
                "kind": "appointment",
                "appointment_id": str(appt.appointment_id),
                "service_id": str(service.service_id),
                "amount": str(service.price),
                "client_id": str(appt.client_id),
                "barber_id": str(appt.barber_id),
            },
        )

        # Devuelve el URL para redirigir
        return (
            jsonify(
                {"ok": True, "checkout_url": session.url, "session_id": session.id}
            ),
            200,
        )

    except Exception as e:
        return jsonify({"ok": False, "message": f"Stripe error: {str(e)}"}), 500


# ==========================================================
# 2) Crear Checkout DIRECTO (sin cita)
# POST /api/stripe/checkout/direct
# body: { "service_id": 1 }
# ==========================================================
# @api.route("/stripe/checkout/direct", methods=["POST"])
# def stripe_checkout_direct():
#    data = request.get_json() or {}
#    service_id = data.get("service_id")

#    if not service_id:
#        return jsonify({"ok": False, "message": "service_id requerido"}), 400

#    service = Service.query.get(int(service_id))
#    if not service:
#        return jsonify({"ok": False, "message": "Servicio no encontrado"}), 404
#        amount_cents = _to_cents(service.price)

#    try:
#        session = stripe.checkout.Session.create(
#            mode="payment",
#            line_items=[{
#                "price_data": {
#                    "currency": "usd",
#                    "product_data": {
#                        "name": f"{service.name} - Pago directo"
#                    },
#                    "unit_amount": amount_cents
#                },
#                "quantity": 1
#            }],
#            success_url=f"{FRONTEND_URL}/#/pago-exitoso?session_id={{CHECKOUT_SESSION_ID}}",
#            cancel_url=f"{FRONTEND_URL}/#/pago-cancelado",
#            metadata={
#                "kind": "direct",
#                "service_id": str(service.service_id),
#                "amount": str(service.price),
#            }
#        )
#        return jsonify({"ok": True, "checkout_url": session.url, "session_id": session.id}), 200

#    except Exception as e:
#        return jsonify({"ok": False, "message": f"Stripe error: {str(e)}"}), 500


@api.route("/stripe/checkout/direct", methods=["POST"])
def stripe_checkout_direct():
    verify_jwt_in_request()
    payer_user_id = int(get_jwt_identity())

    data = request.get_json() or {}
    service_id = data.get("service_id")

    if not service_id:
        return jsonify({"ok": False, "message": "service_id requerido"}), 400

    service = Service.query.get(int(service_id))
    if not service:
        return jsonify({"ok": False, "message": "Servicio no encontrado"}), 404

    amount_cents = int(float(service.price) * 100)

    try:
        session = stripe.checkout.Session.create(
            mode="payment",
            line_items=[
                {
                    "price_data": {
                        "currency": "usd",
                        "product_data": {"name": f"{service.name} - Pago directo"},
                        "unit_amount": amount_cents,
                    },
                    "quantity": 1,
                }
            ],
            success_url=f"{FRONTEND_URL}/pago-exitoso?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{FRONTEND_URL}/pago-cancelado",
            metadata={
                "kind": "direct",
                "service_id": str(service.service_id),
                "amount": str(service.price),
                "payer_user_id": str(payer_user_id),
            },
        )
        return (
            jsonify(
                {"ok": True, "checkout_url": session.url, "session_id": session.id}
            ),
            200,
        )
    except Exception as e:
        return jsonify({"ok": False, "message": f"Stripe error: {str(e)}"}), 500


# ==========================================================
# 3) Webhook Stripe: confirma pago y crea Payment en SQLite
# POST /api/stripe/webhook
# ==========================================================
# @api.route("/stripe/webhook", methods=["POST"])
# def stripe_webhook():
# payload = request.data
# sig_header = request.headers.get("Stripe-Signature")

# if not STRIPE_WEBHOOK_SECRET:
# return "Webhook secret not configured", 500

# try:
# event = stripe.Webhook.construct_event(
# payload=payload,
# sig_header=sig_header,
# secret=STRIPE_WEBHOOK_SECRET
# )
# except ValueError:
# return "Invalid payload", 400
# except stripe.error.SignatureVerificationError:
# return "Invalid signature", 400

# Evento principal de Checkout
# if event["type"] == "checkout.session.completed":
# session = event["data"]["object"]
# md = session.get("metadata", {}) or {}

# stripe_session_id = session.get("id")  # ej: cs_test_...
# kind = md.get("kind")                  # "appointment" | "direct"
# amount = md.get("amount")              # string/decimal
# barber_id = md.get("barber_id")

# 1) Anti-duplicados por sesión
# existing = Payment.query.filter_by(stripe_session_id=stripe_session_id).first()
# if existing:
# return "OK", 200

# 2) Determinar appointment_id y created_by
# appointment_id = None
# created_by_user_id = 1  # admin por defecto si es direct (ajústalo si quieres)


# payer_user_id = None
# if kind == "appointment":
# payer_user_id = int(md.get("client_id"))
# appointment_id = int(md.get("appointment_id"))
# Para tu regla: "cuando barbero completa" / o cobro asociado a cita
# Usamos barber_id como created_by (si viene)
# if barber_id:
# created_by_user_id = int(barber_id)

# 3) Crear registro de pago (confirmado)
# payment = Payment(
# appointment_id=appointment_id,
# payer_user_id=payer_user_id,
# amount=amount,
# method="stripe",
# status="pagado",
# paid_at=datetime.now(timezone.utc),
# created_by_user_id=created_by_user_id,
# stripe_session_id=stripe_session_id
# )
# db.session.add(payment)
# db.session.commit()


# return "OK", 200


@api.route("/stripe/webhook", methods=["POST"])
def stripe_webhook():
    payload = request.data
    sig_header = request.headers.get("Stripe-Signature")

    if not STRIPE_WEBHOOK_SECRET:
        return "Webhook secret not configured", 500

    try:
        event = stripe.Webhook.construct_event(
            payload=payload, sig_header=sig_header, secret=STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        return "Invalid payload", 400
    except stripe.error.SignatureVerificationError:
        return "Invalid signature", 400

    #  Evento principal de Checkout
    if event.get("type") == "checkout.session.completed":
        session = event["data"]["object"]
        md = session.get("metadata", {}) or {}

        stripe_session_id = session.get("id")  # ej: cs_test_...
        kind = md.get("kind")  # "appointment" | "direct"
        # string/decimal (lo guardas en Numeric)
        amount = md.get("amount")

        #  1) Anti-duplicados por sesión (Stripe puede reintentar)
        existing = Payment.query.filter_by(stripe_session_id=stripe_session_id).first()
        if existing:
            return "OK", 200

        #  2) Determinar appointment_id, payer_user_id, created_by_user_id
        appointment_id = None

        # payer_user_id: preferimos metadata payer_user_id (nuevo),
        # si no existe usamos client_id (compatibilidad con lo viejo)
        payer_user_id = None
        if md.get("payer_user_id"):
            try:
                payer_user_id = int(md.get("payer_user_id"))
            except Exception:
                payer_user_id = None
        elif md.get("client_id"):
            try:
                payer_user_id = int(md.get("client_id"))
            except Exception:
                payer_user_id = None

        # created_by_user_id:
        # - si viene barber_id lo usamos
        # - si no, dejamos 1 (admin por defecto)
        created_by_user_id = 1
        if md.get("barber_id"):
            try:
                created_by_user_id = int(md.get("barber_id"))
            except Exception:
                created_by_user_id = 1

        # appointment_id si es pago por cita
        if kind == "appointment" and md.get("appointment_id"):
            try:
                appointment_id = int(md.get("appointment_id"))
            except Exception:
                appointment_id = None

        #  3) Crear registro de pago (confirmado)
        payment = Payment(
            appointment_id=appointment_id,
            payer_user_id=payer_user_id,
            amount=amount,
            method="stripe",
            status="pagado",
            paid_at=datetime.now(timezone.utc),
            created_by_user_id=created_by_user_id,
            stripe_session_id=stripe_session_id,
        )
        db.session.add(payment)
        db.session.commit()

    return "OK", 200


# @api.route("/payments/me", methods=["GET"])
# def my_payments():
# verify_jwt_in_request()
# user_id = int(get_jwt_identity())
# pagos directos del usuario OR pagos ligados a citas donde el usuario es cliente
# payments = (
# Payment.query
# .outerjoin(Appointment, Payment.appointment_id == Appointment.appointment_id)
# .filter(
# (Payment.payer_user_id == user_id) |
# (Appointment.client_id == user_id)
# )
# .order_by(Payment.paid_at.desc())
# .limit(50)
# .all()
# )

# return jsonify({"ok": True, "data": [p.serialize() for p in payments]}), 200


@api.route("/payments/me", methods=["GET"])
def payments_me():
    verify_jwt_in_request()
    user_id = int(get_jwt_identity())

    # Pagos directos: Payment.payer_user_id == user_id
    # Pagos por cita: appointment.client_id == user_id (aunque payer_user_id sea null)
    payments = (
        Payment.query.outerjoin(
            Appointment, Payment.appointment_id == Appointment.appointment_id
        )
        .filter(or_(Payment.payer_user_id == user_id, Appointment.client_id == user_id))
        .order_by(Payment.paid_at.desc())
        .limit(50)
        .all()
    )

    return jsonify({"ok": True, "data": [p.serialize() for p in payments]}), 200


# @api.route("/appointments/<int:appointment_id>/complete-and-pay", methods=["POST"])
# def complete_and_pay(appointment_id):
# Aquí idealmente validarías que el usuario sea barbero/admin
# verify_jwt_in_request()

# appt = Appointment.query.get(appointment_id)
# if not appt:
# return jsonify({"ok": False, "message": "Cita no encontrada"}), 404

# appt.status = "completada"
# db.session.commit()

# service = appt.service
# amount_cents = int(float(service.price) * 100)

# session = stripe.checkout.Session.create(
# mode="payment",
# line_items=[{
# "price_data": {
# "currency": "usd",
# "product_data": {"name": f"{service.name} - Cita #{appt.appointment_id}"},
# "unit_amount": amount_cents
# },
# "quantity": 1
# }],
# success_url=f"{FRONTEND_URL}/#/pago-exitoso?session_id={{CHECKOUT_SESSION_ID}}",
# cancel_url=f"{FRONTEND_URL}/#/pago-cancelado",
# metadata={
# "kind": "appointment",
# "appointment_id": str(appt.appointment_id),
# "amount": str(service.price),
# "client_id": str(appt.client_id),
# "barber_id": str(appt.barber_id),
# }
# )

# return jsonify({"ok": True, "checkout_url": session.url}), 200


@api.route("/appointments/<int:appointment_id>/complete-and-pay", methods=["POST"])
def complete_and_pay(appointment_id):
    verify_jwt_in_request()
    claims = get_jwt()
    user_id = int(get_jwt_identity())

    # Seguridad mínima: solo barbero o admin
    if claims.get("role") not in ["barbero", "admin"] and not claims.get(
        "is_admin", False
    ):
        return jsonify({"ok": False, "message": "No autorizado"}), 403

    appt = Appointment.query.get(appointment_id)
    if not appt:
        return jsonify({"ok": False, "message": "Cita no encontrada"}), 404

    # Si es barbero, debe ser su cita
    if claims.get("role") == "barbero" and appt.barber_id != user_id:
        return (
            jsonify(
                {"ok": False, "message": "No puedes completar citas de otro barbero"}
            ),
            403,
        )

    # marcar completada
    appt.status = "completada"
    db.session.commit()

    service = appt.service
    amount_cents = int(float(service.price) * 100)

    session = stripe.checkout.Session.create(
        mode="payment",
        line_items=[
            {
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": f"{service.name} - Cita #{appt.appointment_id}"
                    },
                    "unit_amount": amount_cents,
                },
                "quantity": 1,
            }
        ],
        success_url=f"{FRONTEND_URL}/pago-exitoso?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{FRONTEND_URL}/pago-cancelado",
        metadata={
            "kind": "appointment",
            "appointment_id": str(appt.appointment_id),
            "amount": str(service.price),
            "payer_user_id": str(appt.client_id),  #  cliente es quien paga
            "barber_id": str(appt.barber_id),  #  barbero como created_by
        },
    )

    return jsonify({"ok": True, "checkout_url": session.url}), 200
