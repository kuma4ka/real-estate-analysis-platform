/**
 * Integration tests for ProtectedRoute component.
 * Build 2 – Frontend integration: ProtectedRoute ↔ AuthContext integration.
 *
 * Tests verify routing behavior when user is unauthenticated, authenticated,
 * or lacks the required role — integrating ProtectedRoute with AuthContext.
 */
import { render, screen } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { describe, it, expect, vi } from 'vitest';
import ProtectedRoute from '../ProtectedRoute';

import { UserRole } from '../../types/user';

type AuthState = {
  user: { id: number; email: string; role: UserRole } | null;
  token: string | null;
  isLoading: boolean;
  login: ReturnType<typeof vi.fn>;
  logout: ReturnType<typeof vi.fn>;
};

// We mock AuthContext to control auth state cleanly in each test
vi.mock('../../context/AuthContext', () => ({
  useAuth: vi.fn(),
}));

import { useAuth } from '../../context/AuthContext';
const mockUseAuth = vi.mocked(useAuth);

/**
 * Helper: Render ProtectedRoute inside MemoryRouter with an initial path.
 * A Login page stub is used to verify redirect targets.
 */
function renderProtected(
  { user = null, token = null, isLoading = false }: Partial<AuthState> = {},
  allowedRoles?: UserRole[],
) {
  mockUseAuth.mockReturnValue({
    user,
    token,
    isLoading,
    login: vi.fn(),
    logout: vi.fn(),
  } as unknown as ReturnType<typeof useAuth>);

  return render(
    <MemoryRouter initialEntries={['/protected']}>
      <Routes>
        <Route path="/login" element={<div>Login Page</div>} />
        <Route
          path="/protected"
          element={
            <ProtectedRoute allowedRoles={allowedRoles}>
              <div>Protected Content</div>
            </ProtectedRoute>
          }
        />
      </Routes>
    </MemoryRouter>,
  );
}

describe('ProtectedRoute', () => {
  it('redirects unauthenticated user (no token, no user) to /login', () => {
    renderProtected({ user: null, token: null });
    expect(screen.getByText('Login Page')).toBeInTheDocument();
    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument();
  });

  it('redirects when token present but user is null', () => {
    renderProtected({ user: null, token: 'some-token' });
    expect(screen.getByText('Login Page')).toBeInTheDocument();
  });

  it('renders children when user and token are present', () => {
    renderProtected({
      user: { id: 1, email: 'test@test.com', role: UserRole.USER },
      token: 'valid-token',
    });
    expect(screen.getByText('Protected Content')).toBeInTheDocument();
    expect(screen.queryByText('Login Page')).not.toBeInTheDocument();
  });

  it('shows loading spinner while auth state is loading', () => {
    renderProtected({ isLoading: true });
    // Should render the spinner div, not redirect or show content
    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument();
    expect(screen.queryByText('Login Page')).not.toBeInTheDocument();
  });

  it('renders children when user has a role within allowedRoles', () => {
    renderProtected(
      { user: { id: 1, email: 'analyst@test.com', role: UserRole.ANALYST }, token: 'tok' },
      [UserRole.ANALYST, UserRole.ADMIN],
    );
    expect(screen.getByText('Protected Content')).toBeInTheDocument();
  });

  it('denies access and shows Access Denied when user lacks required role', () => {
    renderProtected(
      { user: { id: 2, email: 'user@test.com', role: UserRole.USER }, token: 'tok' },
      [UserRole.ADMIN],
    );
    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument();
    expect(screen.getByText('Access Denied')).toBeInTheDocument();
  });

  it('Admin can access a route restricted to Admin only', () => {
    renderProtected(
      { user: { id: 3, email: 'admin@test.com', role: UserRole.ADMIN }, token: 'tok' },
      [UserRole.ADMIN],
    );
    expect(screen.getByText('Protected Content')).toBeInTheDocument();
  });

  it('renders children when no allowedRoles restriction is specified', () => {
    renderProtected({
      user: { id: 4, email: 'anyone@test.com', role: UserRole.USER },
      token: 'tok',
    });
    expect(screen.getByText('Protected Content')).toBeInTheDocument();
  });
});
