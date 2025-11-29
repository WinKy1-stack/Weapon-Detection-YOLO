import { useState, useEffect } from 'react';
import { AlertTriangle, Search, Filter, Trash2, Calendar, Shield } from 'lucide-react';
import { alertsAPI } from '../services/api';
import toast from 'react-hot-toast';

export default function Alerts() {
  const [alerts, setAlerts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    weapon_class: '',
    danger_level: '',
    start_date: '',
    end_date: '',
  });

  useEffect(() => {
    fetchAlerts();
  }, []);

  const fetchAlerts = async () => {
    try {
      setLoading(true);
      const response = await alertsAPI.getAlerts(filters);
      setAlerts(response.alerts || []);
    } catch (error) {
      console.error('Error fetching alerts:', error);
      toast.error('Không thể tải danh sách cảnh báo');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (alertId) => {
    if (!confirm('Bạn có chắc muốn xóa cảnh báo này?')) return;

    try {
      await alertsAPI.deleteAlert(alertId);
      toast.success('Đã xóa cảnh báo');
      fetchAlerts();
    } catch (error) {
      toast.error('Xóa cảnh báo thất bại');
    }
  };

  const handleSearch = () => {
    fetchAlerts();
  };

  const handleReset = () => {
    setFilters({
      weapon_class: '',
      danger_level: '',
      start_date: '',
      end_date: '',
    });
    setTimeout(fetchAlerts, 100);
  };

  const getDangerColor = (level) => {
    switch (level) {
      case 'high': return 'bg-red-500/20 text-red-400 border-red-500/50';
      case 'medium': return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/50';
      case 'low': return 'bg-green-500/20 text-green-400 border-green-500/50';
      default: return 'bg-gray-500/20 text-gray-400 border-gray-500/50';
    }
  };

  const getDangerLabel = (level) => {
    switch (level) {
      case 'high': return 'Cao';
      case 'medium': return 'Trung bình';
      case 'low': return 'Thấp';
      default: return level;
    }
  };

  return (
    <div className="p-6">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2 flex items-center gap-3">
          <AlertTriangle className="w-8 h-8 text-yellow-400" />
          Lịch sử cảnh báo
        </h1>
        <p className="text-gray-400">
          Quản lý và theo dõi các cảnh báo phát hiện vũ khí
        </p>
      </div>

      {/* Filters */}
      <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-xl p-6 mb-6">
        <div className="flex items-center gap-2 mb-4">
          <Filter className="w-5 h-5 text-blue-400" />
          <h2 className="text-lg font-semibold text-white">Bộ lọc</h2>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Loại vũ khí
            </label>
            <input
              type="text"
              value={filters.weapon_class}
              onChange={(e) => setFilters({ ...filters, weapon_class: e.target.value })}
              className="w-full px-4 py-2 bg-slate-700/50 border border-slate-600 rounded-lg text-white placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Ví dụ: knife, gun"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Mức độ nguy hiểm
            </label>
            <select
              value={filters.danger_level}
              onChange={(e) => setFilters({ ...filters, danger_level: e.target.value })}
              className="w-full px-4 py-2 bg-slate-700/50 border border-slate-600 rounded-lg text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="">Tất cả</option>
              <option value="high">Cao</option>
              <option value="medium">Trung bình</option>
              <option value="low">Thấp</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Từ ngày
            </label>
            <input
              type="date"
              value={filters.start_date}
              onChange={(e) => setFilters({ ...filters, start_date: e.target.value })}
              className="w-full px-4 py-2 bg-slate-700/50 border border-slate-600 rounded-lg text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">
              Đến ngày
            </label>
            <input
              type="date"
              value={filters.end_date}
              onChange={(e) => setFilters({ ...filters, end_date: e.target.value })}
              className="w-full px-4 py-2 bg-slate-700/50 border border-slate-600 rounded-lg text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
        </div>

        <div className="flex gap-3">
          <button
            onClick={handleSearch}
            className="bg-blue-600 hover:bg-blue-700 text-white font-semibold px-6 py-2 rounded-lg transition flex items-center gap-2"
          >
            <Search className="w-4 h-4" />
            Tìm kiếm
          </button>
          <button
            onClick={handleReset}
            className="bg-slate-700 hover:bg-slate-600 text-white font-semibold px-6 py-2 rounded-lg transition"
          >
            Đặt lại
          </button>
        </div>
      </div>

      {/* Alerts List */}
      <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-xl p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold text-white">
            Danh sách cảnh báo ({alerts.length})
          </h2>
          <button 
            onClick={fetchAlerts}
            className="text-blue-400 hover:text-blue-300 text-sm font-medium transition"
          >
            Làm mới
          </button>
        </div>

        {loading ? (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
            <p className="text-gray-400 mt-4">Đang tải...</p>
          </div>
        ) : alerts.length === 0 ? (
          <div className="text-center py-12">
            <Shield className="w-16 h-16 text-gray-600 mx-auto mb-4" />
            <p className="text-gray-400 text-lg">Không có cảnh báo nào</p>
            <p className="text-gray-500 text-sm mt-2">Thử thay đổi bộ lọc hoặc phát hiện vũ khí mới</p>
          </div>
        ) : (
          <div className="space-y-3">
            {alerts.map((alert) => (
              <div
                key={alert.id}
                className="bg-slate-700/30 border border-slate-600 rounded-lg p-5 hover:bg-slate-700/50 transition"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-3">
                      <span className={`px-3 py-1 rounded-full text-sm font-semibold border ${getDangerColor(alert.danger_level)}`}>
                        {getDangerLabel(alert.danger_level)}
                      </span>
                      <span className="text-white font-semibold text-lg">
                        {alert.weapon_class || 'Unknown'}
                      </span>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-sm">
                      <div className="flex items-center gap-2 text-gray-300">
                        <Shield className="w-4 h-4 text-blue-400" />
                        <span>Độ tin cậy: <strong>{((alert.confidence || 0) * 100).toFixed(1)}%</strong></span>
                      </div>
                      <div className="flex items-center gap-2 text-gray-300">
                        <Calendar className="w-4 h-4 text-blue-400" />
                        <span>{new Date(alert.timestamp).toLocaleString('vi-VN')}</span>
                      </div>
                      <div className="text-gray-400">
                        {alert.location || 'Unknown location'}
                      </div>
                    </div>
                  </div>

                  <button
                    onClick={() => handleDelete(alert.id)}
                    className="ml-4 p-2 bg-red-500/20 hover:bg-red-500/30 text-red-400 rounded-lg transition"
                    title="Xóa cảnh báo"
                  >
                    <Trash2 className="w-5 h-5" />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
