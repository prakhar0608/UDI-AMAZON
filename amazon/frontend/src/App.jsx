import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { 
  LayoutDashboard, 
  FileText, 
  RefreshCw, 
  Search,
  Target,
  Layers,
  Box,
  Loader2,
  FileSpreadsheet,
  FileCode,
  CheckSquare,
  Square,
  Play,
  CheckCircle2,
  AlertCircle,
  Zap,
  TrendingUp,
  Activity,
  Settings,
  Calendar,
  Clock,
  ArrowRight,
  Terminal,
  Database,
  ChevronRight,
  Monitor,
  Download,
  BarChart4,
  Flame,
  Sparkles,
  Command,
  LayoutGrid,
  History,
  Eye,
  X,
  Table as TableIcon,
  LogOut,
  ChevronDown,
  User,
  ChevronLeft,
  Menu,
  PanelLeftClose,
  BarChart3
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer
} from 'recharts';

// Dynamic API Base
const API_BASE = `http://${window.location.hostname}:8000/api`;

const REPORT_LEVELS = [
  { id: 'spCampaigns', label: 'CAMPAIGN', icon: <Target size={24} />, desc: 'CAMPAIGN LAYER' },
  { id: 'spAdGroups', label: 'AD GROUP', icon: <Layers size={24} />, desc: 'AD GROUP LAYER' },
  { id: 'spProducts', label: 'ASIN', icon: <Box size={24} />, desc: 'ASIN LAYER' },
];

