import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi } from 'vitest';
import UserProfileForm from '../UserProfileForm';
import { useAuth } from '../../../contexts/AuthContext';
import { userService } from '../../../services/user';

// Mock the dependencies
vi.mock('../../../contexts/AuthContext');
vi.mock('../../../services/user');

const mockUser = {
  id: '1',
  first_name: 'John',
  last_name: 'Doe',
  email: 'john.doe@example.com',
  phone: '+1234567890',
  date_of_birth: '1990-01-01',
  address: '123 Main St',
  emergency_contact_name: 'Jane Doe',
  emergency_contact_phone: '+0987654321'
};

describe('UserProfileForm', () => {
  beforeEach(() => {
    useAuth.mockReturnValue({
      user: mockUser
    });
    userService.updateProfile.mockResolvedValue({});
    userService.changePassword.mockResolvedValue({});
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it('renders profile form with user data', () => {
    render(<UserProfileForm />);
    
    expect(screen.getByDisplayValue('John')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Doe')).toBeInTheDocument();
    expect(screen.getByDisplayValue('john.doe@example.com')).toBeInTheDocument();
    expect(screen.getByDisplayValue('+1234567890')).toBeInTheDocument();
    expect(screen.getByDisplayValue('1990-01-01')).toBeInTheDocument();
    expect(screen.getByDisplayValue('123 Main St')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Jane Doe')).toBeInTheDocument();
    expect(screen.getByDisplayValue('+0987654321')).toBeInTheDocument();
  });

  it('updates profile successfully', async () => {
    render(<UserProfileForm />);
    
    const firstNameInput = screen.getByDisplayValue('John');
    fireEvent.change(firstNameInput, { target: { value: 'Johnny' } });
    
    const updateButton = screen.getByText('Update Profile');
    fireEvent.click(updateButton);
    
    await waitFor(() => {
      expect(userService.updateProfile).toHaveBeenCalledWith(
        expect.objectContaining({
          first_name: 'Johnny'
        })
      );
    });
    
    expect(screen.getByText('Profile updated successfully!')).toBeInTheDocument();
  });

  it('shows error message on profile update failure', async () => {
    userService.updateProfile.mockRejectedValue(new Error('Update failed'));
    
    render(<UserProfileForm />);
    
    const updateButton = screen.getByText('Update Profile');
    fireEvent.click(updateButton);
    
    await waitFor(() => {
      expect(screen.getByText('Update failed')).toBeInTheDocument();
    });
  });

  it('shows password change form when button is clicked', () => {
    render(<UserProfileForm />);
    
    const changePasswordButton = screen.getByText('Change Password');
    fireEvent.click(changePasswordButton);
    
    expect(screen.getByLabelText('Current Password *')).toBeInTheDocument();
    expect(screen.getByLabelText('New Password *')).toBeInTheDocument();
    expect(screen.getByLabelText('Confirm New Password *')).toBeInTheDocument();
  });

  it('changes password successfully', async () => {
    render(<UserProfileForm />);
    
    // Show password form
    const changePasswordButton = screen.getByText('Change Password');
    fireEvent.click(changePasswordButton);
    
    // Fill password form
    fireEvent.change(screen.getByLabelText('Current Password *'), {
      target: { value: 'oldpassword' }
    });
    fireEvent.change(screen.getByLabelText('New Password *'), {
      target: { value: 'newpassword123' }
    });
    fireEvent.change(screen.getByLabelText('Confirm New Password *'), {
      target: { value: 'newpassword123' }
    });
    
    // Submit password change
    const submitButton = screen.getByRole('button', { name: 'Change Password' });
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(userService.changePassword).toHaveBeenCalledWith('oldpassword', 'newpassword123');
    });
    
    expect(screen.getByText('Password changed successfully!')).toBeInTheDocument();
  });

  it('shows error when passwords do not match', async () => {
    render(<UserProfileForm />);
    
    // Show password form
    const changePasswordButton = screen.getByText('Change Password');
    fireEvent.click(changePasswordButton);
    
    // Fill password form with mismatched passwords
    fireEvent.change(screen.getByLabelText('Current Password *'), {
      target: { value: 'oldpassword' }
    });
    fireEvent.change(screen.getByLabelText('New Password *'), {
      target: { value: 'newpassword123' }
    });
    fireEvent.change(screen.getByLabelText('Confirm New Password *'), {
      target: { value: 'differentpassword' }
    });
    
    // Submit password change
    const submitButton = screen.getByRole('button', { name: 'Change Password' });
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText('New passwords do not match')).toBeInTheDocument();
    });
    
    expect(userService.changePassword).not.toHaveBeenCalled();
  });

  it('shows error for short password', async () => {
    render(<UserProfileForm />);
    
    // Show password form
    const changePasswordButton = screen.getByText('Change Password');
    fireEvent.click(changePasswordButton);
    
    // Fill password form with short password
    fireEvent.change(screen.getByLabelText('Current Password *'), {
      target: { value: 'oldpassword' }
    });
    fireEvent.change(screen.getByLabelText('New Password *'), {
      target: { value: 'short' }
    });
    fireEvent.change(screen.getByLabelText('Confirm New Password *'), {
      target: { value: 'short' }
    });
    
    // Submit password change
    const submitButton = screen.getByRole('button', { name: 'Change Password' });
    fireEvent.click(submitButton);
    
    await waitFor(() => {
      expect(screen.getByText('Password must be at least 8 characters long')).toBeInTheDocument();
    });
    
    expect(userService.changePassword).not.toHaveBeenCalled();
  });

  it('validates required fields', async () => {
    render(<UserProfileForm />);
    
    // Clear required fields
    const firstNameInput = screen.getByDisplayValue('John');
    fireEvent.change(firstNameInput, { target: { value: '' } });
    
    const updateButton = screen.getByText('Update Profile');
    fireEvent.click(updateButton);
    
    // Form should not submit due to HTML5 validation
    expect(userService.updateProfile).not.toHaveBeenCalled();
  });

  it('disables buttons while loading', async () => {
    userService.updateProfile.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)));
    
    render(<UserProfileForm />);
    
    const updateButton = screen.getByText('Update Profile');
    fireEvent.click(updateButton);
    
    expect(screen.getByText('Updating...')).toBeInTheDocument();
    expect(screen.getByText('Updating...')).toBeDisabled();
    
    await waitFor(() => {
      expect(screen.getByText('Update Profile')).toBeInTheDocument();
    });
  });
});