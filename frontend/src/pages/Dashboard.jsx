import { useEffect, useState } from 'react';
import { Shield, AlertTriangle, Camera, TrendingUp, Activity, Clock } from 'lucide-react';
import { useAuthStore } from '../store/authStore';
import { alertsAPI } from '../services/api';
import toast from 'react-hot-toast';

export default function Dashboard() {
  const user = useAuthStore((state) => state.user);
  const [stats, setStats] = useState({
    total_alerts: 0,
    high_danger: 0,
    medium_danger: 0,
    low_danger: 0,
    today_alerts: 0,
  });
  const [loading, setLoading] = useState(true);
  const [recentAlerts, setRecentAlerts] = useState([]);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const statsData = await alertsAPI.getAlertStats();
      const alertsResponse = await alertsAPI.getAlerts({ limit: 5 });
      
      setStats({
        total_alerts: statsData.total_alerts || 0,
        high_danger: statsData.high_danger || 0,
        medium_danger: statsData.medium_danger || 0,
        low_danger: statsData.low_danger || 0,
        today_alerts: statsData.today_alerts || 0,
      });
      
      setRecentAlerts(alertsResponse.alerts || []);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      toast.error('Không thể tải dữ liệu dashboard');
    } finally {
      setLoading(false);
    }
  };

  const getDangerColor = (level) => {
    switch (level) {
      case 'high': return 'text-red-400 bg-red-500/10';
      case 'medium': return 'text-yellow-400 bg-yellow-500/10';
      case 'low': return 'text-green-400 bg-green-500/10';
      default: return 'text-gray-400 bg-gray-500/10';
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

  const statCards = [
    {
      icon: Shield,
      title: 'Tổng cảnh báo',
      value: stats.total_alerts,
      color: 'blue',
      bgColor: 'bg-blue-500/10',
      iconColor: 'text-blue-400',
    },
    {
      icon: AlertTriangle,
      title: 'Mức độ cao',
      value: stats.high_danger,
      color: 'red',
      bgColor: 'bg-red-500/10',
      iconColor: 'text-red-400',
    },
    {
      icon: Activity,
      title: 'Mức độ trung bình',
      value: stats.medium_danger,
      color: 'yellow',
      bgColor: 'bg-yellow-500/10',
      iconColor: 'text-yellow-400',
    },
    {
      icon: Clock,
      title: 'Hôm nay',
      value: stats.today_alerts,
      color: 'green',
      bgColor: 'bg-green-500/10',
      iconColor: 'text-green-400',
    },
  ];

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-white mb-2">
          Dashboard
        </h1>
        <p className="text-gray-400">
          Xin chào, <span className="text-blue-400 font-semibold">{user?.full_name || 'User'}</span>! Chào mừng trở lại.
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {statCards.map((card, index) => (
          <div
            key={index}
            className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-xl p-6 hover:bg-slate-800/70 transition-all duration-200 hover:scale-105"
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-400 text-sm mb-1">{card.title}</p>
                <p className="text-3xl font-bold text-white">{card.value}</p>
              </div>
              <div className={`p-3 rounded-lg ${card.bgColor}`}>
                <card.icon className={`w-8 h-8 ${card.iconColor}`} />
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Recent Alerts */}
      <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-xl p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold text-white flex items-center gap-2">
            <Camera className="w-6 h-6 text-blue-400" />
            Cảnh báo gần đây
          </h2>
          <button 
            onClick={fetchDashboardData}
            className="text-blue-400 hover:text-blue-300 text-sm font-medium transition"
          >
            Làm mới
          </button>
        </div>

        {loading ? (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
            <p className="text-gray-400 mt-4">Đang tải dữ liệu...</p>
          </div>
        ) : recentAlerts.length === 0 ? (
          <div className="text-center py-12">
            <Shield className="w-16 h-16 text-gray-600 mx-auto mb-4" />
            <p className="text-gray-400 text-lg">Chưa có cảnh báo nào</p>
            <p className="text-gray-500 text-sm mt-2">Hãy thử phát hiện vũ khí từ hình ảnh</p>
          </div>
        ) : (
          <div className="space-y-3">
            {recentAlerts.map((alert, index) => (
              <div
                key={alert.id || index}
                className="bg-slate-700/30 border border-slate-600 rounded-lg p-4 hover:bg-slate-700/50 transition"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <span className={`px-3 py-1 rounded-full text-xs font-semibold ${getDangerColor(alert.danger_level)}`}>
                        {getDangerLabel(alert.danger_level)}
                      </span>
                      <span className="text-gray-400 text-sm">
                        {alert.weapon_class || 'Unknown'}
                      </span>
                    </div>
                    <p className="text-gray-300 text-sm">
                      Độ tin cậy: <span className="font-semibold text-blue-400">{((alert.confidence || 0) * 100).toFixed(1)}%</span>
                    </p>
                    <p className="text-gray-500 text-xs mt-1">
                      {alert.location || 'Unknown location'} • {new Date(alert.timestamp).toLocaleString('vi-VN')}
                    </p>
                  </div>
                  {alert.image_path && (
                    <div className="ml-4">
                      <Camera className="w-8 h-8 text-gray-500" />
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-gradient-to-br from-blue-600 to-blue-800 rounded-xl p-6 text-white">
          <Camera className="w-12 h-12 mb-4 opacity-90" />
          <h3 className="text-xl font-bold mb-2">Phát hiện vũ khí</h3>
          <p className="text-blue-100 mb-4">
            Upload hình ảnh để phát hiện vũ khí với AI
          </p>
          <a 
            href="/detection"
            className="inline-block bg-white text-blue-600 font-semibold px-6 py-2 rounded-lg hover:bg-blue-50 transition"
          >
            Bắt đầu →
          </a>
        </div>

        <div className="bg-gradient-to-br from-purple-600 to-purple-800 rounded-xl p-6 text-white">
          <TrendingUp className="w-12 h-12 mb-4 opacity-90" />
          <h3 className="text-xl font-bold mb-2">Xem phân tích</h3>
          <p className="text-purple-100 mb-4">
            Biểu đồ và thống kê chi tiết
          </p>
          <a 
            href="/analytics"
            className="inline-block bg-white text-purple-600 font-semibold px-6 py-2 rounded-lg hover:bg-purple-50 transition"
          >
            Xem ngay →
          </a>
        </div>
      </div>
    </div>
  );
}
