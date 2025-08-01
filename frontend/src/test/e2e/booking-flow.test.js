import { test, expect } from '@playwright/test';

test.describe('Complete Booking Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Mock API responses
    await page.route('**/api/v1/auth/login', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          access_token: 'mock_token',
          refresh_token: 'mock_refresh_token',
          token_type: 'bearer',
          user: {
            id: '1',
            email: 'test@example.com',
            first_name: 'John',
            last_name: 'Doe',
            role: 'passenger'
          }
        })
      });
    });

    await page.route('**/api/v1/fleet/terminals', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: '1',
            name: 'Central Terminal',
            city: 'New York',
            latitude: 40.7128,
            longitude: -74.0060
          },
          {
            id: '2',
            name: 'Airport Terminal',
            city: 'Los Angeles',
            latitude: 34.0522,
            longitude: -118.2437
          }
        ])
      });
    });

    await page.route('**/api/v1/fleet/trips/search*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: '1',
            route: {
              id: '1',
              origin_terminal: {
                id: '1',
                name: 'Central Terminal',
                city: 'New York'
              },
              destination_terminal: {
                id: '2',
                name: 'Airport Terminal',
                city: 'Los Angeles'
              }
            },
            departure_time: '2024-12-01T10:00:00Z',
            arrival_time: '2024-12-01T16:00:00Z',
            fare: 75.00,
            available_seats: 45,
            bus: {
              id: '1',
              license_plate: 'ABC-123',
              model: 'Mercedes Sprinter',
              capacity: 50
            }
          }
        ])
      });
    });

    await page.route('**/api/v1/bookings', async (route) => {
      if (route.request().method() === 'POST') {
        await route.fulfill({
          status: 201,
          contentType: 'application/json',
          body: JSON.stringify({
            id: 'booking-123',
            trip_id: '1',
            seat_numbers: [1, 2],
            total_amount: 150.00,
            status: 'pending',
            payment_status: 'pending',
            booking_reference: 'BK123456'
          })
        });
      }
    });

    await page.route('**/api/v1/payments/create-intent', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          client_secret: 'pi_test_client_secret',
          payment_intent_id: 'pi_test_123'
        })
      });
    });
  });

  test('complete booking journey from search to payment', async ({ page }) => {
    // Step 1: Navigate to login page
    await page.goto('/login');
    
    // Step 2: Login
    await page.fill('[data-testid=email-input]', 'test@example.com');
    await page.fill('[data-testid=password-input]', 'password123');
    await page.click('[data-testid=login-button]');
    
    // Wait for redirect to dashboard
    await page.waitForURL('/dashboard');
    expect(page.url()).toContain('/dashboard');
    
    // Step 3: Navigate to booking page
    await page.click('[data-testid=book-trip-button]');
    await page.waitForURL('/booking');
    
    // Step 4: Fill trip search form
    await page.selectOption('[data-testid=origin-select]', '1');
    await page.selectOption('[data-testid=destination-select]', '2');
    
    // Set departure date to tomorrow
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    await page.fill('[data-testid=departure-date]', tomorrow.toISOString().split('T')[0]);
    
    await page.fill('[data-testid=passengers-input]', '2');
    
    // Step 5: Search for trips
    await page.click('[data-testid=search-button]');
    
    // Wait for search results
    await page.waitForSelector('[data-testid=trip-results]');
    expect(await page.locator('[data-testid=trip-card]').count()).toBeGreaterThan(0);
    
    // Step 6: Select a trip
    await page.click('[data-testid=select-trip-button]');
    
    // Wait for seat selection page
    await page.waitForSelector('[data-testid=seat-map]');
    
    // Step 7: Select seats
    await page.click('[data-testid=seat-1]');
    await page.click('[data-testid=seat-2]');
    
    // Verify seats are selected
    expect(await page.locator('[data-testid=selected-seats]').textContent()).toContain('2 seats selected');
    
    // Step 8: Proceed to booking summary
    await page.click('[data-testid=continue-button]');
    
    // Wait for booking summary
    await page.waitForSelector('[data-testid=booking-summary]');
    
    // Verify booking details
    expect(await page.locator('[data-testid=total-amount]').textContent()).toContain('$150.00');
    expect(await page.locator('[data-testid=seat-numbers]').textContent()).toContain('1, 2');
    
    // Step 9: Proceed to payment
    await page.click('[data-testid=proceed-to-payment]');
    
    // Wait for payment form
    await page.waitForSelector('[data-testid=payment-form]');
    
    // Step 10: Fill payment details (mock Stripe form)
    await page.fill('[data-testid=card-number]', '4242424242424242');
    await page.fill('[data-testid=card-expiry]', '12/25');
    await page.fill('[data-testid=card-cvc]', '123');
    await page.fill('[data-testid=cardholder-name]', 'John Doe');
    
    // Step 11: Submit payment
    await page.click('[data-testid=pay-button]');
    
    // Wait for payment success
    await page.waitForSelector('[data-testid=payment-success]');
    
    // Verify success message
    expect(await page.locator('[data-testid=success-message]').textContent()).toContain('Booking confirmed');
    expect(await page.locator('[data-testid=booking-reference]').textContent()).toContain('BK123456');
  });

  test('booking flow with seat unavailability', async ({ page }) => {
    // Mock API to return no available seats
    await page.route('**/api/v1/fleet/trips/search*', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: '1',
            route: {
              id: '1',
              origin_terminal: {
                id: '1',
                name: 'Central Terminal',
                city: 'New York'
              },
              destination_terminal: {
                id: '2',
                name: 'Airport Terminal',
                city: 'Los Angeles'
              }
            },
            departure_time: '2024-12-01T10:00:00Z',
            arrival_time: '2024-12-01T16:00:00Z',
            fare: 75.00,
            available_seats: 0,
            bus: {
              id: '1',
              license_plate: 'ABC-123',
              model: 'Mercedes Sprinter',
              capacity: 50
            }
          }
        ])
      });
    });

    await page.goto('/login');
    
    // Login
    await page.fill('[data-testid=email-input]', 'test@example.com');
    await page.fill('[data-testid=password-input]', 'password123');
    await page.click('[data-testid=login-button]');
    
    await page.waitForURL('/dashboard');
    
    // Navigate to booking
    await page.click('[data-testid=book-trip-button]');
    await page.waitForURL('/booking');
    
    // Fill search form
    await page.selectOption('[data-testid=origin-select]', '1');
    await page.selectOption('[data-testid=destination-select]', '2');
    
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    await page.fill('[data-testid=departure-date]', tomorrow.toISOString().split('T')[0]);
    
    // Search for trips
    await page.click('[data-testid=search-button]');
    
    // Wait for results
    await page.waitForSelector('[data-testid=trip-results]');
    
    // Verify trip shows as fully booked
    expect(await page.locator('[data-testid=trip-status]').textContent()).toContain('Fully Booked');
    expect(await page.locator('[data-testid=select-trip-button]')).toBeDisabled();
  });

  test('booking flow with payment failure', async ({ page }) => {
    // Mock payment failure
    await page.route('**/api/v1/payments/create-intent', async (route) => {
      await route.fulfill({
        status: 400,
        contentType: 'application/json',
        body: JSON.stringify({
          error: {
            code: 'PAYMENT_FAILED',
            message: 'Your card was declined'
          }
        })
      });
    });

    await page.goto('/login');
    
    // Complete booking flow up to payment
    await page.fill('[data-testid=email-input]', 'test@example.com');
    await page.fill('[data-testid=password-input]', 'password123');
    await page.click('[data-testid=login-button]');
    
    await page.waitForURL('/dashboard');
    await page.click('[data-testid=book-trip-button]');
    await page.waitForURL('/booking');
    
    await page.selectOption('[data-testid=origin-select]', '1');
    await page.selectOption('[data-testid=destination-select]', '2');
    
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    await page.fill('[data-testid=departure-date]', tomorrow.toISOString().split('T')[0]);
    
    await page.click('[data-testid=search-button]');
    await page.waitForSelector('[data-testid=trip-results]');
    
    await page.click('[data-testid=select-trip-button]');
    await page.waitForSelector('[data-testid=seat-map]');
    
    await page.click('[data-testid=seat-1]');
    await page.click('[data-testid=continue-button]');
    
    await page.waitForSelector('[data-testid=booking-summary]');
    await page.click('[data-testid=proceed-to-payment]');
    
    await page.waitForSelector('[data-testid=payment-form]');
    
    // Fill payment details
    await page.fill('[data-testid=card-number]', '4000000000000002'); // Declined card
    await page.fill('[data-testid=card-expiry]', '12/25');
    await page.fill('[data-testid=card-cvc]', '123');
    await page.fill('[data-testid=cardholder-name]', 'John Doe');
    
    // Submit payment
    await page.click('[data-testid=pay-button]');
    
    // Wait for error message
    await page.waitForSelector('[data-testid=payment-error]');
    
    // Verify error message
    expect(await page.locator('[data-testid=error-message]').textContent()).toContain('Your card was declined');
    expect(await page.locator('[data-testid=retry-button]')).toBeVisible();
  });
});

