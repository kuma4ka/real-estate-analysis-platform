import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import PropertyCard from '../PropertyCard';
import { describe, expect, it, vi } from 'vitest';
import type { Property } from '../../types/property';

vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string, fallback?: string) => fallback ?? key,
  }),
}));

vi.mock('../../context/AuthContext', () => ({
  useAuth: vi.fn(),
}));

import { useAuth } from '../../context/AuthContext';
const mockUseAuth = vi.mocked(useAuth);

const mockProperty: Property = {
  id: 1,
  title: 'Test Apartment',
  price: 50000,
  currency: 'USD',
  address: '123 Test St',
  city: 'Test City',
  district: 'Test District',
  geocode_precision: 'ROOFTOP',
  area: 45,
  rooms: 2,
  floor: 3,
  description: 'A test apartment',
  images: ['/test-image.jpg'],
  source_url: 'http://test.com',
  created_at: '2023-01-01T00:00:00Z',
  lat: 50.45,
  lng: 30.52,
};

function renderCard(property = mockProperty, user: { id: number; email: string; role: string } | null = { id: 1, email: 'test@test.com', role: 'User' }) {
  mockUseAuth.mockReturnValue({ user, token: user ? 'tok' : null, isLoading: false, login: vi.fn(), logout: vi.fn() } as ReturnType<typeof useAuth>);
  return render(
    <MemoryRouter>
      <PropertyCard property={property} />
    </MemoryRouter>
  );
}

describe('PropertyCard', () => {
  it('renders property title and address', () => {
    renderCard();
    expect(screen.getByText('Test Apartment')).toBeInTheDocument();
    expect(screen.getByText('123 Test St')).toBeInTheDocument();
  });

  it('renders formatted price', () => {
    renderCard();
    expect(screen.getByText(/50/)).toBeInTheDocument();
  });

  it('renders fallback when no images provided', () => {
    const { container } = renderCard({ ...mockProperty, images: [] });
    expect(container.querySelector('img')).not.toBeInTheDocument();
  });

  it('renders image when provided', () => {
    renderCard();
    const img = screen.getByRole('img');
    expect(img).toHaveAttribute('src', '/test-image.jpg');
    expect(img).toHaveAttribute('alt', 'Test Apartment');
  });

  it('displays rooms and area', () => {
    renderCard();
    expect(screen.getByText(/2\s*rooms/i)).toBeInTheDocument();
    expect(screen.getByText(/45\s*area_unit/i)).toBeInTheDocument();
  });

  it('shows guest banner when user is not logged in', () => {
    renderCard(mockProperty, null);
    expect(screen.getByText('Sign in to view contacts')).toBeInTheDocument();
  });

  it('does not show guest banner when user is logged in', () => {
    renderCard();
    expect(screen.queryByText('Sign in to view contacts')).not.toBeInTheDocument();
  });

  it('shows city when address is null', () => {
    renderCard({ ...mockProperty, address: null });
    expect(screen.getByText('Test City')).toBeInTheDocument();
  });
});
