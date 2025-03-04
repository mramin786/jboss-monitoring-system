from flask import Flask, request, jsonify, redirect
from flask_cors import CORS
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
import os
import logging
from datetime import timedelta
from storage.file_storage import FileStorage
from services.jboss_cli import JBossCLIService
from services.monitoring import MonitoringService

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'dev-jwt-secret')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=12)
    
    # Environment credentials
    PROD_USERNAME = os.environ.get('PROD_USERNAME', 'prod_admin')
    PROD_PASSWORD = os.environ.get('PROD_PASSWORD', 'prod_password')
    NONPROD_USERNAME = os.environ.get('NONPROD_USERNAME', 'nonprod_admin')
    NONPROD_PASSWORD = os.environ.get('NONPROD_PASSWORD', 'nonprod_password')
    
    # Storage configuration
    STORAGE_DIR = os.environ.get('STORAGE_DIR', 'data')

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)
CORS(app)
jwt = JWTManager(app)

# Initialize services
file_storage = FileStorage(app.config['STORAGE_DIR'])
jboss_cli_service = JBossCLIService()
monitoring_service = MonitoringService(jboss_cli_service)

# Root route
@app.route('/')
def index():
    """Redirect to frontend UI or show API information"""
    return jsonify({
        "name": "JBoss Monitoring API",
        "message": "Please access the UI at http://localhost:3000 or use the API endpoints at /api/*"
    })

# Authentication routes
@app.route('/api/login', methods=['POST'])
def login():
    """Authenticate user and return JWT token"""
    if not request.is_json:
        return jsonify({"error": "Missing JSON in request"}), 400
    
    username = request.json.get('username', None)
    password = request.json.get('password', None)
    environment = request.json.get('environment', 'non-production')
    
    if not username or not password:
        return jsonify({"error": "Missing username or password"}), 400
    
    # Validate credentials based on environment
    if environment.lower() == 'production':
        valid = username == app.config['PROD_USERNAME'] and password == app.config['PROD_PASSWORD']
    else:
        valid = username == app.config['NONPROD_USERNAME'] and password == app.config['NONPROD_PASSWORD']
    
    if not valid:
        return jsonify({"error": "Invalid credentials"}), 401
    
    # Create access token
    access_token = create_access_token(identity={
        'username': username,
        'environment': environment
    })
    
    return jsonify(access_token=access_token, environment=environment), 200

# Host management routes
@app.route('/api/hosts', methods=['GET'])
@jwt_required()
def get_hosts():
    """Get all hosts for the current environment"""
    current_user = get_jwt_identity()
    environment = current_user.get('environment', 'non-production')
    
    hosts = file_storage.get_all_hosts(environment)
    return jsonify(hosts=hosts), 200

@app.route('/api/hosts', methods=['POST'])
@jwt_required()
def add_host():
    """Add a new host"""
    current_user = get_jwt_identity()
    environment = current_user.get('environment', 'non-production')
    
    if not request.is_json:
        return jsonify({"error": "Missing JSON in request"}), 400
    
    host_data = request.json
    host_data['environment'] = environment
    
    host = file_storage.add_host(host_data)
    return jsonify(host=host), 201

@app.route('/api/hosts/bulk', methods=['POST'])
@jwt_required()
def add_hosts_bulk():
    """Add multiple hosts in bulk"""
    current_user = get_jwt_identity()
    environment = current_user.get('environment', 'non-production')
    
    if not request.is_json:
        return jsonify({"error": "Missing JSON in request"}), 400
    
    bulk_data = request.json.get('hosts', [])
    
    # Process bulk data
    hosts = file_storage.bulk_add_hosts(bulk_data, environment)
    return jsonify(hosts=hosts), 201

@app.route('/api/hosts/<int:host_id>', methods=['DELETE'])
@jwt_required()
def delete_host(host_id):
    """Delete a host"""
    current_user = get_jwt_identity()
    environment = current_user.get('environment', 'non-production')
    
    success = file_storage.delete_host(host_id, environment)
    if success:
        return jsonify({"message": "Host deleted successfully"}), 200
    else:
        return jsonify({"error": "Host not found"}), 404

