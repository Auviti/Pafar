import React, { useState, useEffect } from 'react';
import { paymentService } from '../../services/payment';

const PaymentMethods = () => {
  const [paymentMethods, setPaymentMethods] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showAddForm, setShowAddForm] = useState(false);
  const [deletingId, setDeletingId] = useState(null);

  useEffect(() => {
    fetchPaymentMethods();
  }, []);

  const fetchPaymentMethods = async () => {
    try {
      setLoading(true);
      const data = await paymentService.getSavedPaymentMethods();
      setPaymentMethods(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDeletePaymentMethod = async (methodId) => {
    if (!window.confirm('Are you sure you want to delete this payment method?')) {
      return;
    }

    try {
      setDeletingId(methodId);
      await paymentService.deletePaymentMethod(methodId);
      setPaymentMethods(prev => prev.filter(method => method.id !== methodId));
    } catch (err) {
      setError(err.message);
    } finally {
      setDeletingId(null);
    }
  };

  const getCardIcon = (brand) => {
    switch (brand?.toLowerCase()) {
      case 'visa':
        return '💳';
      case 'mastercard':
        return '💳';
      case 'amex':
        return '💳';
      case 'discover':
        return '💳';
      default:
        return '💳';
    }
  };

  const formatCardNumber = (last4) => {
    return `•••• •••• •••• ${last4}`;
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
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Payment Methods</h2>
        <button
          onClick={() => setShowAddForm(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          Add Payment Method
        </button>
      </div>

      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-md">
          <p className="text-red-700">{error}</p>
        </div>
      )}

      {paymentMethods.length === 0 ? (
        <div className="text-center py-12">
          <div className="text-gray-500 text-lg mb-4">No payment methods saved</div>
          <p className="text-gray-400 mb-6">
            Add a payment method to make booking faster and more convenient.
          </p>
          <button
            onClick={() => setShowAddForm(true)}
            className="px-6 py-3 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            Add Your First Payment Method
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {paymentMethods.map((method) => (
            <div key={method.id} className="bg-white border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow">
              <div className="flex justify-between items-start mb-4">
                <div className="flex items-center space-x-3">
                  <span className="text-2xl">{getCardIcon(method.brand)}</span>
                  <div>
                    <p className="font-medium text-gray-900">
                      {method.brand?.toUpperCase()} {formatCardNumber(method.last4)}
                    </p>
                    <p className="text-sm text-gray-600">
                      Expires {method.exp_month}/{method.exp_year}
                    </p>
                  </div>
                </div>
                {method.is_default && (
                  <span className="px-2 py-1 bg-green-100 text-green-800 text-xs font-medium rounded-full">
                    Default
                  </span>
                )}
              </div>

              <div className="mb-4">
                <p className="text-sm text-gray-600">
                  <strong>Cardholder:</strong> {method.cardholder_name || 'N/A'}
                </p>
                <p className="text-sm text-gray-600">
                  <strong>Added:</strong> {new Date(method.created_at).toLocaleDateString()}
                </p>
              </div>

              <div className="flex justify-between items-center">
                <div className="flex space-x-2">
                  {!method.is_default && (
                    <button
                      onClick={() => handleSetDefault(method.id)}
                      className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200 transition-colors"
                    >
                      Set as Default
                    </button>
                  )}
                </div>
                <button
                  onClick={() => handleDeletePaymentMethod(method.id)}
                  disabled={deletingId === method.id}
                  className="px-3 py-1 text-sm bg-red-100 text-red-700 rounded hover:bg-red-200 transition-colors disabled:opacity-50"
                >
                  {deletingId === method.id ? 'Deleting...' : 'Delete'}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Add Payment Method Modal */}
      {showAddForm && (
        <AddPaymentMethodModal
          onClose={() => setShowAddForm(false)}
          onSuccess={() => {
            setShowAddForm(false);
            fetchPaymentMethods();
          }}
        />
      )}
    </div>
  );
};

// Add Payment Method Modal Component
const AddPaymentMethodModal = ({ onClose, onSuccess }) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [formData, setFormData] = useState({
    cardNumber: '',
    expiryMonth: '',
    expiryYear: '',
    cvc: '',
    cardholderName: '',
    setAsDefault: false
  });

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      // In a real implementation, you would use Stripe Elements or similar
      // to securely tokenize the card details before sending to your backend
      const paymentMethodData = {
        card_number: formData.cardNumber.replace(/\s/g, ''),
        exp_month: parseInt(formData.expiryMonth),
        exp_year: parseInt(formData.expiryYear),
        cvc: formData.cvc,
        cardholder_name: formData.cardholderName,
        set_as_default: formData.setAsDefault
      };

      await paymentService.savePaymentMethod(paymentMethodData);
      onSuccess();
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const formatCardNumber = (value) => {
    // Remove all non-digit characters
    const v = value.replace(/\s+/g, '').replace(/[^0-9]/gi, '');
    // Add spaces every 4 digits
    const matches = v.match(/\d{4,16}/g);
    const match = matches && matches[0] || '';
    const parts = [];
    for (let i = 0, len = match.length; i < len; i += 4) {
      parts.push(match.substring(i, i + 4));
    }
    if (parts.length) {
      return parts.join(' ');
    } else {
      return v;
    }
  };

  const handleCardNumberChange = (e) => {
    const formatted = formatCardNumber(e.target.value);
    setFormData(prev => ({ ...prev, cardNumber: formatted }));
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Add Payment Method</h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-md">
            <p className="text-red-700 text-sm">{error}</p>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Card Number *
            </label>
            <input
              type="text"
              name="cardNumber"
              value={formData.cardNumber}
              onChange={handleCardNumberChange}
              placeholder="1234 5678 9012 3456"
              maxLength={19}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Month *
              </label>
              <select
                name="expiryMonth"
                value={formData.expiryMonth}
                onChange={handleInputChange}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">MM</option>
                {Array.from({ length: 12 }, (_, i) => i + 1).map(month => (
                  <option key={month} value={month.toString().padStart(2, '0')}>
                    {month.toString().padStart(2, '0')}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Year *
              </label>
              <select
                name="expiryYear"
                value={formData.expiryYear}
                onChange={handleInputChange}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">YYYY</option>
                {Array.from({ length: 10 }, (_, i) => new Date().getFullYear() + i).map(year => (
                  <option key={year} value={year}>
                    {year}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                CVC *
              </label>
              <input
                type="text"
                name="cvc"
                value={formData.cvc}
                onChange={handleInputChange}
                placeholder="123"
                maxLength={4}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Cardholder Name *
            </label>
            <input
              type="text"
              name="cardholderName"
              value={formData.cardholderName}
              onChange={handleInputChange}
              placeholder="John Doe"
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div className="flex items-center">
            <input
              type="checkbox"
              id="setAsDefault"
              name="setAsDefault"
              checked={formData.setAsDefault}
              onChange={handleInputChange}
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
            <label htmlFor="setAsDefault" className="ml-2 block text-sm text-gray-700">
              Set as default payment method
            </label>
          </div>

          <div className="flex space-x-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
            >
              {loading ? 'Adding...' : 'Add Payment Method'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default PaymentMethods;