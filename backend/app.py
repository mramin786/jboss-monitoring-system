# app.py - Main Flask application
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
import os
import logging
from datetime import datetime, timedelta
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
    
    # JBoss credentials
    JBOSS_USERNAME = os.environ.get('JBOSS_USERNAME', '')
    JBOSS_PASSWORD = os.environ.get('JBOSS_PASSWORD', '')
    
    # Storage configuration
    STORAGE_DIR = os.environ.get('STORAGE_DIR', 'data')

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)
CORS(app, resources={r"/api/*": {"origins": "*"}})
jwt = JWTManager(app)

# Initialize services
file_storage = FileStorage(app.config['STORAGE_DIR'])
jboss_cli_service = JBossCLIService()
monitoring_service = MonitoringService(jboss_cli_service)

def log_request():
    """Log detailed request information for debugging"""
    logger.info(f"Received {request.method} request to {request.path}")
    logger.info(f"Headers: {dict(request.headers)}")
    if request.is_json:
        logger.info(f"JSON data: {request.json}")
    else:
        logger.info(f"Form data: {request.form}")
        logger.info(f"Query params: {request.args}")
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
    log_request()
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
    log_request()
    """Get all hosts for the current environment"""
    current_user = get_jwt_identity()
    environment = current_user.get('environment', 'non-production')
    
    hosts = file_storage.get_all_hosts(environment)
    return jsonify(hosts=hosts), 200

@app.route('/api/hosts', methods=['POST'])
@jwt_required()
def add_host():
    log_request()
    """Add a new host"""
    current_user = get_jwt_identity()
    environment = current_user.get('environment', 'non-production')
    
    if not request.is_json:
        return jsonify({"error": "Missing JSON in request"}), 400
    
    logger.info(f"Received host data: {request.json}")
    
    host_data = request.json
    host_data['environment'] = environment
    
    # Make sure hostname is a string, not an object
    if isinstance(host_data.get('hostname'), dict):
        hostname = host_data.get('hostname', {}).get('hostname', '')
        host_data['hostname'] = hostname
    
    host = file_storage.add_host(host_data)
    return jsonify(host=host), 201

@app.route('/api/hosts/bulk', methods=['POST'])
@jwt_required()
def add_hosts_bulk():
    log_request()
    log_request()
    """Add multiple hosts in bulk"""
    current_user = get_jwt_identity()
    environment = current_user.get('environment', 'non-production')
    
    if not request.is_json:
        return jsonify({"error": "Missing JSON in request"}), 400
    
    bulk_data = request.json.get('hosts', [])
    logger.info(f"Received bulk hosts data: {bulk_data}")
    
    # Process bulk data
    hosts = file_storage.bulk_add_hosts(bulk_data, environment)
    return jsonify(hosts=hosts), 201

