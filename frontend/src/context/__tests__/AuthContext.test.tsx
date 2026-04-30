/**
 * Integration tests for AuthContext (AuthProvider + useAuth hook).
 * Build 2 – Frontend integration: AuthProvider state + sessionStorage interaction.
 *
 * Tests verify that the AuthContext correctly manages auth state,
 * persists tokens to sessionStorage, reads them back on mount, and clears them on logout.
 */
import { render, screen, act, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { AuthProvider, useAuth } from '../../context/AuthContext';

/**
 * Mock jwt-decode so we can control expiry in tests without real JWTs.
 * Tests that need an expired token can override this mock locally.
 */
vi.mock('jwt-decode', () => ({
  jwtDecode: vi.fn(() => ({
    // exp 1 year in the future from now
    exp: Math.floor(Date.now() / 1000) + 60 * 60 * 24 * 365,
    sub: 1,
    role: 'User',
  })),
}));

vi.mock('../../services/api', () => ({
  apiLogout: vi.fn().mockResolvedValue(undefined),
}));

/** A simple consumer component to expose AuthContext values for assertions. */
function AuthConsumer() {
  const { user, token, isLoading, login, logout } = useAuth();
  return (
    <div>
      <span data-testid="isLoading">{String(isLoading)}</span>
      <span data-testid="user">{user ? JSON.stringify(user) : 'null'}</span>
      <span data-testid="token">{token ?? 'null'}</span>
      <button
        onClick={() => login('mock-jwt', { id: 1, email: 'test@test.com', role: 'User' })}
      >
        Login
      </button>
      <button onClick={logout}>Logout</button>
    </div>
  );
}

function renderWithAuth() {
  return render(
    <AuthProvider>
      <AuthConsumer />
    </AuthProvider>,
  );
}

beforeEach(() => {
  sessionStorage.clear();
  vi.clearAllMocks();
});

describe('AuthContext', () => {
  it('initial state has no user and no token when sessionStorage is empty', async () => {
    renderWithAuth();
    await waitFor(() => {
      expect(screen.getByTestId('isLoading').textContent).toBe('false');
    });
    expect(screen.getByTestId('user').textContent).toBe('null');
    expect(screen.getByTestId('token').textContent).toBe('null');
  });

  it('loads user and token from sessionStorage on mount if token is valid', async () => {
    const storedUser = { id: 1, email: 'stored@test.com', role: 'Analyst' };
    sessionStorage.setItem('token', 'existing-jwt');
    sessionStorage.setItem('user', JSON.stringify(storedUser));

    renderWithAuth();
    await waitFor(() => {
      expect(screen.getByTestId('isLoading').textContent).toBe('false');
    });

    expect(screen.getByTestId('token').textContent).toBe('existing-jwt');
    const userVal = JSON.parse(screen.getByTestId('user').textContent!);
    expect(userVal.email).toBe('stored@test.com');
    expect(userVal.role).toBe('Analyst');
  });

  it('clears storage and sets user=null if stored token is expired', async () => {
    const { jwtDecode } = await import('jwt-decode');
    vi.mocked(jwtDecode).mockReturnValueOnce({ exp: 1 } as { exp: number }); // expired

    sessionStorage.setItem('token', 'expired-jwt');
    sessionStorage.setItem('user', JSON.stringify({ id: 99, email: 'old@test.com', role: 'User' }));

    renderWithAuth();
    await waitFor(() => {
      expect(screen.getByTestId('isLoading').textContent).toBe('false');
    });

    expect(screen.getByTestId('user').textContent).toBe('null');
    expect(screen.getByTestId('token').textContent).toBe('null');
    expect(sessionStorage.getItem('token')).toBeNull();
  });

  it('clears storage and sets user=null if stored token is malformed', async () => {
    const { jwtDecode } = await import('jwt-decode');
    vi.mocked(jwtDecode).mockImplementationOnce(() => { throw new Error('bad token'); });

    sessionStorage.setItem('token', 'malformed-jwt');

    renderWithAuth();
    await waitFor(() => {
      expect(screen.getByTestId('isLoading').textContent).toBe('false');
    });

    expect(screen.getByTestId('user').textContent).toBe('null');
    expect(sessionStorage.getItem('token')).toBeNull();
  });

  it('login() saves token and user to state and sessionStorage', async () => {
    renderWithAuth();
    await waitFor(() => {
      expect(screen.getByTestId('isLoading').textContent).toBe('false');
    });

    act(() => {
      screen.getByText('Login').click();
    });

    expect(screen.getByTestId('token').textContent).toBe('mock-jwt');
    const user = JSON.parse(screen.getByTestId('user').textContent!);
    expect(user.email).toBe('test@test.com');
    expect(sessionStorage.getItem('token')).toBe('mock-jwt');
    expect(JSON.parse(sessionStorage.getItem('user')!).role).toBe('User');
  });

  it('logout() clears state and sessionStorage', async () => {
    sessionStorage.setItem('token', 'existing-jwt');
    sessionStorage.setItem('user', JSON.stringify({ id: 1, email: 'me@test.com', role: 'User' }));

    renderWithAuth();
    await waitFor(() => {
      expect(screen.getByTestId('token').textContent).toBe('existing-jwt');
    });

    await act(async () => {
      screen.getByText('Logout').click();
    });

    await waitFor(() => {
      expect(screen.getByTestId('user').textContent).toBe('null');
    });
    expect(screen.getByTestId('token').textContent).toBe('null');
    expect(sessionStorage.getItem('token')).toBeNull();
    expect(sessionStorage.getItem('user')).toBeNull();
  });

  it('isLoading transitions from true to false after mount', async () => {
    renderWithAuth();
    await waitFor(() => {
      expect(screen.getByTestId('isLoading').textContent).toBe('false');
    });
  });
});
