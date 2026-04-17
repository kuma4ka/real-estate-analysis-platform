import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import FilterBar from '../FilterBar';
import { beforeEach, describe, expect, it, vi } from 'vitest';

vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => key,
  }),
}));

describe('FilterBar', () => {
  const mockOnFilterChange = vi.fn();

  beforeEach(() => {
    mockOnFilterChange.mockClear();
  });

  it('renders all filter inputs', () => {
    render(<FilterBar onFilterChange={mockOnFilterChange} />);
    
    expect(screen.getAllByText('city').length).toBeGreaterThan(0);
    expect(screen.getByText('min_price')).toBeInTheDocument();
    expect(screen.getByText('max_price')).toBeInTheDocument();
    expect(screen.getAllByText('rooms').length).toBeGreaterThan(0);
    expect(screen.getByText('sort_by')).toBeInTheDocument();
  });

  it('calls onFilterChange with specific values when apply is clicked', async () => {
    const user = userEvent.setup();
    render(<FilterBar onFilterChange={mockOnFilterChange} />);
    
    const cityInput = screen.getByPlaceholderText('city');
    await user.type(cityInput, 'Kyiv');
    
    const minPriceInput = screen.getByPlaceholderText('0');
    await user.type(minPriceInput, '50000');
    
    const applyButton = screen.getByText('apply');
    await user.click(applyButton);
    
    expect(mockOnFilterChange).toHaveBeenCalledWith(expect.objectContaining({
      city: 'Kyiv',
      price_min: 50000,
    }));
  });

  it('handles room selection toggle', async () => {
    const user = userEvent.setup();
    render(<FilterBar onFilterChange={mockOnFilterChange} />);
    
    const roomButton2 = screen.getByText('2');
    await user.click(roomButton2);
    
    await user.click(screen.getByText('apply'));
    
    expect(mockOnFilterChange).toHaveBeenCalledWith(expect.objectContaining({
      rooms: 2
    }));
    
    await user.click(roomButton2);
    await user.click(screen.getByText('apply'));
    
    expect(mockOnFilterChange).toHaveBeenLastCalledWith(expect.objectContaining({
      rooms: ''
    }));
  });

  it('resets all filters when reset is clicked', async () => {
    const user = userEvent.setup();
    render(<FilterBar onFilterChange={mockOnFilterChange} />);
    
    await user.type(screen.getByPlaceholderText('city'), 'Kyiv');
    await user.click(screen.getByText('2'));
    
    await user.click(screen.getByText('reset'));
    
    expect(mockOnFilterChange).toHaveBeenCalledWith({
      city: '',
      rooms: undefined,
      price_min: undefined,
      price_max: undefined,
      search: '',
      sort: 'newest',
      page: 1
    });
    
    expect(screen.getByPlaceholderText('city')).toHaveValue('');
  });
});
