import React, { useState, useEffect, useMemo } from 'react';
import axios from 'axios';
import { 
  LayoutDashboard, 
  Users, 
  FileText, 
  RefreshCw, 
  Search,
  ChevronRight,
  Target,
  Layers,
  Box,
  Globe,
  Loader2,
  DownloadCloud,
  FileSpreadsheet,
  FileCode,
  CheckSquare,
  Square,
  Play,
  CheckCircle2,
  AlertCircle,
  Zap,
  TrendingUp,
  BarChart3,
  Cpu,
  BrainCircuit,
  Activity,
  ArrowUpRight,
  ArrowDownRight,
  Settings,
  PieChart as PieChartIcon,
  Filter,
  ArrowLeft,
  DollarSign,
  ShoppingCart,
  Coins,
  History,
  Calendar,
  Clock
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  LineChart, 
  Line, 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  Legend
} from 'recharts';

const API_BASE = 'http://localhost:8000/api';

const REPORT_LEVELS = [
  { id: 'spCampaigns', label: 'Campaigns', icon: <Target size={18} />, desc: 'Strategy' },
  { id: 'spAdGroups', label: 'Ad Groups', icon: <Layers size={18} />, desc: 'Structure' },
  { id: 'spProducts', label: 'Products', icon: <Box size={18} />, desc: 'Inventory' },
];

const COLORS = ['#0ea5e9', '#8b5cf6', '#f59e0b', '#10b981', '#ef4444', '#ec4899', '#f97316'];

