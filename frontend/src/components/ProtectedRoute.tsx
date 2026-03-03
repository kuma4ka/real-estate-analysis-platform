import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

interface ProtectedRouteProps {
  children: React.ReactNode;
  allowedRoles?: string[];
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children, allowedRoles }) => {
  const { user, token, isLoading } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-10 w-10 border-2 border-blue-500 border-t-transparent"></div>
      </div>
    );
  }

  if (!token || !user) {
    // Redirect unauthenticated users to login
    return <Navigate to="/login" replace />;
  }

  // If specific roles are required and user does not have them, deny access
  if (allowedRoles && !allowedRoles.includes(user.role)) {
    return (
      <div className="min-h-[50vh] flex flex-col items-center justify-center space-y-4">
        <h2 className="text-3xl font-bold text-gray-800 dark:text-white">Access Denied</h2>
        <p className="text-gray-600 dark:text-gray-300">
          You do not have the required role ({allowedRoles.join(' or ')}) to view this page.
        </p>
        <button 
          onClick={() => window.location.href = '/'}
          className="bg-blue-500 text-white px-4 py-2 rounded shadow hover:bg-blue-600"
        >
          Go Back Home
        </button>
      </div>
    );
  }

  return <>{children}</>;
};

export default ProtectedRoute;
