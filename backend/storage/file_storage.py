# storage/file_storage.py
import os
import json
import logging
from typing import List, Dict, Any, Optional
import threading

logger = logging.getLogger(__name__)

class FileStorage:
    """
    Simple file-based storage system for managing hosts and instances.
    Uses JSON files to store configuration data.
    """
    
    def __init__(self, storage_dir: str = "data"):
        """
        Initialize the file storage
        
        Args:
            storage_dir: Directory to store the data files
        """
        self.storage_dir = storage_dir
        self.prod_file = os.path.join(storage_dir, "production_hosts.json")
        self.nonprod_file = os.path.join(storage_dir, "nonproduction_hosts.json")
        self.lock = threading.Lock()
        
        # Create storage directory if it doesn't exist
        if not os.path.exists(storage_dir):
            os.makedirs(storage_dir)
        
        # Initialize files if they don't exist
        for file_path in [self.prod_file, self.nonprod_file]:
            if not os.path.exists(file_path):
                with open(file_path, "w") as f:
                    json.dump([], f)
    
    def _get_file_path(self, environment: str) -> str:
        """Get the appropriate file path based on environment"""
        return self.prod_file if environment.lower() == "production" else self.nonprod_file
    
    def _read_data(self, environment: str) -> List[Dict[str, Any]]:
        """Read data from the appropriate JSON file"""
        file_path = self._get_file_path(environment)
        try:
            with open(file_path, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading data file {file_path}: {str(e)}")
            return []
    
    def _write_data(self, environment: str, data: List[Dict[str, Any]]) -> bool:
        """Write data to the appropriate JSON file"""
        file_path = self._get_file_path(environment)
        try:
            with open(file_path, "w") as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error writing to data file {file_path}: {str(e)}")
            return False
    
    def get_all_hosts(self, environment: str) -> List[Dict[str, Any]]:
        """
        Get all hosts for a specific environment
        
        Args:
            environment: "production" or "non-production"
            
        Returns:
            List of host dictionaries
        """
        return self._read_data(environment)
    
    def add_host(self, host_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add a new host
        
        Args:
            host_data: Dictionary containing host information
            
        Returns:
            The added host with generated ID
        """
        environment = host_data.get("environment", "non-production")
        
        with self.lock:
            hosts = self._read_data(environment)
            
            # Generate a new ID
            host_id = 1
            if hosts:
                host_id = max(host.get("id", 0) for host in hosts) + 1
            
            # Create new host with ID
            new_host = {
                "id": host_id,
                "hostname": host_data.get("hostname", ""),
                "instances": host_data.get("instances", [])
            }
            
            # Generate IDs for instances if needed
            for i, instance in enumerate(new_host["instances"]):
                if "id" not in instance:
                    instance_id = 1
                    if hosts:
                        # Find highest instance ID across all hosts
                        instance_id = 1
                        for h in hosts:
                            for inst in h.get("instances", []):
                                if inst.get("id", 0) >= instance_id:
                                    instance_id = inst.get("id", 0) + 1
                    
                    instance["id"] = instance_id
            
            # Add host to the list
            hosts.append(new_host)
            
            # Write updated data
            self._write_data(environment, hosts)
            
            return new_host
    
    def add_instance(self, host_id: int, instance_data: Dict[str, Any], environment: str) -> Optional[Dict[str, Any]]:
        """
        Add a new instance to an existing host
        
        Args:
            host_id: ID of the host
            instance_data: Dictionary containing instance information
            environment: "production" or "non-production"
            
        Returns:
            The added instance with generated ID, or None if host not found
        """
        with self.lock:
            hosts = self._read_data(environment)
            
            # Find the host
            host_index = next((i for i, h in enumerate(hosts) if h.get("id") == host_id), None)
            if host_index is None:
                return None
            
            # Generate a new instance ID
            instance_id = 1
            for h in hosts:
                for inst in h.get("instances", []):
                    if inst.get("id", 0) >= instance_id:
                        instance_id = inst.get("id", 0) + 1
            
            # Create new instance with ID
            new_instance = {
                "id": instance_id,
                "name": instance_data.get("name", ""),
                "port": instance_data.get("port", 9990)
            }
            
            # Add instance to the host
            if "instances" not in hosts[host_index]:
                hosts[host_index]["instances"] = []
            
            hosts[host_index]["instances"].append(new_instance)
            
            # Write updated data
            self._write_data(environment, hosts)
            
            return new_instance
    
    def delete_host(self, host_id: int, environment: str) -> bool:
        """
        Delete a host
        
        Args:
            host_id: ID of the host to delete
            environment: "production" or "non-production"
            
        Returns:
            True if successful, False otherwise
        """
        with self.lock:
            hosts = self._read_data(environment)
            
            # Find and remove the host
            for i, host in enumerate(hosts):
                if host.get("id") == host_id:
                    del hosts[i]
                    return self._write_data(environment, hosts)
            
            return False
    
    def delete_instance(self, instance_id: int, environment: str) -> bool:
        """
        Delete an instance
        
        Args:
            instance_id: ID of the instance to delete
            environment: "production" or "non-production"
            
        Returns:
            True if successful, False otherwise
        """
        with self.lock:
            hosts = self._read_data(environment)
            
            # Find and remove the instance
            for host in hosts:
                instances = host.get("instances", [])
                for i, instance in enumerate(instances):
                    if instance.get("id") == instance_id:
                        del instances[i]
                        return self._write_data(environment, hosts)
            
            return False
    
    def get_host_by_id(self, host_id: int, environment: str) -> Optional[Dict[str, Any]]:
        """
        Get a host by ID
        
        Args:
            host_id: ID of the host
            environment: "production" or "non-production"
            
        Returns:
            Host dictionary or None if not found
        """
        hosts = self._read_data(environment)
        
        for host in hosts:
            if host.get("id") == host_id:
                return host
        
        return None
    
    def get_instance_by_id(self, instance_id: int, environment: str) -> Optional[Dict[str, Any]]:
        """
        Get an instance by ID
        
        Args:
            instance_id: ID of the instance
            environment: "production" or "non-production"
            
        Returns:
            Tuple containing (host, instance) or (None, None) if not found
        """
        hosts = self._read_data(environment)
        
        for host in hosts:
            for instance in host.get("instances", []):
                if instance.get("id") == instance_id:
                    return (host, instance)
        
        return (None, None)
    
    def bulk_add_hosts(self, bulk_data: List[str], environment: str) -> List[Dict[str, Any]]:
        """
        Add multiple hosts and instances from bulk data
        
        Args:
            bulk_data: List of strings in format "hostname:port:instance"
            environment: "production" or "non-production"
            
        Returns:
            List of added/updated hosts
        """
        with self.lock:
            hosts = self._read_data(environment)
            updated_hosts = []
            
            for entry in bulk_data:
                # Parse entry (hostname:port:instance)
                parts = entry.split(":")
                if len(parts) < 3:
                    continue
                
                hostname, port_str, instance_name = parts[0], parts[1], parts[2]
                
                try:
                    port = int(port_str)
                except ValueError:
                    continue
                
                # Find if host already exists
                host = next((h for h in hosts if h.get("hostname") == hostname), None)
                
                if host:
                    # Host exists, add instance if it doesn't exist
                    instance_exists = any(
                        i.get("name") == instance_name and i.get("port") == port 
                        for i in host.get("instances", [])
                    )
                    
                    if not instance_exists:
                        # Generate a new instance ID
                        instance_id = 1
                        for h in hosts:
                            for inst in h.get("instances", []):
                                if inst.get("id", 0) >= instance_id:
                                    instance_id = inst.get("id", 0) + 1
                        
                        # Add new instance
                        if "instances" not in host:
                            host["instances"] = []
                        
                        host["instances"].append({
                            "id": instance_id,
                            "name": instance_name,
                            "port": port
                        })
                        
                        if host not in updated_hosts:
                            updated_hosts.append(host)
                else:
                    # Create new host with instance
                    host_id = 1
                    if hosts:
                        host_id = max(h.get("id", 0) for h in hosts) + 1
                    
                    instance_id = 1
                    if hosts:
                        for h in hosts:
                            for inst in h.get("instances", []):
                                if inst.get("id", 0) >= instance_id:
                                    instance_id = inst.get("id", 0) + 1
                    
                    new_host = {
                        "id": host_id,
                        "hostname": hostname,
                        "instances": [{
                            "id": instance_id,
                            "name": instance_name,
                            "port": port
                        }]
                    }
                    
                    hosts.append(new_host)
                    updated_hosts.append(new_host)
            
            # Write updated data
            self._write_data(environment, hosts)
            
            return updated_hosts
