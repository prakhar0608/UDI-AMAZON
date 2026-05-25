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

const Counter = ({ value, prefix = "", suffix = "", decimals = 0 }) => {
  const [displayValue, setDisplayValue] = useState(parseFloat(value) || 0);
  const prevValueRef = useRef(parseFloat(value) || 0);
  
  useEffect(() => {
    const end = parseFloat(value) || 0;
    const start = prevValueRef.current;
    prevValueRef.current = end;
    
    // Skip animation for zero or same value
    if (end === start) {
      setDisplayValue(end);
      return;
    }
    
    const duration = 800; // ms
    let startTime = null;
    let rafId = null;
    
    const animate = (timestamp) => {
      if (!startTime) startTime = timestamp;
      const elapsed = timestamp - startTime;
      const progress = Math.min(elapsed / duration, 1);
      // Ease out cubic
      const eased = 1 - Math.pow(1 - progress, 3);
      const current = start + (end - start) * eased;
      setDisplayValue(current);
      
      if (progress < 1) {
        rafId = requestAnimationFrame(animate);
      }
    };
    
    rafId = requestAnimationFrame(animate);
    return () => {
      if (rafId) cancelAnimationFrame(rafId);
      // On cleanup, always snap to the target value
      setDisplayValue(end);
    };
  }, [value]);

  return (
    <span>
      {prefix}
      {displayValue.toLocaleString(undefined, {
        minimumFractionDigits: decimals,
        maximumFractionDigits: decimals,
      })}
      {suffix}
    </span>
  );
};

const KPICard = ({ title, value, change, isPositive, prefix = "", suffix = "", decimals = 0, sparklineData }) => {
  return (
    <motion.div 
      whileHover={{ y: -2 }}
      className="un-card-compact flex flex-col gap-1 group cursor-pointer"
    >
      <div className="flex justify-between items-start">
        <span className="text-[10px] font-black text-slate-400 uppercase tracking-wider">{title}</span>
        <div className={`flex items-center gap-0.5 text-[10px] font-bold ${isPositive ? 'text-emerald-500' : 'text-rose-500'}`}>
          {isPositive ? '↑' : '↓'} {Math.abs(change)}%
        </div>
      </div>
      <div className="text-xl font-black text-slate-900">
        <Counter value={value} prefix={prefix} suffix={suffix} decimals={decimals} />
      </div>
      <div className="flex items-center justify-between mt-1">
        <span className="text-[9px] text-slate-400 font-medium">vs yesterday</span>
        <div className="h-6 w-16 opacity-40 group-hover:opacity-100 transition-opacity">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={sparklineData}>
              <Area 
                type="monotone" 
                dataKey="val" 
                stroke={isPositive ? '#10b981' : '#f43f5e'} 
                fill={isPositive ? '#10b98120' : '#f43f5e20'} 
                strokeWidth={1.5} 
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>
    </motion.div>
  );
};

