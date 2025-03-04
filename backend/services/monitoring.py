# services/monitoring.py
import logging
from typing import Dict, List, Any
from services.jboss_cli import JBossCLIService

logger = logging.getLogger(__name__)

class MonitoringService:
    """
    Service to coordinate JBoss monitoring activities
    """
    
    def __init__(self, cli_service: JBossCLIService):
        """
        Initialize with a JBossCLIService
        
        Args:
            cli_service: JBossCLIService instance for executing commands
        """
        self.cli_service = cli_service
    
    def check_host(self, host: Dict[str, Any], username: str = None, password: str = None) -> Dict[str, Any]:
        """
        Check the status of a host and all its instances
        
        Args:
            host: Host dictionary with instance information
            username: Username for authentication
            password: Password for authentication
            
        Returns:
            Dictionary with status information for the host and its instances
        """
        hostname = host.get("hostname")
        instances = host.get("instances", [])
        
        host_result = {
            "id": host.get("id"),
            "hostname": hostname,
            "instances": []
        }
        
        for instance in instances:
            instance_id = instance.get("id")
            instance_name = instance.get("name")
            port = instance.get("port")
            
            # Check instance status
            try:
                status = self.cli_service.check_instance_status(hostname, port, username, password)
                
                # If instance is online, check datasources and deployments
                if status.get("status") == "online":
                    datasources = self.cli_service.check_datasources(hostname, port, username, password)
                    deployments = self.cli_service.check_deployments(hostname, port, username, password)
                else:
                    datasources = []
                    deployments = []
                
                instance_result = {
                    "id": instance_id,
                    "name": instance_name,
                    "port": port,
                    "status": status.get("status"),
                    "statusMessage": status.get("message", ""),
                    "datasources": datasources,
                    "warFiles": deployments
                }
                
                host_result["instances"].append(instance_result)
                
            except Exception as e:
                logger.exception(f"Error checking instance {instance_name} on host {hostname}: {str(e)}")
                instance_result = {
                    "id": instance_id,
                    "name": instance_name,
                    "port": port,
                    "status": "error",
                    "statusMessage": str(e),
                    "datasources": [],
                    "warFiles": []
                }
                host_result["instances"].append(instance_result)
        
        return host_result
    
    def check_all_hosts(self, hosts: List[Dict[str, Any]], username: str = None, password: str = None) -> List[Dict[str, Any]]:
        """
        Check the status of multiple hosts
        
        Args:
            hosts: List of host dictionaries
            username: Username for authentication
            password: Password for authentication
            
        Returns:
            List of host status dictionaries
        """
        results = []
        
        for host in hosts:
            try:
                host_result = self.check_host(host, username, password)
                results.append(host_result)
            except Exception as e:
                logger.exception(f"Error checking host {host.get('hostname')}: {str(e)}")
                # Add error result
                results.append({
                    "id": host.get("id"),
                    "hostname": host.get("hostname"),
                    "status": "error",
                    "statusMessage": str(e),
                    "instances": []
                })
        
        return results
    
    def check_instance(self, host: Dict[str, Any], instance: Dict[str, Any], username: str = None, password: str = None) -> Dict[str, Any]:
        """
        Check the status of a specific instance
        
        Args:
            host: Host dictionary
            instance: Instance dictionary
            username: Username for authentication
            password: Password for authentication
            
        Returns:
            Dictionary with detailed status information for the instance
        """
        hostname = host.get("hostname")
        instance_id = instance.get("id")
        instance_name = instance.get("name")
        port = instance.get("port")
        
        try:
            # Check instance status
            status = self.cli_service.check_instance_status(hostname, port, username, password)
            
            # If instance is online, check datasources and deployments
            if status.get("status") == "online":
                datasources = self.cli_service.check_datasources(hostname, port, username, password)
                deployments = self.cli_service.check_deployments(hostname, port, username, password)
            else:
                datasources = []
                deployments = []
            
            result = {
                "host": {
                    "id": host.get("id"),
                    "hostname": hostname
                },
                "instance": {
                    "id": instance_id,
                    "name": instance_name,
                    "port": port
                },
                "status": status.get("status"),
                "statusMessage": status.get("message", ""),
                "datasources": datasources,
                "warFiles": deployments
            }
            
            return result
            
        except Exception as e:
            logger.exception(f"Error checking instance {instance_name} on host {hostname}: {str(e)}")
            return {
                "host": {
                    "id": host.get("id"),
                    "hostname": hostname
                },
                "instance": {
                    "id": instance_id,
                    "name": instance_name,
                    "port": port
                },
                "status": "error",
                "statusMessage": str(e),
                "datasources": [],
                "warFiles": []
            }
