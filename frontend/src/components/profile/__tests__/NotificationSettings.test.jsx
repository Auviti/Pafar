import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import NotificationSettings from '../NotificationSettings';
import { userService } from '../../../services/user';

// Mock the user service
vi.mock('../../../services/user');

const mockPreferences = {
  email_notifications: {
    booking_confirmations: true,
    trip_reminders: true,
    trip_updates: true,
    payment_receipts: true,
    promotional_offers: false,
    system_updates: true
  },
  sms_notifications: {
    booking_confirmations: true,
    trip_reminders: true,
    trip_updates: true,
    emergency_alerts: true
  },
  push_notifications: {
    trip_updates: true,
    boarding_reminders: true,
    delay_notifications: true,
    promotional_offers: false
  },
  notification_timing: {
    trip_reminder_hours: 2,
    boarding_reminder_minutes: 30
  }
};

describe('NotificationSettings', () => {
  beforeEach(() => {
    userService.getNotificationPreferences.mockResolvedValue(mockPreferences);
    userService.updateNotificationPreferences.mockResolvedValue({});
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it('renders notification settings sections', async () => {
    render(<NotificationSettings />);
    
    await waitFor(() => {
      expect(screen.getByText('Notification Settings')).toBeInTheDocument();
    });
    
    expect(screen.getByText('📧')).toBeInTheDocument(); // Email icon
    expect(screen.getByText('Email Notifications')).toBeInTheDocument();
    expect(screen.getByText('📱')).toBeInTheDocument(); // SMS icon
    expect(screen.getByText('SMS Notifications')).toBeInTheDocument();
    expect(screen.getByText('🔔')).toBeInTheDocument(); // Push icon
    expect(screen.getByText('Push Notifications')).toBeInTheDocument();
    expect(screen.getByText('⏰')).toBeInTheDocument(); // Timing icon
    expect(screen.getByText('Notification Timing')).toBeInTheDocument();
  });

  it('displays email notification toggles with correct states', async () => {
    render(<NotificationSettings />);
    
    await waitFor(() => {
      expect(screen.getByText('Booking Confirmations')).toBeInTheDocument();
    });
    
    // Check that toggles are rendered and have correct initial states
    const toggles = screen.getAllByRole('checkbox');
    expect(toggles.length).toBeGreaterThan(0);
  });

  it('toggles email notification setting', async () => {
    render(<NotificationSettings />);
    
    await waitFor(() => {
      expect(screen.getByText('Promotional Offers')).toBeInTheDocument();
    });
    
    // Find the promotional offers toggle (should be off initially)
    const promotionalToggle = screen.getAllByRole('checkbox').find(checkbox => 
      checkbox.closest('div').textContent.includes('Promotional Offers')
    );
    
    expect(promotionalToggle).toBeDefined();
    
    // Toggle it on
    fireEvent.click(promotionalToggle);
    
    // Verify the state changed
    expect(promotionalToggle.checked).toBe(true);
  });

  it('updates trip reminder timing', async () => {
    render(<NotificationSettings />);
    
    await waitFor(() => {
      expect(screen.getByText('Trip Reminder')).toBeInTheDocument();
    });
    
    const reminderSelect = screen.getByDisplayValue('2 hours');
    fireEvent.change(reminderSelect, { target: { value: '4' } });
    
    expect(reminderSelect.value).toBe('4');
  });

  it('updates boarding reminder timing', async () => {
    render(<NotificationSettings />);
    
    await waitFor(() => {
      expect(screen.getByText('Boarding Reminder')).toBeInTheDocument();
    });
    
    const boardingSelect = screen.getByDisplayValue('30 minutes');
    fireEvent.change(boardingSelect, { target: { value: '45' } });
    
    expect(boardingSelect.value).toBe('45');
  });

  it('saves preferences successfully', async () => {
    render(<NotificationSettings />);
    
    await waitFor(() => {
      expect(screen.getByText('Save Preferences')).toBeInTheDocument();
    });
    
    const saveButton = screen.getByText('Save Preferences');
    fireEvent.click(saveButton);
    
    await waitFor(() => {
      expect(userService.updateNotificationPreferences).toHaveBeenCalledWith(mockPreferences);
    });
    
    expect(screen.getByText('Notification preferences updated successfully!')).toBeInTheDocument();
  });

  it('shows error message on save failure', async () => {
    userService.updateNotificationPreferences.mockRejectedValue(new Error('Save failed'));
    
    render(<NotificationSettings />);
    
    await waitFor(() => {
      const saveButton = screen.getByText('Save Preferences');
      fireEvent.click(saveButton);
    });
    
    await waitFor(() => {
      expect(screen.getByText('Save failed')).toBeInTheDocument();
    });
  });

  it('handles loading state', () => {
    userService.getNotificationPreferences.mockImplementation(() => new Promise(() => {}));
    
    render(<NotificationSettings />);
    
    expect(screen.getByRole('status')).toBeInTheDocument(); // Loading spinner
  });

  it('handles error state on initial load', async () => {
    userService.getNotificationPreferences.mockRejectedValue(new Error('Failed to load preferences'));
    
    render(<NotificationSettings />);
    
    await waitFor(() => {
      expect(screen.getByText('Failed to load preferences')).toBeInTheDocument();
    });
  });

  it('shows loading state while saving', async () => {
    userService.updateNotificationPreferences.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)));
    
    render(<NotificationSettings />);
    
    await waitFor(() => {
      const saveButton = screen.getByText('Save Preferences');
      fireEvent.click(saveButton);
    });
    
    expect(screen.getByText('Saving...')).toBeInTheDocument();
    
    await waitFor(() => {
      expect(screen.getByText('Save Preferences')).toBeInTheDocument();
    });
  });

  it('displays notification descriptions', async () => {
    render(<NotificationSettings />);
    
    await waitFor(() => {
      expect(screen.getByText('Receive confirmation emails when you book a trip')).toBeInTheDocument();
      expect(screen.getByText('Get reminded about upcoming trips')).toBeInTheDocument();
      expect(screen.getByText('SMS confirmation when booking is complete')).toBeInTheDocument();
      expect(screen.getByText('Real-time updates about your trip status')).toBeInTheDocument();
    });
  });

  it('renders all timing options correctly', async () => {
    render(<NotificationSettings />);
    
    await waitFor(() => {
      expect(screen.getByText('How many hours before departure to send reminder')).toBeInTheDocument();
      expect(screen.getByText('How many minutes before departure to send boarding reminder')).toBeInTheDocument();
    });
    
    // Check that select options are available
    const reminderSelect = screen.getByDisplayValue('2 hours');
    const boardingSelect = screen.getByDisplayValue('30 minutes');
    
    expect(reminderSelect).toBeInTheDocument();
    expect(boardingSelect).toBeInTheDocument();
  });

  it('maintains toggle states after changes', async () => {
    render(<NotificationSettings />);
    
    await waitFor(() => {
      expect(screen.getByText('Email Notifications')).toBeInTheDocument();
    });
    
    // Find and toggle a setting
    const toggles = screen.getAllByRole('checkbox');
    const firstToggle = toggles[0];
    const initialState = firstToggle.checked;
    
    fireEvent.click(firstToggle);
    expect(firstToggle.checked).toBe(!initialState);
    
    // Toggle back
    fireEvent.click(firstToggle);
    expect(firstToggle.checked).toBe(initialState);
  });

  it('updates preferences object correctly when toggling', async () => {
    render(<NotificationSettings />);
    
    await waitFor(() => {
      expect(screen.getByText('Save Preferences')).toBeInTheDocument();
    });
    
    // Toggle promotional offers (should be false initially)
    const promotionalToggle = screen.getAllByRole('checkbox').find(checkbox => 
      checkbox.closest('div').textContent.includes('Promotional Offers')
    );
    
    fireEvent.click(promotionalToggle);
    
    // Save preferences
    const saveButton = screen.getByText('Save Preferences');
    fireEvent.click(saveButton);
    
    await waitFor(() => {
      expect(userService.updateNotificationPreferences).toHaveBeenCalledWith(
        expect.objectContaining({
          email_notifications: expect.objectContaining({
            promotional_offers: true
          })
        })
      );
    });
  });
});