const TrendChart = ({ data }) => {
  const [activeTab, setActiveTab] = useState('spend');
  
  const tabs = [
    { id: 'spend', label: 'Spend', color: '#ff9900', prefix: '₹' },
    { id: 'sales', label: 'Sales', color: '#10b981', prefix: '₹' },
    { id: 'roas', label: 'ROAS', color: '#3b82f6', suffix: 'x' },
    { id: 'acos', label: 'ACOS', color: '#ef4444', suffix: '%' },
  ];

  const activeColor = tabs.find(t => t.id === activeTab).color;

  return (
    <div className="un-card !p-6 flex flex-col gap-6">
      <div className="flex justify-between items-center">
        <h3 className="text-sm font-black text-slate-900 uppercase tracking-tight flex items-center gap-2">
          <Activity size={16} className="text-un-amazon" /> Performance Trends
        </h3>
        <div className="flex bg-slate-50 p-1 rounded-lg border border-slate-200">
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-3 py-1.5 text-[10px] font-black rounded-md transition-all ${
                activeTab === tab.id 
                  ? 'bg-white text-slate-900 shadow-sm border border-slate-200' 
                  : 'text-slate-400 hover:text-slate-600'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>
      
      <div className="h-[250px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={data}>
            <defs>
              <linearGradient id="chartGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor={activeColor} stopOpacity={0.1}/>
                <stop offset="95%" stopColor={activeColor} stopOpacity={0}/>
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
            <XAxis 
              dataKey="day" 
              axisLine={false} 
              tickLine={false} 
              tick={{fontSize: 10, fontWeight: 700, fill: '#94a3b8'}} 
              dy={10}
            />
            <YAxis 
              axisLine={false} 
              tickLine={false} 
              tick={{fontSize: 10, fontWeight: 700, fill: '#94a3b8'}}
            />
            <Tooltip 
              contentStyle={{ 
                borderRadius: '12px', 
                border: '1px solid #e2e8f0', 
                boxShadow: '0 10px 15px -3px rgb(0 0 0 / 0.1)',
                fontSize: '11px',
                fontWeight: 'bold'
              }}
            />
            <Area 
              type="monotone" 
              dataKey={activeTab} 
              stroke={activeColor} 
              strokeWidth={3} 
              fillOpacity={1} 
              fill="url(#chartGradient)" 
              animationDuration={1500}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

const InsightCard = ({ title, value, icon: Icon, colorClass }) => (
  <motion.div 
    whileHover={{ y: -2 }}
    className="un-card-compact !p-4 flex items-center gap-4 cursor-pointer"
  >
    <div className={`p-2.5 rounded-lg ${colorClass} bg-opacity-10 shadow-sm`}>
      <Icon size={16} className={colorClass.replace('bg-', 'text-')} />
    </div>
    <div>
      <div className="text-[9px] font-black text-slate-400 uppercase tracking-widest">{title}</div>
      <div className="text-sm font-black text-slate-900">{value}</div>
    </div>
  </motion.div>
);

const ItemTable = ({ items, title, prefix = "" }) => {
  if (!items || items.length === 0) return null;

  return (
    <div className="un-card !p-0 overflow-hidden border-slate-200 shadow-sm mt-8">
      <div className="px-8 py-6 bg-slate-50 border-b border-slate-200 flex justify-between items-center">
        <h3 className="text-xs font-black text-slate-900 uppercase tracking-widest flex items-center gap-2">
          <Table size={14} className="text-un-amazon" /> {title} Performance
        </h3>
        <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest">{items.length} Items</span>
      </div>
      <div className="overflow-x-auto un-scrollbar">
        <table className="w-full text-left">
          <thead className="bg-white text-[9px] font-black uppercase tracking-widest text-slate-400 border-b border-slate-100">
            <tr>
              <th className="px-8 py-4">Name</th>
              <th className="px-8 py-4 text-right">Spend</th>
              <th className="px-8 py-4 text-right">Sales</th>
              <th className="px-8 py-4 text-right">Clicks</th>
              <th className="px-8 py-4 text-right">Orders</th>
              <th className="px-8 py-4 text-right">ROAS</th>
              <th className="px-8 py-4 text-right">ACOS</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-50">
            {items.map((item, i) => (
              <tr key={i} className="group hover:bg-slate-50 transition-colors">
                <td className="px-8 py-4">
                  <div className="text-sm font-black text-slate-900 truncate max-w-[300px]" title={item.name}>{item.name}</div>
                </td>
                <td className="px-8 py-4 text-right text-sm font-bold text-slate-600">
                  {prefix}{item.spend.toLocaleString()}
                </td>
                <td className="px-8 py-4 text-right text-sm font-bold text-slate-900">
                  {prefix}{item.sales.toLocaleString()}
                </td>
                <td className="px-8 py-4 text-right text-sm font-bold text-slate-500">
                  {item.clicks.toLocaleString()}
                </td>
                <td className="px-8 py-4 text-right text-sm font-bold text-slate-500">
                  {item.orders.toLocaleString()}
                </td>
                <td className="px-8 py-4 text-right">
                  <span className={`px-3 py-1 rounded-lg text-[10px] font-black ${item.roas >= 2 ? 'bg-emerald-50 text-emerald-600' : 'bg-slate-50 text-slate-600'}`}>
                    {item.roas.toFixed(2)}x
                  </span>
                </td>
                <td className="px-8 py-4 text-right">
                  <span className={`px-3 py-1 rounded-lg text-[10px] font-black ${item.acos <= 30 && item.acos > 0 ? 'bg-blue-50 text-blue-600' : 'bg-slate-50 text-slate-600'}`}>
                    {item.acos.toFixed(2)}%
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

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

  const [realtimeData, setRealtimeData] = useState({
    spend: 0, sales: 0, roas: 0, acos: 0, ctr: 0, cpc: 0, cvr: 0, trend: [], items: []
  });
  const [isRealtimeLoading, setIsRealtimeLoading] = useState(false);

  useEffect(() => {
    fetchRealtimeAnalytics();
  }, [selectedIds, selectedLevel, startDate, endDate]);

  const fetchRealtimeAnalytics = async () => {
    if (selectedIds.length === 0) {
        setRealtimeData({spend: 0, sales: 0, roas: 0, acos: 0, ctr: 0, cpc: 0, cvr: 0, trend: []});
        return;
    }
    setIsRealtimeLoading(true);
    try {
        const res = await axios.post(`${API_BASE}/analytics/realtime`, {
            ids: selectedIds,
            report_type: selectedLevel,
            start_date: startDate,
            end_date: endDate
        });
        setRealtimeData(res.data);
    } catch (err) {
        console.error("Realtime analytics fetch failed", err);
    } finally {
        setIsRealtimeLoading(false);
    }
  };

  const kpiData = [
    { title: 'Spend', value: realtimeData.spend, change: 0, isPositive: false, prefix: "₹", decimals: 2, sparkline: realtimeData.trend.map(d => ({val: d.spend})) },
    { title: 'Sales', value: realtimeData.sales, change: 0, isPositive: true, prefix: "₹", decimals: 2, sparkline: realtimeData.trend.map(d => ({val: d.sales})) },
    { title: 'ROAS', value: realtimeData.roas, change: 0, isPositive: true, suffix: "x", decimals: 2, sparkline: realtimeData.trend.map(d => ({val: d.roas})) },
    { title: 'ACOS', value: realtimeData.acos, change: 0, isPositive: true, suffix: "%", decimals: 2, sparkline: realtimeData.trend.map(d => ({val: d.acos})) },
    { title: 'CTR', value: realtimeData.ctr, change: 0, isPositive: true, suffix: "%", decimals: 2, sparkline: realtimeData.trend.map(d => ({val: d.spend > 0 ? (realtimeData.clicks / (realtimeData.spend * 100)) : 0})) }, // Simplified CTR sparkline logic
    { title: 'CPC', value: realtimeData.cpc, change: 0, isPositive: false, prefix: "₹", decimals: 2, sparkline: realtimeData.trend.map(d => ({val: d.spend / 10})) },
    { title: 'CVR', value: realtimeData.cvr, change: 0, isPositive: true, suffix: "%", decimals: 2, sparkline: realtimeData.trend.map(d => ({val: d.sales / 100})) },
  ];

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
      alert("Account discovery failed. Please check your .env API keys and internet connection.");
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
                    const displayMsg = job.message.toLowerCase().includes("polling") 
                        ? "Preparing campaign insights..." 
                        : job.message;
                    addLog("SYNC", displayMsg);
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
                    fetchRealtimeAnalytics();
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
                <div className="animate-float-subtle flex-1 flex justify-center pl-4">
                  <img 
                    src="https://upload.wikimedia.org/wikipedia/commons/a/a9/Amazon_logo.svg" 
                    className="h-7 w-auto object-contain" 
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
                className="flex flex-col items-center w-full"
              >
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
          <div className="my-1 border-t border-slate-100 mx-3 opacity-50" />
          <SidebarLink icon={<Target size={22} />} label="Campaign" active={view === 'campaign'} onClick={() => { setView('campaign'); setSelectedLevel('spCampaigns'); }} isCollapsed={isCollapsed} />
          <SidebarLink icon={<Layers size={22} />} label="Ad Group" active={view === 'ad-group'} onClick={() => { setView('ad-group'); setSelectedLevel('spAdGroups'); }} isCollapsed={isCollapsed} />
          <SidebarLink icon={<Box size={22} />} label="ASIN" active={view === 'asin'} onClick={() => { setView('asin'); setSelectedLevel('spProducts'); }} isCollapsed={isCollapsed} />
          <div className="my-1 border-t border-slate-100 mx-3 opacity-50" />
          <SidebarLink icon={<BarChart3 size={22} />} label="Analytics" active={view === 'analytics'} onClick={() => setView('analytics')} isCollapsed={isCollapsed} />
          <SidebarLink icon={<History size={22} />} label="History" active={view === 'reports'} onClick={() => setView('reports')} isCollapsed={isCollapsed} />
        </nav>
        
        {/* Action Buttons - Bottom */}
        <div className="mt-auto flex flex-col gap-1.5">
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
        </div>
      </motion.aside>

      <motion.div 
        animate={{ marginLeft: isCollapsed ? 72 : 256 }}
        transition={{ type: 'spring', stiffness: 300, damping: 30 }}
        className="flex-1 flex flex-col overflow-hidden relative"
      >
        
        {/* Top Header Section (Searchable Dropdown for Accounts) */}
        <div className="bg-white/80 backdrop-blur-md border-b border-slate-200 px-10 py-4 flex items-center justify-between z-30">
          <div className="flex items-center gap-6">
            <div className="text-left">
              <div className="text-[9px] font-black uppercase tracking-widest text-slate-400">System Status</div>
              <div className="text-xs font-black text-emerald-600 flex items-center gap-2">
                <div className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                OPERATIONAL
              </div>
            </div>
          </div>

          <div className="relative" ref={dropdownRef}>
            <button 
              onClick={() => setIsAccountDropdownOpen(!isAccountDropdownOpen)}
              className="flex items-center gap-4 px-5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl hover:border-un-amazon/40 transition-all group"
            >
              <div className="w-8 h-8 rounded-lg bg-un-amazon/10 text-un-amazon flex items-center justify-center">
                <User size={16} />
              </div>
              <div className="text-left">
                <div className="text-[9px] font-black uppercase tracking-widest text-slate-400">Target Accounts</div>
                <div className="text-xs font-black text-slate-900">
                  {selectedIds.length === 0 ? "Select Accounts" : `${selectedIds.length} Selected`}
                </div>
              </div>
              <ChevronDown size={16} className={`text-slate-300 transition-transform ${isAccountDropdownOpen ? 'rotate-180' : ''}`} />
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
                    <div className="flex items-center gap-2 mb-2 px-6">
                      <button 
                        onClick={handleDiscover}
                        disabled={isDiscovering}
                        className="flex-1 flex items-center justify-center gap-2 py-3 bg-un-amazon/10 text-un-amazon rounded-xl text-[10px] font-black uppercase tracking-widest hover:bg-un-amazon/20 transition-all disabled:opacity-50"
                      >
                        {isDiscovering ? <Loader2 size={12} className="animate-spin" /> : <RefreshCw size={12} />}
                        Discover Accounts
                      </button>
                      <button 
                        onClick={() => setSelectedIds(selectedIds.length === profiles.length ? [] : profiles.map(p => p.id))}
                        className="flex-1 py-3 border border-slate-200 text-slate-400 rounded-xl text-[10px] font-black uppercase tracking-widest hover:bg-slate-50 transition-all"
                      >
                        {selectedIds.length === profiles.length ? "Deselect All" : "Select All"}
                      </button>
                    </div>
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
        <main className="flex-1 overflow-y-auto p-10 un-scrollbar bg-white/50">
          <AnimatePresence mode="wait">
            {view === 'dashboard' && (
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="max-w-[1600px] mx-auto space-y-8"
              >
                <header className="flex justify-between items-end border-b border-slate-100 pb-6">
                  <div className="space-y-3">
                    <div className="inline-flex items-center gap-2 px-3 py-1 bg-slate-100/50 rounded-full border border-slate-200">
                      <Sparkles size={12} className="text-un-amazon" />
                      <span className="text-[9px] font-black uppercase tracking-widest text-slate-500">Enterprise Ad Intelligence</span>
                    </div>
                    <h1 className="text-5xl font-black tracking-tight leading-none text-slate-900">
                      Amazon <span className="text-gradient">Intelligence</span>
                    </h1>
                  </div>

                  {lastSyncResult && (
                    <motion.div 
                      initial={{ opacity: 0, scale: 0.95 }}
                      animate={{ opacity: 1, scale: 1 }}
                      className="un-card-compact !py-3 !px-5 bg-slate-900 flex items-center gap-4 text-white border-un-amazon/20 shadow-xl shadow-un-amazon/10"
                    >
                      <div className="w-10 h-10 bg-un-amazon rounded-xl flex items-center justify-center">
                        <Download size={20} className="text-slate-900" />
                      </div>
                      <div>
                        <div className="text-[9px] font-black text-slate-400 uppercase tracking-widest mb-0.5">Sync Complete</div>
                        <div className="flex gap-4">
                            <button 
                            onClick={() => handleDownload(lastSyncResult.xlsx_name)}
                            className="text-xs font-black hover:text-un-amazon transition-colors flex items-center gap-1 group"
                            >
                            EXCEL <ChevronRight size={14} />
                            </button>
                            <button 
                            onClick={() => handlePreview(lastSyncResult.csv_name)}
                            className="text-xs font-black hover:text-un-amazon transition-colors flex items-center gap-1 group"
                            >
                            PREVIEW <Eye size={14} />
                            </button>
                        </div>
                      </div>
                    </motion.div>
                  )}
                </header>

                {/* Executive KPI Strip */}
                <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4">
                  {kpiData.map((kpi, idx) => (
                    <KPICard key={idx} {...kpi} sparklineData={kpi.sparkline} />
                  ))}
                </div>

                {/* Trend Analytics Section */}
                <div className="grid grid-cols-12 gap-6 items-start">
                  <div className="col-span-12 lg:col-span-8 relative">
                    {isRealtimeLoading && (
                        <div className="absolute inset-0 bg-white/50 backdrop-blur-sm z-10 flex items-center justify-center rounded-2xl">
                            <Loader2 className="animate-spin text-un-amazon" size={32} />
                        </div>
                    )}
                    <TrendChart data={realtimeData.trend && realtimeData.trend.length > 0 ? realtimeData.trend : []} />
                  </div>
                  <div className="col-span-12 lg:col-span-4 grid grid-cols-1 gap-4">
                    <InsightCard 
                      title="Best Performing Day" 
                      value={realtimeData.trend && realtimeData.trend.length > 0 
                        ? realtimeData.trend.reduce((best, d) => d.roas > best.roas ? d : best, realtimeData.trend[0]).date 
                        : "No data"} 
                      icon={Flame} 
                      colorClass="bg-orange-500" 
                    />
                    <InsightCard 
                      title="Highest ROAS" 
                      value={realtimeData.trend && realtimeData.trend.length > 0 
                        ? realtimeData.trend.reduce((best, d) => d.roas > best.roas ? d : best, realtimeData.trend[0]).roas + "x"
                        : "0x"} 
                      icon={TrendingUp} 
                      colorClass="bg-emerald-500" 
                    />
                    <InsightCard 
                      title="Lowest ACOS" 
                      value={realtimeData.trend && realtimeData.trend.length > 0 
                        ? realtimeData.trend.filter(d => d.acos > 0).reduce((best, d) => d.acos < best.acos ? d : best, realtimeData.trend.filter(d => d.acos > 0)[0] || {acos: 0}).acos + "%"
                        : "0%"}
                      icon={Sparkles} 
                      colorClass="bg-blue-500" 
                    />
                  </div>
                </div>

                <div className="grid grid-cols-12 gap-6">
                  <div className="col-span-12 un-card !p-8">
                    <div className="flex items-center gap-3 mb-6">
                      <div className="p-2 bg-un-amazon/10 rounded-xl text-un-amazon">
                        <Calendar size={18} />
                      </div>
                      <h3 className="text-[10px] font-black uppercase tracking-widest text-slate-400">Date Range Selection</h3>
                    </div>

                    <div className="grid grid-cols-11 items-center gap-4">
                      <div className="col-span-5 space-y-2">
                        <label className="text-[9px] font-black text-slate-500 uppercase tracking-widest ml-1">Start Date</label>
                        <input 
                          type="date" 
                          value={startDate}
                          onChange={(e) => setStartDate(e.target.value)}
                          className="w-full bg-slate-50 border border-slate-200 rounded-xl py-3 px-6 text-sm font-black focus:border-un-amazon/40 focus:bg-white outline-none transition-all"
                        />
                      </div>
                      <div className="col-span-1 flex justify-center mt-6">
                        <ArrowRight className="text-slate-200" size={20} />
                      </div>
                      <div className="col-span-5 space-y-2">
                        <label className="text-[9px] font-black text-slate-500 uppercase tracking-widest ml-1">End Date</label>
                        <input 
                          type="date" 
                          value={endDate}
                          onChange={(e) => setEndDate(e.target.value)}
                          className="w-full bg-slate-50 border border-slate-200 rounded-xl py-3 px-6 text-sm font-black focus:border-un-amazon/40 focus:bg-white outline-none transition-all"
                        />
                      </div>
                    </div>
                  </div>
                </div>

                <div className="flex flex-col items-center gap-8 pb-12">
                  <div className="text-center space-y-2">
                    <p className="text-xs font-bold text-slate-400 uppercase tracking-widest">Select a level from the sidebar to view detailed analytics and run exports</p>
                  </div>
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

            {(view === 'campaign' || view === 'ad-group' || view === 'asin') && (
              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                className="max-w-[1600px] mx-auto space-y-8"
              >
                <header className="flex justify-between items-end border-b border-slate-100 pb-6">
                  <div className="space-y-3">
                    <div className="inline-flex items-center gap-2 px-3 py-1 bg-un-amazon/10 rounded-full border border-un-amazon/20">
                      <Target size={12} className="text-un-amazon" />
                      <span className="text-[9px] font-black uppercase tracking-widest text-un-amazon">
                        {view.toUpperCase().replace('-', ' ')} LEVEL ANALYTICS
                      </span>
                    </div>
                    <h1 className="text-5xl font-black tracking-tight leading-none text-slate-900 capitalize">
                      {view.replace('-', ' ')} <span className="text-gradient">Performance</span>
                    </h1>
                  </div>

                  <div className="flex items-center gap-4">
                    <button 
                      onClick={runBulkSync} 
                      disabled={isBulkRunning || selectedIds.length === 0} 
                      className="btn-un-amazon flex items-center gap-3 px-8 py-4 text-sm font-black group shadow-lg hover:shadow-un-amazon/20"
                    >
                      {isBulkRunning ? (
                        <div className="flex items-center gap-3">
                          <Loader2 size={18} className="animate-spin text-white" />
                          <span className="animate-pulse">
                            {logs.length > 0 && logs[logs.length-1].message.toLowerCase().includes("polling") 
                              ? "PREPARING CAMPAIGN INSIGHTS..." 
                              : logs.length > 0 ? logs[logs.length-1].message.toUpperCase() : 'EXECUTING...'}
                          </span>
                        </div>
                      ) : (
                        <><Play size={18} fill="currentColor" /> RUN EXPORT</>
                      )}
                    </button>
                  </div>
                </header>

                <div className="grid grid-cols-12 gap-6">
                  <div className="col-span-12 un-card !p-8 flex items-center justify-between">
                    <div className="flex items-center gap-8 flex-1">
                      <div className="space-y-1.5 flex-1">
                        <label className="text-[9px] font-black text-slate-400 uppercase tracking-widest ml-1">Start Date</label>
                        <input 
                          type="date" 
                          value={startDate}
                          onChange={(e) => setStartDate(e.target.value)}
                          className="w-full bg-slate-50 border border-slate-200 rounded-xl py-3 px-6 text-sm font-black focus:border-un-amazon/40 focus:bg-white outline-none transition-all"
                        />
                      </div>
                      <ArrowRight className="text-slate-200 mt-6" size={20} />
                      <div className="space-y-1.5 flex-1">
                        <label className="text-[9px] font-black text-slate-400 uppercase tracking-widest ml-1">End Date</label>
                        <input 
                          type="date" 
                          value={endDate}
                          onChange={(e) => setEndDate(e.target.value)}
                          className="w-full bg-slate-50 border border-slate-200 rounded-xl py-3 px-6 text-sm font-black focus:border-un-amazon/40 focus:bg-white outline-none transition-all"
                        />
                      </div>
                    </div>
                  </div>
                </div>

                {/* Executive KPI Strip */}
                <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-4">
                  {kpiData.map((kpi, idx) => (
                    <KPICard key={idx} {...kpi} sparklineData={kpi.sparkline} />
                  ))}
                </div>

                {/* Detailed Item List */}
                <ItemTable 
                  items={realtimeData.items} 
                  title={view.replace('-', ' ').toUpperCase()} 
                  prefix="₹"
                />

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
              <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-8 max-w-[1600px] mx-auto">
                 <header className="border-b border-slate-100 pb-4">
                  <h1 className="text-4xl font-black tracking-tight text-slate-900">Intelligence <span className="text-gradient">Analytics</span></h1>
                </header>
                <div className="grid grid-cols-12 gap-6">
                  <div className="col-span-12 un-card h-[400px] !p-6">
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
                initial={{ opacity: 0, x: 10 }}
                animate={{ opacity: 1, x: 0 }}
                className="space-y-8 max-w-[1600px] mx-auto"
              >
                <header className="border-b border-slate-100 pb-4">
                  <h1 className="text-4xl font-black tracking-tight text-slate-900">The <span className="text-un-amazon">Vault</span></h1>
                </header>

                <div className="un-card !p-0 overflow-hidden border-slate-200 shadow-sm">
                  <table className="w-full text-left">
                    <thead className="bg-slate-50 text-[9px] font-black uppercase tracking-widest text-slate-400">
                      <tr>
                        <th className="px-8 py-4">Classification</th>
                        <th className="px-8 py-4">Identifier</th>
                        <th className="px-8 py-4">Generated At</th>
                        <th className="px-8 py-4 text-right">Action</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {reports.map((r, i) => (
                        <tr key={i} className="group hover:bg-slate-50 transition-colors">
                          <td className="px-8 py-4">
                            <span className={`px-4 py-1.5 rounded-xl text-[9px] font-black uppercase tracking-widest border ${
                              r.name.includes('Campaigns') ? 'bg-orange-50 border-orange-100 text-orange-600' : 'bg-slate-50 border-slate-200 text-slate-600'
                            }`}>
                              {r.name.includes('Campaigns') ? 'STRATEGIC' : 'DATA'}
                            </span>
                          </td>
                          <td className="px-8 py-4 font-black text-slate-900 text-lg">{r.name}</td>
                          <td className="px-8 py-4 text-slate-400 text-xs font-bold">{new Date(r.created_at).toLocaleString()}</td>
                          <td className="px-8 py-4 text-right">
                            <div className="flex justify-end gap-3 opacity-0 group-hover:opacity-100 transition-opacity">
                              <button onClick={() => handlePreview(r.csv)} className="p-3 bg-white border border-slate-200 rounded-xl hover:text-un-amazon transition-all"><Eye size={18} /></button>
                              <button onClick={() => handleDownload(r.xlsx)} className="p-3 bg-white border border-slate-200 rounded-xl hover:text-emerald-600 transition-all"><FileSpreadsheet size={18} /></button>
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
