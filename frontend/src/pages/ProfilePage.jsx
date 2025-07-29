import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import UserProfileForm from '../components/profile/UserProfileForm';
import BookingHistory from '../components/profile/BookingHistory';
import PaymentMethods from '../components/profile/PaymentMethods';
import NotificationSettings from '../components/profile/NotificationSettings';
import ReviewHistory from '../components/profile/ReviewHistory';

const ProfilePage = () => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('profile');
  const [loading, setLoading] = useState(false);

  const tabs = [
    { id: 'profile', label: 'Profile', icon: '👤' },
    { id: 'bookings', label: 'My Bookings', icon: '🎫' },
    { id: 'payments', label: 'Payment Methods', icon: '💳' },
    { id: 'reviews', label: 'My Reviews', icon: '⭐' },
    { id: 'notifications', label: 'Notifications', icon: '🔔' },
  ];

  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Please log in</h2>
          <p className="text-gray-600">You need to be logged in to view your profile.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
          <div className="flex items-center space-x-4">
            <div className="w-16 h-16 bg-blue-500 rounded-full flex items-center justify-center text-white text-2xl font-bold">
              {user.first_name?.[0]}{user.last_name?.[0]}
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                {user.first_name} {user.last_name}
              </h1>
              <p className="text-gray-600">{user.email}</p>
              {user.phone && <p className="text-gray-600">{user.phone}</p>}
            </div>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="bg-white rounded-lg shadow-sm mb-6">
          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-8 px-6">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`py-4 px-1 border-b-2 font-medium text-sm flex items-center space-x-2 ${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <span>{tab.icon}</span>
                  <span>{tab.label}</span>
                </button>
              ))}
            </nav>
          </div>
        </div>

        {/* Tab Content */}
        <div className="bg-white rounded-lg shadow-sm">
          {activeTab === 'profile' && <UserProfileForm />}
          {activeTab === 'bookings' && <BookingHistory />}
          {activeTab === 'payments' && <PaymentMethods />}
          {activeTab === 'reviews' && <ReviewHistory />}
          {activeTab === 'notifications' && <NotificationSettings />}
        </div>
      </div>
    </div>
  );
};

export default ProfilePage;