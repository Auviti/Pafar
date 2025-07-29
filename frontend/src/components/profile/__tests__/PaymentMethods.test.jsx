import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import PaymentMethods from '../PaymentMethods';
import { paymentService } from '../../../services/payment';

// Mock the payment service
vi.mock('../../../services/payment');

const mockPaymentMethods = [
  {
    id: '1',
    brand: 'visa',
    last4: '4242',
    exp_month: 12,
    exp_year: 2025,
    cardholder_name: 'John Doe',
    is_default: true,
    created_at: '2024-01-15T10:00:00Z'
  },
  {
    id: '2',
    brand: 'mastercard',
    last4: '5555',
    exp_month: 6,
    exp_year: 2026,
    cardholder_name: 'John Doe',
    is_default: false,
    created_at: '2024-01-10T09:00:00Z'
  }
];

describe('PaymentMethods', () => {
  beforeEach(() => {
    paymentService.getSavedPaymentMethods.mockResolvedValue(mockPaymentMethods);
    paymentService.savePaymentMethod.mockResolvedValue({});
    paymentService.deletePaymentMethod = vi.fn().mockResolvedValue({});
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it('renders payment methods list', async () => {
    render(<PaymentMethods />);
    
    await waitFor(() => {
      expect(screen.getByText('Payment Methods')).toBeInTheDocument();
    });
    
    expect(screen.getByText('VISA •••• •••• •••• 4242')).toBeInTheDocument();
    expect(screen.getByText('MASTERCARD •••• •••• •••• 5555')).toBeInTheDocument();
    expect(screen.getByText('Expires 12/2025')).toBeInTheDocument();
    expect(screen.getByText('Expires 6/2026')).toBeInTheDocument();
  });

  it('shows default badge for default payment method', async () => {
    render(<PaymentMethods />);
    
    await waitFor(() => {
      expect(screen.getByText('Default')).toBeInTheDocument();
    });
  });

  it('shows add payment method button', async () => {
    render(<PaymentMethods />);
    
    await waitFor(() => {
      expect(screen.getByText('Add Payment Method')).toBeInTheDocument();
    });
  });

  it('opens add payment method modal', async () => {
    render(<PaymentMethods />);
    
    await waitFor(() => {
      const addButton = screen.getByText('Add Payment Method');
      fireEvent.click(addButton);
    });
    
    expect(screen.getByText('Add Payment Method')).toBeInTheDocument();
    expect(screen.getByLabelText('Card Number *')).toBeInTheDocument();
    expect(screen.getByLabelText('Month *')).toBeInTheDocument();
    expect(screen.getByLabelText('Year *')).toBeInTheDocument();
    expect(screen.getByLabelText('CVC *')).toBeInTheDocument();
    expect(screen.getByLabelText('Cardholder Name *')).toBeInTheDocument();
  });

  it('formats card number input correctly', async () => {
    render(<PaymentMethods />);
    
    await waitFor(() => {
      const addButton = screen.getByText('Add Payment Method');
      fireEvent.click(addButton);
    });
    
    const cardNumberInput = screen.getByLabelText('Card Number *');
    fireEvent.change(cardNumberInput, { target: { value: '4242424242424242' } });
    
    expect(cardNumberInput.value).toBe('4242 4242 4242 4242');
  });

  it('submits new payment method', async () => {
    render(<PaymentMethods />);
    
    await waitFor(() => {
      const addButton = screen.getByText('Add Payment Method');
      fireEvent.click(addButton);
    });
    
    // Fill form
    fireEvent.change(screen.getByLabelText('Card Number *'), {
      target: { value: '4242424242424242' }
    });
    fireEvent.change(screen.getByLabelText('Month *'), {
      target: { value: '12' }
    });
    fireEvent.change(screen.getByLabelText('Year *'), {
      target: { value: '2025' }
    });
    fireEvent.change(screen.getByLabelText('CVC *'), {
      target: { value: '123' }
    });
    fireEvent.change(screen.getByLabelText('Cardholder Name *'), {
      target: { value: 'John Doe' }
    });
    
    // Submit form
    const submitButton = screen.getByRole('button', { name: /Add Payment Method/ });
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(paymentService.savePaymentMethod).toHaveBeenCalledWith({
        card_number: '4242424242424242',
        exp_month: 12,
        exp_year: 2025,
        cvc: '123',
        cardholder_name: 'John Doe',
        set_as_default: false
      });
    });
  });

  it('deletes payment method with confirmation', async () => {
    // Mock window.confirm
    global.confirm = vi.fn(() => true);
    
    render(<PaymentMethods />);
    
    await waitFor(() => {
      const deleteButtons = screen.getAllByText('Delete');
      fireEvent.click(deleteButtons[0]);
    });
    
    expect(global.confirm).toHaveBeenCalledWith('Are you sure you want to delete this payment method?');
    
    await waitFor(() => {
      expect(paymentService.deletePaymentMethod).toHaveBeenCalledWith('1');
    });
  });

  it('does not delete payment method when confirmation is cancelled', async () => {
    // Mock window.confirm to return false
    global.confirm = vi.fn(() => false);
    
    render(<PaymentMethods />);
    
    await waitFor(() => {
      const deleteButtons = screen.getAllByText('Delete');
      fireEvent.click(deleteButtons[0]);
    });
    
    expect(global.confirm).toHaveBeenCalled();
    expect(paymentService.deletePaymentMethod).not.toHaveBeenCalled();
  });

  it('shows empty state when no payment methods', async () => {
    paymentService.getSavedPaymentMethods.mockResolvedValue([]);
    
    render(<PaymentMethods />);
    
    await waitFor(() => {
      expect(screen.getByText('No payment methods saved')).toBeInTheDocument();
      expect(screen.getByText('Add a payment method to make booking faster and more convenient.')).toBeInTheDocument();
      expect(screen.getByText('Add Your First Payment Method')).toBeInTheDocument();
    });
  });

  it('handles loading state', () => {
    paymentService.getSavedPaymentMethods.mockImplementation(() => new Promise(() => {}));
    
    render(<PaymentMethods />);
    
    expect(screen.getByRole('status')).toBeInTheDocument(); // Loading spinner
  });

  it('handles error state', async () => {
    paymentService.getSavedPaymentMethods.mockRejectedValue(new Error('Failed to fetch payment methods'));
    
    render(<PaymentMethods />);
    
    await waitFor(() => {
      expect(screen.getByText('Failed to fetch payment methods')).toBeInTheDocument();
    });
  });

  it('validates required fields in add form', async () => {
    render(<PaymentMethods />);
    
    await waitFor(() => {
      const addButton = screen.getByText('Add Payment Method');
      fireEvent.click(addButton);
    });
    
    // Try to submit without filling required fields
    const submitButton = screen.getByRole('button', { name: /Add Payment Method/ });
    fireEvent.click(submitButton);
    
    // Form should not submit due to HTML5 validation
    expect(paymentService.savePaymentMethod).not.toHaveBeenCalled();
  });

  it('closes modal when cancel is clicked', async () => {
    render(<PaymentMethods />);
    
    await waitFor(() => {
      const addButton = screen.getByText('Add Payment Method');
      fireEvent.click(addButton);
    });
    
    expect(screen.getByLabelText('Card Number *')).toBeInTheDocument();
    
    const cancelButton = screen.getByText('Cancel');
    fireEvent.click(cancelButton);
    
    expect(screen.queryByLabelText('Card Number *')).not.toBeInTheDocument();
  });

  it('closes modal when X button is clicked', async () => {
    render(<PaymentMethods />);
    
    await waitFor(() => {
      const addButton = screen.getByText('Add Payment Method');
      fireEvent.click(addButton);
    });
    
    expect(screen.getByLabelText('Card Number *')).toBeInTheDocument();
    
    const closeButton = screen.getByRole('button', { name: '' }); // X button
    fireEvent.click(closeButton);
    
    expect(screen.queryByLabelText('Card Number *')).not.toBeInTheDocument();
  });

  it('shows loading state while deleting', async () => {
    global.confirm = vi.fn(() => true);
    paymentService.deletePaymentMethod.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)));
    
    render(<PaymentMethods />);
    
    await waitFor(() => {
      const deleteButtons = screen.getAllByText('Delete');
      fireEvent.click(deleteButtons[0]);
    });
    
    expect(screen.getByText('Deleting...')).toBeInTheDocument();
    
    await waitFor(() => {
      expect(screen.queryByText('Deleting...')).not.toBeInTheDocument();
    });
  });

  it('displays cardholder names correctly', async () => {
    render(<PaymentMethods />);
    
    await waitFor(() => {
      expect(screen.getAllByText('John Doe')).toHaveLength(2);
    });
  });

  it('displays creation dates correctly', async () => {
    render(<PaymentMethods />);
    
    await waitFor(() => {
      expect(screen.getByText('1/15/2024')).toBeInTheDocument();
      expect(screen.getByText('1/10/2024')).toBeInTheDocument();
    });
  });
});