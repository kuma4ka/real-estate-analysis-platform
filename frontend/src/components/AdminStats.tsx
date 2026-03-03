import React, { useState, useEffect } from 'react';
import { fetchWithAuth, API_BASE_URL } from '../services/api';

interface SystemStats {
  total_users: number;
  total_properties: number;
  active_properties: number;
  role_distribution: Record<string, number>;
}

const AdminStats: React.FC = () => {
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadStats = async () => {
      try {
        const response = await fetchWithAuth(`${API_BASE_URL}/admin/system`);
        if (!response.ok) {
          throw new Error('Failed to fetch system statistics');
        }
        const data = await response.json() as SystemStats;
        setStats(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'An error occurred');
      } finally {
        setLoading(false);
      }
    };

    loadStats();
  }, []);

  if (loading) {
    return <div className="animate-pulse flex space-x-4 p-4"><div className="h-4 bg-gray-300 rounded w-3/4"></div></div>;
  }

  if (error) {
    return <div className="p-4 bg-red-50 text-red-600 rounded-md">Error loading admin stats: {error}</div>;
  }

  if (!stats) return null;

  return (
    <div className="bg-white dark:bg-gray-800 shadow rounded-lg mb-8 overflow-hidden border border-red-200 dark:border-red-900/30">
      <div className="px-6 py-5 border-b border-gray-200 dark:border-gray-700 bg-red-50 dark:bg-red-900/10 flex justify-between items-center">
        <h3 className="text-lg font-bold text-red-800 dark:text-red-400">🛡️ Admin Dashboard</h3>
        <span className="bg-red-100 text-red-800 text-xs font-medium px-2.5 py-0.5 rounded dark:bg-red-900 dark:text-red-300">Live</span>
      </div>
      <div className="px-6 py-5">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
          <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg text-center shadow-sm">
            <p className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">Total Users</p>
            <p className="text-2xl font-bold text-gray-900 dark:text-white">{stats.total_users}</p>
          </div>
          <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg text-center shadow-sm">
            <p className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">Total Properties</p>
            <p className="text-2xl font-bold text-gray-900 dark:text-white">{stats.total_properties}</p>
          </div>
          <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg text-center shadow-sm">
            <p className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">Active Properties</p>
            <p className="text-2xl font-bold text-green-600 dark:text-green-400">{stats.active_properties}</p>
          </div>
        </div>

        <div>
          <h4 className="text-sm font-semibold text-gray-900 dark:text-white mb-3 uppercase tracking-wider">Role Distribution</h4>
          <div className="flex gap-4 flex-wrap">
            {Object.entries(stats.role_distribution).map(([role, count]) => (
              <div key={role} className="flex items-center gap-2 border border-gray-200 dark:border-gray-600 rounded-full px-4 py-1.5 bg-white dark:bg-gray-800 shadow-sm">
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">{role}:</span>
                <span className="text-sm font-bold text-blue-600 dark:text-blue-400">{count}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminStats;
