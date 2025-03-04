  _mock_execute_command(host, port, command) {
    logger.info(`MOCK MODE: Simulating command '${command}' on ${host}:${port}`);
    
    // Handle different command types
    if (command == ":read-attribute(name=server-state)") {
      // Always show as online for testing
      return [true, {"outcome": "success", "result": "running"}];
    } 
    else if (command.includes("/subsystem=datasources:read-resource")) {
      // Always return some datasources for testing
      return [true, {
        "outcome": "success",
        "result": {
          "data-source": {
            "MainDS": {
              "jndi-name": "java:jboss/datasources/MainDS",
              "driver-name": "mysql",
              "enabled": true,
            },
            "ReportingDS": {
              "jndi-name": "java:jboss/datasources/ReportingDS",
              "driver-name": "oracle",
              "enabled": true,
            }
          },
          "xa-data-source": {
            "TransactionDS": {
              "jndi-name": "java:jboss/datasources/TransactionDS",
              "driver-name": "postgresql",
              "enabled": true,
            }
          }
        }
      }];
    }
    else if (command.includes("test-connection-in-pool")) {
      // For testing, always return success
      return [true, {"outcome": "success"}];
    }
    else if (command.includes("/deployment=*:read-resource")) {
      // For testing, always return some deployments
      return [true, {
        "outcome": "success",
        "result": {
          "app.war": {
            "runtime-name": "app.war",
            "enabled": true,
            "status": "OK"
          },
          "admin.war": {
            "runtime-name": "admin.war",
            "enabled": true,
            "status": "OK"
          }
        }
      }];
    }
    else {
      // Default response for unknown commands
      return [true, {"outcome": "success", "result": "Command executed in mock mode"}];
    }
  }
