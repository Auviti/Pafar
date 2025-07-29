import React, { useState, useEffect } from 'react';
import { userService } from '../../services/user';

const NotificationSettings = () => {
  const [preferences, setPreferences] = useState({
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
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState({ type: '', text: '' });

  useEffect(() => {
    fetchPreferences();
  }, []);

  const fetchPreferences = async () => {
    try {
      setLoading(true);
      const data = await userService.getNotificationPreferences();
      setPreferences(data);
    } catch (error) {
      setMessage({ type: 'error', text: error.message });
    } finally {
      setLoading(false);
    }
  };

  const handleToggle = (category, setting) => {
    setPreferences(prev => ({
      ...prev,
      [category]: {
        ...prev[category],
        [setting]: !prev[category][setting]
      }
    }));
  };

  const handleTimingChange = (setting, value) => {
    setPreferences(prev => ({
      ...prev,
      notification_timing: {
        ...prev.notification_timing,
        [setting]: parseInt(value)
      }
    }));
  };

  const handleSave = async () => {
    setSaving(true);
    setMessage({ type: '', text: '' });

    try {
      await userService.updateNotificationPreferences(preferences);
      setMessage({ type: 'success', text: 'Notification preferences updated successfully!' });
    } catch (error) {
      setMessage({ type: 'error', text: error.message });
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600" role="status" aria-label="Loading"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <div className="max-w-3xl mx-auto">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Notification Settings</h2>

        {message.text && (
          <div className={`mb-6 p-4 rounded-md ${
            message.type === 'success' 
              ? 'bg-green-50 text-green-700 border border-green-200' 
              : 'bg-red-50 text-red-700 border border-red-200'
          }`}>
            {message.text}
          </div>
        )}

        <div className="space-y-8">
          {/* Email Notifications */}
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <div className="flex items-center mb-4">
              <span className="text-2xl mr-3">📧</span>
              <h3 className="text-lg font-semibold text-gray-900">Email Notifications</h3>
            </div>
            <div className="space-y-4">
              {Object.entries(preferences.email_notifications).map(([key, value]) => (
                <div key={key} className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-gray-900">
                      {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                    </p>
                    <p className="text-sm text-gray-600">
                      {getNotificationDescription('email', key)}
                    </p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={value}
                      onChange={() => handleToggle('email_notifications', key)}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                  </label>
                </div>
              ))}
            </div>
          </div>

          {/* SMS Notifications */}
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <div className="flex items-center mb-4">
              <span className="text-2xl mr-3">📱</span>
              <h3 className="text-lg font-semibold text-gray-900">SMS Notifications</h3>
            </div>
            <div className="space-y-4">
              {Object.entries(preferences.sms_notifications).map(([key, value]) => (
                <div key={key} className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-gray-900">
                      {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                    </p>
                    <p className="text-sm text-gray-600">
                      {getNotificationDescription('sms', key)}
                    </p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={value}
                      onChange={() => handleToggle('sms_notifications', key)}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                  </label>
                </div>
              ))}
            </div>
          </div>

          {/* Push Notifications */}
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <div className="flex items-center mb-4">
              <span className="text-2xl mr-3">🔔</span>
              <h3 className="text-lg font-semibold text-gray-900">Push Notifications</h3>
            </div>
            <div className="space-y-4">
              {Object.entries(preferences.push_notifications).map(([key, value]) => (
                <div key={key} className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-gray-900">
                      {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                    </p>
                    <p className="text-sm text-gray-600">
                      {getNotificationDescription('push', key)}
                    </p>
                  </div>
                  <label className="relative inline-flex items-center cursor-pointer">
                    <input
                      type="checkbox"
                      checked={value}
                      onChange={() => handleToggle('push_notifications', key)}
                      className="sr-only peer"
                    />
                    <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                  </label>
                </div>
              ))}
            </div>
          </div>

          {/* Notification Timing */}
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <div className="flex items-center mb-4">
              <span className="text-2xl mr-3">⏰</span>
              <h3 className="text-lg font-semibold text-gray-900">Notification Timing</h3>
            </div>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-gray-900">Trip Reminder</p>
                  <p className="text-sm text-gray-600">How many hours before departure to send reminder</p>
                </div>
                <select
                  value={preferences.notification_timing.trip_reminder_hours}
                  onChange={(e) => handleTimingChange('trip_reminder_hours', e.target.value)}
                  className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value={1}>1 hour</option>
                  <option value={2}>2 hours</option>
                  <option value={4}>4 hours</option>
                  <option value={6}>6 hours</option>
                  <option value={12}>12 hours</option>
                  <option value={24}>24 hours</option>
                </select>
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-gray-900">Boarding Reminder</p>
                  <p className="text-sm text-gray-600">How many minutes before departure to send boarding reminder</p>
                </div>
                <select
                  value={preferences.notification_timing.boarding_reminder_minutes}
                  onChange={(e) => handleTimingChange('boarding_reminder_minutes', e.target.value)}
                  className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value={15}>15 minutes</option>
                  <option value={30}>30 minutes</option>
                  <option value={45}>45 minutes</option>
                  <option value={60}>1 hour</option>
                </select>
              </div>
            </div>
          </div>
        </div>

        {/* Save Button */}
        <div className="mt-8 flex justify-end">
          <button
            onClick={handleSave}
            disabled={saving}
            className="px-6 py-3 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {saving ? 'Saving...' : 'Save Preferences'}
          </button>
        </div>
      </div>
    </div>
  );
};

// Helper function to get notification descriptions
const getNotificationDescription = (type, key) => {
  const descriptions = {
    email: {
      booking_confirmations: 'Receive confirmation emails when you book a trip',
      trip_reminders: 'Get reminded about upcoming trips',
      trip_updates: 'Receive updates about delays, cancellations, or changes',
      payment_receipts: 'Get email receipts for your payments',
      promotional_offers: 'Receive special offers and discounts',
      system_updates: 'Important system maintenance and update notifications'
    },
    sms: {
      booking_confirmations: 'SMS confirmation when booking is complete',
      trip_reminders: 'Text reminders about upcoming trips',
      trip_updates: 'SMS alerts for trip delays or changes',
      emergency_alerts: 'Critical safety and emergency notifications'
    },
    push: {
      trip_updates: 'Real-time updates about your trip status',
      boarding_reminders: 'Reminders when it\'s time to board',
      delay_notifications: 'Instant alerts about delays or changes',
      promotional_offers: 'Push notifications for special deals'
    }
  };

  return descriptions[type]?.[key] || 'Notification setting';
};

export default NotificationSettings;