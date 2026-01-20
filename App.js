import React, { useState, useRef, useEffect } from 'react';
import { Upload, FileText, User, CheckCircle, XCircle, Filter, Search, BarChart3, AlertTriangle, Clock, Users } from 'lucide-react';

// API functions
const API_BASE_URL = 'http://localhost:8000';

const api = {
  uploadPDF: async (file) => {
    console.log('API: Starting upload for file:', file.name, 'Size:', file.size, 'bytes');
    
    const formData = new FormData();
    formData.append('file', file);
    
    console.log('API: Sending request to', `${API_BASE_URL}/upload-pdf/`);
    
    const response = await fetch(`${API_BASE_URL}/upload-pdf/`, {
      method: 'POST',
      body: formData,
    });
    
    console.log('API: Response status:', response.status);
    console.log('API: Response headers:', response.headers);
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error('API: Error response:', errorText);
      throw new Error(`HTTP ${response.status}: ${errorText}`);
    }
    
    const data = await response.json();
    console.log('API: Success response:', data);
    return data;
  },
  
  getBugReports: async (filters = {}) => {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => {
      if (value) params.append(key, value);
    });
    
    const response = await fetch(`${API_BASE_URL}/bug-reports/?${params}`);
    if (!response.ok) {
      throw new Error('Failed to fetch bug reports');
    }
    
    return response.json();
  },
  
  assignBug: async (bugId, action, assignedDeveloper = null) => {
    const response = await fetch(`${API_BASE_URL}/assign-bug/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        bug_id: bugId,
        action: action,
        assigned_developer: assignedDeveloper,
      }),
    });
    
    if (!response.ok) {
      throw new Error('Failed to assign bug');
    }
    
    return response.json();
  },
  
  getDevelopers: async () => {
    const response = await fetch(`${API_BASE_URL}/developers/`);
    if (!response.ok) {
      throw new Error('Failed to fetch developers');
    }
    
    return response.json();
  },
  
  getAnalytics: async () => {
    const response = await fetch(`${API_BASE_URL}/analytics/`);
    if (!response.ok) {
      throw new Error('Failed to fetch analytics');
    }
    
    return response.json();
  }
};

const BugTriageSystem = () => {
  const [selectedFile, setSelectedFile] = useState(null);
  const [isUploading, setIsUploading] = useState(false);
  const [bugReports, setBugReports] = useState([]);
  const [developers, setDevelopers] = useState([]);
  const [activeTab, setActiveTab] = useState('upload');
  const [searchTerm, setSearchTerm] = useState('');
  const [filterBy, setFilterBy] = useState('all');
  const [analytics, setAnalytics] = useState(null);
  const [error, setError] = useState('');
  const fileInputRef = useRef(null);

  // Load initial data
  useEffect(() => {
    loadDevelopers();
    loadBugReports();
  }, []);

  // Load analytics when tab changes
  useEffect(() => {
    if (activeTab === 'analytics') {
      loadAnalytics();
    }
  }, [activeTab]);

  const loadDevelopers = async () => {
    try {
      const devs = await api.getDevelopers();
      setDevelopers(devs.map(dev => dev.name));
    } catch (error) {
      console.error('Error loading developers:', error);
      // Fallback to mock data
      setDevelopers([
        'Alice Johnson', 'Bob Smith', 'Carol Davis', 'David Wilson',
        'Emma Brown', 'Frank Miller', 'Grace Lee', 'Henry Taylor'
      ]);
    }
  };

  const loadBugReports = async () => {
    try {
      const reports = await api.getBugReports();
      setBugReports(reports);
    } catch (error) {
      console.error('Error loading bug reports:', error);
      // Start with empty array - reports will be loaded after upload
    }
  };

  const loadAnalytics = async () => {
    try {
      const analyticsData = await api.getAnalytics();
      setAnalytics(analyticsData);
    } catch (error) {
      console.error('Error loading analytics:', error);
      // Fallback to calculated analytics
      const totalReports = bugReports.length;
      const approvedReports = bugReports.filter(b => b.status === 'approved').length;
      const pendingReports = bugReports.filter(b => b.status === 'pending').length;
      
      setAnalytics({
        total_reports: totalReports,
        approved_reports: approvedReports,
        pending_reports: pendingReports,
        developer_distribution: {},
        severity_distribution: {},
        component_distribution: {},
        average_confidence: 0.85
      });
    }
  };

  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (file && file.type === 'application/pdf') {
      setSelectedFile(file);
      setError('');
    } else {
      setError('Please select a valid PDF file');
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) {
      // If no file selected, just show demo data
      const mockReports = [
        {
          id: Date.now() + 1,
          title: "Demo: Login form validation fails on special characters",
          description: "This is demo data since no PDF was selected. When users enter special characters in the email field, the validation logic throws an exception...",
          severity: "High",
          component: "Authentication",
          predicted_developer: "Alice Johnson",
          confidence_score: 0.87,
          assignment_reason: "Expertise in frontend, javascript, ui; Component specialist (authentication); High similarity to past assignments",
          status: "pending",
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        },
        {
          id: Date.now() + 2,
          title: "Demo: Memory leak in data processing module",
          description: "This is demo data since no PDF was selected. The application consumes increasing amounts of memory when processing large datasets...",
          severity: "Critical",
          component: "Data Processing",
          predicted_developer: "Bob Smith",
          confidence_score: 0.92,
          assignment_reason: "Expertise in backend, python, database; Critical issue requires senior expertise; High similarity to past assignments",
          status: "pending",
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        }
      ];
      
      setBugReports(mockReports);
      setActiveTab('triage');
      setError('Showing demo data - no PDF file was selected');
      return;
    }
    
    setIsUploading(true);
    setError('');
    
    try {
      console.log('Uploading file:', selectedFile.name, 'Size:', selectedFile.size);
      
      // Make the actual API call
      const reports = await api.uploadPDF(selectedFile);
      console.log('API Response:', reports);
      
      setBugReports(reports);
      setActiveTab('triage');
      setSelectedFile(null);
      
      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
      
      setError('');
    } catch (error) {
      console.error('Upload error details:', error);
      
      // Show detailed error information
      let errorMessage = 'Failed to upload PDF: ';
      if (error.message) {
        errorMessage += error.message;
      }
      if (error.response) {
        errorMessage += ` (Status: ${error.response.status})`;
      }
      
      setError(errorMessage);
      
      // Don't show demo data if there was an actual API error
      setBugReports([]);
    } finally {
      setIsUploading(false);
    }
  };

  const handleAssignmentAction = async (bugId, action, newDeveloper = null) => {
    try {
      await api.assignBug(bugId, action, newDeveloper);
      
      // Update local state
      setBugReports(prev => prev.map(bug => {
        if (bug.id === bugId) {
          return {
            ...bug,
            status: action,
            assigned_developer: newDeveloper || bug.predicted_developer
          };
        }
        return bug;
      }));
    } catch (error) {
      console.error('Error updating assignment:', error);
      
      // Fallback: update local state anyway for demo
      setBugReports(prev => prev.map(bug => {
        if (bug.id === bugId) {
          return {
            ...bug,
            status: action,
            assigned_developer: newDeveloper || bug.predicted_developer
          };
        }
        return bug;
      }));
      
      setError('Assignment updated locally (API connection failed)');
    }
  };

  const getSeverityColor = (severity) => {
    switch (severity?.toLowerCase()) {
      case 'critical': return 'text-red-600 bg-red-50';
      case 'high': return 'text-orange-600 bg-orange-50';
      case 'medium': return 'text-yellow-600 bg-yellow-50';
      case 'low': return 'text-green-600 bg-green-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  const getConfidenceColor = (confidence) => {
    if (confidence >= 0.8) return 'text-green-600';
    if (confidence >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  const filteredBugs = bugReports.filter(bug => {
    const matchesSearch = bug.title?.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         bug.description?.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesFilter = filterBy === 'all' || bug.status === filterBy || bug.severity?.toLowerCase() === filterBy.toLowerCase();
    return matchesSearch && matchesFilter;
  });

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-lg p-6 mb-8">
          <h1 className="text-3xl font-bold text-gray-800 mb-2">Intelligent Bug Triage System</h1>
          <p className="text-gray-600">Automatically assign bug reports to the most suitable developers using AI</p>
          {error && (
            <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
              <p className="text-yellow-800 text-sm">{error}</p>
            </div>
          )}
        </div>

        {/* Navigation Tabs */}
        <div className="bg-white rounded-lg shadow-lg mb-8">
          <div className="flex border-b border-gray-200">
            <button
              onClick={() => setActiveTab('upload')}
              className={`px-6 py-4 font-medium ${
                activeTab === 'upload' 
                ? 'text-blue-600 border-b-2 border-blue-600' 
                : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              <Upload className="inline-block w-5 h-5 mr-2" />
              Upload Reports
            </button>
            <button
              onClick={() => setActiveTab('triage')}
              className={`px-6 py-4 font-medium ${
                activeTab === 'triage' 
                ? 'text-blue-600 border-b-2 border-blue-600' 
                : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              <FileText className="inline-block w-5 h-5 mr-2" />
              Bug Triage ({bugReports.length})
            </button>
            <button
              onClick={() => setActiveTab('analytics')}
              className={`px-6 py-4 font-medium ${
                activeTab === 'analytics' 
                ? 'text-blue-600 border-b-2 border-blue-600' 
                : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              <BarChart3 className="inline-block w-5 h-5 mr-2" />
              Analytics
            </button>
          </div>

          {/* Upload Tab */}
          {activeTab === 'upload' && (
            <div className="p-6">
              <div className="max-w-2xl mx-auto">
                <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-blue-400 transition-colors">
                  <Upload className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">Upload Bug Reports PDF</h3>
                  <p className="text-gray-500 mb-4">Select a PDF file containing multiple bug reports for automated triage</p>
                  
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".pdf"
                    onChange={handleFileSelect}
                    className="hidden"
                  />
                  
                  <button
                    onClick={() => fileInputRef.current?.click()}
                    className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition-colors mb-4"
                  >
                    Select PDF File
                  </button>
                  
                  {selectedFile && (
                    <div className="mt-4 p-4 bg-blue-50 rounded-lg">
                      <p className="text-sm text-blue-800">
                        Selected: {selectedFile.name} ({selectedFile.size >= 1024 * 1024 
                          ? `${(selectedFile.size / 1024 / 1024).toFixed(2)} MB`
                          : selectedFile.size >= 1024 
                            ? `${(selectedFile.size / 1024).toFixed(2)} KB`
                            : `${selectedFile.size} bytes`
                        })
                      </p>
                    </div>
                  )}
                </div>

                {selectedFile && (
                  <div className="mt-6 text-center">
                    <button
                      onClick={handleUpload}
                      disabled={isUploading}
                      className="bg-green-600 text-white px-8 py-3 rounded-lg hover:bg-green-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {isUploading ? (
                        <>
                          <Clock className="inline-block w-5 h-5 mr-2 animate-spin" />
                          Processing PDF...
                        </>
                      ) : (
                        <>
                          <FileText className="inline-block w-5 h-5 mr-2" />
                          Process & Analyze
                        </>
                      )}
                    </button>
                  </div>
                )}
                
                <div className="mt-8 p-4 bg-gray-50 rounded-lg">
                  <h4 className="font-medium text-gray-800 mb-2">Note:</h4>
                  <p className="text-sm text-gray-600">
                    If you don't have a PDF ready, click "Process & Analyze" without selecting a file to see the system with demo data.
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Triage Tab */}
          {activeTab === 'triage' && (
            <div className="p-6">
              {/* Filters and Search */}
              <div className="flex flex-col md:flex-row gap-4 mb-6">
                <div className="flex-1">
                  <div className="relative">
                    <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
                    <input
                      type="text"
                      placeholder="Search bug reports..."
                      value={searchTerm}
                      onChange={(e) => setSearchTerm(e.target.value)}
                      className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                </div>
                <div className="flex gap-2">
                  <select
                    value={filterBy}
                    onChange={(e) => setFilterBy(e.target.value)}
                    className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="all">All Status</option>
                    <option value="pending">Pending</option>
                    <option value="approved">Approved</option>
                    <option value="rejected">Rejected</option>
                  </select>
                </div>
              </div>

              {/* Bug Reports List */}
              <div className="space-y-4">
                {filteredBugs.map((bug) => (
                  <div key={bug.id} className="bg-gray-50 rounded-lg p-6 border border-gray-200">
                    <div className="flex justify-between items-start mb-4">
                      <div className="flex-1">
                        <h3 className="text-lg font-semibold text-gray-800 mb-2">{bug.title}</h3>
                        <p className="text-gray-600 mb-4">{bug.description}</p>
                        
                        <div className="flex flex-wrap gap-2 mb-4">
                          <span className={`px-3 py-1 rounded-full text-sm font-medium ${getSeverityColor(bug.severity)}`}>
                            <AlertTriangle className="inline-block w-4 h-4 mr-1" />
                            {bug.severity}
                          </span>
                          <span className="px-3 py-1 bg-blue-50 text-blue-700 rounded-full text-sm font-medium">
                            {bug.component}
                          </span>
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-4">
                        <div className="flex flex-col gap-2">
                          <div className="flex items-center gap-2">
                            <User className="w-4 h-4 text-gray-500" />
                            <span className="text-sm font-medium text-gray-700">Predicted: {bug.predicted_developer}</span>
                            <span className={`text-sm font-medium ${getConfidenceColor(bug.confidence_score)}`}>
                              ({Math.round((bug.confidence_score || 0) * 100)}%)
                            </span>
                          </div>
                          {bug.assignment_reason && (
                            <div className="flex items-start gap-2">
                              <div className="w-4 h-4 mt-0.5">💡</div>
                              <span className="text-xs text-gray-600 italic">
                                Reason: {bug.assignment_reason}
                              </span>
                            </div>
                          )}
                        </div>
                        {bug.status !== 'pending' && (
                          <span className={`px-2 py-1 rounded text-xs font-medium ${
                            bug.status === 'approved' ? 'bg-green-100 text-green-800' :
                            bug.status === 'rejected' ? 'bg-red-100 text-red-800' :
                            'bg-yellow-100 text-yellow-800'
                          }`}>
                            {bug.status.toUpperCase()}
                          </span>
                        )}
                      </div>
                      
                      {bug.status === 'pending' && (
                        <div className="flex gap-2">
                          <button
                            onClick={() => handleAssignmentAction(bug.id, 'approved')}
                            className="flex items-center gap-1 px-3 py-1 bg-green-600 text-white rounded hover:bg-green-700 transition-colors text-sm"
                          >
                            <CheckCircle className="w-4 h-4" />
                            Approve
                          </button>
                          <button
                            onClick={() => handleAssignmentAction(bug.id, 'rejected')}
                            className="flex items-center gap-1 px-3 py-1 bg-red-600 text-white rounded hover:bg-red-700 transition-colors text-sm"
                          >
                            <XCircle className="w-4 h-4" />
                            Reject
                          </button>
                          <select
                            onChange={(e) => handleAssignmentAction(bug.id, 'modified', e.target.value)}
                            className="px-2 py-1 border border-gray-300 rounded text-sm focus:ring-2 focus:ring-blue-500"
                          >
                            <option value="">Reassign to...</option>
                            {developers.map(dev => (
                              <option key={dev} value={dev}>{dev}</option>
                            ))}
                          </select>
                        </div>
                      )}
                    </div>
                  </div>
                ))}
                
                {filteredBugs.length === 0 && (
                  <div className="text-center py-8">
                    <FileText className="mx-auto h-12 w-12 text-gray-400 mb-4" />
                    <h3 className="text-lg font-medium text-gray-900 mb-2">No Bug Reports Found</h3>
                    <p className="text-gray-500">Upload a PDF file to get started with bug triage.</p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Analytics Tab */}
          {activeTab === 'analytics' && (
            <div className="p-6">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                <div className="bg-blue-50 p-6 rounded-lg">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-blue-600 font-medium">Total Reports</p>
                      <p className="text-2xl font-bold text-blue-800">{analytics?.total_reports || bugReports.length}</p>
                    </div>
                    <FileText className="w-8 h-8 text-blue-600" />
                  </div>
                </div>
                <div className="bg-green-50 p-6 rounded-lg">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-green-600 font-medium">Approved</p>
                      <p className="text-2xl font-bold text-green-800">
                        {analytics?.approved_reports || bugReports.filter(b => b.status === 'approved').length}
                      </p>
                    </div>
                    <CheckCircle className="w-8 h-8 text-green-600" />
                  </div>
                </div>
                <div className="bg-yellow-50 p-6 rounded-lg">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-yellow-600 font-medium">Pending Review</p>
                      <p className="text-2xl font-bold text-yellow-800">
                        {analytics?.pending_reports || bugReports.filter(b => b.status === 'pending').length}
                      </p>
                    </div>
                    <Clock className="w-8 h-8 text-yellow-600" />
                  </div>
                </div>
              </div>

              <div className="bg-gray-50 p-6 rounded-lg">
                <h3 className="text-lg font-semibold text-gray-800 mb-4">Developer Assignment Distribution</h3>
                <div className="space-y-3">
                  {developers.slice(0, 4).map((dev, index) => (
                    <div key={dev} className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <Users className="w-4 h-4 text-gray-500" />
                        <span className="text-sm font-medium text-gray-700">{dev}</span>
                      </div>
                      <div className="flex items-center gap-3">
                        <div className="w-24 bg-gray-200 rounded-full h-2">
                          <div 
                            className="bg-blue-600 h-2 rounded-full" 
                            style={{ width: `${(index + 1) * 25}%` }}
                          ></div>
                        </div>
                        <span className="text-sm text-gray-600 w-8">{index + 1}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default BugTriageSystem;