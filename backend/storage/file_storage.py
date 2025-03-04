# storage/file_storage.py
import os
import json
import logging
from typing import List, Dict, Any, Optional
import threading
from datetime import datetime

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
        self.reports_dir = os.path.join(storage_dir, "reports")
        self.lock = threading.Lock()
        
        # Create storage directory if it doesn't exist
        if not os.path.exists(storage_dir):
            os.makedirs(storage_dir)
        
        # Create reports directory if it doesn't exist
        if not os.path.exists(self.reports_dir):
            os.makedirs(self.reports_dir)
        
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
            logger.info(f"Reading data from {file_path}")
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
                logger.info(f"Writing {len(data)} hosts to {file_path}")
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
        
        # Check if hostname includes port and instance (space-separated)
        hostname = host_data.get("hostname", "")
        logger.info(f"Adding host with data: {host_data}, hostname: {hostname}")
        
        if isinstance(hostname, str) and ' ' in hostname:
            parts = hostname.strip().split()
            if len(parts) >= 3:
                # Format is "hostname port instance_name"
                hostname = parts[0]
                try:
                    port = int(parts[1])
                    instance_name = ' '.join(parts[2:])
                    
                    # Update host data
                    host_data["hostname"] = hostname
                    if "instances" not in host_data:
                        host_data["instances"] = []
                    
                    # Add instance
                    host_data["instances"].append({
                        "name": instance_name,
                        "port": port
                    })
                except ValueError:
                    logger.error(f"Invalid port number in hostname: {hostname}")
        
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
            bulk_data: List of strings in format "hostname port instance_name"
            environment: "production" or "non-production"
            
        Returns:
            List of added/updated hosts
        """
        with self.lock:
            hosts = self._read_data(environment)
            updated_hosts = []
            
            for entry in bulk_data:
                # Parse entry (hostname port instance_name)
                logger.info(f"Processing bulk entry: {entry}")
                parts = entry.strip().split()
                if len(parts) < 3:
                    logger.warning(f"Skipping invalid entry (not enough parts): {entry}")
                    continue
                
                hostname = parts[0]
                try:
                    port = int(parts[1])
                except ValueError:
                    logger.warning(f"Invalid port number in entry: {entry}")
                    continue
                    
                instance_name = ' '.join(parts[2:])
                
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
    
    def save_report(self, report_data: Dict[str, Any], environment: str) -> Dict[str, Any]:
        """
        Save a monitoring report
        
        Args:
            report_data: Report data to save
            environment: "production" or "non-production"
            
        Returns:
            Report metadata including ID and timestamp
        """
        # Generate timestamp in EST
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        report_id = f"{environment}_{timestamp}"
        
        # Create report metadata
        metadata = {
            "id": report_id,
            "timestamp": timestamp,
            "environment": environment,
            "host_count": len(report_data),
            "created_by": report_data.get("created_by", "system")
        }
        
        # Add metadata to report
        report_data["metadata"] = metadata
        
        # Save report to file
        report_path = os.path.join(self.reports_dir, f"{report_id}.json")
        try:
            with open(report_path, "w") as f:
                json.dump(report_data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving report: {str(e)}")
            return None
        
        return metadata
    
    def get_recent_reports(self, environment: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get recent reports for an environment
        
        Args:
            environment: "production" or "non-production"
            limit: Maximum number of reports to return
            
        Returns:
            List of report metadata
        """
        reports = []
        
        # Find report files for the environment
        for filename in os.listdir(self.reports_dir):
            if filename.startswith(environment) and filename.endswith(".json"):
                try:
                    with open(os.path.join(self.reports_dir, filename), "r") as f:
                        report = json.load(f)
                        if "metadata" in report:
                            reports.append(report["metadata"])
                except Exception as e:
                    logger.error(f"Error reading report {filename}: {str(e)}")
        
        # Sort by timestamp (newest first) and limit
        reports.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return reports[:limit]
    
    def get_report(self, report_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific report by ID
        
        Args:
            report_id: ID of the report
            
        Returns:
            Report data or None if not found
        """
        report_path = os.path.join(self.reports_dir, f"{report_id}.json")
        
        if not os.path.exists(report_path):
            return None
        
        try:
            with open(report_path, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading report {report_id}: {str(e)}")
            return None
