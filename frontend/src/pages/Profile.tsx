import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { fetchWithAuth, API_BASE_URL } from '../services/api';
import AdminStats from '../components/AdminStats';
import { useTranslation } from 'react-i18next';
import { UserRole } from '../types/user';

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
      <h2 className="text-3xl font-bold text-text-main tracking-tight mb-8 flex items-center gap-3">
        <span className="bg-primary/10 text-primary p-2 rounded-xl">👤</span>
        {t('profile_title', 'User Profile')}
      </h2>
      
      {user.role === UserRole.ADMIN && <AdminStats />}

      <div className="bg-surface border border-border shadow-card rounded-2xl mb-8 overflow-hidden">
        <div className="px-6 py-5 border-b border-border bg-background/50">
          <h3 className="text-lg font-semibold text-text-main">{t('profile_account_details', 'Account Details')}</h3>
        </div>
        <div className="px-6 py-6">
          <dl className="grid grid-cols-1 gap-x-4 gap-y-6 sm:grid-cols-2">
            <div className="sm:col-span-1">
              <dt className="text-sm font-medium text-text-muted mb-1">{t('profile_email', 'Email Address')}</dt>
              <dd className="text-base text-text-main font-semibold flex items-center gap-2">
                <svg className="w-5 h-5 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" /></svg>
                {user.email}
              </dd>
            </div>
            <div className="sm:col-span-1">
              <dt className="text-sm font-medium text-text-muted mb-1">{t('profile_role', 'Role')}</dt>
              <dd className="text-base text-text-main font-semibold flex items-center gap-2">
                 <svg className="w-5 h-5 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" /></svg>
                <span className="px-2.5 py-1 bg-primary/10 text-primary border border-primary/20 rounded-md text-xs tracking-wide uppercase">
                   {user.role === UserRole.ADMIN ? t('admin_role', 'Admin') : user.role === UserRole.ANALYST ? t('analyst_role', 'Analyst') : user.role === UserRole.USER ? t('user_role', 'User') : t('guest_role', 'Guest')}
                </span>
              </dd>
            </div>
          </dl>
        </div>
      </div>

      <div className="bg-surface border border-border shadow-card rounded-2xl overflow-hidden">
        <div className="px-6 py-5 border-b border-border bg-background/50">
          <h3 className="text-lg font-semibold text-text-main">{t('profile_change_password', 'Change Password')}</h3>
        </div>
        <div className="px-6 py-6">
          {status && (
            <div className={`p-4 mb-6 rounded-xl text-sm font-medium flex items-center gap-3 ${status.type === 'error' ? 'bg-red-500/10 text-red-500 border border-red-500/20' : 'bg-green-500/10 text-green-500 border border-green-500/20'}`}>
              <span className="text-xl">{status.type === 'error' ? '⚠️' : '✅'}</span>
              {status.message}
            </div>
          )}

          <form onSubmit={handlePasswordChange} className="space-y-5 max-w-md">
            <div>
              <label className="block text-sm font-medium text-text-main mb-1.5">{t('profile_old_password', 'Old Password')}</label>
              <input
                type="password"
                required
                className="w-full px-4 py-2.5 border border-border rounded-xl focus:ring-2 focus:ring-primary focus:border-primary bg-background text-text-main transition-colors"
                value={oldPassword}
                onChange={(e) => setOldPassword(e.target.value)}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-text-main mb-1.5">{t('profile_new_password', 'New Password')}</label>
              <input
                type="password"
                required
                className="w-full px-4 py-2.5 border border-border rounded-xl focus:ring-2 focus:ring-primary focus:border-primary bg-background text-text-main transition-colors"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-text-main mb-1.5">{t('profile_confirm_password', 'Confirm New Password')}</label>
              <input
                type="password"
                required
                className="w-full px-4 py-2.5 border border-border rounded-xl focus:ring-2 focus:ring-primary focus:border-primary bg-background text-text-main transition-colors"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
              />
            </div>
            
            <div className="pt-4">
              <button
                type="submit"
                disabled={loading}
                className="w-full sm:w-auto bg-primary text-white font-medium py-2.5 px-6 rounded-xl hover:bg-primary-hover focus:ring-4 focus:ring-primary/20 disabled:opacity-60 disabled:cursor-not-allowed transition-all"
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
