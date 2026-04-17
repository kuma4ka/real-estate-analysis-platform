/**
 * Integration tests for the api.ts service module.
 * Build 2 – Frontend + Backend integration (fetch mocked at boundary).
 *
 * Tests verify that api.ts correctly builds URLs, attaches auth headers,
 * handles error responses, and parses JSON — integrating service logic
 * with the browser fetch API.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import {
  fetchWithAuth,
  fetchProperties,
  fetchAllPropertiesForMap,
  fetchStats,
  fetchForecast,
} from '../api';


function mockFetch(body: unknown, ok = true, status = 200) {
  return vi.fn().mockResolvedValue({
    ok,
    status,
    statusText: ok ? 'OK' : 'Error',
    json: async () => body,
    blob: async () => new Blob(),
  });
}

beforeEach(() => {
  vi.stubGlobal('fetch', mockFetch({}));
  localStorage.clear();
});

afterEach(() => {
  vi.unstubAllGlobals();
});


describe('fetchWithAuth', () => {
  it('includes Bearer token from localStorage when present', async () => {
    localStorage.setItem('token', 'test-jwt-token');
    const fetchMock = mockFetch({ ok: true });
    vi.stubGlobal('fetch', fetchMock);

    await fetchWithAuth('/api/v1/test');

    const calledHeaders = new Headers(fetchMock.mock.calls[0][1].headers);
    expect(calledHeaders.get('Authorization')).toBe('Bearer test-jwt-token');
  });

  it('sends no Authorization header when no token in localStorage', async () => {
    const fetchMock = mockFetch({});
    vi.stubGlobal('fetch', fetchMock);

    await fetchWithAuth('/api/v1/test');

    const calledHeaders = new Headers(fetchMock.mock.calls[0][1]?.headers ?? {});
    expect(calledHeaders.get('Authorization')).toBeNull();
  });
});


describe('fetchProperties', () => {
  it('builds URL with city and page params correctly', async () => {
    const fetchMock = mockFetch({ data: [], meta: { page: 1, per_page: 20, total_pages: 0, total_items: 0 } });
    vi.stubGlobal('fetch', fetchMock);

    await fetchProperties({ city: 'Київ', page: 2 });

    const calledUrl: string = fetchMock.mock.calls[0][0];
    const decodedUrl = decodeURIComponent(calledUrl);
    expect(decodedUrl).toContain('city=Київ');
    expect(calledUrl).toContain('page=2');
    expect(calledUrl).toContain('/api/v1/properties');
  });

  it('does not include empty optional params in URL', async () => {
    const fetchMock = mockFetch({ data: [], meta: {} });
    vi.stubGlobal('fetch', fetchMock);

    await fetchProperties({});

    const calledUrl: string = fetchMock.mock.calls[0][0];
    expect(calledUrl).not.toContain('city=');
    expect(calledUrl).not.toContain('rooms=');
  });

  it('throws when API returns a non-ok response', async () => {
    vi.stubGlobal('fetch', mockFetch({}, false, 500));
    await expect(fetchProperties({})).rejects.toThrow();
  });

  it('returns parsed PropertiesResponse on success', async () => {
    const mockResponse = {
      data: [{ id: 1, title: 'Test' }],
      meta: { page: 1, per_page: 20, total_pages: 1, total_items: 1 },
    };
    vi.stubGlobal('fetch', mockFetch(mockResponse));

    const result = await fetchProperties({ page: 1 });
    expect(result.meta.total_items).toBe(1);
    expect(result.data[0].title).toBe('Test');
  });

  it('includes price_min and price_max when provided', async () => {
    const fetchMock = mockFetch({ data: [], meta: {} });
    vi.stubGlobal('fetch', fetchMock);

    await fetchProperties({ price_min: 50000, price_max: 100000 });

    const calledUrl: string = fetchMock.mock.calls[0][0];
    expect(calledUrl).toContain('price_min=50000');
    expect(calledUrl).toContain('price_max=100000');
  });

  it('includes sort param when provided', async () => {
    const fetchMock = mockFetch({ data: [], meta: {} });
    vi.stubGlobal('fetch', fetchMock);

    await fetchProperties({ sort: 'cheapest' });

    const calledUrl: string = fetchMock.mock.calls[0][0];
    expect(calledUrl).toContain('sort=cheapest');
  });

  it('includes search param when provided', async () => {
    const fetchMock = mockFetch({ data: [], meta: {} });
    vi.stubGlobal('fetch', fetchMock);

    await fetchProperties({ search: 'мансарда' });

    const calledUrl: string = fetchMock.mock.calls[0][0];
    expect(calledUrl).toContain('search=');
  });
});


describe('fetchAllPropertiesForMap', () => {
  it('calls the correct /map endpoint', async () => {
    const fetchMock = mockFetch({ data: [], count: 0 });
    vi.stubGlobal('fetch', fetchMock);

    await fetchAllPropertiesForMap();

    expect(fetchMock.mock.calls[0][0]).toContain('/api/v1/properties/map');
  });

  it('throws on non-ok response', async () => {
    vi.stubGlobal('fetch', mockFetch({}, false, 503));
    await expect(fetchAllPropertiesForMap()).rejects.toThrow();
  });

  it('returns count and data fields from response', async () => {
    const mockPayload = { data: [{ id: 1, lat: 50.45, lng: 30.52 }], count: 1 };
    vi.stubGlobal('fetch', mockFetch(mockPayload));

    const result = await fetchAllPropertiesForMap();
    expect(result.count).toBe(1);
    expect(result.data.length).toBe(1);
  });
});


describe('fetchStats', () => {
  it('calls /api/v1/stats endpoint', async () => {
    const fetchMock = mockFetch({ total_active: 10 });
    vi.stubGlobal('fetch', fetchMock);

    await fetchStats();

    expect(fetchMock.mock.calls[0][0]).toContain('/api/v1/stats');
  });

  it('throws on HTTP error', async () => {
    vi.stubGlobal('fetch', mockFetch({}, false, 403));
    await expect(fetchStats()).rejects.toThrow();
  });
});


describe('fetchForecast', () => {
  it('calls /api/v1/stats/forecast without city param when not provided', async () => {
    const fetchMock = mockFetch({ forecast: [], historical: [] });
    vi.stubGlobal('fetch', fetchMock);

    await fetchForecast();

    const calledUrl: string = fetchMock.mock.calls[0][0];
    expect(calledUrl).toContain('/api/v1/stats/forecast');
    expect(calledUrl).not.toContain('city=');
  });

  it('appends city query param when city is provided', async () => {
    const fetchMock = mockFetch({ forecast: [], historical: [], city: 'Київ' });
    vi.stubGlobal('fetch', fetchMock);

    await fetchForecast('Київ');

    const calledUrl: string = fetchMock.mock.calls[0][0];
    expect(calledUrl).toContain('city=');
    expect(decodeURIComponent(calledUrl)).toContain('Київ');
  });

  it('throws on HTTP error', async () => {
    vi.stubGlobal('fetch', mockFetch({}, false, 401));
    await expect(fetchForecast()).rejects.toThrow();
  });

  it('returns forecast and historical arrays from response', async () => {
    const mockPayload = {
      city: null,
      available_cities: ['Київ'],
      r_squared: 0.9,
      slope_per_day: 5.0,
      historical: [{ date: '2025-01-01', avg_price: 50000 }],
      forecast: [{ date: '2025-02-01', predicted_price: 52000, lower: 50000, upper: 54000 }],
    };
    vi.stubGlobal('fetch', mockFetch(mockPayload));

    const result = await fetchForecast();
    expect(result.historical).toHaveLength(1);
    expect(result.forecast).toHaveLength(1);
    expect(result.r_squared).toBe(0.9);
  });
});


describe('downloadStatsCsv', async () => {
  const { downloadStatsCsv } = await import('../api');

  it('calls the correct /stats/export endpoint', async () => {
    const fetchMock = mockFetch(new Blob(['csv,data']), true, 200);
    vi.stubGlobal('fetch', fetchMock);

    vi.stubGlobal('URL', {
      createObjectURL: vi.fn().mockReturnValue('blob:test'),
      revokeObjectURL: vi.fn(),
    });

    const mockAnchor = { href: '', download: '', click: vi.fn(), style: { display: '' } };
    const createElementSpy = vi.spyOn(document, 'createElement').mockReturnValue(mockAnchor as unknown as HTMLAnchorElement);
    vi.spyOn(document.body, 'appendChild').mockImplementation(() => document.body);

    await downloadStatsCsv();

    expect(fetchMock.mock.calls[0][0]).toContain('/api/v1/stats/export');
    expect(mockAnchor.click).toHaveBeenCalled();
    createElementSpy.mockRestore();
  });

  it('throws when export endpoint returns non-ok', async () => {
    vi.stubGlobal('fetch', mockFetch({}, false, 403));
    await expect(downloadStatsCsv()).rejects.toThrow();
  });
});

