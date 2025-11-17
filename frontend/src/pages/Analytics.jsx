import { useEffect, useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line } from 'recharts';
import { alertsAPI } from '../services/api';
import toast from 'react-hot-toast';

const COLORS = ['#0ea5e9', '#f59e0b', '#ef4444', '#10b981', '#8b5cf6', '#ec4899'];

export default function Analytics() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [period, setPeriod] = useState(7);

  useEffect(() => {
    loadStats();
  }, [period]);

  const loadStats = async () => {
    try {
      const response = await alertsAPI.getAlertStats(period);
      setStats(response.data);
    } catch (error) {
      toast.error('Failed to load statistics');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-400">Loading analytics...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">Analytics</h1>
          <p className="text-gray-400 mt-1">Weapon detection statistics and trends</p>
        </div>
        <select
          value={period}
          onChange={(e) => setPeriod(parseInt(e.target.value))}
          className="px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white"
        >
          <option value={7}>Last 7 days</option>
          <option value={30}>Last 30 days</option>
          <option value={90}>Last 90 days</option>
        </select>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="card">
          <p className="text-gray-400 text-sm">Total Alerts</p>
          <p className="text-3xl font-bold text-white mt-2">{stats?.total_alerts || 0}</p>
        </div>
        <div className="card">
          <p className="text-gray-400 text-sm">Average per Day</p>
          <p className="text-3xl font-bold text-white mt-2">
            {((stats?.total_alerts || 0) / (stats?.period_days || 1)).toFixed(1)}
          </p>
        </div>
        <div className="card">
          <p className="text-gray-400 text-sm">Unique Weapons</p>
          <p className="text-3xl font-bold text-white mt-2">
            {stats?.weapon_distribution?.length || 0}
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Weapon Distribution Pie Chart */}
        <div className="card">
          <h3 className="text-xl font-semibold text-white mb-4">Weapon Distribution</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={stats?.weapon_distribution || []}
                dataKey="count"
                nameKey="weapon"
                cx="50%"
                cy="50%"
                outerRadius={100}
                label={(entry) => `${entry.weapon}: ${entry.count}`}
              >
                {stats?.weapon_distribution?.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip
                contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155' }}
                labelStyle={{ color: '#fff' }}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Danger Level Distribution */}
        <div className="card">
          <h3 className="text-xl font-semibold text-white mb-4">Danger Level Distribution</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={stats?.danger_distribution || []}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis 
                dataKey="level" 
                stroke="#94a3b8"
                tick={{ fill: '#94a3b8' }}
              />
              <YAxis 
                stroke="#94a3b8"
                tick={{ fill: '#94a3b8' }}
              />
              <Tooltip
                contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155' }}
                labelStyle={{ color: '#fff' }}
              />
              <Bar dataKey="count" fill="#0ea5e9" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Daily Trend */}
        <div className="card lg:col-span-2">
          <h3 className="text-xl font-semibold text-white mb-4">Daily Alert Trends</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={stats?.daily_trends || []}>
              <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
              <XAxis 
                dataKey="date" 
                stroke="#94a3b8"
                tick={{ fill: '#94a3b8' }}
              />
              <YAxis 
                stroke="#94a3b8"
                tick={{ fill: '#94a3b8' }}
              />
              <Tooltip
                contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #334155' }}
                labelStyle={{ color: '#fff' }}
              />
              <Legend />
              <Line 
                type="monotone" 
                dataKey="count" 
                stroke="#0ea5e9" 
                strokeWidth={2}
                name="Alerts"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
