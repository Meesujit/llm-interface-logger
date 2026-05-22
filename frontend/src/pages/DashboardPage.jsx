import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { LineChart, Line, BarChart, Bar, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { MessageSquare, Clock, AlertTriangle, Zap, Hash, RefreshCw } from 'lucide-react';
import client from '../api/client';

export default function DashboardPage() {
  const navigate = useNavigate();
  const [window, setWindow] = useState('24h');
  const [metrics, setMetrics] = useState(null);
  const [recentLogs, setRecentLogs] = useState([]);
  const [loading, setLoading] = useState(false);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [metricsRes, logsRes] = await Promise.all([client.get('/logs/metrics', { params: { window } }), client.get('/logs', { params: { limit: 20 } })]);
      setMetrics(metricsRes.data); setRecentLogs(logsRes.data.logs);
    } catch (err) { console.error('Failed to fetch dashboard data:', err); }
    finally { setLoading(false); }
  }, [window]);

  useEffect(() => { fetchData(); const interval = setInterval(fetchData, 30000); return () => clearInterval(interval); }, [fetchData]);

  const windows = ['1h', '6h', '24h', '7d'];
  const statCards = metrics ? [
    { label: 'Avg Latency', value: `${metrics.avg_latency_ms} ms`, icon: Clock, color: 'text-blue-400' },
    { label: 'Total Requests', value: metrics.total_requests, icon: Zap, color: 'text-green-400' },
    { label: 'Error Rate', value: `${(metrics.error_rate * 100).toFixed(2)}%`, icon: AlertTriangle, color: 'text-red-400' },
    { label: 'Total Tokens', value: metrics.total_tokens.toLocaleString(), icon: Hash, color: 'text-purple-400' },
  ] : [];

  const providerChartData = metrics?.by_provider ? Object.entries(metrics.by_provider).map(([name, data]) => ({ name, requests: data.requests, avg_latency: Math.round(data.avg_latency_ms) })) : [];

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <header className="h-14 border-b border-gray-800 bg-gray-900 flex items-center justify-between px-6">
        <div className="flex items-center gap-3">
          <button onClick={() => navigate('/')} className="p-1.5 rounded-lg bg-gray-800 hover:bg-gray-700 text-gray-400 hover:text-white transition-colors"><MessageSquare className="w-4 h-4" /></button>
          <h1 className="text-lg font-bold">Inference Dashboard</h1>
        </div>
        <button onClick={fetchData} disabled={loading} className="p-1.5 rounded-lg bg-gray-800 hover:bg-gray-700 text-gray-400 hover:text-white transition-colors"><RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} /></button>
      </header>

      <div className="p-6 max-w-7xl mx-auto space-y-6">
        <div className="flex gap-2">
          {windows.map((w) => (<button key={w} onClick={() => setWindow(w)} className={`px-4 py-1.5 rounded-lg text-sm font-medium transition-all ${window === w ? 'bg-primary-600 text-white' : 'bg-gray-800 text-gray-400 hover:text-white hover:bg-gray-700'}`}>{w}</button>))}
        </div>

        <div className="grid grid-cols-4 gap-4">
          {statCards.map((card) => (<div key={card.label} className="bg-gray-900 border border-gray-800 rounded-xl p-5"><div className="flex items-center gap-2 mb-2"><card.icon className={`w-5 h-5 ${card.color}`} /><span className="text-xs text-gray-500 uppercase tracking-wider">{card.label}</span></div><p className="text-2xl font-bold">{card.value}</p></div>))}
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
            <h3 className="text-sm font-semibold text-gray-300 mb-4">Latency Over Time</h3>
            {metrics?.latency_over_time?.length > 0 ? (<ResponsiveContainer width="100%" height={250}><LineChart data={metrics.latency_over_time}><CartesianGrid strokeDasharray="3 3" stroke="#1f2937" /><XAxis dataKey="timestamp" tick={{ fill: '#6b7280', fontSize: 11 }} tickFormatter={(t) => { const d = new Date(t); return window === '1h' ? `${d.getMinutes()}m` : `${d.getHours()}:${String(d.getMinutes()).padStart(2, '0')}`; }} /><YAxis tick={{ fill: '#6b7280', fontSize: 11 }} /><Tooltip contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '8px' }} labelStyle={{ color: '#d1d5db' }} /><Line type="monotone" dataKey="avg_latency_ms" stroke="#818cf8" strokeWidth={2} dot={false} /></LineChart></ResponsiveContainer>) : <p className="text-sm text-gray-500 text-center py-12">No data yet</p>}
          </div>
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
            <h3 className="text-sm font-semibold text-gray-300 mb-4">Requests by Provider</h3>
            {providerChartData.length > 0 ? (<ResponsiveContainer width="100%" height={250}><BarChart data={providerChartData}><CartesianGrid strokeDasharray="3 3" stroke="#1f2937" /><XAxis dataKey="name" tick={{ fill: '#6b7280', fontSize: 11 }} /><YAxis tick={{ fill: '#6b7280', fontSize: 11 }} /><Tooltip contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '8px' }} labelStyle={{ color: '#d1d5db' }} /><Bar dataKey="requests" fill="#6366f1" radius={[4, 4, 0, 0]} /></BarChart></ResponsiveContainer>) : <p className="text-sm text-gray-500 text-center py-12">No data yet</p>}
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
            <h3 className="text-sm font-semibold text-gray-300 mb-4">Errors Over Time</h3>
            {metrics?.errors_over_time?.length > 0 ? (<ResponsiveContainer width="100%" height={250}><AreaChart data={metrics.errors_over_time}><CartesianGrid strokeDasharray="3 3" stroke="#1f2937" /><XAxis dataKey="timestamp" tick={{ fill: '#6b7280', fontSize: 11 }} tickFormatter={(t) => { const d = new Date(t); return `${d.getHours()}:${String(d.getMinutes()).padStart(2, '0')}`; }} /><YAxis tick={{ fill: '#6b7280', fontSize: 11 }} /><Tooltip contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #374151', borderRadius: '8px' }} labelStyle={{ color: '#d1d5db' }} /><Area type="monotone" dataKey="count" stroke="#ef4444" fill="#ef444420" strokeWidth={2} /></AreaChart></ResponsiveContainer>) : <p className="text-sm text-gray-500 text-center py-12">No data yet</p>}
          </div>
        </div>

        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5">
          <h3 className="text-sm font-semibold text-gray-300 mb-4">Recent Logs</h3>
          <div className="overflow-x-auto"><table className="w-full text-sm"><thead><tr className="text-left text-gray-500 text-xs uppercase tracking-wider"><th className="pb-3 pr-4">Request ID</th><th className="pb-3 pr-4">Provider</th><th className="pb-3 pr-4">Model</th><th className="pb-3 pr-4">Latency</th><th className="pb-3 pr-4">Status</th><th className="pb-3 pr-4">Time</th></tr></thead><tbody>{recentLogs.map((log) => (<tr key={log.id} className="border-t border-gray-800/50"><td className="py-2.5 pr-4 text-gray-400 font-mono text-xs">{log.request_id?.slice(0, 12)}...</td><td className="py-2.5 pr-4"><span className={`text-xs px-2 py-0.5 rounded-full ${log.provider === 'groq' ? 'bg-orange-500/20 text-orange-400' : 'bg-blue-500/20 text-blue-400'}`}>{log.provider}</span></td><td className="py-2.5 pr-4 text-gray-400 text-xs">{log.model}</td><td className="py-2.5 pr-4 text-gray-300">{log.latency_ms} ms</td><td className="py-2.5 pr-4"><span className={`text-xs px-2 py-0.5 rounded-full ${log.status === 'success' ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}`}>{log.status}</span></td><td className="py-2.5 text-gray-500 text-xs">{log.created_at ? new Date(log.created_at).toLocaleTimeString() : ''}</td></tr>))}{recentLogs.length === 0 && <tr><td colSpan={6} className="py-8 text-center text-gray-500">No logs yet</td></tr>}</tbody></table></div>
        </div>
      </div>
    </div>
  );
}