test.describe('Trip Tracking Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Mock authentication
    await page.route('**/api/v1/auth/login', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          access_token: 'mock_token',
          user: {
            id: '1',
            email: 'test@example.com',
            first_name: 'John',
            last_name: 'Doe'
          }
        })
      });
    });

    // Mock user bookings
    await page.route('**/api/v1/bookings/my-bookings', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: 'booking-123',
            trip: {
              id: 'trip-123',
              route: {
                origin_terminal: { name: 'Central Terminal', city: 'New York' },
                destination_terminal: { name: 'Airport Terminal', city: 'Los Angeles' }
              },
              departure_time: '2024-12-01T10:00:00Z',
              status: 'in_progress',
              bus: {
                license_plate: 'ABC-123',
                model: 'Mercedes Sprinter'
              }
            },
            seat_numbers: [1, 2],
            status: 'confirmed'
          }
        ])
      });
    });

    // Mock trip location
    await page.route('**/api/v1/tracking/trips/trip-123/location', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          latitude: 40.7128,
          longitude: -74.0060,
          speed: 65.5,
          heading: 180,
          recorded_at: '2024-12-01T11:30:00Z'
        })
      });
    });
  });

  test('complete trip tracking flow', async ({ page }) => {
    await page.goto('/login');
    
    // Login
    await page.fill('[data-testid=email-input]', 'test@example.com');
    await page.fill('[data-testid=password-input]', 'password123');
    await page.click('[data-testid=login-button]');
    
    await page.waitForURL('/dashboard');
    
    // Navigate to trip tracking
    await page.click('[data-testid=track-trips-button]');
    await page.waitForURL('/tracking');
    
    // Verify active trips are displayed
    expect(await page.locator('[data-testid=active-trip]').count()).toBeGreaterThan(0);
    
    // Click on a trip to track
    await page.click('[data-testid=track-trip-button]');
    
    // Wait for tracking map to load
    await page.waitForSelector('[data-testid=tracking-map]');
    
    // Verify trip information is displayed
    expect(await page.locator('[data-testid=trip-info]').textContent()).toContain('ABC-123');
    expect(await page.locator('[data-testid=route-info]').textContent()).toContain('Central Terminal → Airport Terminal');
    expect(await page.locator('[data-testid=trip-status]').textContent()).toContain('In Progress');
    
    // Verify location information
    expect(await page.locator('[data-testid=current-speed]').textContent()).toContain('65.5 mph');
    expect(await page.locator('[data-testid=last-update]').textContent()).toContain('11:30 AM');
    
    // Test map controls
    await page.click('[data-testid=center-on-bus]');
    await page.click('[data-testid=toggle-traffic]');
    
    // Verify controls work
    expect(await page.locator('[data-testid=traffic-toggle]')).toHaveClass(/active/);
  });
});

