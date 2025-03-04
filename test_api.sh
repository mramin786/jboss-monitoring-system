#!/bin/bash
echo "Testing adding a host..."
curl -X POST http://localhost:5000/api/test \
  -H "Content-Type: application/json" \
  -d '{"hostname": "test-host", "instances": [{"name": "test-instance", "port": 9990}]}'
echo