@app.route('/api/hosts/<int:host_id>', methods=['DELETE'])
@jwt_required()
def delete_host(host_id):
    log_request()
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
    log_request()
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
    log_request()
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
    
    # Get JBoss credentials
    jboss_username = request.args.get('username', app.config['JBOSS_USERNAME'])
    jboss_password = request.args.get('password', app.config['JBOSS_PASSWORD'])
    
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
                jboss_username, 
                jboss_password
            )
            
            # If instance is online, check datasources and deployments
            if status.get("status") == "online":
                datasources = jboss_cli_service.check_datasources(
                    host.get("hostname"), 
                    port, 
                    jboss_username, 
                    jboss_password
                )
                
                deployments = jboss_cli_service.check_deployments(
                    host.get("hostname"), 
                    port, 
                    jboss_username, 
                    jboss_password
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
    
    # Save this as a report if requested
    save_report = request.args.get('save_report', 'false').lower() == 'true'
    if save_report:
        report_data = {
            "results": results,
            "created_by": username,
            "timestamp": datetime.now().isoformat()
        }
        report_metadata = file_storage.save_report(report_data, environment)
        return jsonify(results=results, report=report_metadata), 200
    
    return jsonify(results=results), 200

@app.route('/api/monitoring/instance/<int:instance_id>', methods=['GET'])
@jwt_required()
def get_instance_status(instance_id):
    """Get detailed status of a specific instance"""
    current_user = get_jwt_identity()
    environment = current_user.get('environment', 'non-production')
    
    # Get JBoss credentials
    jboss_username = request.args.get('username', app.config['JBOSS_USERNAME'])
    jboss_password = request.args.get('password', app.config['JBOSS_PASSWORD'])
    
    # Find the instance
    host_instance = file_storage.get_instance_by_id(instance_id, environment)
    if not host_instance or not host_instance[0] or not host_instance[1]:
        return jsonify({"error": "Instance not found"}), 404
    
    host, instance = host_instance
    
    # Check instance status
    status = jboss_cli_service.check_instance_status(
        host.get("hostname"), 
        instance.get("port"), 
        jboss_username, 
        jboss_password
    )
    
    # If instance is online, check datasources and deployments
    if status.get("status") == "online":
        datasources = jboss_cli_service.check_datasources(
            host.get("hostname"), 
            instance.get("port"), 
            jboss_username, 
            jboss_password
        )
        
        deployments = jboss_cli_service.check_deployments(
            host.get("hostname"), 
            instance.get("port"), 
            jboss_username, 
            jboss_password
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

# Report routes
@app.route('/api/reports', methods=['GET'])
@jwt_required()
def get_reports():
    """Get a list of recent reports"""
    current_user = get_jwt_identity()
    environment = current_user.get('environment', 'non-production')
    
    # Get recent reports
    limit = int(request.args.get('limit', 5))
    reports = file_storage.get_recent_reports(environment, limit)
    
    return jsonify(reports=reports), 200

@app.route('/api/reports/<report_id>', methods=['GET'])
@jwt_required()
def get_report(report_id):
    """Get a specific report"""
    report = file_storage.get_report(report_id)
    
    if not report:
        return jsonify({"error": "Report not found"}), 404
    
    return jsonify(report=report), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

# Test endpoint - no authentication required
@app.route('/api/test', methods=['POST'])
def test_endpoint():
    """Test endpoint for debugging"""
    log_request()
    
    try:
        if request.is_json:
            data = request.json
            return jsonify({"message": "Test successful", "received": data}), 200
        else:
            return jsonify({"error": "Missing JSON in request"}), 400
    except Exception as e:
        logger.error(f"Error in test endpoint: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

# Simple host add endpoint without authentication for testing
@app.route('/api/hosts/test-add', methods=['POST'])
def test_add_host():
    """Add a host without authentication (for testing only)"""
    try:
        logger.info(f"Received test add host request: {request.method} to {request.path}")
        
        if request.is_json:
            host_data = request.json
            logger.info(f"Test add host JSON data: {host_data}")
            
            # Use non-production environment
            environment = "non-production"
            host_data['environment'] = environment
            
            # Process the host data
            hostname = host_data.get('hostname', '')
            logger.info(f"Test hostname: {hostname}, type: {type(hostname)}")
            
            if not hostname:
                logger.error("Test missing hostname")
                return jsonify({"error": "Hostname is required"}), 400
                
            # Create the host
            host = file_storage.add_host(host_data)
            return jsonify({"success": True, "host": host}), 201
        else:
            logger.error("Test request is not JSON")
            return jsonify({"error": "Missing JSON in request"}), 400
    except Exception as e:
        logger.error(f"Error in test add host: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": f"Failed to add host: {str(e)}"}), 500

# Test endpoint to get hosts without authentication
@app.route('/api/hosts', methods=['GET'])
def get_hosts_without_auth():
    """Get all hosts without authentication"""
    try:
        logger.info(f"Received get hosts request: {request.method} to {request.path}")
        logger.info(f"Query params: {request.args}")
        
        environment = request.args.get('environment', 'non-production')
        logger.info(f"Getting hosts for environment: {environment}")
        
        hosts = file_storage.get_all_hosts(environment)
        logger.info(f"Found {len(hosts)} hosts")
        
        # Debug output of hosts
        for host in hosts:
            logger.info(f"Host: {host.get('hostname')}, ID: {host.get('id')}, Instances: {len(host.get('instances', []))}")
        
        return jsonify(hosts=hosts), 200
    except Exception as e:
        logger.error(f"Error getting hosts: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": f"Failed to get hosts: {str(e)}"}), 500
# Test endpoint to get hosts without authentication
@app.route('/api/hosts/test-get', methods=['GET'])
def test_get_hosts():
    """Get all hosts without authentication"""
    try:
        logger.info(f"Received test get hosts request: {request.method} to {request.path}")
        
        environment = request.args.get('environment', 'non-production')
        logger.info(f"Getting hosts for environment: {environment}")
        
        hosts = file_storage.get_all_hosts(environment)
        logger.info(f"Found {len(hosts)} hosts")
        
        # Debug output of hosts
        for host in hosts:
            logger.info(f"Host: {host.get('hostname')}, ID: {host.get('id')}, Instances: {len(host.get('instances', []))}")
        
        return jsonify(hosts=hosts), 200
    except Exception as e:
        logger.error(f"Error getting hosts: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": f"Failed to get hosts: {str(e)}"}), 500

# Test endpoint to delete a host without authentication
@app.route('/api/hosts/test-delete/<int:host_id>', methods=['DELETE'])
def test_delete_host(host_id):
    """Delete a host without authentication"""
    try:
        logger.info(f"Received test delete host request: {request.method} to {request.path}")
        logger.info(f"Deleting host with ID: {host_id}")
        
        environment = request.args.get('environment', 'non-production')
        
        success = file_storage.delete_host(host_id, environment)
        if success:
            return jsonify({"message": "Host deleted successfully"}), 200
        else:
            return jsonify({"error": "Host not found"}), 404
    except Exception as e:
        logger.error(f"Error deleting host: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": f"Failed to delete host: {str(e)}"}), 500

# Test endpoint to check for duplicates before adding a host
@app.route('/api/hosts/test-check-duplicate', methods=['POST'])
def test_check_duplicate():
    """Check if a host+instance combination already exists"""
    try:
        logger.info(f"Received test check duplicate request: {request.method} to {request.path}")
        
        if request.is_json:
            data = request.json
            logger.info(f"Check duplicate JSON data: {data}")
            
            hostname = data.get('hostname', '')
            port = data.get('port', 0)
            instance_name = data.get('instance_name', '')
            environment = data.get('environment', 'non-production')
            
            # Read the hosts
            hosts = file_storage.get_all_hosts(environment)
            
            # Check for duplicate
            for host in hosts:
                if host.get('hostname') == hostname:
                    for instance in host.get('instances', []):
                        if instance.get('name') == instance_name and instance.get('port') == port:
                            return jsonify({
                                "duplicate": True,
                                "message": f"Host {hostname} with instance {instance_name} on port {port} already exists."
                            }), 200
            
            return jsonify({"duplicate": False}), 200
        else:
            return jsonify({"error": "Missing JSON in request"}), 400
    except Exception as e:
        logger.error(f"Error checking duplicate: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({"error": str(e)}), 500
