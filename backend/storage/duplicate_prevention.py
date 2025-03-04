# Update file_storage.py to prevent duplicates

# In the add_host method, add duplicate checking:
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
        
        # Check for duplicate hostname and instance
        hostname = host_data.get("hostname", "")
        instances = host_data.get("instances", [])
        
        # Check if this exact host and instance combination already exists
        for existing_host in hosts:
            if existing_host.get("hostname") == hostname:
                for instance in instances:
                    instance_name = instance.get("name")
                    instance_port = instance.get("port")
                    duplicate_found = False
                    
                    for existing_instance in existing_host.get("instances", []):
                        if (existing_instance.get("name") == instance_name and 
                            existing_instance.get("port") == instance_port):
                            logger.info(f"Duplicate found: {hostname} {instance_port} {instance_name}")
                            duplicate_found = True
                            break
                            
                    if duplicate_found:
                        return existing_host  # Return existing host instead of creating duplicate
        
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
