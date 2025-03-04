// src/context/AuthContext.js
import React, { createContext, useState, useContext, useEffect } from 'react';
import api from '../services/api';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
  const [currentUser, setCurrentUser] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [token, setToken] = useState(localStorage.getItem('authToken') || '');
  const [environment, setEnvironment] = useState(localStorage.getItem('environment') || 'non-production');
  const [loading, setLoading] = useState(true);

  // Check if token exists on startup
  useEffect(() => {
    const checkAuth = async () => {
      const storedToken = localStorage.getItem('authToken');
      const storedEnvironment = localStorage.getItem('environment');
      
      if (storedToken) {
        setToken(storedToken);
        setEnvironment(storedEnvironment || 'non-production');
        setIsAuthenticated(true);
        
        // Setup token for API requests
        api.setToken(storedToken);
        
        // Fetch user data or validate token if needed
        try {
          // Could add token validation here if needed
          setIsAuthenticated(true);
        } catch (error) {
          console.error('Token validation failed:', error);
          logout();
        }
      }
      
      setLoading(false);
    };
    
    checkAuth();
  }, []);

  const login = async (username, password, env = 'non-production') => {
    try {
      setLoading(true);
      const response = await api.login(username, password, env);
      
      const { access_token, environment } = response;
      
      // Store token and user info
      localStorage.setItem('authToken', access_token);
      localStorage.setItem('environment', environment);
      
      // Update state
      setToken(access_token);
      setEnvironment(environment);
      setCurrentUser({ username, environment });
      setIsAuthenticated(true);
      
      // Setup token for API requests
      api.setToken(access_token);
      
      setLoading(false);
      return true;
    } catch (error) {
      console.error('Login failed:', error);
      setLoading(false);
      throw error;
    }
  };

  const logout = () => {
    // Clear storage and state
    localStorage.removeItem('authToken');
    localStorage.removeItem('environment');
    setToken('');
    setCurrentUser(null);
    setIsAuthenticated(false);
    api.setToken('');
  };

  const switchEnvironment = async (newEnvironment, username, password) => {
    try {
      // Need to re-authenticate with the new environment
      await login(username, password, newEnvironment);
      return true;
    } catch (error) {
      console.error('Environment switch failed:', error);
      throw error;
    }
  };

  const value = {
    currentUser,
    token,
    environment,
    isAuthenticated,
    loading,
    login,
    logout,
    switchEnvironment
  };

  return (
    <AuthContext.Provider value={value}>
      {!loading && children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