function App() {
  const [profiles, setProfiles] = useState([]);
  const [reports, setReports] = useState([]);
  const [rangeData, setRangeData] = useState(null);
  const [selectedIds, setSelectedIds] = useState([]);
  const [selectedLevel, setSelectedLevel] = useState('spCampaigns');
  const [isBulkRunning, setIsBulkRunning] = useState(false);
  const [isDiscovering, setIsDiscovering] = useState(false);
  const [logs, setLogs] = useState([]);
  
  const [previewData, setPreviewData] = useState(null);
  const [isPreviewLoading, setIsPreviewLoading] = useState(false);
  
  const [isAccountDropdownOpen, setIsAccountDropdownOpen] = useState(false);
  const [accountSearchTerm, setAccountSearchTerm] = useState('');
  
  const [startDate, setStartDate] = useState(() => {
    const d = new Date();
    d.setDate(1);
    return d.toISOString().split('T')[0];
  });
  const [endDate, setEndDate] = useState(() => {
    const d = new Date();
    d.setDate(d.getDate() - 1);
    return d.toISOString().split('T')[0];
  });
  
  const [view, setView] = useState('dashboard');
  const [lastSyncResult, setLastSyncResult] = useState(null);
  const [isCollapsed, setIsCollapsed] = useState(false);
  const dropdownRef = useRef(null);

  useEffect(() => {
    fetchProfiles();
    fetchReports();
    fetchRangeAnalytics();
    
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsAccountDropdownOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const addLog = (tag, message) => {
    setLogs(prev => [...prev.slice(-49), { id: Date.now(), tag, message, time: new Date().toLocaleTimeString() }]);
  };

  const fetchProfiles = async () => {
    try {
      const res = await axios.get(`${API_BASE}/profiles`);
      setProfiles(res.data);
    } catch (err) {
      addLog("ERROR", "Data node link failed.");
    }
  };

  const fetchRangeAnalytics = async () => {
    try {
      const res = await axios.get(`${API_BASE}/analytics/ranges`);
      setRangeData(res.data);
    } catch (err) {}
  };

  const handleDiscover = async () => {
    setIsDiscovering(true);
    try {
      const res = await axios.post(`${API_BASE}/discover`);
      setProfiles(res.data);
    } catch (err) {
      addLog("ERROR", "Discovery failed.");
    } finally {
      setIsDiscovering(false);
    }
  };

  const fetchReports = async () => {
    try {
      const res = await axios.get(`${API_BASE}/reports`);
      setReports(res.data);
    } catch (err) {}
  };

  const toggleSelect = (id) => {
    setSelectedIds(prev => 
      prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
    );
  };

  const runBulkSync = async () => {
    if (selectedIds.length === 0) return;

    setIsBulkRunning(true);
    setLastSyncResult(null);
    addLog("START", `Submitting ${selectedLevel} export...`);

    try {
        // Step 1: Submit the job (returns immediately)
        const submitRes = await axios.post(`${API_BASE}/fetch-bulk`, {
            ids: selectedIds,
            report_type: selectedLevel,
            start_date: startDate,
            end_date: endDate
        }, { timeout: 30000 }); // 30s is plenty for job submission
        
        if (submitRes.data.status !== 'accepted' || !submitRes.data.job_id) {
            addLog("FAIL", "Server rejected the export request.");
            setIsBulkRunning(false);
            return;
        }
        
        const jobId = submitRes.data.job_id;
        addLog("QUEUE", `Job ${jobId} queued. Polling for status...`);
        
        // Step 2: Poll for completion
        let lastMsg = "";
        const pollInterval = setInterval(async () => {
            try {
                const statusRes = await axios.get(`${API_BASE}/jobs/${jobId}`, { timeout: 10000 });
                const job = statusRes.data;
                
                // Show progress updates in the console
                if (job.message && job.message !== lastMsg) {
                    lastMsg = job.message;
                    addLog("SYNC", job.message);
                }
                
                if (job.status === 'success') {
                    clearInterval(pollInterval);
                    const results = job.results || [];
                    if (results.length > 0) {
                        addLog("SUCCESS", `Extracted data for ${results.length} accounts.`);
                        setLastSyncResult(results[0]);
                        handlePreview(results[0].csv_name);
                    } else {
                        addLog("WARN", "No data returned for selected window.");
                    }
                    setIsBulkRunning(false);
                    fetchReports();
                    fetchRangeAnalytics();
                } else if (job.status === 'failed') {
                    clearInterval(pollInterval);
                    addLog("FAIL", job.message || "Export failed.");
                    setIsBulkRunning(false);
                    fetchReports();
                }
            } catch (pollErr) {
                // Transient poll error — keep trying
                console.warn("Poll error:", pollErr);
            }
        }, 5000); // Poll every 5 seconds
        
    } catch (err) {
        console.error(err);
        addLog("FAIL", "Failed to submit export job. Check server.");
        setIsBulkRunning(false);
    }
  };

  const handlePreview = async (filename) => {
    setIsPreviewLoading(true);
    try {
        const res = await axios.get(`${API_BASE}/reports/preview/${filename}`);
        setPreviewData(res.data);
    } catch (err) {
        addLog("ERROR", "Failed to load data preview.");
    } finally {
        setIsPreviewLoading(false);
    }
  };

  const handleDownload = (filename) => {
    window.open(`${API_BASE}/reports/download/${filename}`, '_blank');
  };

  const filteredProfiles = profiles.filter(p => 
    p.display_name.toLowerCase().includes(accountSearchTerm.toLowerCase()) ||
    p.region.toLowerCase().includes(accountSearchTerm.toLowerCase())
  );

  return (
    <div className="min-h-screen bg-un-main text-slate-800 flex font-sans overflow-hidden bg-un-grid">
      
      {/* Sidebar */}
      <motion.aside 
        initial={false}
        animate={{ width: isCollapsed ? 72 : 256 }}
        transition={{ type: 'spring', stiffness: 300, damping: 30 }}
        className="fixed left-0 top-0 h-screen bg-white border-r border-slate-200 flex flex-col p-3 z-40 overflow-visible"
      >
        {/* Top Section - Logo & Toggle */}
        <div className="flex flex-col items-center pt-[20px] mb-1 relative w-full">
          <AnimatePresence mode="wait">
            {!isCollapsed ? (
              <motion.div 
                key="open-header"
                initial={{ opacity: 0, x: -10 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -10 }}
                className="flex items-center justify-between w-full px-3"
              >
                <div className="animate-float-subtle">
                  <img 
                    src="https://upload.wikimedia.org/wikipedia/commons/a/a9/Amazon_logo.svg" 
                    className="h-5 w-auto object-contain" 
                    alt="Amazon" 
                  />
                </div>
                <button 
                  onClick={() => setIsCollapsed(true)} 
                  className="p-2 text-slate-400 hover:text-un-amazon hover:bg-slate-50 rounded-xl transition-all"
                  title="Collapse Sidebar"
                >
                  <ChevronLeft size={18} />
                </button>
              </motion.div>
            ) : (
              <motion.div 
                key="collapsed-header"
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.8 }}
                className="flex flex-col items-center gap-3 w-full"
              >
                <div className="w-[44px] h-[44px] bg-[#FFF3E0] rounded-xl flex items-center justify-center overflow-hidden shadow-sm">
                  <img 
                    src="/amazon_smile.jpg" 
                    style={{ width: '38px', height: 'auto' }} 
                    className="object-contain opacity-100" 
                    alt="Smile" 
                  />
                </div>
                <button 
                  onClick={() => setIsCollapsed(false)} 
                  className="p-2 text-slate-400 hover:text-un-amazon hover:bg-slate-50 rounded-xl transition-all"
                  title="Expand Sidebar"
                >
                  <Menu size={20} />
                </button>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
        
        {/* Main Nav - Middle */}
        <nav className="flex flex-col gap-1.5">
          <SidebarLink icon={<LayoutGrid size={22} />} label="Dashboard" active={view === 'dashboard'} onClick={() => setView('dashboard')} isCollapsed={isCollapsed} />
          <SidebarLink icon={<BarChart3 size={22} />} label="Analytics" active={view === 'analytics'} onClick={() => setView('analytics')} isCollapsed={isCollapsed} />
          <SidebarLink icon={<History size={22} />} label="History" active={view === 'reports'} onClick={() => setView('reports')} isCollapsed={isCollapsed} />
        </nav>
        
        {/* Action Buttons - Bottom */}
        <div className="mt-auto flex flex-col gap-1.5">
          <button 
            onClick={handleDiscover} 
            disabled={isDiscovering} 
            className={`flex items-center gap-4 w-full py-3.5 rounded-2xl text-slate-500 hover:text-un-amazon hover:bg-slate-50 transition-all group ${isCollapsed ? 'justify-center px-0' : 'px-5'}`}
          >
            <div className="group-hover:rotate-180 transition-transform duration-500">
              {isDiscovering ? <Loader2 size={22} className="animate-spin" /> : <RefreshCw size={22} />}
            </div>
            {!isCollapsed && <span className="text-sm font-bold tracking-tight">Refresh</span>}
          </button>
          
          <button className={`flex items-center gap-4 w-full py-3.5 rounded-2xl text-slate-500 hover:text-slate-900 hover:bg-slate-50 transition-all ${isCollapsed ? 'justify-center px-0' : 'px-5'}`}>
            <div className="p-0.5">
              <div className="w-6 h-6 rounded-lg bg-slate-900 flex items-center justify-center text-white font-black text-[8px] shadow-sm">
                UN
              </div>
            </div>
            {!isCollapsed && <span className="text-sm font-bold tracking-tight">Profile</span>}
          </button>

          <button className={`flex items-center gap-4 w-full py-3.5 rounded-2xl text-slate-500 hover:text-rose-500 hover:bg-rose-50 transition-all group ${isCollapsed ? 'justify-center px-0' : 'px-5'}`}>
            <div className="transition-colors">
              <LogOut size={22} />
            </div>
            {!isCollapsed && <span className="text-sm font-bold tracking-tight">Sign Out</span>}
          </button>

          {!isCollapsed && (
            <div className="mt-8 px-5 py-6 bg-slate-50 rounded-[2rem] border border-slate-100 flex flex-col gap-4">
              <div className="flex items-center gap-3">
                <Terminal size={14} className="text-un-amazon" />
                <span className="text-[10px] font-black uppercase tracking-widest text-slate-400">System Console</span>
              </div>
              <div className="space-y-3 max-h-[200px] overflow-y-auto un-scrollbar pr-2">
                {logs.length === 0 && <div className="text-[10px] font-bold text-slate-300 italic">No activity recorded...</div>}
                {[...logs].reverse().map(log => (
                  <div key={log.id} className="flex flex-col gap-1">
                    <div className="flex items-center justify-between">
                      <span className={`text-[9px] font-black uppercase tracking-tighter ${log.tag === 'ERROR' || log.tag === 'FAIL' ? 'text-rose-500' : 'text-un-amazon'}`}>{log.tag}</span>
                      <span className="text-[8px] font-bold text-slate-300">{log.time}</span>
                    </div>
                    <div className="text-[10px] font-bold text-slate-600 leading-tight break-words">{log.message}</div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </motion.aside>

      <motion.div 
        animate={{ marginLeft: isCollapsed ? 72 : 256 }}
        transition={{ type: 'spring', stiffness: 300, damping: 30 }}
        className="flex-1 flex flex-col overflow-hidden relative"
      >
        
        {/* Top Header Section (Searchable Dropdown for Accounts) */}
        <div className="bg-white/80 backdrop-blur-md border-b border-slate-200 px-16 py-8 flex items-center justify-between z-30">
          <div className="flex items-center gap-8">
            <div className="text-left">
              <div className="text-[10px] font-black uppercase tracking-widest text-slate-400">System Status</div>
              <div className="text-sm font-black text-emerald-600 flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                ONLINE
              </div>
            </div>
          </div>

          <div className="relative" ref={dropdownRef}>
            <button 
              onClick={() => setIsAccountDropdownOpen(!isAccountDropdownOpen)}
              className="flex items-center gap-6 px-8 py-4 bg-slate-50 border border-slate-200 rounded-2xl hover:border-un-amazon/40 transition-all group"
            >
              <div className="w-10 h-10 rounded-xl bg-un-amazon/10 text-un-amazon flex items-center justify-center">
                <User size={20} />
              </div>
              <div className="text-left">
                <div className="text-[10px] font-black uppercase tracking-widest text-slate-400">Target Accounts</div>
                <div className="text-sm font-black text-slate-900">
                  {selectedIds.length === 0 ? "Select Accounts" : `${selectedIds.length} Accounts Selected`}
                </div>
              </div>
              <ChevronDown size={20} className={`text-slate-300 transition-transform ${isAccountDropdownOpen ? 'rotate-180' : ''}`} />
            </button>

            <AnimatePresence>
              {isAccountDropdownOpen && (
                <motion.div 
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: 10 }}
                  className="absolute right-0 mt-4 w-[400px] bg-white border border-slate-200 rounded-3xl shadow-2xl shadow-slate-200/50 overflow-hidden"
                >
                  <div className="p-6 border-b border-slate-100 bg-slate-50">
                    <div className="relative">
                      <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400" size={16} />
                      <input 
                        type="text" 
                        placeholder="Search accounts..." 
                        className="w-full bg-white border border-slate-200 rounded-xl py-4 pl-12 pr-6 text-sm font-bold focus:border-un-amazon/40 outline-none transition-all"
                        value={accountSearchTerm}
                        onChange={(e) => setAccountSearchTerm(e.target.value)}
                        onClick={(e) => e.stopPropagation()}
                      />
                    </div>
                  </div>
                  <div className="max-h-[400px] overflow-y-auto un-scrollbar p-4 space-y-2">
                    <button 
                      onClick={() => setSelectedIds(selectedIds.length === profiles.length ? [] : profiles.map(p => p.id))}
                      className="w-full text-left px-6 py-4 rounded-xl text-xs font-black uppercase tracking-widest text-un-amazon hover:bg-un-amazon/5 transition-colors"
                    >
                      {selectedIds.length === profiles.length ? "Deselect All" : "Select All Available"}
                    </button>
                    {filteredProfiles.map(p => (
                      <div 
                        key={p.id}
                        onClick={() => toggleSelect(p.id)}
                        className={`flex items-center gap-4 px-6 py-4 rounded-2xl cursor-pointer transition-all ${selectedIds.includes(p.id) ? 'bg-un-amazon/5 border border-un-amazon/20' : 'hover:bg-slate-50 border border-transparent'}`}
                      >
                        <div className={`w-5 h-5 rounded-md border-2 flex items-center justify-center transition-all ${selectedIds.includes(p.id) ? 'bg-un-amazon border-un-amazon text-slate-900' : 'border-slate-200 text-transparent'}`}>
                          <CheckSquare size={12} strokeWidth={4} />
                        </div>
                        <div className="flex-1 truncate">
                          <div className="text-sm font-black text-slate-900">{p.display_name}</div>
                          <div className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">{p.region}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>

        {/* Dashboard */}
        <main className="flex-1 overflow-y-auto p-16 un-scrollbar">
          <AnimatePresence mode="wait">
            {view === 'dashboard' && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="max-w-7xl mx-auto space-y-16"
              >
                <header className="flex justify-between items-start">
                  <div className="space-y-6">
                    <div className="inline-flex items-center gap-3 px-5 py-2 bg-slate-100 rounded-full border border-slate-200">
                      <Sparkles size={14} className="text-un-amazon" />
                      <span className="text-[10px] font-black uppercase tracking-[0.2em] text-slate-500">Decision Intelligence Platform</span>
                    </div>
                    <h1 className="text-[5.5rem] font-black tracking-tight leading-[0.85] text-slate-900">
                      Amazon <br/> <span className="text-gradient">Intelligence</span>
                    </h1>
                  </div>

                  {lastSyncResult && (
                    <motion.div 
                      initial={{ opacity: 0, scale: 0.9 }}
                      animate={{ opacity: 1, scale: 1 }}
                      className="un-card !p-8 bg-slate-900 flex items-center gap-8 text-white border-un-amazon/20"
                    >
                      <div className="w-16 h-16 bg-un-amazon rounded-3xl flex items-center justify-center shadow-2xl shadow-un-amazon/20">
                        <Download size={32} className="text-slate-900" />
                      </div>
                      <div>
                        <div className="text-[10px] font-black text-slate-400 uppercase tracking-widest mb-2">Extraction Finalized</div>
                        <div className="flex gap-4">
                            <button 
                            onClick={() => handleDownload(lastSyncResult.xlsx_name)}
                            className="text-lg font-black hover:text-un-amazon transition-colors flex items-center gap-2 group"
                            >
                            EXCEL <ChevronRight size={18} />
                            </button>
                            <button 
                            onClick={() => handlePreview(lastSyncResult.csv_name)}
                            className="text-lg font-black hover:text-un-amazon transition-colors flex items-center gap-2 group"
                            >
                            PREVIEW <Eye size={18} />
                            </button>
                        </div>
                      </div>
                    </motion.div>
                  )}
                </header>

                <div className="grid grid-cols-12 gap-10">
                  <div className="col-span-12 un-card">
                    <div className="flex items-center gap-4 mb-12">
                      <div className="p-3 bg-un-amazon/10 rounded-2xl text-un-amazon">
                        <Calendar size={24} />
                      </div>
                      <div>
                        <h3 className="text-xs font-black uppercase tracking-[0.3em] text-slate-400">Date Range</h3>
                      </div>
                    </div>

                    <div className="grid grid-cols-11 items-center gap-6">
                      <div className="col-span-5 space-y-4">
                        <label className="text-[11px] font-black text-slate-500 uppercase tracking-widest ml-1">Start Date</label>
                        <input 
                          type="date" 
                          value={startDate}
                          onChange={(e) => setStartDate(e.target.value)}
                          className="w-full bg-slate-50 border border-slate-200 rounded-[2rem] py-6 px-10 text-lg font-black focus:border-un-amazon/40 focus:bg-white outline-none transition-all shadow-sm"
                        />
                      </div>
                      <div className="col-span-1 flex justify-center mt-8">
                        <ArrowRight className="text-slate-200" size={32} />
                      </div>
                      <div className="col-span-5 space-y-4">
                        <label className="text-[11px] font-black text-slate-500 uppercase tracking-widest ml-1">End Date</label>
                        <input 
                          type="date" 
                          value={endDate}
                          onChange={(e) => setEndDate(e.target.value)}
                          className="w-full bg-slate-50 border border-slate-200 rounded-[2rem] py-6 px-10 text-lg font-black focus:border-un-amazon/40 focus:bg-white outline-none transition-all shadow-sm"
                        />
                      </div>
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-10">
                  {REPORT_LEVELS.map((level) => (
                    <button
                      key={level.id}
                      onClick={() => setSelectedLevel(level.id)}
                      className={`group relative p-12 rounded-[4.5rem] border-2 transition-all duration-700 ${
                        selectedLevel === level.id 
                          ? `bg-white ${level.id === 'spProducts' ? 'border-orange-500 shadow-orange-500/10' : 'border-un-amazon shadow-un-amazon/10'} shadow-2xl -translate-y-2` 
                          : 'bg-white border-slate-100 hover:border-slate-200 hover:shadow-xl'
                      }`}
                    >
                      <div className="flex flex-col items-center text-center">
                        <div className={`p-6 rounded-[2rem] mb-8 transition-all duration-700 ${
                          selectedLevel === level.id 
                            ? `${level.id === 'spProducts' ? 'bg-orange-500' : 'bg-un-amazon'} text-slate-900 shadow-xl` 
                            : 'bg-slate-50 text-slate-400 group-hover:scale-110'
                        }`}>
                          {level.icon}
                        </div>
                        <div className={`text-[10px] font-black uppercase tracking-[0.3em] mb-3 ${
                          selectedLevel === level.id 
                            ? (level.id === 'spProducts' ? 'text-orange-500' : 'text-un-amazon')
                            : 'text-slate-400'
                        }`}>
                          {level.desc}
                        </div>
                        <div className="text-3xl font-black text-slate-900 tracking-tighter">{level.label}</div>
                      </div>
                    </button>
                  ))}
                </div>

                <div className="flex flex-col items-center gap-12 pb-24">
                  <button onClick={runBulkSync} disabled={isBulkRunning || selectedIds.length === 0} className="btn-un-amazon flex items-center gap-8 px-24 py-12 text-3xl group">
                    {isBulkRunning ? <><Loader2 size={40} className="animate-spin" /> EXPORTING...</> : <><Play size={40} fill="currentColor" className="group-hover:translate-x-3 transition-transform duration-700" /> EXPORT DATA</>}
                  </button>
                </div>

                {/* Data Preview Section */}
                <AnimatePresence>
                    {previewData && (
                        <motion.div 
                            initial={{ opacity: 0, y: 40 }}
                            animate={{ opacity: 1, y: 0 }}
                            exit={{ opacity: 0, y: 40 }}
                            className="un-card !p-0 overflow-hidden"
                        >
                            <div className="px-12 py-10 bg-slate-50 border-b border-slate-200 flex justify-between items-center">
                                <div className="flex items-center gap-4">
                                    <TableIcon size={20} className="text-un-amazon" />
                                    <span className="text-xl font-black text-slate-900">Intelligence <span className="text-un-amazon">Preview</span></span>
                                    <span className="px-4 py-1.5 bg-white border border-slate-200 rounded-full text-[10px] font-black text-slate-400 uppercase tracking-widest ml-4">Showing 100 of {previewData.total_rows} rows</span>
                                </div>
                                <button onClick={() => setPreviewData(null)} className="p-3 hover:bg-slate-200 rounded-2xl transition-colors">
                                    <X size={20} />
                                </button>
                            </div>
                            <div className="overflow-x-auto un-scrollbar max-h-[600px]">
                                <table className="w-full text-left border-collapse">
                                    <thead className="sticky top-0 bg-white shadow-sm z-10">
                                        <tr>
                                            {previewData.columns.map(col => (
                                                <th key={col} className="px-10 py-6 text-[10px] font-black uppercase tracking-widest text-slate-400 border-b border-slate-100">{col}</th>
                                            ))}
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-slate-50">
                                        {previewData.data.map((row, i) => (
                                            <tr key={i} className="hover:bg-slate-50 transition-colors">
                                                {previewData.columns.map(col => (
                                                    <td key={col} className="px-10 py-6 text-sm font-bold text-slate-600 truncate max-w-[200px]">{row[col]}</td>
                                                ))}
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>
              </motion.div>
            )}

            {view === 'analytics' && (
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-16">
                 <header>
                  <h1 className="text-6xl font-black tracking-tighter text-slate-900">Intelligence <span className="text-gradient">Analytics</span></h1>
                </header>
                <div className="grid grid-cols-12 gap-10">
                  <div className="col-span-12 un-card h-[500px]">
                    <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={rangeData?.ranges || []}>
                          <defs>
                            <linearGradient id="unSales" x1="0" y1="0" x2="0" y2="1">
                              <stop offset="5%" stopColor="#ff9900" stopOpacity={0.1}/>
                              <stop offset="95%" stopColor="#ff9900" stopOpacity={0}/>
                            </linearGradient>
                          </defs>
                          <CartesianGrid strokeDasharray="10 10" vertical={false} stroke="#f1f5f9" />
                          <XAxis dataKey="Ranges" axisLine={false} tickLine={false} />
                          <YAxis axisLine={false} tickLine={false} />
                          <Tooltip />
                          <Area type="monotone" dataKey="total_sales" stroke="#ff9900" strokeWidth={5} fill="url(#unSales)" />
                        </AreaChart>
                      </ResponsiveContainer>
                  </div>
                </div>
              </motion.div>
            )}

            {view === 'reports' && (
              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                className="space-y-16"
              >
                <header>
                  <h1 className="text-6xl font-black tracking-tighter text-slate-900">The <span className="text-un-amazon">Vault</span></h1>
                </header>

                <div className="un-card !p-0 overflow-hidden border-slate-200">
                  <table className="w-full text-left">
                    <thead className="bg-slate-50 text-[11px] font-black uppercase tracking-[0.4em] text-slate-400">
                      <tr>
                        <th className="px-12 py-10">Classification</th>
                        <th className="px-12 py-10">Identifier</th>
                        <th className="px-12 py-10">Generated At</th>
                        <th className="px-12 py-10 text-right">Action</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {reports.map((r, i) => (
                        <tr key={i} className="group hover:bg-slate-50 transition-colors">
                          <td className="px-12 py-10">
                            <span className={`px-6 py-2.5 rounded-2xl text-[10px] font-black uppercase tracking-[0.2em] border ${
                              r.name.includes('Campaigns') ? 'bg-orange-50 border-orange-100 text-orange-600' : 'bg-slate-50 border-slate-200 text-slate-600'
                            }`}>
                              {r.name.includes('Campaigns') ? 'STRATEGIC' : 'DATA'}
                            </span>
                          </td>
                          <td className="px-12 py-10 font-black text-slate-900 text-xl">{r.name}</td>
                          <td className="px-12 py-10 text-slate-400 text-sm font-bold">{new Date(r.created_at).toLocaleString()}</td>
                          <td className="px-12 py-10 text-right">
                            <div className="flex justify-end gap-6 opacity-0 group-hover:opacity-100 transition-opacity">
                              <button onClick={() => handlePreview(r.csv)} className="p-5 bg-white border border-slate-200 rounded-[1.5rem] hover:text-un-amazon transition-all"><Eye size={24} /></button>
                              <button onClick={() => handleDownload(r.xlsx)} className="p-5 bg-white border border-slate-200 rounded-[1.5rem] hover:text-emerald-600 transition-all"><FileSpreadsheet size={24} /></button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </main>

        {/* Global Loading Overlay for Preview */}
        {isPreviewLoading && (
            <div className="absolute inset-0 bg-white/60 backdrop-blur-sm z-50 flex items-center justify-center">
                <div className="flex flex-col items-center gap-6">
                    <Loader2 size={64} className="animate-spin text-un-amazon" />
                    <span className="text-lg font-black text-slate-900 uppercase tracking-widest">Streaming Intelligence...</span>
                </div>
            </div>
        )}
      </motion.div>
    </div>
  );
}

function SidebarLink({ icon, label, active, onClick, isCollapsed }) {
  return (
    <button 
      onClick={onClick} 
      className={`flex items-center gap-4 w-full py-3.5 rounded-2xl transition-all duration-300 ${
        active 
          ? 'bg-un-amazon/10 text-un-amazon shadow-sm' 
          : 'text-slate-500 hover:text-slate-900 hover:bg-slate-50'
      } ${isCollapsed ? 'justify-center px-0' : 'px-5'}`}
    >
      <div className={`${active ? 'scale-110' : ''} transition-transform`}>
        {icon}
      </div>
      {!isCollapsed && (
        <motion.span 
          initial={{ opacity: 0, x: -10 }}
          animate={{ opacity: 1, x: 0 }}
          className={`text-sm font-bold tracking-tight ${active ? 'font-black' : ''} whitespace-nowrap`}
        >
          {label}
        </motion.span>
      )}
    </button>
  );
}

export default App;
