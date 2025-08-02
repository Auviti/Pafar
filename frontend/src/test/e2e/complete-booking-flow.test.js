/**
 * End-to-end tests for complete booking flow
 */
import { test, expect } from '@playwright/test';

test.describe('Complete Booking Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Mock API responses
    await page.route('**/api/v1/terminals', async (route) => {
      await route.fulfill({
        json: [
          { id: '1', name: 'Central Terminal', city: 'New York' },
          { id: '2', name: 'Airport Terminal', city: 'Los Angeles' },
          { id: '3', name: 'Downtown Station', city: 'Chicago' },
        ],
      });
    });

    await page.route('**/api/v1/auth/register', async (route) => {
      await route.fulfill({
        json: {
          id: '1',
          email: 'test@example.com',
          firstName: 'John',
          lastName: 'Doe',
          role: 'passenger',
        },
      });
    });

    await page.route('**/api/v1/auth/login', async (route) => {
      await route.fulfill({
        json: {
          user: {
            id: '1',
            email: 'test@example.com',
            firstName: 'John',
            lastName: 'Doe',
          },
          access_token: 'mock-token',
          refresh_token: 'mock-refresh-token',
        },
      });
    });

    await page.route('**/api/v1/bookings/trips/search', async (route) => {
      await route.fulfill({
        json: [
          {
            id: '1',
            departure_time: '2024-12-25T10:00:00Z',
            arrival_time: '2024-12-25T14:00:00Z',
            fare: 50,
            available_seats: 15,
            estimated_duration: 240,
            origin_terminal: {
              name: 'Central Terminal',
              city: 'New York',
            },
            destination_terminal: {
              name: 'Airport Terminal',
              city: 'Los Angeles',
            },
            bus: {
              model: 'Mercedes Sprinter',
              license_plate: 'ABC-123',
              amenities: ['WiFi', 'AC', 'USB Charging'],
            },
          },
        ],
      });
    });

    await page.route('**/api/v1/bookings', async (route) => {
      await route.fulfill({
        json: {
          id: '1',
          booking_reference: 'BK123456',
          status: 'pending',
          payment_status: 'pending',
          seat_numbers: [1, 2],
          total_amount: 100,
          trip: {
            id: '1',
            departure_time: '2024-12-25T10:00:00Z',
            origin_terminal: { name: 'Central Terminal', city: 'New York' },
            destination_terminal: { name: 'Airport Terminal', city: 'Los Angeles' },
          },
        },
      });
    });

    await page.route('**/api/v1/payments/create-intent', async (route) => {
      await route.fulfill({
        json: {
          payment_intent_id: 'pi_test_123',
          client_secret: 'pi_test_123_secret',
        },
      });
    });

    await page.route('**/api/v1/payments/confirm', async (route) => {
      await route.fulfill({
        json: {
          id: '1',
          status: 'completed',
          booking_id: '1',
        },
      });
    });

    await page.goto('/');
  });

  test('should complete full booking flow from registration to payment', async ({ page }) => {
    // Step 1: User Registration
    await page.click('text=Sign Up');
    await page.fill('[data-testid=first-name-input]', 'John');
    await page.fill('[data-testid=last-name-input]', 'Doe');
    await page.fill('[data-testid=email-input]', 'test@example.com');
    await page.fill('[data-testid=password-input]', 'password123');
    await page.fill('[data-testid=confirm-password-input]', 'password123');
    await page.click('[data-testid=register-button]');

    // Verify registration success
    await expect(page.locator('[data-testid=success-message]')).toContainText('Registration successful');

    // Step 2: User Login
    await page.fill('[data-testid=email-input]', 'test@example.com');
    await page.fill('[data-testid=password-input]', 'password123');
    await page.click('[data-testid=login-button]');

    // Verify login success and navigation to dashboard
    await expect(page).toHaveURL('/dashboard');
    await expect(page.locator('[data-testid=welcome-message]')).toContainText('Welcome, John!');

    // Step 3: Trip Search
    await page.click('[data-testid=book-trip-button]');
    
    // Fill search form
    await page.selectOption('[data-testid=origin-select]', '1');
    await page.selectOption('[data-testid=destination-select]', '2');
    await page.fill('[data-testid=departure-date-input]', '2024-12-25');
    await page.selectOption('[data-testid=passengers-select]', '2');
    
    await page.click('[data-testid=search-button]');

    // Verify search results
    await expect(page.locator('[data-testid=trip-results]')).toBeVisible();
    await expect(page.locator('[data-testid=trip-card]')).toHaveCount(1);
    await expect(page.locator('text=Central Terminal')).toBeVisible();
    await expect(page.locator('text=Airport Terminal')).toBeVisible();
    await expect(page.locator('text=$50.00')).toBeVisible();

    // Step 4: Trip Selection and Seat Selection
    await page.click('[data-testid=select-trip-button]');

    // Verify seat map is displayed
    await expect(page.locator('[data-testid=seat-map]')).toBeVisible();
    await expect(page.locator('text=Select Your Seats')).toBeVisible();

    // Select seats
    await page.click('[data-testid=seat-1]');
    await page.click('[data-testid=seat-2]');

    // Verify seat selection
    await expect(page.locator('[data-testid=selected-seats]')).toContainText('Seats: 1, 2');
    await expect(page.locator('[data-testid=total-amount]')).toContainText('Total: $100.00');

    await page.click('[data-testid=continue-to-payment-button]');

    // Step 5: Booking Summary
    await expect(page.locator('[data-testid=booking-summary]')).toBeVisible();
    await expect(page.locator('text=Central Terminal → Airport Terminal')).toBeVisible();
    await expect(page.locator('text=Seats: 1, 2')).toBeVisible();
    await expect(page.locator('text=Total: $100.00')).toBeVisible();

    await page.click('[data-testid=proceed-to-payment-button]');

    // Step 6: Payment
    await expect(page.locator('[data-testid=payment-form]')).toBeVisible();

    // Fill payment details
    await page.fill('[data-testid=card-number-input]', '4242424242424242');
    await page.fill('[data-testid=expiry-input]', '12/25');
    await page.fill('[data-testid=cvc-input]', '123');
    await page.fill('[data-testid=cardholder-name-input]', 'John Doe');

    await page.click('[data-testid=pay-button]');

    // Step 7: Booking Confirmation
    await expect(page.locator('[data-testid=booking-success]')).toBeVisible();
    await expect(page.locator('text=Booking Confirmed!')).toBeVisible();
    await expect(page.locator('text=BK123456')).toBeVisible();
    await expect(page.locator('[data-testid=download-receipt-button]')).toBeVisible();
    await expect(page.locator('[data-testid=view-booking-details-button]')).toBeVisible();

    // Verify booking appears in user's booking history
    await page.click('[data-testid=view-bookings-button]');
    await expect(page.locator('[data-testid=booking-history]')).toBeVisible();
    await expect(page.locator('text=BK123456')).toBeVisible();
    await expect(page.locator('text=Confirmed')).toBeVisible();
  });

  test('should handle booking cancellation flow', async ({ page }) => {
    // Mock existing booking
    await page.route('**/api/v1/bookings/my-bookings', async (route) => {
      await route.fulfill({
        json: [
          {
            id: '1',
            booking_reference: 'BK123456',
            status: 'confirmed',
            payment_status: 'completed',
            seat_numbers: [1, 2],
            total_amount: 100,
            created_at: '2024-12-20T10:00:00Z',
            trip: {
              id: '1',
              departure_time: '2024-12-25T10:00:00Z',
              origin_terminal: { name: 'Central Terminal', city: 'New York' },
              destination_terminal: { name: 'Airport Terminal', city: 'Los Angeles' },
            },
          },
        ],
      });
    });

    await page.route('**/api/v1/bookings/1/cancel', async (route) => {
      await route.fulfill({
        json: {
          id: '1',
          status: 'cancelled',
          refund_amount: 80, // 20% cancellation fee
        },
      });
    });

    // Login first
    await page.click('text=Sign In');
    await page.fill('[data-testid=email-input]', 'test@example.com');
    await page.fill('[data-testid=password-input]', 'password123');
    await page.click('[data-testid=login-button]');

    // Navigate to bookings
    await page.click('[data-testid=my-bookings-button]');

    // Verify booking is displayed
    await expect(page.locator('[data-testid=booking-card]')).toBeVisible();
    await expect(page.locator('text=BK123456')).toBeVisible();
    await expect(page.locator('text=Confirmed')).toBeVisible();

    // Cancel booking
    await page.click('[data-testid=cancel-booking-button]');

    // Confirm cancellation in modal
    await expect(page.locator('[data-testid=cancellation-modal]')).toBeVisible();
    await expect(page.locator('text=Cancellation Fee: $20.00')).toBeVisible();
    await expect(page.locator('text=Refund Amount: $80.00')).toBeVisible();

    await page.click('[data-testid=confirm-cancellation-button]');

    // Verify cancellation success
    await expect(page.locator('[data-testid=cancellation-success]')).toBeVisible();
    await expect(page.locator('text=Booking cancelled successfully')).toBeVisible();
    await expect(page.locator('text=Cancelled')).toBeVisible();
  });

  test('should handle payment failure and retry', async ({ page }) => {
    // Mock payment failure
    await page.route('**/api/v1/payments/confirm', async (route) => {
      const requestCount = route.request().headers()['x-request-count'] || '0';
      
      if (parseInt(requestCount) === 0) {
        // First attempt fails
        await route.fulfill({
          status: 400,
          json: {
            error: 'card_declined',
            message: 'Your card was declined',
          },
        });
      } else {
        // Second attempt succeeds
        await route.fulfill({
          json: {
            id: '1',
            status: 'completed',
            booking_id: '1',
          },
        });
      }
    });

    // Complete booking flow up to payment
    await page.click('text=Sign In');
    await page.fill('[data-testid=email-input]', 'test@example.com');
    await page.fill('[data-testid=password-input]', 'password123');
    await page.click('[data-testid=login-button]');

    await page.click('[data-testid=book-trip-button]');
    await page.selectOption('[data-testid=origin-select]', '1');
    await page.selectOption('[data-testid=destination-select]', '2');
    await page.fill('[data-testid=departure-date-input]', '2024-12-25');
    await page.click('[data-testid=search-button]');
    await page.click('[data-testid=select-trip-button]');
    await page.click('[data-testid=seat-1]');
    await page.click('[data-testid=continue-to-payment-button]');
    await page.click('[data-testid=proceed-to-payment-button]');

    // Fill payment details
    await page.fill('[data-testid=card-number-input]', '4000000000000002'); // Declined card
    await page.fill('[data-testid=expiry-input]', '12/25');
    await page.fill('[data-testid=cvc-input]', '123');
    await page.fill('[data-testid=cardholder-name-input]', 'John Doe');

    // First payment attempt
    await page.click('[data-testid=pay-button]');

    // Verify payment failure
    await expect(page.locator('[data-testid=payment-error]')).toBeVisible();
    await expect(page.locator('text=Your card was declined')).toBeVisible();
    await expect(page.locator('[data-testid=retry-payment-button]')).toBeVisible();

    // Update card details and retry
    await page.fill('[data-testid=card-number-input]', '4242424242424242'); // Valid card
    
    // Add request count header for retry
    await page.route('**/api/v1/payments/confirm', async (route) => {
      const request = route.request();
      const headers = { ...request.headers(), 'x-request-count': '1' };
      await route.continue({ headers });
    });

    await page.click('[data-testid=retry-payment-button]');

    // Verify payment success
    await expect(page.locator('[data-testid=booking-success]')).toBeVisible();
    await expect(page.locator('text=Booking Confirmed!')).toBeVisible();
  });

  test('should handle network errors gracefully', async ({ page }) => {
    // Simulate network failure
    await page.route('**/api/v1/bookings/trips/search', async (route) => {
      await route.abort('failed');
    });

    // Login and attempt search
    await page.click('text=Sign In');
    await page.fill('[data-testid=email-input]', 'test@example.com');
    await page.fill('[data-testid=password-input]', 'password123');
    await page.click('[data-testid=login-button]');

    await page.click('[data-testid=book-trip-button]');
    await page.selectOption('[data-testid=origin-select]', '1');
    await page.selectOption('[data-testid=destination-select]', '2');
    await page.fill('[data-testid=departure-date-input]', '2024-12-25');
    await page.click('[data-testid=search-button]');

    // Verify error handling
    await expect(page.locator('[data-testid=network-error]')).toBeVisible();
    await expect(page.locator('text=Network error occurred')).toBeVisible();
    await expect(page.locator('[data-testid=retry-button]')).toBeVisible();

    // Mock successful retry
    await page.route('**/api/v1/bookings/trips/search', async (route) => {
      await route.fulfill({
        json: [
          {
            id: '1',
            departure_time: '2024-12-25T10:00:00Z',
            arrival_time: '2024-12-25T14:00:00Z',
            fare: 50,
            available_seats: 15,
            origin_terminal: { name: 'Central Terminal', city: 'New York' },
            destination_terminal: { name: 'Airport Terminal', city: 'Los Angeles' },
            bus: { model: 'Mercedes Sprinter', license_plate: 'ABC-123' },
          },
        ],
      });
    });

    await page.click('[data-testid=retry-button]');

    // Verify successful retry
    await expect(page.locator('[data-testid=trip-results]')).toBeVisible();
    await expect(page.locator('[data-testid=trip-card]')).toHaveCount(1);
  });

  test('should maintain booking state across page refreshes', async ({ page }) => {
    // Complete booking flow up to seat selection
    await page.click('text=Sign In');
    await page.fill('[data-testid=email-input]', 'test@example.com');
    await page.fill('[data-testid=password-input]', 'password123');
    await page.click('[data-testid=login-button]');

    await page.click('[data-testid=book-trip-button]');
    await page.selectOption('[data-testid=origin-select]', '1');
    await page.selectOption('[data-testid=destination-select]', '2');
    await page.fill('[data-testid=departure-date-input]', '2024-12-25');
    await page.click('[data-testid=search-button]');
    await page.click('[data-testid=select-trip-button]');
    await page.click('[data-testid=seat-1]');

    // Verify state before refresh
    await expect(page.locator('[data-testid=selected-seats]')).toContainText('Seats: 1');

    // Refresh page
    await page.reload();

    // Verify state is maintained
    await expect(page.locator('[data-testid=seat-map]')).toBeVisible();
    await expect(page.locator('[data-testid=selected-seats]')).toContainText('Seats: 1');
    await expect(page.locator('[data-testid=seat-1]')).toHaveClass(/selected/);
  });

  test('should handle concurrent booking attempts', async ({ page, context }) => {
    // Create second page for concurrent user
    const page2 = await context.newPage();

    // Mock limited seats
    let availableSeats = 1;
    await page.route('**/api/v1/bookings/trips/search', async (route) => {
      await route.fulfill({
        json: [
          {
            id: '1',
            departure_time: '2024-12-25T10:00:00Z',
            arrival_time: '2024-12-25T14:00:00Z',
            fare: 50,
            available_seats: availableSeats,
            origin_terminal: { name: 'Central Terminal', city: 'New York' },
            destination_terminal: { name: 'Airport Terminal', city: 'Los Angeles' },
            bus: { model: 'Mercedes Sprinter', license_plate: 'ABC-123' },
          },
        ],
      });
    });

    await page2.route('**/api/v1/bookings/trips/search', async (route) => {
      await route.fulfill({
        json: [
          {
            id: '1',
            departure_time: '2024-12-25T10:00:00Z',
            arrival_time: '2024-12-25T14:00:00Z',
            fare: 50,
            available_seats: availableSeats,
            origin_terminal: { name: 'Central Terminal', city: 'New York' },
            destination_terminal: { name: 'Airport Terminal', city: 'Los Angeles' },
            bus: { model: 'Mercedes Sprinter', license_plate: 'ABC-123' },
          },
        ],
      });
    });

    // Mock booking success for first user
    await page.route('**/api/v1/bookings', async (route) => {
      if (availableSeats > 0) {
        availableSeats--;
        await route.fulfill({
          json: {
            id: '1',
            booking_reference: 'BK123456',
            status: 'confirmed',
            seat_numbers: [1],
            total_amount: 50,
          },
        });
      } else {
        await route.fulfill({
          status: 409,
          json: {
            error: 'seats_unavailable',
            message: 'Selected seats are no longer available',
          },
        });
      }
    });

    // Mock booking failure for second user
    await page2.route('**/api/v1/bookings', async (route) => {
      await route.fulfill({
        status: 409,
        json: {
          error: 'seats_unavailable',
          message: 'Selected seats are no longer available',
        },
      });
    });

    // Both users login and search for same trip
    await Promise.all([
      (async () => {
        await page.goto('/');
        await page.click('text=Sign In');
        await page.fill('[data-testid=email-input]', 'user1@example.com');
        await page.fill('[data-testid=password-input]', 'password123');
        await page.click('[data-testid=login-button]');
        await page.click('[data-testid=book-trip-button]');
        await page.selectOption('[data-testid=origin-select]', '1');
        await page.selectOption('[data-testid=destination-select]', '2');
        await page.fill('[data-testid=departure-date-input]', '2024-12-25');
        await page.click('[data-testid=search-button]');
        await page.click('[data-testid=select-trip-button]');
        await page.click('[data-testid=seat-1]');
        await page.click('[data-testid=continue-to-payment-button]');
        await page.click('[data-testid=proceed-to-payment-button]');
        await page.fill('[data-testid=card-number-input]', '4242424242424242');
        await page.fill('[data-testid=expiry-input]', '12/25');
        await page.fill('[data-testid=cvc-input]', '123');
        await page.click('[data-testid=pay-button]');
      })(),
      (async () => {
        await page2.goto('/');
        await page2.click('text=Sign In');
        await page2.fill('[data-testid=email-input]', 'user2@example.com');
        await page2.fill('[data-testid=password-input]', 'password123');
        await page2.click('[data-testid=login-button]');
        await page2.click('[data-testid=book-trip-button]');
        await page2.selectOption('[data-testid=origin-select]', '1');
        await page2.selectOption('[data-testid=destination-select]', '2');
        await page2.fill('[data-testid=departure-date-input]', '2024-12-25');
        await page2.click('[data-testid=search-button]');
        await page2.click('[data-testid=select-trip-button]');
        await page2.click('[data-testid=seat-1]');
        await page2.click('[data-testid=continue-to-payment-button]');
        await page2.click('[data-testid=proceed-to-payment-button]');
        await page2.fill('[data-testid=card-number-input]', '4242424242424242');
        await page2.fill('[data-testid=expiry-input]', '12/25');
        await page2.fill('[data-testid=cvc-input]', '123');
        await page2.click('[data-testid=pay-button]');
      })(),
    ]);

    // Verify first user succeeds
    await expect(page.locator('[data-testid=booking-success]')).toBeVisible();
    await expect(page.locator('text=Booking Confirmed!')).toBeVisible();

    // Verify second user gets appropriate error
    await expect(page2.locator('[data-testid=booking-error]')).toBeVisible();
    await expect(page2.locator('text=Selected seats are no longer available')).toBeVisible();
    await expect(page2.locator('[data-testid=search-again-button]')).toBeVisible();

    await page2.close();
  });

  test('should support accessibility features throughout booking flow', async ({ page }) => {
    // Enable screen reader simulation
    await page.addInitScript(() => {
      window.speechSynthesis = {
        speak: (utterance) => {
          window.lastSpokenText = utterance.text;
        },
        cancel: () => {},
        getVoices: () => [],
      };
    });

    // Complete booking flow with keyboard navigation
    await page.keyboard.press('Tab'); // Navigate to Sign In
    await page.keyboard.press('Enter');
    
    await page.keyboard.press('Tab'); // Navigate to email field
    await page.keyboard.type('test@example.com');
    await page.keyboard.press('Tab'); // Navigate to password field
    await page.keyboard.type('password123');
    await page.keyboard.press('Tab'); // Navigate to login button
    await page.keyboard.press('Enter');

    // Verify ARIA announcements
    const lastSpoken = await page.evaluate(() => window.lastSpokenText);
    expect(lastSpoken).toContain('Login successful');

    // Continue with keyboard navigation for booking
    await page.keyboard.press('Tab'); // Navigate to book trip button
    await page.keyboard.press('Enter');

    // Verify form has proper ARIA labels
    await expect(page.locator('[aria-label="Origin terminal"]')).toBeVisible();
    await expect(page.locator('[aria-label="Destination terminal"]')).toBeVisible();
    await expect(page.locator('[aria-label="Departure date"]')).toBeVisible();

    // Test high contrast mode
    await page.emulateMedia({ colorScheme: 'dark' });
    await expect(page.locator('[data-testid=search-form]')).toBeVisible();

    // Test screen reader compatibility
    const searchButton = page.locator('[data-testid=search-button]');
    await expect(searchButton).toHaveAttribute('aria-label', 'Search for available trips');
  });
});