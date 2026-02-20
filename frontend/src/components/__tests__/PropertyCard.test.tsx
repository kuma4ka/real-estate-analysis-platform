import { render, screen } from '@testing-library/react';
import PropertyCard from '../PropertyCard';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { Property } from '../../types/property';

// Mock react-i18next
vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => key,
  }),
}));

const mockProperty: Property = {
  id: 1,
  title: 'Test Apartment',
  price: 50000,
  currency: 'USD',
  address: '123 Test St',
  city: 'Test City',
  district: 'Test District',
  region: 'Test Region',
  area: 45,
  rooms: 2,
  description: 'A test apartment',
  images: ['/test-image.jpg'],
  source_url: 'http://test.com',
  created_at: '2023-01-01T00:00:00Z',
  lat: 50.45,
  lng: 30.52
};

describe('PropertyCard', () => {
  it('renders property title and address', () => {
    render(<PropertyCard property={mockProperty} />);
    
    expect(screen.getByText('Test Apartment')).toBeInTheDocument();
    expect(screen.getByText('123 Test St')).toBeInTheDocument();
  });

  it('renders formatted price', () => {
    render(<PropertyCard property={mockProperty} />);
    
    // 50 000 US$ or similar formatting based on locale
    // We can check if the basic number sequence is there
    const priceElement = screen.getByText(/50/);
    expect(priceElement).toBeInTheDocument();
  });

  it('renders fallback when no images provided', () => {
    const noImageProperty = { ...mockProperty, images: [] };
    const { container } = render(<PropertyCard property={noImageProperty} />);
    
    // Should not render an img tag
    expect(container.querySelector('img')).not.toBeInTheDocument();
  });

  it('renders image when provided', () => {
    render(<PropertyCard property={mockProperty} />);
    
    const img = screen.getByRole('img');
    expect(img).toHaveAttribute('src', '/test-image.jpg');
    expect(img).toHaveAttribute('alt', 'Test Apartment');
  });

  it('displays rooms and area', () => {
    render(<PropertyCard property={mockProperty} />);
    
    expect(screen.getByText(/2\s*rooms/)).toBeInTheDocument();
    expect(screen.getByText(/45\s*area_unit/)).toBeInTheDocument();
  });
});
