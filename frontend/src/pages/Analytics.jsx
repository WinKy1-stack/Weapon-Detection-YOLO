import { useEffect, useState } from 'react';
import { TrendingUp, PieChart, BarChart3, Activity, Calendar, Target, RefreshCw } from 'lucide-react';
import { alertsAPI } from '../services/api';
import toast from 'react-hot-toast';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  ArcElement,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js';
import { Bar, Pie, Line } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  ArcElement,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

export default function Analytics() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [alerts, setAlerts] = useState([]);

  useEffect(() => {
    fetchStats();
    fetchAlerts();
  }, []);

  const fetchStats = async () => {
    try {
      setLoading(true);
      const response = await alertsAPI.getAlertStats(7);
      const data = response.data || response;
      setStats(data);
    } catch (error) {
      console.error('Error fetching stats:', error);
      toast.error('Không thể tải thống kê');
    } finally {
      setLoading(false);
    }
  };

  const fetchAlerts = async () => {
    try {
      const response = await alertsAPI.getAlerts({ limit: 100 });
      const alertsData = response.data || response;
      setAlerts(alertsData?.alerts || []);
    } catch (error) {
      console.error('Error fetching alerts:', error);
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

  const total = (stats?.total_alerts || 0);
  
  // Prepare chart data
  const dangerDistribution = stats?.danger_distribution || [];
  const weaponDistribution = stats?.weapon_distribution || [];
  const dailyTrends = stats?.daily_trends || [];

  // Danger level pie chart
  const dangerPieData = {
    labels: dangerDistribution.map(d => {
      switch(d.level) {
        case 'high': return 'Nguy hiểm cao';
        case 'medium': return 'Trung bình';
        case 'low': return 'Thấp';
        default: return d.level;
      }
    }),
    datasets: [{
      data: dangerDistribution.map(d => d.count),
      backgroundColor: [
        'rgba(239, 68, 68, 0.8)',   // red
        'rgba(251, 191, 36, 0.8)',  // yellow
        'rgba(34, 197, 94, 0.8)',   // green
      ],
      borderColor: [
        'rgba(239, 68, 68, 1)',
        'rgba(251, 191, 36, 1)',
        'rgba(34, 197, 94, 1)',
      ],
      borderWidth: 2
    }]
  };

  // Weapon type bar chart
  const weaponBarData = {
    labels: weaponDistribution.map(w => w.weapon || 'Unknown'),
    datasets: [{
      label: 'Số lần phát hiện',
      data: weaponDistribution.map(w => w.count),
      backgroundColor: 'rgba(59, 130, 246, 0.8)',
      borderColor: 'rgba(59, 130, 246, 1)',
      borderWidth: 2
    }]
  };

  // Daily trend line chart
  const dailyLineData = {
    labels: dailyTrends.map(d => {
      const date = new Date(d.date);
      return `${date.getDate()}/${date.getMonth() + 1}`;
    }),
    datasets: [{
      label: 'Cảnh báo',
      data: dailyTrends.map(d => d.count),
      borderColor: 'rgba(139, 92, 246, 1)',
      backgroundColor: 'rgba(139, 92, 246, 0.1)',
      tension: 0.4,
      fill: true
    }]
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: true,
    plugins: {
      legend: {
        labels: {
          color: 'rgb(209, 213, 219)',
          font: { size: 12 }
        }
      }
    },
    scales: {
      x: {
        ticks: { color: 'rgb(156, 163, 175)' },
        grid: { color: 'rgba(75, 85, 99, 0.3)' }
      },
      y: {
        ticks: { color: 'rgb(156, 163, 175)' },
        grid: { color: 'rgba(75, 85, 99, 0.3)' }
      }
    }
  };

  const pieOptions = {
    responsive: true,
    maintainAspectRatio: true,
    plugins: {
      legend: {
        position: 'bottom',
        labels: {
          color: 'rgb(209, 213, 219)',
          padding: 15,
          font: { size: 12 }
        }
      }
    }
  };

  // Calculate status stats from alerts
  const weaponsWithPersonCount = alerts.filter(a => a.status === 'held_by_person').length;
  const weaponsNoOwnerCount = alerts.filter(a => a.status === 'no_owner').length;

  const statusPieData = {
    labels: ['Người cầm', 'Không người cầm'],
    datasets: [{
      data: [weaponsWithPersonCount, weaponsNoOwnerCount],
      backgroundColor: [
        'rgba(251, 191, 36, 0.8)',
        'rgba(156, 163, 175, 0.8)',
      ],
      borderColor: [
        'rgba(251, 191, 36, 1)',
        'rgba(156, 163, 175, 1)',
      ],
      borderWidth: 2
    }]
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white mb-2 flex items-center gap-3">
            <TrendingUp className="w-8 h-8 text-purple-400" />
            Phân tích & Thống kê
          </h1>
          <p className="text-gray-400">
            Tổng quan về các cảnh báo và phát hiện vũ khí (7 ngày gần nhất)
          </p>
        </div>
        <button
          onClick={() => { fetchStats(); fetchAlerts(); }}
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg flex items-center gap-2 transition"
        >
          <RefreshCw className="w-4 h-4" />
          Làm mới
        </button>
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
            <span className="text-3xl font-bold">
              {dangerDistribution.find(d => d.level === 'high')?.count || 0}
            </span>
          </div>
          <p className="text-red-100 font-medium">Nguy hiểm cao</p>
        </div>

        <div className="bg-gradient-to-br from-yellow-600 to-yellow-800 rounded-xl p-6 text-white">
          <div className="flex items-center justify-between mb-2">
            <BarChart3 className="w-8 h-8 opacity-80" />
            <span className="text-3xl font-bold">
              {dangerDistribution.find(d => d.level === 'medium')?.count || 0}
            </span>
          </div>
          <p className="text-yellow-100 font-medium">Trung bình</p>
        </div>

        <div className="bg-gradient-to-br from-green-600 to-green-800 rounded-xl p-6 text-white">
          <div className="flex items-center justify-between mb-2">
            <Calendar className="w-8 h-8 opacity-80" />
            <span className="text-3xl font-bold">
              {dailyTrends[dailyTrends.length - 1]?.count || 0}
            </span>
          </div>
          <p className="text-green-100 font-medium">Hôm nay</p>
        </div>
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* Danger Level Distribution */}
        <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-xl p-6">
          <div className="flex items-center gap-2 mb-4">
            <PieChart className="w-6 h-6 text-purple-400" />
            <h2 className="text-xl font-semibold text-white">Phân bố mức độ nguy hiểm</h2>
          </div>
          {dangerDistribution.length > 0 ? (
            <div className="h-64 flex items-center justify-center">
              <Pie data={dangerPieData} options={pieOptions} />
            </div>
          ) : (
            <div className="h-64 flex items-center justify-center text-gray-400">
              Chưa có dữ liệu
            </div>
          )}
        </div>

        {/* Person-Held vs No Owner */}
        <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-xl p-6">
          <div className="flex items-center gap-2 mb-4">
            <PieChart className="w-6 h-6 text-yellow-400" />
            <h2 className="text-xl font-semibold text-white">Người cầm vs Không người cầm</h2>
          </div>
          {(weaponsWithPersonCount + weaponsNoOwnerCount) > 0 ? (
            <div className="h-64 flex items-center justify-center">
              <Pie data={statusPieData} options={pieOptions} />
            </div>
          ) : (
            <div className="h-64 flex items-center justify-center text-gray-400">
              Chưa có dữ liệu
            </div>
          )}
        </div>

        {/* Weapon Type Distribution */}
        <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-xl p-6">
          <div className="flex items-center gap-2 mb-4">
            <BarChart3 className="w-6 h-6 text-blue-400" />
            <h2 className="text-xl font-semibold text-white">Phân bố theo loại vũ khí</h2>
          </div>
          {weaponDistribution.length > 0 ? (
            <div className="h-64">
              <Bar data={weaponBarData} options={chartOptions} />
            </div>
          ) : (
            <div className="h-64 flex items-center justify-center text-gray-400">
              Chưa có dữ liệu
            </div>
          )}
        </div>

        {/* Daily Trends */}
        <div className="bg-slate-800/50 backdrop-blur-sm border border-slate-700 rounded-xl p-6">
          <div className="flex items-center gap-2 mb-4">
            <Activity className="w-6 h-6 text-purple-400" />
            <h2 className="text-xl font-semibold text-white">Xu hướng theo ngày</h2>
          </div>
          {dailyTrends.length > 0 ? (
            <div className="h-64">
              <Line data={dailyLineData} options={chartOptions} />
            </div>
          ) : (
            <div className="h-64 flex items-center justify-center text-gray-400">
              Chưa có dữ liệu
            </div>
          )}
        </div>
      </div>

      {/* Stats Summary */}
      <div className="bg-gradient-to-r from-purple-600/20 to-blue-600/20 border border-purple-500/30 rounded-xl p-6">
        <h3 className="text-xl font-semibold text-white mb-4">📊 Tổng quan</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center">
            <p className="text-gray-400 text-sm mb-1">Tổng cảnh báo</p>
            <p className="text-3xl font-bold text-white">{stats?.total_alerts || 0}</p>
          </div>
          <div className="text-center">
            <p className="text-gray-400 text-sm mb-1">Người cầm vũ khí</p>
            <p className="text-3xl font-bold text-yellow-400">{weaponsWithPersonCount}</p>
          </div>
          <div className="text-center">
            <p className="text-gray-400 text-sm mb-1">Không người cầm</p>
            <p className="text-3xl font-bold text-gray-400">{weaponsNoOwnerCount}</p>
          </div>
          <div className="text-center">
            <p className="text-gray-400 text-sm mb-1">Loại vũ khí</p>
            <p className="text-3xl font-bold text-blue-400">{weaponDistribution.length}</p>
          </div>
        </div>
      </div>
    </div>
  );
}
