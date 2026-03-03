import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { fetchWithAuth, API_BASE_URL } from '../services/api';
import AdminStats from '../components/AdminStats';
import { useTranslation } from 'react-i18next';

const Profile: React.FC = () => {
  const { user } = useAuth();
  const { t } = useTranslation();
  
  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  
  const [status, setStatus] = useState<{ type: 'error' | 'success', message: string } | null>(null);
  const [loading, setLoading] = useState(false);

  const handlePasswordChange = async (e: React.FormEvent) => {
    e.preventDefault();
    setStatus(null);

    if (newPassword !== confirmPassword) {
      setStatus({ type: 'error', message: t('error_passwords_mismatch', 'New passwords do not match') });
      return;
    }

    if (newPassword.length < 6) {
      setStatus({ type: 'error', message: t('error_password_length', 'New password must be at least 6 characters') });
      return;
    }

    setLoading(true);

    try {
      const response = await fetchWithAuth(`${API_BASE_URL}/auth/me/password`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          old_password: oldPassword,
          new_password: newPassword
        })
      });

      let data: Record<string, unknown>;
      try {
        data = await response.json();
      } catch {
        if (response.status === 429) {
          throw new Error(t('error_too_many_requests', 'Too many requests. Please try again later.'));
        }
        throw new Error(t('error_password_update_failed', 'Failed to update password. Server error.'));
      }

      if (!response.ok) {
        let errorMessage = (data.message as string) || t('error_password_update_failed', 'Failed to update password');
        if (data.errors && typeof data.errors === 'object') {
          errorMessage = Object.values(data.errors).flat().join(' ');
        }
        throw new Error(errorMessage);
      }

      setStatus({ type: 'success', message: t('success_password_updated', 'Password updated successfully') });
      setOldPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (err) {
      setStatus({ type: 'error', message: err instanceof Error ? err.message : String(err) });
    } finally {
      setLoading(false);
    }
  };

  if (!user) return null;

  return (
    <div className="max-w-2xl mx-auto py-12 px-4 sm:px-6 lg:px-8">
      <h2 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-indigo-600 dark:from-blue-400 dark:to-indigo-400 mb-8">
        {t('profile_title', 'User Profile')}
      </h2>
      
      {user.role === 'Admin' && <AdminStats />}

      <div className="bg-white dark:bg-gray-800 shadow rounded-lg mb-8 overflow-hidden">
        <div className="px-6 py-5 border-b border-gray-200 dark:border-gray-700">
          <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100">{t('profile_account_details', 'Account Details')}</h3>
        </div>
        <div className="px-6 py-5">
          <dl className="grid grid-cols-1 gap-x-4 gap-y-6 sm:grid-cols-2">
            <div className="sm:col-span-1">
              <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">{t('profile_email', 'Email Address')}</dt>
              <dd className="mt-1 text-sm text-gray-900 dark:text-gray-100 font-semibold">{user.email}</dd>
            </div>
            <div className="sm:col-span-1">
              <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">{t('profile_role', 'Role')}</dt>
              <dd className="mt-1 text-sm text-gray-900 dark:text-gray-100 font-semibold">
                <span className="px-2 py-1 bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200 rounded text-xs">
                  {user.role === 'Admin' ? t('admin_role', 'Admin') : user.role === 'Analyst' ? t('analyst_role', 'Analyst') : user.role === 'User' ? t('user_role', 'User') : t('guest_role', 'Guest')}
                </span>
              </dd>
            </div>
          </dl>
        </div>
      </div>

      <div className="bg-white dark:bg-gray-800 shadow rounded-lg overflow-hidden">
        <div className="px-6 py-5 border-b border-gray-200 dark:border-gray-700">
          <h3 className="text-lg font-medium text-gray-900 dark:text-gray-100">{t('profile_change_password', 'Change Password')}</h3>
        </div>
        <div className="px-6 py-5">
          {status && (
            <div className={`p-4 mb-4 rounded-md text-sm ${status.type === 'error' ? 'bg-red-50 text-red-700 dark:bg-red-900/50 dark:text-red-200' : 'bg-green-50 text-green-700 dark:bg-green-900/50 dark:text-green-200'}`}>
              {status.message}
            </div>
          )}

          <form onSubmit={handlePasswordChange} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('profile_old_password', 'Old Password')}</label>
              <input
                type="password"
                required
                className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 bg-gray-50 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                value={oldPassword}
                onChange={(e) => setOldPassword(e.target.value)}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('profile_new_password', 'New Password')}</label>
              <input
                type="password"
                required
                className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 bg-gray-50 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{t('profile_confirm_password', 'Confirm New Password')}</label>
              <input
                type="password"
                required
                className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 bg-gray-50 dark:bg-gray-700 dark:border-gray-600 dark:text-white"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
              />
            </div>
            
            <div className="pt-2">
              <button
                type="submit"
                disabled={loading}
                className="w-full sm:w-auto bg-blue-600 text-white font-semibold py-2 px-6 rounded-lg hover:bg-blue-700 disabled:opacity-50 transition"
              >
                {loading ? t('profile_changing_pwd', 'Changing...') : t('profile_change_pwd_btn', 'Change Password')}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default Profile;
