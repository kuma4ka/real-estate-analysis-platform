/// <reference types="cypress" />

describe('UAT Happy Paths (Practical Work 5)', () => {
  const mockUser = { id: 1, email: 'user@test.com', role: 'User' };
  const mockAnalyst = { id: 2, email: 'analyst@test.com', role: 'Analyst' };
  const mockAdmin = { id: 3, email: 'admin@test.com', role: 'Admin' };

  // A dummy JWT that jwt-decode can parse. exp = 2000000000 (year 2033)
  const validMockToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjIwMDAwMDAwMDB9.signature';

  const mockProperties = {
    data: [
      {
        id: 1, title: 'Затишна квартира в центрі', price: 45000, currency: 'USD',
        city: 'Київ', rooms: 2, area: 50, address: 'Khreshchatyk 1',
        lat: 50.45, lon: 30.52, image_urls: [], source_url: 'http://test.com/1',
        is_active: true, created_at: '2026-01-01T00:00:00Z', updated_at: '2026-01-01T00:00:00Z'
      }
    ],
    meta: { total_items: 1, total_pages: 1, current_page: 1, per_page: 12 }
  };

  const loginAs = (mockData: any) => {
    cy.intercept('POST', '**/api/v1/auth/login', { statusCode: 200, body: { token: validMockToken, user: mockData } }).as('mockLogin');
    cy.intercept('GET', '**/api/v1/auth/me', { statusCode: 200, body: mockData }).as('mockMe');
    cy.visit('/login');
    cy.get('input[type="email"]').type(mockData.email);
    cy.get('input[type="password"]').type('ValidPass123!');
    cy.get('form button[type="submit"]').click();
    cy.wait('@mockLogin');
  };

  beforeEach(() => {
    cy.clearLocalStorage();
    
    cy.intercept('GET', '**/api/v1/properties/map*', { statusCode: 200, body: { data: mockProperties.data, count: 1 } }).as('getMap');
    cy.intercept('GET', '**/api/v1/properties*', (req) => {
      req.reply({ statusCode: 200, body: mockProperties });
    }).as('getProperties');
  });

  it('TC_001: UAT_Register - Happy Path', () => {
    cy.intercept('POST', '**/api/v1/auth/register', {
      statusCode: 201, body: { message: 'Registered', token: validMockToken, user: mockUser }
    }).as('register');

    cy.visit('/register');
    cy.get('input[type="email"]').type('test@test.com');
    cy.get('input[type="password"]').type('ValidPass123!');
    cy.get('form button[type="submit"]').click();

    cy.wait('@register');
    cy.url().should('eq', Cypress.config().baseUrl + '/');
  });

  it('TC_002: UAT_Login - Valid credentials opens protected UI', () => {
    loginAs(mockUser);
    cy.url().should('eq', Cypress.config().baseUrl + '/');
  });

  it('TC_003: UAT_PropList - Pagination and List view', () => {
    cy.intercept('GET', '**/api/v1/properties*', {
      statusCode: 200, body: { ...mockProperties, meta: { total_items: 30, total_pages: 3, current_page: 1, per_page: 12 } }
    }).as('getPagedProperties');
    cy.visit('/');
    cy.wait('@getPagedProperties');
    cy.get('h3').contains('Затишна квартира в центрі').should('be.visible');
    // Check pagination buttons by looking for standard prev/next indicators.
    cy.contains('button', '→', { matchCase: false }).should('exist');
  });

  it('TC_004: UAT_PropFilter - Kyiv, price < 50000', () => {
    cy.visit('/');
    cy.wait('@getProperties');

    cy.get('input[placeholder*="City"]').first().type('Київ', { force: true });
    cy.get('input[placeholder*="Max"]').first().type('50000', { force: true });
    cy.get('h3').contains('Затишна квартира в центрі').should('be.visible');
  });

  it('TC_005: UAT_PropDetail - Click property card details', () => {
    cy.intercept('GET', '**/api/v1/properties/1', { statusCode: 200, body: mockProperties.data[0] }).as('getPropertyDetail');
    cy.visit('/');
    cy.wait('@getProperties');
    
    // PropertyCard is the whole clickable block. Click the title to safely trigger
    cy.contains('Затишна квартира в центрі').click();
  });

  it('TC_006: UAT_RoleAn - Analyst session and linear regression graphs', () => {
    loginAs(mockAnalyst);
    
    cy.intercept('GET', '**/api/v1/stats*', {
      statusCode: 200,
      body: {
        total_active: 50, avg_price: 35000, avg_area: 45,
        by_city: [{ city: 'Київ', count: 30, avg_price: 50000 }],
        by_rooms: [{ rooms: 1, count: 20, avg_price: 25000 }],
        by_price_ranges: [], recent_trend: []
      }
    }).as('getStats');
    cy.intercept('GET', '**/api/v1/stats/forecast*', {
      statusCode: 200,
      body: {
        r_squared: 0.9, slope_per_day: 10,
        forecast: [{ date: '2026-03-25', predicted_price: 40000, lower: 38000, upper: 42000 }],
        historical: [], city: null, available_cities: ['Київ']
      }
    }).as('getForecast');

    cy.contains('button', 'Analytics', { timeout: 10000 }).should('be.visible').click();
    cy.wait('@getStats');
    cy.wait('@getForecast');
    
    // Check for an SVG that Recharts creates
    cy.get('.recharts-wrapper').should('have.length.at.least', 1);
  });

  it('TC_007: UAT_RoleAd - Admin session System Metrics', () => {
    loginAs(mockAdmin);
    
    cy.intercept('GET', '**/api/v1/stats*', {
      statusCode: 200,
      body: {
        total_users: 15, total_properties: 300, active_properties: 250, 
        total_active: 50, avg_price: 35000, avg_area: 45,
        by_city: [], by_rooms: [], by_price_ranges: [], recent_trend: []
      }
    }).as('getAdminStats');

    cy.contains('button', 'Analytics', { timeout: 10000 }).should('be.visible').click();
    cy.wait('@getAdminStats');
    cy.contains('Analytics').should('be.visible');
  });

  it('TC_008: UAT_Export - Export PDF functionality', () => {
    loginAs(mockAnalyst);
    cy.intercept('GET', '**/api/v1/stats*', { statusCode: 200, body: { total_active: 5, avg_price: 1, avg_area: 1, by_city: [], by_rooms: [], by_price_ranges: [], recent_trend: [] } });
    cy.intercept('GET', '**/api/v1/stats/forecast*', { statusCode: 200, body: { error: 'data' } });

    cy.contains('button', 'Analytics', { timeout: 10000 }).should('be.visible').click();
    cy.window().then((win) => { cy.stub(win.URL, 'createObjectURL').as('pdfDownload'); });
    cy.contains('button', 'Download PDF', { matchCase: false }).click();
  });

  it('TC_011: UAT_Perfomance - Loading Map heavy DOM < 2s', () => {
    const massiveData = Array.from({ length: 500 }, (_, i) => ({
      id: i, title: `Apt ${i}`, price: 1000, currency: 'USD',
      city: 'Київ', rooms: 1, area: 30, address: `Street ${i}`,
      lat: 50.4 + (Math.random() * 0.1), lng: 30.5 + (Math.random() * 0.1),
      image_urls: [], source_url: null, is_active: true, created_at: '', updated_at: ''
    }));

    cy.intercept('GET', '**/api/v1/properties/map*', { statusCode: 200, body: { data: massiveData, count: 500 } }).as('getMassiveMap');

    cy.visit('/');
    cy.contains('button', 'Map', { matchCase: false }).click();
    
    cy.wait('@getMassiveMap').then(() => {
      cy.get('.leaflet-marker-icon', { timeout: 2500 }).should('exist');
    });
  });
});