@app.route('/api/hosts/<int:host_id>/instances', methods=['POST'])
@jwt_required()
def add_instance(host_id):
    """Add a new instance to a host"""
    current_user = get_jwt_identity()
    environment = current_user.get('environment', 'non-production')
    
    if not request.is_json:
        return jsonify({"error": "Missing JSON in request"}), 400
    
    instance_data = request.json
    instance = file_storage.add_instance(host_id, instance_data, environment)
    
    if instance:
        return jsonify(instance=instance), 201
    else:
        return jsonify({"error": "Host not found"}), 404

@app.route('/api/instances/<int:instance_id>', methods=['DELETE'])
@jwt_required()
def delete_instance(instance_id):
    """Delete an instance"""
    current_user = get_jwt_identity()
    environment = current_user.get('environment', 'non-production')
    
    success = file_storage.delete_instance(instance_id, environment)
    if success:
        return jsonify({"message": "Instance deleted successfully"}), 200
    else:
        return jsonify({"error": "Instance not found"}), 404

# Monitoring routes
@app.route('/api/monitoring/status', methods=['GET'])
@jwt_required()
def get_monitoring_status():
    """Get status of all hosts and instances"""
    current_user = get_jwt_identity()
    environment = current_user.get('environment', 'non-production')
    username = current_user.get('username')
    
    # Get password based on environment
    if environment.lower() == 'production':
        password = app.config['PROD_PASSWORD']
    else:
        password = app.config['NONPROD_PASSWORD']
    
    # Get all hosts for the environment
    hosts = file_storage.get_all_hosts(environment)
    
    # Initialize results structure
    results = []
    
    # Check each host and its instances
    for host in hosts:
        host_result = {
            "id": host.get("id"),
            "hostname": host.get("hostname"),
            "instances": []
        }
        
        for instance in host.get("instances", []):
            instance_id = instance.get("id")
            instance_name = instance.get("name")
            port = instance.get("port")
            
            # Check instance status
            status = jboss_cli_service.check_instance_status(
                host.get("hostname"), 
                port, 
                username, 
                password
            )
            
            # If instance is online, check datasources and deployments
            if status.get("status") == "online":
                datasources = jboss_cli_service.check_datasources(
                    host.get("hostname"), 
                    port, 
                    username, 
                    password
                )
                
                deployments = jboss_cli_service.check_deployments(
                    host.get("hostname"), 
                    port, 
                    username, 
                    password
                )
            else:
                datasources = []
                deployments = []
            
            instance_result = {
                "id": instance_id,
                "name": instance_name,
                "port": port,
                "status": status.get("status"),
                "datasources": datasources,
                "warFiles": deployments
            }
            
            host_result["instances"].append(instance_result)
        
        results.append(host_result)
    
    return jsonify(results=results), 200

@app.route('/api/monitoring/instance/<int:instance_id>', methods=['GET'])
@jwt_required()
def get_instance_status(instance_id):
    """Get detailed status of a specific instance"""
    current_user = get_jwt_identity()
    environment = current_user.get('environment', 'non-production')
    username = current_user.get('username')
    
    # Get password based on environment
    if environment.lower() == 'production':
        password = app.config['PROD_PASSWORD']
    else:
        password = app.config['NONPROD_PASSWORD']
    
    # Find the instance
    host_instance = file_storage.get_instance_by_id(instance_id, environment)
    if not host_instance or not host_instance[0] or not host_instance[1]:
        return jsonify({"error": "Instance not found"}), 404
    
    host, instance = host_instance
    
    # Check instance status
    status = jboss_cli_service.check_instance_status(
        host.get("hostname"), 
        instance.get("port"), 
        username, 
        password
    )
    
    # If instance is online, check datasources and deployments
    if status.get("status") == "online":
        datasources = jboss_cli_service.check_datasources(
            host.get("hostname"), 
            instance.get("port"), 
            username, 
            password
        )
        
        deployments = jboss_cli_service.check_deployments(
            host.get("hostname"), 
            instance.get("port"), 
            username, 
            password
        )
    else:
        datasources = []
        deployments = []
    
    result = {
        "host": {
            "id": host.get("id"),
            "hostname": host.get("hostname")
        },
        "instance": {
            "id": instance.get("id"),
            "name": instance.get("name"),
            "port": instance.get("port")
        },
        "status": status.get("status"),
        "datasources": datasources,
        "warFiles": deployments
    }
    
    return jsonify(status=result), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
