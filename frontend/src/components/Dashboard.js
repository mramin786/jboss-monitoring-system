// src/components/Dashboard.js
import React, { useState, useEffect, useCallback } from 'react';
import { 
  Server, Database, Package, Plus, Trash2, RefreshCw, 
  CheckCircle, XCircle, LogOut, AlertTriangle, AlertCircle, 
  Settings, ChevronDown, Info
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';

// Component for displaying the status indicator
const StatusIndicator = ({ status }) => {
  if (status === 'online' || status === 'connected' || status === 'deployed') {
    return <CheckCircle className="text-green-500" size={18} />;
  } else if (status === 'warning') {
    return <AlertTriangle className="text-yellow-500" size={18} />;
  }
  return <XCircle className="text-red-500" size={18} />;
};

// Modal component for adding hosts
const AddHostModal = ({ isOpen, onClose, onAdd }) => {
  const [hostname, setHostname] = useState('');
  const [bulkInput, setBulkInput] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [error, setError] = useState('');
  
  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setIsProcessing(true);
    
    try {
      if (hostname) {
        // Add single host
        await api.addHost(hostname);
      } else if (bulkInput) {
        // Process bulk input
        const lines = bulkInput.split('\n').filter(line => line.trim() !== '');
        await api.bulkAddHosts(lines);
      } else {
        setError('Please enter either a hostname or bulk data');
        setIsProcessing(false);
        return;
      }
      
      onAdd();
      onClose();
    } catch (err) {
      console.error('Error adding host:', err);
      setError(err.error || 'Failed to add host. Please check your input.');
    } finally {
      setIsProcessing(false);
    }
  };
  
  if (!isOpen) return null;
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-70 flex items-center justify-center p-4 z-50">
      <div className="bg-gray-800 rounded-lg w-full max-w-lg">
        <div className="p-4 border-b border-gray-700 flex justify-between items-center">
          <h3 className="text-lg font-medium text-white">Add New Host</h3>
          <button 
            className="text-gray-400 hover:text-white"
            onClick={onClose}
          >
            &times;
          </button>
        </div>
        
        <form onSubmit={handleSubmit}>
          <div className="p-4">
            {error && (
              <div className="mb-4 bg-red-900/30 border border-red-500 rounded-md p-3">
                <p className="text-red-100 text-sm">{error}</p>
              </div>
            )}
            
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-300 mb-1">Host Name</label>
              <input 
                type="text" 
                className="w-full bg-gray-700 border border-gray-600 rounded-md py-2 px-3 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="e.g., jboss-server.example.com"
                value={hostname}
                onChange={(e) => setHostname(e.target.value)}
              />
            </div>
            
            <div className="mb-1">
              <label className="block text-sm font-medium text-gray-300 mb-1">
                OR Bulk Add (hostname:port:instance)
              </label>
              <textarea 
                className="w-full bg-gray-700 border border-gray-600 rounded-md py-2 px-3 text-white focus:outline-none focus:ring-2 focus:ring-blue-500 h-32"
                placeholder="server1.example.com:8080:instance1&#10;server1.example.com:8081:instance2&#10;server2.example.com:8080:instance1"
                value={bulkInput}
                onChange={(e) => setBulkInput(e.target.value)}
              />
            </div>
            <p className="text-xs text-gray-400 mt-1 mb-4">
              Enter one entry per line in format: hostname:port:instance
            </p>
          </div>
          
          <div className="p-4 border-t border-gray-700 flex justify-end space-x-3">
            <button 
              type="button"
              className="px-4 py-2 bg-gray-700 text-white rounded-md hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-gray-500"
              onClick={onClose}
            >
              Cancel
            </button>
            <button 
              type="submit"
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500 flex items-center disabled:opacity-50"
              disabled={isProcessing}
            >
              {isProcessing ? (
                <>
                  <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Processing...
                </>
              ) : (
                <>
                  <Plus size={18} className="mr-1" />
                  Add Host
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// Main Dashboard component
const Dashboard = () => {
  const { currentUser, environment, logout } = useAuth();
  const [hosts, setHosts] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [showAddModal, setShowAddModal] = useState(false);
  const [refreshInterval, setRefreshInterval] = useState(30); // seconds
  const [lastRefresh, setLastRefresh] = useState(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [expandedHosts, setExpandedHosts] = useState({});

  // Load hosts and status data
  const fetchData = useCallback(async () => {
    try {
      setIsLoading(true);
      setError('');
      
      const statusData = await api.getMonitoringStatus();
      setHosts(statusData);
      setLastRefresh(new Date());
      
      // Initialize expanded state for new hosts
      const newExpandedState = { ...expandedHosts };
      statusData.forEach(host => {
        if (!(host.id in newExpandedState)) {
          newExpandedState[host.id] = true; // Default to expanded
        }
      });
      setExpandedHosts(newExpandedState);
      
    } catch (err) {
      console.error('Error fetching data:', err);
      setError('Failed to load monitoring data. Please try again.');
    } finally {
      setIsLoading(false);
    }
  }, [expandedHosts]);

  // Initial data load
  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Set up auto-refresh
  useEffect(() => {
    let intervalId;
    
    if (autoRefresh && refreshInterval > 0) {
      intervalId = setInterval(() => {
        fetchData();
      }, refreshInterval * 1000);
    }
    
    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [autoRefresh, refreshInterval, fetchData]);

  // Handle deleting a host
  const handleDeleteHost = async (hostId) => {
    if (!window.confirm('Are you sure you want to delete this host?')) return;
    
    try {
      await api.deleteHost(hostId);
      // Refresh data after deletion
      fetchData();
    } catch (err) {
      console.error('Error deleting host:', err);
      alert('Failed to delete host. Please try again.');
    }
  };

  // Toggle host expansion
  const toggleHostExpansion = (hostId) => {
    setExpandedHosts(prev => ({
      ...prev,
      [hostId]: !prev[hostId]
    }));
  };

  // Calculate time since last refresh
  const getTimeSinceRefresh = () => {
    if (!lastRefresh) return 'Never';
    
    const seconds = Math.floor((new Date() - lastRefresh) / 1000);
    
    if (seconds < 60) return `${seconds} seconds ago`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)} minutes ago`;
    return `${Math.floor(seconds / 3600)} hours ago`;
  };

  return (
    <div className="min-h-screen bg-gray-900 text-gray-100">
      {/* Header */}
      <header className="bg-gray-800 p-4 shadow-md">
        <div className="container mx-auto flex justify-between items-center">
          <div className="flex items-center space-x-2">
            <Server className="text-blue-400" />
            <h1 className="text-xl font-bold">JBoss Monitoring Dashboard</h1>
          </div>
          
          <div className="flex items-center space-x-4">
            <div className="flex items-center text-sm text-gray-400">
              <span className="mr-1">Environment:</span>
              <span className={`font-medium ${environment.toLowerCase() === 'production' ? 'text-red-400' : 'text-green-400'}`}>
                {environment}
              </span>
            </div>
            
            <div className="flex items-center space-x-2">
              <button
                className="flex items-center space-x-1 bg-blue-600 hover:bg-blue-700 px-3 py-1 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                onClick={fetchData}
                disabled={isLoading}
              >
                <RefreshCw size={16} className={isLoading ? "animate-spin" : ""} />
                <span>Refresh</span>
              </button>
              
              <button
                className="text-gray-400 hover:text-white p-1 rounded-full focus:outline-none focus:ring-2 focus:ring-gray-500"
                onClick={logout}
                title="Logout"
              >
                <LogOut size={18} />
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="container mx-auto p-4">
        {/* Dashboard controls */}
        <div className="mb-6 flex flex-wrap justify-between items-center gap-4">
          <div className="flex items-center text-sm text-gray-400">
            <Info size={14} className="mr-1" />
            <span>Last refresh: {getTimeSinceRefresh()}</span>
            
            <div className="ml-4 flex items-center">
              <label className="flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  className="form-checkbox text-blue-500"
                  checked={autoRefresh}
                  onChange={(e) => setAutoRefresh(e.target.checked)}
                />
                <span className="ml-1">Auto-refresh</span>
              </label>
              
              {autoRefresh && (
                <select
                  className="ml-2 bg-gray-800 border border-gray-700 rounded text-sm p-1"
                  value={refreshInterval}
                  onChange={(e) => setRefreshInterval(Number(e.target.value))}
                >
                  <option value="10">10s</option>
                  <option value="30">30s</option>
                  <option value="60">1m</option>
                  <option value="300">5m</option>
                </select>
              )}
            </div>
          </div>
          
          <button 
            className="flex items-center space-x-1 bg-green-600 hover:bg-green-700 px-3 py-2 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
            onClick={() => setShowAddModal(true)}
          >
            <Plus size={16} />
            <span>Add Host</span>
          </button>
        </div>
        
        {/* Error message */}
        {error && (
          <div className="mb-6 bg-red-900/30 border border-red-500 rounded-md p-4">
            <div className="flex">
              <AlertCircle className="text-red-500 mr-3 flex-shrink-0" size={24} />
              <p className="text-red-100">{error}</p>
            </div>
          </div>
        )}

        {/* Host List */}
        <div className="grid gap-6">
          {hosts.map(host => (
            <div key={host.id} className="bg-gray-800 rounded-lg shadow-lg overflow-hidden">
              <div 
                className="bg-gray-700 p-4 flex justify-between items-center cursor-pointer"
                onClick={() => toggleHostExpansion(host.id)}
              >
                <div className="flex items-center space-x-2">
                  <Server className="text-blue-400" />
                  <h2 className="font-bold">{host.hostname}</h2>
                  <ChevronDown 
                    size={18} 
                    className={`text-gray-400 transition-transform ${expandedHosts[host.id] ? 'rotate-180' : ''}`}
                  />
                </div>
                <button 
                  className="text-red-400 hover:text-red-300 p-1"
                  onClick={(e) => {
                    e.stopPropagation();
                    handleDeleteHost(host.id);
                  }}
                >
                  <Trash2 size={18} />
                </button>
              </div>
              
              {/* Instances */}
              {expandedHosts[host.id] && (
                <div className="divide-y divide-gray-700">
                  {host.instances && host.instances.length > 0 ? (
                    host.instances.map(instance => (
                      <div key={instance.id} className="p-4">
                        <div className="flex items-center space-x-2 mb-3">
                          <div className={`w-3 h-3 rounded-full ${
                            instance.status === 'online' ? 'bg-green-500' : 'bg-red-500'
                          }`}></div>
                          <h3 className="font-medium text-lg">{instance.name} (Port: {instance.port})</h3>
                        </div>
                        
                        {/* Instance details */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-2">
                          {/* Datasources */}
                          <div className="bg-gray-750 bg-opacity-50 rounded p-3">
                            <div className="flex items-center space-x-2 mb-2 text-blue-300">
                              <Database size={16} />
                              <h4 className="font-medium">Datasources</h4>
                            </div>
                            {instance.datasources && instance.datasources.length > 0 ? (
                              <ul className="space-y-1">
                                {instance.datasources.map((ds, idx) => (
                                  <li key={ds.id || idx} className="flex justify-between items-center">
                                    <span>{ds.name}</span>
                                    <StatusIndicator status={ds.status} />
                                  </li>
                                ))}
                              </ul>
                            ) : (
                              <p className="text-gray-400 text-sm">No datasources available</p>
                            )}
                          </div>
                          
                          {/* WAR Files */}
                          <div className="bg-gray-750 bg-opacity-50 rounded p-3">
                            <div className="flex items-center space-x-2 mb-2 text-purple-300">
                              <Package size={16} />
                              <h4 className="font-medium">WAR Files</h4>
                            </div>
                            {instance.warFiles && instance.warFiles.length > 0 ? (
                              <ul className="space-y-1">
                                {instance.warFiles.map((war, idx) => (
                                  <li key={war.id || idx} className="flex justify-between items-center">
                                    <span>{war.name}</span>
                                    <StatusIndicator status={war.status} />
                                  </li>
                                ))}
                              </ul>
                            ) : (
                              <p className="text-gray-400 text-sm">No WAR files available</p>
                            )}
                          </div>
                        </div>
                      </div>
                    ))
                  ) : (
                    <div className="p-4 text-center text-gray-400">
                      No instances configured for this host
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Empty state */}
        {!isLoading && hosts.length === 0 && (
          <div className="bg-gray-800 rounded-lg p-8 text-center">
            <AlertCircle className="mx-auto text-yellow-400 mb-3" size={48} />
            <h3 className="text-xl font-medium mb-2">No hosts configured</h3>
            <p className="text-gray-400 mb-4">Add hosts to begin monitoring your JBoss servers</p>
            <button 
              className="bg-blue-600 hover:bg-blue-700 px-4 py-2 rounded-md inline-flex items-center focus:outline-none focus:ring-2 focus:ring-blue-500"
              onClick={() => setShowAddModal(true)}
            >
              <Plus size={16} className="mr-2" />
              <span>Add Host</span>
            </button>
          </div>
        )}
        
        {/* Loading indicator */}
        {isLoading && hosts.length === 0 && (
          <div className="flex justify-center items-center p-12">
            <svg className="animate-spin h-10 w-10 text-blue-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
          </div>
        )}
      </div>

      {/* Add Host Modal */}
      <AddHostModal
        isOpen={showAddModal}
        onClose={() => setShowAddModal(false)}
        onAdd={fetchData}
      />
    </div>
  );
};

export default Dashboard;
