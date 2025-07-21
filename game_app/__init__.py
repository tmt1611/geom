from flask import Flask

def create_app():
    """Create and configure an instance of the Flask application."""
    # When using an app factory like this, Flask uses the package name ('game_app')
    # to determine the root path. By default, it looks for the 'templates' and
    # 'static' folders inside that package directory.
    # Since these folders are in the project root (one level above the 'game_app'
    # package), we need to provide the correct relative paths to them.
    app = Flask(__name__, template_folder='../templates', static_folder='../static')

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