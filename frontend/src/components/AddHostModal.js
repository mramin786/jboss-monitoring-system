import React, { useState } from 'react';
import { Plus } from 'lucide-react';
import axios from 'axios';

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
      console.log("Submit with hostname:", hostname, "bulk:", bulkInput);
      
      // Use this variable to track if any hosts were added
      let hostsAdded = false;
      
      if (hostname.trim()) {
        // Add single host directly using test endpoint
        console.log("Adding single host:", hostname);
        
        // Parse the hostname if it contains spaces
        let payload = { hostname };
        
        if (hostname.includes(' ')) {
          const parts = hostname.split(/\s+/);
          if (parts.length >= 3) {
            const host = parts[0];
            const port = parseInt(parts[1], 10);
            const name = parts.slice(2).join('_');
            
            console.log(`Parsed: host=${host}, port=${port}, name=${name}`);
            payload = {
              hostname: host,
              instances: [{ name, port }]
            };
          }
        }
        
        console.log('Sending payload:', payload);
        
        // Use the test endpoint that doesn't require auth
        const response = await axios.post('http://localhost:5000/api/hosts/test-add', payload);
        console.log("Response:", response.data);
        hostsAdded = true;
      } else if (bulkInput.trim()) {
        // Process bulk input
        const lines = bulkInput.split('\n').filter(line => line.trim() !== '');
        console.log("Bulk lines:", lines);
        
        // Process each line individually
        for (const line of lines) {
          const parts = line.split(/\s+/);
          if (parts.length < 3) {
            console.warn(`Skipping invalid line: ${line}`);
            continue;
          }
          
          const host = parts[0];
          const port = parseInt(parts[1], 10);
          const name = parts.slice(2).join('_');
          
          const payload = {
            hostname: host,
            instances: [{ name, port }]
          };
          
          console.log('Sending bulk payload:', payload);
          await axios.post('http://localhost:5000/api/hosts/test-add', payload);
          hostsAdded = true;
        }
      } else {
        setError('Please enter either a hostname or bulk data');
        setIsProcessing(false);
        return;
      }
      
      // Only if we got here successfully, call onAdd and close
      if (hostsAdded) {
        console.log("Hosts added successfully, calling onAdd() and closing modal");
        // Ensure we're calling onAdd with no parameters
        onAdd();
        // Clear the form inputs
        setHostname('');
        setBulkInput('');
        // Close the modal
        onClose();
      }
    } catch (err) {
      console.error('Error adding host:', err);
      setError(err.response?.data?.error || err.message || 'Failed to add host. Please check your input.');
    } finally {
      // Always reset the processing state
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
                placeholder="e.g., ftc-lbjbsapp211 9990 DEV_CAMS_01"
                value={hostname}
                onChange={(e) => setHostname(e.target.value)}
              />
            </div>
            
            <div className="mb-1">
              <label className="block text-sm font-medium text-gray-300 mb-1">
                OR Bulk Add (hostname port instance_name)
              </label>
              <textarea 
                className="w-full bg-gray-700 border border-gray-600 rounded-md py-2 px-3 text-white focus:outline-none focus:ring-2 focus:ring-blue-500 h-32"
                placeholder="ftc-lbjbsapp211 9990 DEV_CAMS_01&#10;ftc-lbjbsapp211 10090 DEV_ABC_01"
                value={bulkInput}
                onChange={(e) => setBulkInput(e.target.value)}
              />
            </div>
            <p className="text-xs text-gray-400 mt-1 mb-4">
              Enter one entry per line in format: hostname port instance_name
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

export default AddHostModal;
