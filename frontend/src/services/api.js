// src/services/api.js
import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:5000/api';

class ApiService {
  constructor() {
    this.api = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    // Setup interceptors for token handling
    this.api.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('authToken');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );
    
    // Handle 401 responses
    this.api.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response && error.response.status === 401) {
          // Token expired or invalid
          localStorage.removeItem('authToken');
          localStorage.removeItem('environment');
          window.location.href = '/login';
        }
        return Promise.reject(error);
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
      const response = await this.api.post('/login', {
        username,
        password,
        environment
      });
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : error;
    }
  }
  
  // Host management endpoints
  async getHosts() {
    try {
      const response = await this.api.get('/hosts');
      return response.data.hosts;
    } catch (error) {
      throw error.response ? error.response.data : error;
    }
  }
  
  async addHost(hostname, instances = []) {
    try {
      const response = await this.api.post('/hosts', {
        hostname,
        instances
      });
      return response.data.host;
    } catch (error) {
      throw error.response ? error.response.data : error;
    }
  }
  
  async bulkAddHosts(hostsData) {
    try {
      const response = await this.api.post('/hosts/bulk', {
        hosts: hostsData
      });
      return response.data.hosts;
    } catch (error) {
      throw error.response ? error.response.data : error;
    }
  }
  
  async deleteHost(hostId) {
    try {
      const response = await this.api.delete(`/hosts/${hostId}`);
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : error;
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
      throw error.response ? error.response.data : error;
    }
  }
  
  async deleteInstance(instanceId) {
    try {
      const response = await this.api.delete(`/instances/${instanceId}`);
      return response.data;
    } catch (error) {
      throw error.response ? error.response.data : error;
    }
  }
  
  // Monitoring endpoints
  async getMonitoringStatus() {
    try {
      const response = await this.api.get('/monitoring/status');
      return response.data.results;
    } catch (error) {
      throw error.response ? error.response.data : error;
    }
  }
  
  async getInstanceStatus(instanceId) {
    try {
      const response = await this.api.get(`/monitoring/instance/${instanceId}`);
      return response.data.status;
    } catch (error) {
      throw error.response ? error.response.data : error;
    }
  }
}

const apiService = new ApiService();
export default apiService;
