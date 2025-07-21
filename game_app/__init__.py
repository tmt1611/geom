from flask import Flask

def create_app():
    """Create and configure an instance of the Flask application."""
    app = Flask(__name__)

    # Initialize game state and file watcher
    from . import game_logic
    from . import utils
    
    # This needs to be done before the first request,
    # so doing it at app creation is fine.
    game_logic.init_game_state()
    utils.calculate_startup_hash()

    # Register Blueprints
    from . import routes
    app.register_blueprint(routes.main_routes)

    return app