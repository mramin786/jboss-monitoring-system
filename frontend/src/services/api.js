// src/services/api.js
import axios from 'axios';

// This should match the URL where the backend API is accessible from the browser
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:5000/api';

class ApiService {
  constructor() {
    console.log("API URL:", API_BASE_URL);
    this.api = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    // Setup interceptors for token handling
    this.api.interceptors.request.use(
      (config) => {
        console.log("API Request:", config.method, config.url, config.data);
        const token = localStorage.getItem('authToken');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => {
        console.error("API Request Error:", error);
        return Promise.reject(error);
      }
    );
    
    // Handle responses and errors
    this.api.interceptors.response.use(
      (response) => {
        console.log("API Response:", response.status, response.data);
        return response;
      },
      (error) => {
        console.error("API Response Error:", error);
        console.error("Error details:", error.response?.data || error.message);
        if (error.response && error.response.status === 401) {
          // Token expired or invalid
          localStorage.removeItem('authToken');
          localStorage.removeItem('environment');
          window.location.href = '/login';
        }
        return Promise.reject(error.response ? error.response.data : error);
      }
    );
  }
  
  // Set auth token for requests
  setToken(token) {
    if (token) {
      this.api.defaults.headers.common.Authorization = `Bearer ${token}`;
    } else {
      delete this.api.defaults.headers.common.Authorization;
    }
  }
  
  // Auth endpoints
  async login(username, password, environment = 'non-production') {
    try {
      console.log("Login request:", { username, environment });
      const response = await this.api.post('/login', {
        username,
        password,
        environment
      });
      return response.data;
    } catch (error) {
      console.error("Login error:", error);
      throw error;
    }
  }
  
  // Host management endpoints
  async getHosts() {
    try {
      const response = await this.api.get('/hosts');
      return response.data.hosts;
    } catch (error) {
      console.error("Get hosts error:", error);
      throw error;
    }
  }
  
  async addHost(hostname) {
    try {
      console.log("Adding host:", hostname);
      
      // Format for "hostname port instance_name"
      if (typeof hostname === 'string' && hostname.includes(' ')) {
        const parts = hostname.trim().split(/\s+/);
        if (parts.length >= 3) {
          const host = parts[0];
          const port = parseInt(parts[1], 10);
          const name = parts.slice(2).join('_');
          
          console.log("Parsed host data:", { host, port, name });
          
          const response = await this.api.post('/hosts', {
            hostname: host,
            instances: [{ name, port }]
          });
          return response.data.host;
        }
      }
      
      // Simple hostname only
      console.log("Adding simple hostname:", hostname);
      const response = await this.api.post('/hosts', { hostname });
      return response.data.host;
    } catch (error) {
      console.error("Add host error:", error);
      throw error;
    }
  }
  
  async bulkAddHosts(hostsData) {
    try {
      console.log("Bulk adding hosts:", hostsData);
      const response = await this.api.post('/hosts/bulk', {
        hosts: hostsData
      });
      console.log("Bulk add response:", response.data);
      return response.data.hosts;
    } catch (error) {
      console.error("Bulk add hosts error:", error);
      throw error;
    }
  }
  
  async deleteHost(hostId) {
    try {
      const response = await this.api.delete(`/hosts/${hostId}`);
      return response.data;
    } catch (error) {
      throw error;
    }
  }
  
  async addInstance(hostId, name, port) {
    try {
      const response = await this.api.post(`/hosts/${hostId}/instances`, {
        name,
        port
      });
      return response.data.instance;
    } catch (error) {
      throw error;
    }
  }
  
  async deleteInstance(instanceId) {
    try {
      const response = await this.api.delete(`/instances/${instanceId}`);
      return response.data;
    } catch (error) {
      throw error;
    }
  }
  
  // Monitoring endpoints
  async getMonitoringStatus(jbossCredentials = null, saveReport = false) {
    try {
      let url = '/monitoring/status';
      const params = new URLSearchParams();
      
      if (saveReport) {
        params.append('save_report', 'true');
      }
      
      if (jbossCredentials) {
        params.append('username', jbossCredentials.username);
        params.append('password', jbossCredentials.password);
      }
      
      if (params.toString()) {
        url += `?${params.toString()}`;
      }
      
      const response = await this.api.get(url);
      return response.data.results;
    } catch (error) {
      throw error;
    }
  }
  
  async getInstanceStatus(instanceId, jbossCredentials = null) {
    try {
      let url = `/monitoring/instance/${instanceId}`;
      
      if (jbossCredentials) {
        url += `?username=${encodeURIComponent(jbossCredentials.username)}&password=${encodeURIComponent(jbossCredentials.password)}`;
      }
      
      const response = await this.api.get(url);
      return response.data.status;
    } catch (error) {
      throw error;
    }
  }
  
  // Report endpoints
  async getReports(limit = 5) {
    try {
      const response = await this.api.get(`/reports?limit=${limit}`);
      return response.data.reports;
    } catch (error) {
      throw error;
    }
  }
  
  async getReport(reportId) {
    try {
      const response = await this.api.get(`/reports/${reportId}`);
      return response.data.report;
    } catch (error) {
      throw error;
    }
  }
}

const apiService = new ApiService();
export default apiService;
