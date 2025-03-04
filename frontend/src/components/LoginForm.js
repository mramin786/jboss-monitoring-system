// src/components/LoginForm.js
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Server, Shield, AlertCircle } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

const LoginForm = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [environment, setEnvironment] = useState('non-production');
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  
  const { login } = useAuth();
  const navigate = useNavigate();
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    
    if (!username || !password) {
      setError('Please enter both username and password');
      return;
    }
    
    setIsLoading(true);
    try {
      await login(username, password, environment);
      navigate('/');
    } catch (err) {
      console.error('Login error:', err);
      setError(err.error || 'Failed to login. Please check your credentials.');
    } finally {
      setIsLoading(false);
    }
  };
  
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-900 px-4">
      <div className="max-w-md w-full bg-gray-800 rounded-lg shadow-lg overflow-hidden">
        <div className="bg-gray-700 p-6">
          <div className="flex justify-center mb-3">
            <Server size={48} className="text-blue-400" />
          </div>
          <h2 className="text-center text-2xl font-bold text-white">
            JBoss Monitoring System
          </h2>
          <p className="mt-2 text-center text-gray-400">
            Sign in to access the monitoring dashboard
          </p>
        </div>
        
        <form className="p-6 space-y-4" onSubmit={handleSubmit}>
          {error && (
            <div className="bg-red-900/30 border border-red-500 rounded-md p-3 flex items-start">
              <AlertCircle className="text-red-500 mr-2 flex-shrink-0 mt-0.5" size={18} />
              <p className="text-red-100 text-sm">{error}</p>
            </div>
          )}
          
          <div>
            <label htmlFor="environment" className="block text-sm font-medium text-gray-300 mb-1">
              Environment
            </label>
            <div className="flex space-x-4">
              <label className="flex items-center cursor-pointer">
                <input
                  type="radio"
                  className="form-radio text-blue-500"
                  name="environment"
                  value="non-production"
                  checked={environment === 'non-production'}
                  onChange={() => setEnvironment('non-production')}
                />
                <span className="ml-2 text-gray-300">Non-Production</span>
              </label>
              <label className="flex items-center cursor-pointer">
                <input
                  type="radio"
                  className="form-radio text-blue-500"
                  name="environment"
                  value="production"
                  checked={environment === 'production'}
                  onChange={() => setEnvironment('production')}
                />
                <span className="ml-2 text-gray-300">Production</span>
              </label>
            </div>
          </div>
          
          <div>
            <label htmlFor="username" className="block text-sm font-medium text-gray-300 mb-1">
              Username
            </label>
            <input
              id="username"
              type="text"
              className="w-full bg-gray-700 border border-gray-600 rounded-md py-2 px-3 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Enter your username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />
          </div>
          
          <div>
            <label htmlFor="password" className="block text-sm font-medium text-gray-300 mb-1">
              Password
            </label>
            <input
              id="password"
              type="password"
              className="w-full bg-gray-700 border border-gray-600 rounded-md py-2 px-3 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Enter your password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          
          <div>
            <button
              type="submit"
              className="w-full bg-blue-600 hover:bg-blue-700 text-white py-2 px-4 rounded-md flex justify-center items-center transition duration-150 disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={isLoading}
            >
              {isLoading ? (
                <>
                  <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Signing in...
                </>
              ) : (
                <>
                  <Shield className="mr-2" size={18} />
                  Sign in
                </>
              )}
            </button>
          </div>
        </form>
        
        <div className="px-6 pb-6 text-center">
          <p className="text-sm text-gray-400">
            Default credentials - Non-Production: nonprod_admin / nonprod_password
          </p>
          <p className="text-sm text-gray-400 mt-1">
            Production: prod_admin / prod_password
          </p>
        </div>
      </div>
    </div>
  );
};

export default LoginForm;
