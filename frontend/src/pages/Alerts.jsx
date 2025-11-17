import { useEffect, useState } from 'react';
import { Filter, Search, Calendar } from 'lucide-react';
import { alertsAPI } from '../services/api';
import toast from 'react-hot-toast';
import { format } from 'date-fns';

export default function Alerts() {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    weapon_class: '',
    danger_level: '',
  });

  useEffect(() => {
    loadAlerts();
  }, [filters]);

  const loadAlerts = async () => {
    try {
      const response = await alertsAPI.getAlerts({ 
        limit: 50,
        ...filters 
      });
      setAlerts(response.data);
    } catch (error) {
      toast.error('Failed to load alerts');
    } finally {
      setLoading(false);
    }
  };

  const getDangerColor = (level) => {
    if (level.includes('CAO')) return 'bg-red-500/20 text-red-400 border-red-500/50';
    if (level.includes('TRUNG')) return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/50';
    return 'bg-blue-500/20 text-blue-400 border-blue-500/50';
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">Alert History</h1>
          <p className="text-gray-400 mt-1">View all weapon detection alerts</p>
        </div>
        <button
          onClick={loadAlerts}
          className="btn btn-primary"
        >
          Refresh
        </button>
      </div>

      {/* Filters */}
      <div className="card">
        <div className="flex items-center gap-4">
          <Filter className="w-5 h-5 text-gray-400" />
          <div className="flex-1 grid grid-cols-1 md:grid-cols-2 gap-4">
            <select
              value={filters.weapon_class}
              onChange={(e) => setFilters({ ...filters, weapon_class: e.target.value })}
              className="px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white"
            >
              <option value="">All Weapons</option>
              <option value="pistol">Pistol</option>
              <option value="firearm">Firearm</option>
              <option value="knife">Knife</option>
              <option value="grenade">Grenade</option>
              <option value="rocket">Rocket</option>
              <option value="fire">Fire</option>
            </select>

            <select
              value={filters.danger_level}
              onChange={(e) => setFilters({ ...filters, danger_level: e.target.value })}
              className="px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white"
            >
              <option value="">All Danger Levels</option>
              <option value="NGUY HIỂM CAO">High Danger</option>
              <option value="TRUNG BÌNH">Medium</option>
              <option value="THẤP">Low</option>
            </select>
          </div>
        </div>
      </div>

      {/* Alerts Grid */}
      {loading ? (
        <div className="flex items-center justify-center h-64">
          <div className="text-gray-400">Loading alerts...</div>
        </div>
      ) : alerts.length > 0 ? (
        <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
          {alerts.map((alert) => (
            <div key={alert._id} className="card group hover:border-primary-500 transition-colors cursor-pointer">
              {/* Alert Image */}
              {alert.image_path && (
                <div className="mb-4 rounded-lg overflow-hidden bg-slate-700">
                  <img
                    src={`http://localhost:8000/snapshots/${alert.image_path.split('/').pop()}`}
                    alt={alert.weapon_class}
                    className="w-full h-48 object-cover"
                    onError={(e) => {
                      e.target.style.display = 'none';
                    }}
                  />
                </div>
              )}

              {/* Alert Info */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold text-white capitalize">
                    {alert.weapon_class}
                  </h3>
                  <span className={`px-3 py-1 rounded-full text-xs font-medium border ${getDangerColor(alert.danger_level)}`}>
                    {alert.danger_level}
                  </span>
                </div>

                <div className="space-y-2 text-sm">
                  <div className="flex items-center justify-between">
                    <span className="text-gray-400">Confidence</span>
                    <span className="text-white font-medium">{(alert.confidence * 100).toFixed(1)}%</span>
                  </div>
                  
                  {alert.distance && (
                    <div className="flex items-center justify-between">
                      <span className="text-gray-400">Distance</span>
                      <span className="text-white font-medium">{alert.distance.toFixed(2)}m</span>
                    </div>
                  )}

                  <div className="flex items-center justify-between">
                    <span className="text-gray-400">Status</span>
                    <span className="text-white font-medium">{alert.status}</span>
                  </div>

                  <div className="flex items-center gap-2 text-gray-400 pt-2 border-t border-slate-700">
                    <Calendar className="w-4 h-4" />
                    <span className="text-xs">
                      {format(new Date(alert.timestamp), 'MMM dd, yyyy HH:mm:ss')}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="card text-center py-12">
          <p className="text-gray-400">No alerts found</p>
        </div>
      )}
    </div>
  );
}