function App() {
  const [profiles, setProfiles] = useState([]);
  const [reports, setReports] = useState([]);
  const [rangeData, setRangeData] = useState(null);
  const [selectedProfile, setSelectedProfile] = useState(null);
  const [selectedIds, setSelectedIds] = useState([]);
  const [selectedLevel, setSelectedLevel] = useState('spCampaigns');
  const [syncStatus, setSyncStatus] = useState({});
  const [isBulkRunning, setIsBulkRunning] = useState(false);
  const [isDiscovering, setIsDiscovering] = useState(false);
  
  // Date Filters
  const [startDate, setStartDate] = useState(() => {
    const d = new Date();
    d.setDate(1); // Default to start of month
    return d.toISOString().split('T')[0];
  });
  const [useMtd, setUseMtd] = useState(true);
  
  const [searchTerm, setSearchTerm] = useState('');
  const [view, setView] = useState('dashboard');
  const [lastSyncResult, setLastSyncResult] = useState(null);

  useEffect(() => {
    fetchProfiles();
    fetchReports();
    fetchRangeAnalytics();
  }, []);

  const fetchProfiles = async () => {
    try {
      const res = await axios.get(`${API_BASE}/profiles`);
      setProfiles(res.data);
      if (res.data.length > 0 && !selectedProfile) {
        setSelectedProfile(res.data[0]);
      }
    } catch (err) {
      console.error('Failed to fetch profiles', err);
    }
  };

  const fetchRangeAnalytics = async () => {
    try {
      const res = await axios.get(`${API_BASE}/analytics/ranges`);
      setRangeData(res.data);
    } catch (err) {
      console.error('Failed to fetch range analytics', err);
    }
  };

  const handleDiscover = async () => {
    setIsDiscovering(true);
    try {
      const res = await axios.post(`${API_BASE}/discover`);
      setProfiles(res.data);
      alert(`Discovery complete: Found ${res.data.length} accounts.`);
    } catch (err) {
      alert('Discovery failed: ' + (err.response?.data?.detail || err.message));
    } finally {
      setIsDiscovering(false);
    }
  };

  const fetchReports = async () => {
    try {
      const res = await axios.get(`${API_BASE}/reports`);
      setReports(res.data);
    } catch (err) {
      console.error('Failed to fetch reports', err);
    }
  };

  const toggleSelect = (id) => {
    setSelectedIds(prev => 
      prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
    );
  };

  const selectAll = () => {
    if (selectedIds.length === filteredProfiles.length) {
      setSelectedIds([]);
    } else {
      setSelectedIds(filteredProfiles.map(p => p.id));
    }
  };

  const runBulkSync = async () => {
    const idsToRun = selectedIds.length > 0 ? selectedIds : (selectedProfile ? [selectedProfile.id] : []);
    if (idsToRun.length === 0) return;

    setIsBulkRunning(true);
    setLastSyncResult(null);
    const newStatus = { ...syncStatus };
    idsToRun.forEach(id => newStatus[id] = 'running');
    setSyncStatus(newStatus);

    let lastRes = null;
    for (const id of idsToRun) {
      try {
        const res = await axios.post(`${API_BASE}/fetch/${id}`, {
          report_type: selectedLevel,
          mtd: useMtd,
          start_date: useMtd ? null : startDate
        }, {
          params: { // Using params because our backend handles them as query/path
             report_type: selectedLevel,
             mtd: useMtd,
             start_date: useMtd ? null : startDate
          }
        });
        setSyncStatus(prev => ({ ...prev, [id]: 'success' }));
        lastRes = res.data;
      } catch (err) {
        setSyncStatus(prev => ({ ...prev, [id]: 'error' }));
      }
    }

    setIsBulkRunning(false);
    setLastSyncResult(lastRes);
    fetchReports();
    fetchRangeAnalytics();
  };

  const handleDownload = (filename) => {
    window.open(`${API_BASE}/reports/download/${filename}`, '_blank');
  };

  const filteredProfiles = profiles.filter(p => 
    p.display_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    p.region.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 flex font-sans overflow-hidden bg-ai-grid">
      {/* Sidebar 1: Pro Navigation */}
      <aside className="w-20 bg-white border-r border-slate-200 flex flex-col items-center py-8 gap-10 z-20 shadow-sm">
        <div className="relative group">
          <div className="absolute -inset-1 bg-ai-gradient rounded-2xl blur opacity-20 group-hover:opacity-40 transition duration-500"></div>
          <div className="relative bg-white p-3 rounded-2xl border border-slate-200 shadow-sm">
            <BrainCircuit className="text-ai-neon" size={24} />
          </div>
        </div>
        
        <nav className="flex flex-col gap-6">
          <NavIcon 
            icon={<LayoutDashboard size={24} />} 
            active={view === 'dashboard'} 
            onClick={() => setView('dashboard')} 
            label="Sync"
          />
          <NavIcon 
            icon={<BarChart3 size={24} />} 
            active={view === 'analytics'} 
            onClick={() => setView('analytics')} 
            label="Trends"
          />
          <NavIcon 
            icon={<FileText size={24} />} 
            active={view === 'reports'} 
            onClick={() => setView('reports')} 
            label="Vault"
          />
        </nav>
        
        <div className="mt-auto flex flex-col gap-6">
          <button 
            onClick={handleDiscover}
            disabled={isDiscovering}
            className="p-3 text-slate-400 hover:text-ai-neon transition-all hover:scale-110"
          >
            {isDiscovering ? <Loader2 size={24} className="animate-spin" /> : <RefreshCw size={24} />}
          </button>
        </div>
      </aside>

      {/* Sidebar 2: Nodes */}
      <aside className="w-80 bg-white/60 border-r border-slate-200 flex flex-col z-10 backdrop-blur-xl">
        <div className="p-6 border-b border-slate-200">
          <div className="flex justify-between items-center mb-6">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-ai-neon animate-pulse"></div>
              <h2 className="text-xs font-black uppercase tracking-[0.2em] text-slate-400">Client Nodes</h2>
            </div>
            <button 
              onClick={selectAll}
              className="text-[10px] font-bold text-ai-neon hover:bg-ai-neon/10 transition-colors px-2 py-1 rounded"
            >
              {selectedIds.length === filteredProfiles.length && filteredProfiles.length > 0 ? 'DESELECT' : 'SELECT ALL'}
            </button>
          </div>
          <div className="relative group">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 group-focus-within:text-ai-neon transition-colors" size={14} />
            <input 
              type="text" 
              placeholder="Search nodes..." 
              className="w-full bg-slate-100 border border-transparent rounded-xl py-3 pl-10 pr-4 text-xs focus:bg-white focus:border-ai-neon/30 outline-none transition-all"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
        </div>
        <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-3 custom-scrollbar">
          {filteredProfiles.map((p) => (
            <motion.div
              layout
              key={p.id}
              onClick={() => setSelectedProfile(p)}
              className={`relative flex items-center gap-4 p-4 rounded-xl transition-all border ${
                selectedProfile?.id === p.id 
                  ? 'bg-ai-neon/5 border-ai-neon/20 shadow-sm' 
                  : 'hover:bg-slate-100 border-transparent'
              }`}
            >
              <button 
                onClick={(e) => { e.stopPropagation(); toggleSelect(p.id); }}
                className={`transition-all transform hover:scale-110 ${selectedIds.includes(p.id) ? 'text-ai-neon' : 'text-slate-300'}`}
              >
                {selectedIds.includes(p.id) ? <CheckSquare size={20} /> : <Square size={20} />}
              </button>
              <div className="flex-1 overflow-hidden">
                <div className="flex justify-between items-center mb-1">
                  <span className={`font-bold text-sm truncate ${selectedProfile?.id === p.id ? 'text-slate-900' : 'text-slate-600'}`}>
                    {p.display_name}
                  </span>
                  <StatusIcon status={syncStatus[p.id]} />
                </div>
                <div className="flex items-center gap-2 text-[10px] font-bold text-slate-400">
                  <span className="bg-slate-200 px-1.5 py-0.5 rounded uppercase">{p.region}</span>
                  <span className="opacity-60">{p.currency_code}</span>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 overflow-y-auto p-12 relative bg-white/20">
        <AnimatePresence mode="wait">
          {view === 'dashboard' && (
            <motion.div
              key="dashboard"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="max-w-6xl mx-auto space-y-12"
            >
              <header className="flex justify-between items-end">
                <div>
                  <h1 className="text-6xl font-black tracking-tighter text-slate-900 mb-4">
                    Data Intelligence Engine
                  </h1>
                  <p className="text-slate-500 text-xl font-medium max-w-2xl italic">
                    Configure date range and layer to synthesize Amazon Advertising artifacts.
                  </p>
                </div>
                {lastSyncResult && (
                  <motion.div 
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="p-6 bg-green-50 border border-green-100 rounded-3xl flex items-center gap-6"
                  >
                    <div className="p-3 bg-green-500 text-white rounded-full">
                      <CheckCircle2 size={24} />
                    </div>
                    <div>
                      <div className="text-xs font-black uppercase text-green-700 tracking-widest mb-1">Report Generated</div>
                      <div className="flex gap-2">
                        <button 
                          onClick={() => handleDownload(lastSyncResult.xlsx_name)}
                          className="px-4 py-2 bg-green-600 text-white text-[10px] font-bold rounded-lg hover:bg-green-700 transition-all flex items-center gap-2"
                        >
                          <FileSpreadsheet size={14} /> DOWNLOAD EXCEL
                        </button>
                        <button 
                          onClick={() => setLastSyncResult(null)}
                          className="p-2 text-slate-400 hover:text-slate-600"
                        >
                          <RefreshCw size={14} />
                        </button>
                      </div>
                    </div>
                  </motion.div>
                )}
              </header>

              {/* Date Filter Bar */}
              <div className="grid grid-cols-2 gap-8">
                <div className="glass-card border-slate-200 p-8">
                  <div className="flex items-center gap-3 mb-6">
                    <Calendar className="text-ai-neon" size={20} />
                    <h3 className="text-sm font-black uppercase tracking-widest text-slate-400">Date Intelligence</h3>
                  </div>
                  
                  <div className="flex flex-col gap-6">
                    <div className="flex gap-4">
                      <button 
                        onClick={() => setUseMtd(true)}
                        className={`flex-1 py-4 px-6 rounded-2xl border font-bold text-xs transition-all ${useMtd ? 'bg-slate-900 text-white border-slate-900 shadow-lg' : 'bg-white text-slate-500 border-slate-200 hover:border-slate-300'}`}
                      >
                        CURRENT MONTH (MTD)
                      </button>
                      <button 
                        onClick={() => setUseMtd(false)}
                        className={`flex-1 py-4 px-6 rounded-2xl border font-bold text-xs transition-all ${!useMtd ? 'bg-slate-900 text-white border-slate-900 shadow-lg' : 'bg-white text-slate-500 border-slate-200 hover:border-slate-300'}`}
                      >
                        CUSTOM RANGE
                      </button>
                    </div>

                    {!useMtd && (
                      <motion.div 
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        className="flex flex-col gap-2"
                      >
                        <span className="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-1">Start Date</span>
                        <input 
                          type="date" 
                          value={startDate}
                          onChange={(e) => setStartDate(e.target.value)}
                          className="w-full bg-slate-100 border border-transparent rounded-xl p-4 text-sm font-bold focus:bg-white focus:border-ai-neon/30 outline-none transition-all"
                        />
                        <p className="text-[9px] text-slate-400 italic mt-1">Report will fetch from this date until today.</p>
                      </motion.div>
                    )}
                  </div>
                </div>

                <div className="glass-card border-slate-200 p-8 flex flex-col justify-center">
                  <div className="flex items-center gap-3 mb-6">
                    <Clock className="text-ai-purple" size={20} />
                    <h3 className="text-sm font-black uppercase tracking-widest text-slate-400">System Readiness</h3>
                  </div>
                  <div className="space-y-4">
                    <div className="flex justify-between items-center">
                      <span className="text-xs font-bold text-slate-600">Active Nodes</span>
                      <span className="text-xs font-black text-slate-900">{selectedIds.length || 1}</span>
                    </div>
                    <div className="h-px bg-slate-100 w-full"></div>
                    <div className="flex justify-between items-center">
                      <span className="text-xs font-bold text-slate-600">Selected Layer</span>
                      <span className="text-xs font-black text-ai-neon uppercase">{selectedLevel.replace('sp', '')}</span>
                    </div>
                    <div className="h-px bg-slate-100 w-full"></div>
                    <div className="flex justify-between items-center">
                      <span className="text-xs font-bold text-slate-600">Date Scope</span>
                      <span className="text-xs font-black text-ai-purple uppercase">{useMtd ? 'Month to Date' : `From ${startDate}`}</span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Selection Grids */}
              <div className="grid grid-cols-3 gap-6">
                {REPORT_LEVELS.map((level) => (
                  <button
                    key={level.id}
                    onClick={() => setSelectedLevel(level.id)}
                    className={`group flex items-start gap-5 p-8 rounded-3xl border transition-all duration-500 ${
                      selectedLevel === level.id 
                        ? 'bg-white border-ai-neon shadow-xl shadow-ai-neon/5' 
                        : 'bg-white/50 border-slate-200 hover:border-slate-300'
                    }`}
                  >
                    <div className={`p-4 rounded-2xl transition-all duration-500 ${selectedLevel === level.id ? 'bg-ai-neon text-white shadow-lg shadow-ai-neon/20' : 'bg-slate-100 text-slate-400 group-hover:text-slate-600'}`}>
                      {level.icon}
                    </div>
                    <div className="text-left">
                      <div className={`font-black text-xl mb-1 ${selectedLevel === level.id ? 'text-slate-900' : 'text-slate-500'}`}>{level.label}</div>
                      <div className="text-[10px] text-slate-400 uppercase tracking-widest font-bold">{level.desc}</div>
                    </div>
                  </button>
                ))}
              </div>

              {/* Action Bar */}
              <div className="glass-card flex items-center justify-center p-12 border border-slate-200 shadow-2xl shadow-slate-200/50">
                <button 
                  onClick={runBulkSync}
                  disabled={isBulkRunning || (selectedIds.length === 0 && !selectedProfile)}
                  className="bg-slate-900 text-white hover:bg-ai-neon px-20 py-8 rounded-[2.5rem] font-black transition-all flex items-center justify-center gap-6 active:scale-95 disabled:opacity-20 text-2xl shadow-2xl hover:shadow-ai-neon/20 group/btn"
                >
                  {isBulkRunning ? (
                    <><Loader2 size={32} className="animate-spin" /> SYNTHESIZING...</>
                  ) : (
                    <><Play size={32} fill="currentColor" className="group-hover/btn:translate-x-1 transition-transform" /> INITIATE INTELLIGENCE FETCH</>
                  )}
                </button>
              </div>
            </motion.div>
          )}

          {view === 'analytics' && (
            <motion.div
              key="analytics"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="max-w-7xl mx-auto space-y-10"
            >
              <header className="flex justify-between items-center">
                <div>
                  <h1 className="text-5xl font-black tracking-tight text-slate-900 mb-2">Performance Trends</h1>
                  <p className="text-slate-500 text-lg">Pivoted analytics across intelligence nodes.</p>
                </div>
                <button 
                  onClick={fetchRangeAnalytics}
                  className="p-4 bg-white border border-slate-200 rounded-2xl text-slate-400 hover:text-ai-neon transition-all"
                >
                  <RefreshCw size={20} />
                </button>
              </header>

              {rangeData ? (
                <div className="grid grid-cols-2 gap-8">
                  <div className="col-span-2 glass-card border-slate-200 min-h-[400px]">
                    <h3 className="text-lg font-black mb-8 flex items-center gap-3">
                      <TrendingUp className="text-ai-neon" size={20} />
                      Range Performance Index
                    </h3>
                    <div className="h-[350px]">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={rangeData.ranges}>
                          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                          <XAxis dataKey="Ranges" axisLine={false} tickLine={false} fontSize={12} fontWeight="bold" />
                          <YAxis axisLine={false} tickLine={false} fontSize={10} />
                          <Tooltip 
                            contentStyle={{ background: '#fff', border: '1px solid #e2e8f0', borderRadius: '12px', boxShadow: '0 10px 15px -3px rgba(0,0,0,0.1)' }}
                          />
                          <Legend />
                          <Bar dataKey="total_sales" name="MTD Sales" fill="#0ea5e9" radius={[4, 4, 0, 0]} />
                          <Bar dataKey="total_spend" name="MTD Spend" fill="#f59e0b" radius={[4, 4, 0, 0]} />
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="glass-card flex flex-col items-center justify-center p-40 border-slate-200 border-dashed">
                  <Loader2 size={40} className="animate-spin text-slate-200 mb-6" />
                  <p className="text-slate-400 font-bold tracking-widest uppercase">Fetching Range Analytics...</p>
                </div>
              )}
            </motion.div>
          )}

          {view === 'reports' && (
            <motion.div
              key="reports"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="max-w-6xl mx-auto space-y-10"
            >
              <header className="flex justify-between items-end">
                <div>
                  <h1 className="text-5xl font-black tracking-tight text-slate-900 mb-2">Vault</h1>
                  <p className="text-slate-500 text-lg">Historical decision artifacts.</p>
                </div>
                <button 
                  onClick={fetchReports}
                  className="p-4 bg-white border border-slate-200 rounded-2xl text-slate-400 hover:text-slate-900 transition-all"
                >
                  <RefreshCw size={20} />
                </button>
              </header>

              <div className="glass-card !p-0 overflow-hidden border-slate-200 shadow-xl shadow-slate-200/50">
                <table className="w-full text-left">
                  <thead className="bg-slate-50 border-b border-slate-200 text-[10px] font-black uppercase tracking-widest text-slate-400">
                    <tr>
                      <th className="px-10 py-6">Layer</th>
                      <th className="px-10 py-6">Signature</th>
                      <th className="px-10 py-6">Timestamp</th>
                      <th className="px-10 py-6 text-right">Artifacts</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {reports.map((r, i) => (
                      <tr key={i} className="group hover:bg-slate-50 transition-colors">
                        <td className="px-10 py-6">
                          <span className={`px-4 py-1.5 rounded-full text-[10px] font-black uppercase tracking-widest border ${
                            r.name.includes('Campaigns') ? 'bg-blue-50 border-blue-100 text-blue-600' : 
                            r.name.includes('AdGroups') ? 'bg-purple-50 border-purple-100 text-purple-600' : 
                            'bg-amber-50 border-amber-100 text-amber-600'
                          }`}>
                            {r.name.includes('Campaigns') ? 'Campaign' : r.name.includes('AdGroups') ? 'Ad Group' : 'Product'}
                          </span>
                        </td>
                        <td className="px-10 py-6 font-bold text-slate-700">{r.name}</td>
                        <td className="px-10 py-6 text-slate-400 text-sm font-mono">{new Date(r.created_at).toLocaleString()}</td>
                        <td className="px-10 py-6 text-right">
                          <div className="flex justify-end gap-3">
                            {r.csv && <ArtifactBtn icon={<FileCode size={18} />} onClick={() => handleDownload(r.csv)} />}
                            {r.xlsx && <ArtifactBtn icon={<FileSpreadsheet size={18} />} onClick={() => handleDownload(r.xlsx)} isExcel />}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </motion.div>
          )}
        </ AnimatePresence>
      </main>
    </div>
  );
}

function NavIcon({ icon, active, onClick, label }) {
  return (
    <div className="flex flex-col items-center gap-1">
      <button 
        onClick={onClick}
        className={`p-3 rounded-2xl transition-all ${active ? 'bg-slate-900 text-white shadow-xl shadow-slate-900/20' : 'text-slate-400 hover:text-slate-900 hover:bg-slate-100'}`}
      >
        {icon}
      </button>
      <span className={`text-[8px] font-black uppercase tracking-widest ${active ? 'text-slate-900' : 'text-slate-400'}`}>{label}</span>
    </div>
  );
}

function ArtifactBtn({ icon, onClick, isExcel }) {
  return (
    <button 
      onClick={onClick}
      className={`p-3 rounded-xl border border-slate-200 transition-all hover:scale-105 active:scale-95 ${isExcel ? 'bg-green-50 text-green-600 hover:border-green-300' : 'bg-slate-50 text-slate-600 hover:border-slate-300'}`}
    >
      {icon}
    </button>
  );
}

function StatusIcon({ status }) {
  if (status === 'running') return <Loader2 size={12} className="animate-spin text-ai-neon" />;
  if (status === 'success') return <CheckCircle2 size={12} className="text-green-500" />;
  if (status === 'error') return <AlertCircle size={12} className="text-red-500" />;
  return <div className="w-1.5 h-1.5 rounded-full bg-slate-200" />;
}

export default App;
