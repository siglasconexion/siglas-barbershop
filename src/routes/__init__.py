from flask import Blueprint


def register_blueprints(app):
    from src.routes.person_routes import bp as person_bp

    # from src.routes.person_type_routes import bp as person_type_bp
    # from src.routes.barber_type_routes import bp as barber_type_bp
    # from src.routes.barber_routes import bp as barber_bp
    # from src.routes.client_routes import bp as client_bp
    # from src.routes.appointment_status_routes import bp as appointment_status_bp
    # from src.routes.service_type_routes import bp as service_type_bp
    # from src.routes.service_routes import bp as service_bp
    # from src.routes.appointment_routes import bp as appointment_bp
    # from src.routes.email_routes import bp as email_bp
    # from src.routes.telephone_type_routes import bp as telephone_type_bp
    # from src.routes.telephone_routes import bp as telephone_bp
    # from src.routes.social_media_type_routes import bp as social_media_type_bp
    # from src.routes.social_media_routes import bp as social_media_bp
    # from src.routes.role_type_routes import bp as role_type_bp
    # from src.routes.user_routes import bp as user_bp
    # from src.routes.payment_type_routes import bp as payment_type_bp
    # from src.routes.payment_routes import bp as payment_bp

    app.register_blueprint(person_bp, url_prefix="/api/person")
    # app.register_blueprint(person_type_bp, url_prefix="/api/person_type")
    # app.register_blueprint(barber_type_bp, url_prefix="/api/barber_type")
    # app.register_blueprint(barber_bp, url_prefix="/api/barber")
    # app.register_blueprint(client_bp, url_prefix="/api/client")
    # app.register_blueprint(appointment_status_bp, url_prefix="/api/#appointment_status")
    # app.register_blueprint(service_type_bp, url_prefix="/api/service_type")
    # app.register_blueprint(service_bp, url_prefix="/api/service")
    # app.register_blueprint(appointment_bp, url_prefix="/api/appointment")
    # app.register_blueprint(email_bp, url_prefix="/api/email")
    # app.register_blueprint(telephone_type_bp, url_prefix="/api/telephone_type")
    # app.register_blueprint(telephone_bp, url_prefix="/api/telephone")
    # app.register_blueprint(social_media_type_bp, url_prefix="/api/social_media_type")
    # app.register_blueprint(social_media_bp, url_prefix="/api/social_media")
    # app.register_blueprint(role_type_bp, url_prefix="/api/role_type")
    # app.register_blueprint(user_bp, url_prefix="/api/user")
    # app.register_blueprint(payment_type_bp, url_prefix="/api/payment_type")
    # app.register_blueprint(payment_bp, url_prefix="/api/payment")
