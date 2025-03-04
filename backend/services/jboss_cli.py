# services/jboss_cli.py
import subprocess
import json
import logging
import os
import random
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class JBossCLIService:
    """Service to execute JBoss CLI commands and parse results"""
    
    def __init__(self):
        # Default CLI path - update this with the actual path for your environment
        self.cli_path = os.environ.get("JBOSS_CLI_PATH", "/app/jboss/bin/jboss-cli.sh")
        
        # Check if CLI exists
        self.mock_mode = not os.path.isfile(self.cli_path)
        if self.mock_mode:
            logger.warning(f"JBoss CLI not found at {self.cli_path}, running in mock mode!")
        else:
            logger.info(f"Using JBoss CLI at: {self.cli_path}")
            
        # Default credentials (can be overridden during API calls)
        self.default_username = os.environ.get("JBOSS_USERNAME")
        self.default_password = os.environ.get("JBOSS_PASSWORD")
    
    def execute_command(self, host: str, port: int, command: str, 
                        username: Optional[str] = None, 
                        password: Optional[str] = None) -> Tuple[bool, Any]:
        """
        Execute a JBoss CLI command against a specific host and port
        
        Args:
            host: The hostname or IP address
            port: The management port number
            command: The CLI command to execute
            username: Optional username for authentication
            password: Optional password for authentication
            
        Returns:
            Tuple containing success status and command result
        """
        # If in mock mode, return simulated data
        if self.mock_mode:
            return self._mock_execute_command(host, port, command)
        
        # Use provided credentials or fall back to defaults
        username = username or self.default_username
        password = password or self.default_password
        
        try:
            # Build the CLI command
            cli_command = [
                self.cli_path,
                "-c",  # Connect mode
                f"--controller={host}:{port}",
                f"--command={command}"
            ]
            
            # Add credentials if provided
            if username and password:
                cli_command.extend([
                    f"--user={username}",
                    f"--password={password}"
                ])
            
            logger.info(f"Executing command on {host}:{port}")
            logger.debug(f"Command: {' '.join(cli_command)}")
            
            # Execute the command
            process = subprocess.Popen(
                cli_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            stdout, stderr = process.communicate()
            
            if process.returncode != 0:
                logger.error(f"Error executing JBoss CLI command: {stderr}")
                return False, stderr
            
            # Parse the output
            try:
                # Try to parse as JSON if possible
                return True, json.loads(stdout)
            except json.JSONDecodeError:
                # Otherwise return as string
                return True, stdout.strip()
                
        except Exception as e:
            logger.exception(f"Exception executing JBoss CLI command: {str(e)}")
            return False, str(e)
    
    def _mock_execute_command(self, host: str, port: int, command: str) -> Tuple[bool, Any]:
        """
        Simulate JBoss CLI command execution for mock mode
        
        Args:
            host: The hostname or IP address
            port: The management port number
            command: The CLI command to execute
            
        Returns:
            Tuple containing success status and simulated result
        """
        logger.info(f"MOCK MODE: Simulating command '{command}' on {host}:{port}")
        
        # Handle different command types
        if command == ":read-attribute(name=server-state)":
            # Based on host and port, randomly determine if server is online
            # Use a hash of the host+port to ensure consistent results
            is_online = hash(f"{host}:{port}") % 10 < 8  # 80% chance of being online
            if is_online:
                return True, {"outcome": "success", "result": "running"}
            else:
                return False, "Failed to connect to the controller"
                
        elif "/subsystem=datasources:read-resource" in command:
            # Return simulated datasources
            return True, {
                "outcome": "success",
                "result": {
                    "data-source": {
                        "MainDS": {
                            "jndi-name": "java:jboss/datasources/MainDS",
                            "driver-name": "mysql",
                            "enabled": True,
                        },
                        "ReportingDS": {
                            "jndi-name": "java:jboss/datasources/ReportingDS",
                            "driver-name": "oracle",
                            "enabled": True,
                        }
                    },
                    "xa-data-source": {
                        "TransactionDS": {
                            "jndi-name": "java:jboss/datasources/TransactionDS",
                            "driver-name": "postgresql",
                            "enabled": True,
                        }
                    }
                }
            }
            
        elif "test-connection-in-pool" in command:
            # Simulate datasource connection test
            # Extract the datasource name from the command
            ds_name = command.split("=")[1].split(":")[0]
            # Randomly determine if connection is successful, but weight towards success
            success = random.random() > 0.2  # 80% chance of success
            if success:
                return True, {"outcome": "success"}
            else:
                return False, {"outcome": "failed", "failure-description": f"Could not connect to {ds_name}"}
                
        elif "/deployment=*:read-resource" in command:
            # Return simulated deployments
            return True, {
                "outcome": "success",
                "result": {
                    "app.war": {
                        "runtime-name": "app.war",
                        "enabled": True,
                        "status": "OK"
                    },
                    "admin.war": {
                        "runtime-name": "admin.war",
                        "enabled": True,
                        "status": "OK"
                    },
                    "api.war": {
                        "runtime-name": "api.war",
                        "enabled": random.choice([True, False]),
                        "status": random.choice(["OK", "FAILED"])
                    }
                }
            }
            
        else:
            # Default response for unknown commands
            return True, {"outcome": "success", "result": "Command executed in mock mode"}
    
    def check_instance_status(self, host: str, port: int, 
                             username: Optional[str] = None, 
                             password: Optional[str] = None) -> Dict[str, Any]:
        """
        Check if a JBoss instance is running
        
        Args:
            host: The hostname or IP address
            port: The management port number
            username: Optional username for authentication
            password: Optional password for authentication
            
        Returns:
            Dictionary with status information
        """
        # Simple read-attribute command to check server status
        command = ":read-attribute(name=server-state)"
        success, result = self.execute_command(host, port, command, username, password)
        
        if not success:
            return {
                "status": "offline",
                "message": str(result)
            }
        
        # Check if result contains "running" to confirm server is up
        if isinstance(result, dict) and result.get("result") == "running":
            return {
                "status": "online",
                "message": "Server is running"
            }
        elif isinstance(result, str) and "running" in result:
            return {
                "status": "online",
                "message": "Server is running"
            }
        else:
            return {
                "status": "offline",
                "message": f"Unexpected response: {result}"
            }
    
    def check_datasources(self, host: str, port: int, 
                         username: Optional[str] = None, 
                         password: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Check all datasources status
        
        Args:
            host: The hostname or IP address
            port: The management port number
            username: Optional username for authentication
            password: Optional password for authentication
            
        Returns:
            List of dictionaries with datasource status information
        """
        # First, list all datasources
        command = "/subsystem=datasources:read-resource(recursive=true)"
        success, result = self.execute_command(host, port, command, username, password)
        
        if not success:
            logger.error(f"Failed to list datasources: {result}")
            return []
        
        datasources = []
        
        # Parse the result to extract datasource information
        try:
            if isinstance(result, dict) and "result" in result:
                # Extract XA and non-XA datasources
                xa_datasources = result["result"].get("xa-data-source", {})
                non_xa_datasources = result["result"].get("data-source", {})
                
                # Process non-XA datasources
                for ds_name, ds_info in non_xa_datasources.items():
                    # Test datasource connection
                    test_command = f"/subsystem=datasources/data-source={ds_name}:test-connection-in-pool"
                    test_success, test_result = self.execute_command(
                        host, port, test_command, username, password
                    )
                    
                    ds_status = {
                        "name": ds_name,
                        "type": "non-xa",
                        "jndi_name": ds_info.get("jndi-name", ""),
                        "driver": ds_info.get("driver-name", ""),
                        "enabled": ds_info.get("enabled", False),
                    }
                    
                    if test_success and isinstance(test_result, dict) and test_result.get("outcome") == "success":
                        ds_status["status"] = "connected"
                    else:
                        ds_status["status"] = "failed"
                    
                    datasources.append(ds_status)
                
                # Process XA datasources
                for ds_name, ds_info in xa_datasources.items():
                    # Test datasource connection
                    test_command = f"/subsystem=datasources/xa-data-source={ds_name}:test-connection-in-pool"
                    test_success, test_result = self.execute_command(
                        host, port, test_command, username, password
                    )
                    
                    ds_status = {
                        "name": ds_name,
                        "type": "xa",
                        "jndi_name": ds_info.get("jndi-name", ""),
                        "driver": ds_info.get("driver-name", ""),
                        "enabled": ds_info.get("enabled", False),
                    }
                    
                    if test_success and isinstance(test_result, dict) and test_result.get("outcome") == "success":
                        ds_status["status"] = "connected"
                    else:
                        ds_status["status"] = "failed"
                    
                    datasources.append(ds_status)
            
        except Exception as e:
            logger.exception(f"Error parsing datasource results: {str(e)}")
        
        return datasources
    
    def check_deployments(self, host: str, port: int, 
                         username: Optional[str] = None, 
                         password: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Check all deployments (WAR files) status
        
        Args:
            host: The hostname or IP address
            port: The management port number
            username: Optional username for authentication
            password: Optional password for authentication
            
        Returns:
            List of dictionaries with deployment status information
        """
        # Get all deployments
        command = "/deployment=*:read-resource(include-runtime=true)"
        success, result = self.execute_command(host, port, command, username, password)
        
        if not success:
            logger.error(f"Failed to list deployments: {result}")
            return []
        
        deployments = []
        
        # Parse the result to extract deployment information
        try:
            if isinstance(result, dict) and "result" in result:
                for deployment_name, deployment_info in result["result"].items():
                    # Only process WAR files
                    if deployment_name.endswith(".war") or deployment_name.endswith(".ear"):
                        deployment_status = {
                            "name": deployment_name,
                            "runtime_name": deployment_info.get("runtime-name", ""),
                            "enabled": deployment_info.get("enabled", False),
                        }
                        
                        # Check deployment status
                        if deployment_info.get("enabled", False) and deployment_info.get("status") == "OK":
                            deployment_status["status"] = "deployed"
                        else:
                            deployment_status["status"] = "failed"
                        
                        deployments.append(deployment_status)
            
        except Exception as e:
            logger.exception(f"Error parsing deployment results: {str(e)}")
        
        return deployments
