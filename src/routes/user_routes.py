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
