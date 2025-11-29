import { useEffect, useState } from 'react';
import { TrendingUp, PieChart, BarChart3, Activity, Calendar, Target } from 'lucide-react';
import { alertsAPI } from '../services/api';
import toast from 'react-hot-toast';

export default function Analytics() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      setLoading(true);
      const data = await alertsAPI.getStats();
      setStats(data);
    } catch (error) {
      console.error('Error fetching stats:', error);
      toast.error('Không thể tải thống kê');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="p-6 flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-400">Đang tải thống kê...</p>
        </div>
      </div>
    );
  }

  const total = (stats?.high_danger || 0) + (stats?.medium_danger || 0) + (stats?.low_danger || 0);
  const highPercent = total > 0 ? ((stats?.high_danger || 0) / total * 100).toFixed(1) : 0;
  const mediumPercent = total > 0 ? ((stats?.medium_danger || 0) / total * 100).toFixed(1) : 0;
  const lowPercent = total > 0 ? ((stats?.low_danger || 0) / total * 100).toFixed(1) : 0;

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-white mb-2 flex items-center gap-3">
          <TrendingUp className="w-8 h-8 text-purple-400" />
          Phân tích & Thống kê
        </h1>
        <p className="text-gray-400">
          Tổng quan về các cảnh báo và phát hiện vũ khí
        </p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div className="bg-gradient-to-br from-blue-600 to-blue-800 rounded-xl p-6 text-white">
          <div className="flex items-center justify-between mb-2">
            <Target className="w-8 h-8 opacity-80" />
            <span className="text-3xl font-bold">{stats?.total_alerts || 0}</span>
          </div>
          <p className="text-blue-100 font-medium">Tổng cảnh báo</p>
        </div>

        <div className="bg-gradient-to-br from-red-600 to-red-800 rounded-xl p-6 text-white">
          <div className="flex items-center justify-between mb-2">
            <Activity className="w-8 h-8 opacity-80" />
            <span className="text-3xl font-bold">{stats?.high_danger || 0}</span>
          </div>
          <p className="text-red-100 font-medium">Nguy hiểm cao</p>
        </div>

        <div className="bg-gradient-to-br from-yellow-600 to-yellow-800 rounded-xl p-6 text-white">
          <div className="flex items-center justify-between mb-2">
            <BarChart3 className="w-8 h-8 opacity-80" />
            <span className="text-3xl font-bold">{stats?.medium_danger || 0}</span>
          </div>
          <p className="text-yellow-100 font-medium">Trung bình</p>
        </div>

        <div className="bg-gradient-to-br from-green-600 to-green-800 rounded-xl p-6 text-white">
          <div className="flex items-center justify-between mb-2">
            <Calendar className="w-8 h-8 opacity-80" />
            <span className="text-3xl font-bold">{stats?.today_alerts || 0}</span>
          </div>
          <p className="text-green-100 font-medium">Hôm nay</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Danger Level Distribution */}
        <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-xl p-6">
          <div className="flex items-center gap-2 mb-6">
            <PieChart className="w-6 h-6 text-purple-400" />
            <h2 className="text-xl font-semibold text-white">Phân bố mức độ nguy hiểm</h2>
          </div>

          <div className="space-y-6">
            {/* High Danger */}
            <div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-gray-300 font-medium">Nguy hiểm cao</span>
                <span className="text-red-400 font-bold">{highPercent}%</span>
              </div>
              <div className="w-full bg-slate-700 rounded-full h-3 overflow-hidden">
                <div 
                  className="bg-gradient-to-r from-red-500 to-red-600 h-full rounded-full transition-all duration-500"
                  style={{ width: `${highPercent}%` }}
                ></div>
              </div>
              <p className="text-gray-400 text-sm mt-1">{stats?.high_danger || 0} cảnh báo</p>
            </div>

            {/* Medium Danger */}
            <div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-gray-300 font-medium">Trung bình</span>
                <span className="text-yellow-400 font-bold">{mediumPercent}%</span>
              </div>
              <div className="w-full bg-slate-700 rounded-full h-3 overflow-hidden">
                <div 
                  className="bg-gradient-to-r from-yellow-500 to-yellow-600 h-full rounded-full transition-all duration-500"
                  style={{ width: `${mediumPercent}%` }}
                ></div>
              </div>
              <p className="text-gray-400 text-sm mt-1">{stats?.medium_danger || 0} cảnh báo</p>
            </div>

            {/* Low Danger */}
            <div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-gray-300 font-medium">Nguy hiểm thấp</span>
                <span className="text-green-400 font-bold">{lowPercent}%</span>
              </div>
              <div className="w-full bg-slate-700 rounded-full h-3 overflow-hidden">
                <div 
                  className="bg-gradient-to-r from-green-500 to-green-600 h-full rounded-full transition-all duration-500"
                  style={{ width: `${lowPercent}%` }}
                ></div>
              </div>
              <p className="text-gray-400 text-sm mt-1">{stats?.low_danger || 0} cảnh báo</p>
            </div>
          </div>

          {total === 0 && (
            <div className="text-center py-8">
              <p className="text-gray-400">Chưa có dữ liệu thống kê</p>
            </div>
          )}
        </div>

        {/* Quick Stats */}
        <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-xl p-6">
          <div className="flex items-center gap-2 mb-6">
            <BarChart3 className="w-6 h-6 text-blue-400" />
            <h2 className="text-xl font-semibold text-white">Thống kê nhanh</h2>
          </div>

          <div className="space-y-4">
            <div className="bg-slate-700/30 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-400 text-sm mb-1">Tổng cảnh báo</p>
                  <p className="text-3xl font-bold text-white">{stats?.total_alerts || 0}</p>
                </div>
                <div className="p-3 bg-blue-500/20 rounded-lg">
                  <Target className="w-8 h-8 text-blue-400" />
                </div>
              </div>
            </div>

            <div className="bg-slate-700/30 rounded-lg p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-400 text-sm mb-1">Cảnh báo hôm nay</p>
                  <p className="text-3xl font-bold text-white">{stats?.today_alerts || 0}</p>
                </div>
                <div className="p-3 bg-green-500/20 rounded-lg">
                  <Calendar className="w-8 h-8 text-green-400" />
                </div>
              </div>
            </div>

            <div className="bg-gradient-to-r from-purple-600/20 to-blue-600/20 border border-purple-500/30 rounded-lg p-4">
              <p className="text-purple-300 text-sm mb-2">Tỷ lệ nguy hiểm</p>
              <div className="flex items-end gap-2">
                <span className="text-red-400 font-bold text-xl">{highPercent}%</span>
                <span className="text-gray-400 text-sm mb-1">cao</span>
                <span className="text-yellow-400 font-bold text-xl ml-3">{mediumPercent}%</span>
                <span className="text-gray-400 text-sm mb-1">TB</span>
                <span className="text-green-400 font-bold text-xl ml-3">{lowPercent}%</span>
                <span className="text-gray-400 text-sm mb-1">thấp</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Refresh Button */}
      <div className="mt-6 text-center">
        <button
          onClick={fetchStats}
          className="bg-blue-600 hover:bg-blue-700 text-white font-semibold px-8 py-3 rounded-lg transition inline-flex items-center gap-2"
        >
          <Activity className="w-5 h-5" />
          Làm mới dữ liệu
        </button>
      </div>
    </div>
  );
}
