"""Main Flask application"""
import logging
from datetime import datetime
from flask import Flask, jsonify
from flask_cors import CORS

from shared.config import settings
from shared.logger import setup_logging, get_logger

from domains.auth.routes import auth_bp
from domains.pods.routes import pods_bp
from domains.discord.routes import discord_bp
from domains.ssh.routes import ssh_bp
from domains.files.routes import files_bp

# Setup logging
setup_logging()
logger = get_logger(__name__)

# Create Flask app
app = Flask(__name__)
CORS(app)

# Log all requests
@app.before_request
def log_request():
    from flask import request
    logger.info(f'{request.method} {request.path} - {request.remote_addr}')

# Register blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(pods_bp)
app.register_blueprint(discord_bp)
app.register_blueprint(ssh_bp)
app.register_blueprint(files_bp)

# Health check endpoint
@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'service': 'godfather-backend',
        'timestamp': datetime.utcnow().isoformat()
    })

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f'Internal server error: {error}', exc_info=True)
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Validate settings
    try:
        settings.validate()
        logger.info('Configuration validated successfully')
    except ValueError as e:
        logger.error(f'Configuration error: {e}')
        exit(1)
    
    # Run app
    logger.info('Starting Godfather Backend')
    app.run(host='0.0.0.0', port=5000, debug=False)
