import { useEffect, useState } from 'react';
import { Activity, Shield, AlertTriangle, Clock } from 'lucide-react';
import { alertsAPI } from '../services/api';
import toast from 'react-hot-toast';

export default function Dashboard() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [recentAlerts, setRecentAlerts] = useState([]);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      const [statsRes, alertsRes] = await Promise.all([
        alertsAPI.getAlertStats(7),
        alertsAPI.getAlerts({ limit: 5 }),
      ]);
      setStats(statsRes.data);
      setRecentAlerts(alertsRes.data);
    } catch (error) {
      toast.error('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-400">Loading dashboard...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-white">Dashboard</h1>
        <p className="text-gray-400 mt-1">Overview of weapon detection system</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard
          title="Total Alerts"
          value={stats?.total_alerts || 0}
          icon={AlertTriangle}
          color="text-danger-500"
          bgColor="bg-danger-500/10"
        />
        <StatCard
          title="High Danger"
          value={stats?.danger_distribution?.find(d => d.level.includes('CAO'))?.count || 0}
          icon={Shield}
          color="text-red-500"
          bgColor="bg-red-500/10"
        />
        <StatCard
          title="Active Period"
          value={`${stats?.period_days || 0} days`}
          icon={Clock}
          color="text-primary-500"
          bgColor="bg-primary-500/10"
        />
        <StatCard
          title="Detection Rate"
          value={`${((stats?.total_alerts || 0) / (stats?.period_days || 1)).toFixed(1)}/day`}
          icon={Activity}
          color="text-green-500"
          bgColor="bg-green-500/10"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Weapon Distribution */}
        <div className="card">
          <h3 className="text-xl font-semibold text-white mb-4">Weapon Distribution</h3>
          <div className="space-y-3">
            {stats?.weapon_distribution?.map((item) => (
              <div key={item.weapon} className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-2 h-2 rounded-full bg-primary-500"></div>
                  <span className="text-gray-300 capitalize">{item.weapon}</span>
                </div>
                <span className="text-white font-semibold">{item.count}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Recent Alerts */}
        <div className="card">
          <h3 className="text-xl font-semibold text-white mb-4">Recent Alerts</h3>
          <div className="space-y-3">
            {recentAlerts.length > 0 ? (
              recentAlerts.map((alert) => (
                <div key={alert._id} className="flex items-center justify-between p-3 bg-slate-700 rounded-lg">
                  <div>
                    <p className="text-white font-medium capitalize">{alert.weapon_class}</p>
                    <p className="text-sm text-gray-400">
                      {new Date(alert.timestamp).toLocaleString()}
                    </p>
                  </div>
                  <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                    alert.danger_level.includes('CAO') 
                      ? 'bg-red-500/20 text-red-400'
                      : 'bg-yellow-500/20 text-yellow-400'
                  }`}>
                    {alert.confidence.toFixed(0)}%
                  </span>
                </div>
              ))
            ) : (
              <p className="text-gray-400 text-center py-4">No alerts yet</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function StatCard({ title, value, icon: Icon, color, bgColor }) {
  return (
    <div className="card">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-gray-400 text-sm">{title}</p>
          <p className="text-2xl font-bold text-white mt-1">{value}</p>
        </div>
        <div className={`p-3 rounded-lg ${bgColor}`}>
          <Icon className={`w-6 h-6 ${color}`} />
        </div>
      </div>
    </div>
  );
}
