from flask import Flask

def create_app():
    """Create and configure an instance of the Flask application."""
    # When using an app factory like this, Flask uses the package name ('game_app')
    # to determine the root path. By default, it looks for the 'templates' and
    # 'static' folders inside that package directory.
    # Since these folders are in the project root (one level above the 'game_app'
    # package), we need to provide the correct relative paths to them.
    app = Flask(__name__, template_folder='../templates', static_folder='../static')

    # Import and initialize utilities
    from . import utils
    utils.calculate_startup_hash()

    # Import game logic. The game instance is created when the module is imported.
    from . import game_logic

    # Register Blueprints
    from . import routes
    app.register_blueprint(routes.main_routes)

    return app