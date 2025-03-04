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