test.describe('User Profile Management', () => {
  test.beforeEach(async ({ page }) => {
    await page.route('**/api/v1/auth/login', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          access_token: 'mock_token',
          user: {
            id: '1',
            email: 'test@example.com',
            first_name: 'John',
            last_name: 'Doe',
            phone: '+1234567890'
          }
        })
      });
    });

    await page.route('**/api/v1/auth/me', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: '1',
          email: 'test@example.com',
          first_name: 'John',
          last_name: 'Doe',
          phone: '+1234567890'
        })
      });
    });
  });

  test('complete profile update flow', async ({ page }) => {
    await page.goto('/login');
    
    // Login
    await page.fill('[data-testid=email-input]', 'test@example.com');
    await page.fill('[data-testid=password-input]', 'password123');
    await page.click('[data-testid=login-button]');
    
    await page.waitForURL('/dashboard');
    
    // Navigate to profile
    await page.click('[data-testid=profile-menu]');
    await page.click('[data-testid=profile-link]');
    await page.waitForURL('/profile');
    
    // Verify current profile information
    expect(await page.locator('[data-testid=first-name-input]').inputValue()).toBe('John');
    expect(await page.locator('[data-testid=last-name-input]').inputValue()).toBe('Doe');
    expect(await page.locator('[data-testid=email-input]').inputValue()).toBe('test@example.com');
    expect(await page.locator('[data-testid=phone-input]').inputValue()).toBe('+1234567890');
    
    // Mock profile update
    await page.route('**/api/v1/auth/profile', async (route) => {
      if (route.request().method() === 'PUT') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            id: '1',
            email: 'test@example.com',
            first_name: 'Jane',
            last_name: 'Smith',
            phone: '+1987654321'
          })
        });
      }
    });
    
    // Update profile information
    await page.fill('[data-testid=first-name-input]', 'Jane');
    await page.fill('[data-testid=last-name-input]', 'Smith');
    await page.fill('[data-testid=phone-input]', '+1987654321');
    
    // Save changes
    await page.click('[data-testid=save-profile-button]');
    
    // Wait for success message
    await page.waitForSelector('[data-testid=success-message]');
    expect(await page.locator('[data-testid=success-message]').textContent()).toContain('Profile updated successfully');
  });
});