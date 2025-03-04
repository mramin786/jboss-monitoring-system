// src/components/Dashboard.js
import React, { useState, useEffect, useCallback } from 'react';
import { 
  Server, Database, Package, Plus, Trash2, RefreshCw, 
  CheckCircle, XCircle, LogOut, AlertTriangle, AlertCircle, 
  Settings, ChevronDown, Info, FileText, Download
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import AddHostModal from './AddHostModal';
import axios from 'axios';
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

// JBoss credentials modal component
const CredentialsModal = ({ isOpen, onClose, onSubmit, title }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  
  const handleSubmit = (e) => {
    e.preventDefault();
    
    if (!username || !password) {
      setError('Please enter both username and password');
      return;
    }
    
    onSubmit({ username, password });
    onClose();
  };
  
  if (!isOpen) return null;
  
  return (
    <div className="fixed inset-0 bg-black bg-opacity-70 flex items-center justify-center p-4 z-50">
      <div className="bg-gray-800 rounded-lg w-full max-w-md">
        <div className="p-4 border-b border-gray-700 flex justify-between items-center">
          <h3 className="text-lg font-medium text-white">{title || 'JBoss Credentials'}</h3>
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
              <label className="block text-sm font-medium text-gray-300 mb-1">Username</label>
              <input 
                type="text" 
                className="w-full bg-gray-700 border border-gray-600 rounded-md py-2 px-3 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="JBoss username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
              />
            </div>
            
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-300 mb-1">Password</label>
              <input 
                type="password" 
                className="w-full bg-gray-700 border border-gray-600 rounded-md py-2 px-3 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="JBoss password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>
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
              className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-500 flex items-center"
            >
              Submit
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// Report list component
const ReportList = ({ reports, onViewReport }) => {
  if (!reports || reports.length === 0) {
    return (
      <div className="bg-gray-800 rounded-lg p-4 text-center text-gray-400">
        No reports available
      </div>
    );
  }
  
  // Function to format timestamp to local date/time in EST
  const formatTimestamp = (timestamp) => {
    if (!timestamp) return 'Unknown';
    
    const date = new Date(timestamp.replace(/_/g, ':'));
    // Format to EST timezone
    const options = { 
      timeZone: 'America/New_York',
      year: 'numeric', 
      month: 'short', 
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      hour12: true
    };
    
    return new Intl.DateTimeFormat('en-US', options).format(date) + ' EST';
  };
  
  return (
    <div className="bg-gray-800 rounded-lg overflow-hidden">
      <div className="bg-gray-700 p-3 border-b border-gray-600">
        <h3 className="font-medium text-white flex items-center">
          <FileText size={16} className="mr-2 text-blue-400" />
          Recent Reports
        </h3>
      </div>
      <div className="divide-y divide-gray-700">
        {reports.map(report => (
          <div key={report.id} className="p-3 hover:bg-gray-750 flex justify-between items-center">
            <div>
              <div className="font-medium">{report.environment} Report</div>
              <div className="text-sm text-gray-400">{formatTimestamp(report.timestamp)}</div>
            </div>
            <button
              className="px-3 py-1 bg-blue-600 hover:bg-blue-700 rounded flex items-center text-sm"
              onClick={() => onViewReport(report.id)}
            >
              <Download size={14} className="mr-1" />
              View
            </button>
          </div>
        ))}
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
  const [showCredentialsModal, setShowCredentialsModal] = useState(false);
  const [refreshInterval, setRefreshInterval] = useState(30); // seconds
  const [lastRefresh, setLastRefresh] = useState(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [expandedHosts, setExpandedHosts] = useState({});
  const [reports, setReports] = useState([]);
  const [currentReport, setCurrentReport] = useState(null);
  const [isGeneratingReport, setIsGeneratingReport] = useState(false);

  // Handle adding a host
  const handleAddHost = async (hostname, bulkLines) => {
    try {
      console.log("handleAddHost called", { hostname, bulkLines });
      
      // Force a data refresh regardless of what was added
      fetchData();
      
      return true;
    } catch (err) {
      console.error("Error in handleAddHost:", err);
      throw err;
    }
  };

  // Load hosts and status data
  const fetchData = useCallback(async (jbossCredentials = null) => {
    try {
      console.log("Fetching data...");
      setIsLoading(true);
      setError('');
      
      // Use a direct fetch to the backend to get hosts without authentication
      console.log("Fetching hosts directly from backend...");
      const response = await axios.get('http://localhost:5000/api/hosts/test-get?environment=non-production');
      console.log("Hosts response:", response.data);
      
      if (response.data.hosts) {
        console.log(`Found ${response.data.hosts.length} hosts:`, response.data.hosts);
        setHosts(response.data.hosts);
      } else {
        console.log("No hosts found in response");
        setHosts([]);
      }
      
      setLastRefresh(new Date());
      
      // Initialize expanded state for new hosts
      const newExpandedState = { ...expandedHosts };
      if (response.data.hosts) {
        response.data.hosts.forEach(host => {
          if (!(host.id in newExpandedState)) {
            newExpandedState[host.id] = true; // Default to expanded
          }
        });
      }
      setExpandedHosts(newExpandedState);
      
      // Fetch recent reports
      fetchReports();
      
    } catch (err) {
      console.error('Error fetching data:', err);
      setError('Failed to load monitoring data. Please try again.');
    } finally {
      setIsLoading(false);
    }
  }, [expandedHosts]);

  // Fetch reports
  const fetchReports = async () => {
    try {
      const reportData = await api.getReports(5);
      setReports(reportData);
    } catch (err) {
      console.error('Error fetching reports:', err);
      // Don't show error for reports failure
    }
  };

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

  // Handle JBoss credentials submission
  const handleCredentialsSubmit = (credentials) => {
    fetchData(credentials);
  };

  // Handle generating a report
  const handleGenerateReport = () => {
    setIsGeneratingReport(true);
    setShowCredentialsModal(true);
  };

  // Handle generating report with credentials
  const handleReportWithCredentials = async (credentials) => {
    try {
      setIsLoading(true);
      setError('');
      
      // Get status data and save as report
      const statusData = await api.getMonitoringStatus(credentials, true);
      
      // Fetch updated report list
      await fetchReports();
      
      setLastRefresh(new Date());
      
    } catch (err) {
      console.error('Error generating report:', err);
      setError('Failed to generate report. Please try again.');
    } finally {
      setIsLoading(false);
      setIsGeneratingReport(false);
    }
  };

  // Handle viewing a report
  const handleViewReport = async (reportId) => {
    try {
      const report = await api.getReport(reportId);
      setCurrentReport(report);
      // You could display the report in a modal or new page
      console.log("Report data:", report);
      
      // For now, just download it as JSON
      const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(report, null, 2));
      const downloadAnchorNode = document.createElement('a');
      downloadAnchorNode.setAttribute("href", dataStr);
      downloadAnchorNode.setAttribute("download", `report_${reportId}.json`);
      document.body.appendChild(downloadAnchorNode);
      downloadAnchorNode.click();
      downloadAnchorNode.remove();
      
    } catch (err) {
      console.error('Error fetching report:', err);
      alert('Failed to fetch report. Please try again.');
    }
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
                onClick={() => fetchData()}
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
          
          <div className="flex space-x-2">
            <button 
              className="flex items-center space-x-1 bg-green-600 hover:bg-green-700 px-3 py-2 rounded-md focus:outline-none focus:ring-2 focus:ring-green-500"
              onClick={() => setShowAddModal(true)}
            >
              <Plus size={16} />
              <span>Add Host</span>
            </button>
            
            <button 
              className="flex items-center space-x-1 bg-purple-600 hover:bg-purple-700 px-3 py-2 rounded-md focus:outline-none focus:ring-2 focus:ring-purple-500"
              onClick={handleGenerateReport}
              disabled={isGeneratingReport}
            >
              <FileText size={16} />
              <span>Generate Report</span>
            </button>
          </div>
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

        {/* Debug info */}
        <div className="mb-6 bg-blue-900/30 border border-blue-500 rounded-md p-4">
          <div className="flex">
            <Info className="text-blue-500 mr-3 flex-shrink-0" size={24} />
            <div>
              <p className="text-blue-100">Debug Info:</p>
              <p className="text-blue-100">Hosts count: {hosts ? hosts.length : 0}</p>
              <p className="text-blue-100">Hosts data: {JSON.stringify(hosts).slice(0, 100)}...</p>
            </div>
          </div>
        </div>

        {/* Main content grid */}
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 min-h-screen">
          {/* Left column - Hosts */}
          <div className="lg:col-span-3">
            {/* Host List */}
            <div className="grid gap-6">
              {hosts && hosts.length > 0 ? (
                hosts.map(host => (
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
                ))
              ) : (
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
            </div>
            
            {/* Loading indicator */}
            {isLoading && (
              <div className="flex justify-center items-center p-12">
                <svg className="animate-spin h-10 w-10 text-blue-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
              </div>
            )}
          </div>
          
          {/* Right column - Reports */}
          <div className="lg:col-span-1">
            <ReportList reports={reports} onViewReport={handleViewReport} />
          </div>
        </div>
      </div>

      {/* Add Host Modal */}
      <AddHostModal
        isOpen={showAddModal}
        onClose={() => setShowAddModal(false)}
        onAdd={handleAddHost}
      />
      
      {/* Credentials Modal */}
      <CredentialsModal
        isOpen={showCredentialsModal}
        onClose={() => {
          setShowCredentialsModal(false);
          setIsGeneratingReport(false);
        }}
        onSubmit={isGeneratingReport ? handleReportWithCredentials : handleCredentialsSubmit}
        title={isGeneratingReport ? "Enter JBoss Credentials for Report" : "Enter JBoss Credentials"}
      />
    </div>
  );
};

export default Dashboard;
