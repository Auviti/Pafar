import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi } from 'vitest';
import ReviewModeration from '../ReviewModeration';
import { adminService } from '../../../services/admin';

// Mock the admin service
vi.mock('../../../services/admin', () => ({
  adminService: {
    getReviews: vi.fn(),
    getFlaggedReviews: vi.fn(),
    moderateReview: vi.fn(),
  },
}));

// Mock window.alert
global.alert = vi.fn();

const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

const renderWithQueryClient = (component) => {
  const queryClient = createTestQueryClient();
  return render(
    <QueryClientProvider client={queryClient}>
      {component}
    </QueryClientProvider>
  );
};

const mockReviewsData = {
  reviews: [
    {
      id: '1',
      user_name: 'John Passenger',
      user_email: 'john@example.com',
      rating: 5,
      comment: 'Excellent service! The bus was clean and the driver was professional.',
      trip_route: 'Lagos - Abuja',
      trip_date: '2024-01-15T08:00:00Z',
      bus_number: 'BUS-001',
      driver_name: 'John Driver',
      status: 'pending',
      created_at: '2024-01-15T16:00:00Z',
      flags: [],
    },
    {
      id: '2',
      user_name: 'Jane Passenger',
      user_email: 'jane@example.com',
      rating: 2,
      comment: 'This is inappropriate content that should be flagged.',
      trip_route: 'Abuja - Kano',
      trip_date: '2024-01-14T10:00:00Z',
      bus_number: 'BUS-002',
      driver_name: 'Jane Driver',
      status: 'pending',
      created_at: '2024-01-14T18:00:00Z',
      flags: ['inappropriate', 'spam'],
    },
  ],
  stats: {
    pending: 2,
    approved: 15,
    rejected: 3,
  },
};

const mockFlaggedReviews = [
  {
    id: '2',
    user_name: 'Jane Passenger',
    user_email: 'jane@example.com',
    rating: 2,
    comment: 'This is inappropriate content that should be flagged.',
    trip_route: 'Abuja - Kano',
    trip_date: '2024-01-14T10:00:00Z',
    bus_number: 'BUS-002',
    driver_name: 'Jane Driver',
    status: 'pending',
    created_at: '2024-01-14T18:00:00Z',
    flags: ['inappropriate', 'spam'],
  },
];

describe('ReviewModeration', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders review moderation interface', async () => {
    adminService.getReviews.mockResolvedValue(mockReviewsData);
    adminService.getFlaggedReviews.mockResolvedValue(mockFlaggedReviews);

    renderWithQueryClient(<ReviewModeration />);

    await waitFor(() => {
      expect(screen.getByText('Review Moderation')).toBeInTheDocument();
    });

    // Check header stats
    expect(screen.getByText('2')).toBeInTheDocument(); // Pending reviews
    expect(screen.getByText('Pending Reviews')).toBeInTheDocument();
    expect(screen.getByText('1')).toBeInTheDocument(); // Flagged reviews
    expect(screen.getByText('Flagged Reviews')).toBeInTheDocument();
    expect(screen.getByText('15')).toBeInTheDocument(); // Approved today
    expect(screen.getByText('Approved Today')).toBeInTheDocument();
  });

  it('displays filter tabs with correct counts', async () => {
    adminService.getReviews.mockResolvedValue(mockReviewsData);
    adminService.getFlaggedReviews.mockResolvedValue(mockFlaggedReviews);

    renderWithQueryClient(<ReviewModeration />);

    await waitFor(() => {
      expect(screen.getByText('Pending (2)')).toBeInTheDocument();
    });

    // Check all filter tabs
    expect(screen.getByText('Pending (2)')).toBeInTheDocument();
    expect(screen.getByText('Flagged (1)')).toBeInTheDocument();
    expect(screen.getByText('Approved')).toBeInTheDocument();
    expect(screen.getByText('Rejected')).toBeInTheDocument();
    expect(screen.getByText('All Reviews')).toBeInTheDocument();

    // Check that pending tab is active by default
    const pendingTab = screen.getByText('Pending (2)');
    expect(pendingTab).toHaveClass('active');
  });

  it('displays reviews in card format', async () => {
    adminService.getReviews.mockResolvedValue(mockReviewsData);
    adminService.getFlaggedReviews.mockResolvedValue(mockFlaggedReviews);

    renderWithQueryClient(<ReviewModeration />);

    await waitFor(() => {
      expect(screen.getByText('John Passenger')).toBeInTheDocument();
    });

    // Check review details
    expect(screen.getByText('John Passenger')).toBeInTheDocument();
    expect(screen.getByText('Jane Passenger')).toBeInTheDocument();
    expect(screen.getByText('Lagos - Abuja')).toBeInTheDocument();
    expect(screen.getByText('Abuja - Kano')).toBeInTheDocument();

    // Check ratings (stars)
    const stars = screen.getAllByText('⭐');
    expect(stars.length).toBeGreaterThan(0);

    // Check status badges
    expect(screen.getAllByText('pending')).toHaveLength(2);
  });

  it('shows flag indicators for flagged reviews', async () => {
    adminService.getReviews.mockResolvedValue(mockReviewsData);
    adminService.getFlaggedReviews.mockResolvedValue(mockFlaggedReviews);

    renderWithQueryClient(<ReviewModeration />);

    await waitFor(() => {
      expect(screen.getByText('🚩 2')).toBeInTheDocument();
    });

    // Check that flagged review has different styling
    const flaggedCard = screen.getByText('Jane Passenger').closest('.review-card');
    expect(flaggedCard).toHaveClass('flagged');
  });

  it('switches to flagged reviews tab', async () => {
    adminService.getReviews.mockResolvedValue(mockReviewsData);
    adminService.getFlaggedReviews.mockResolvedValue(mockFlaggedReviews);

    renderWithQueryClient(<ReviewModeration />);

    await waitFor(() => {
      expect(screen.getByText('Flagged (1)')).toBeInTheDocument();
    });

    const flaggedTab = screen.getByText('Flagged (1)');
    fireEvent.click(flaggedTab);

    await waitFor(() => {
      expect(flaggedTab).toHaveClass('active');
    });
  });

  it('opens review details modal when View Details is clicked', async () => {
    adminService.getReviews.mockResolvedValue(mockReviewsData);
    adminService.getFlaggedReviews.mockResolvedValue(mockFlaggedReviews);

    renderWithQueryClient(<ReviewModeration />);

    await waitFor(() => {
      expect(screen.getAllByText('View Details')).toHaveLength(2);
    });

    const viewDetailsButtons = screen.getAllByText('View Details');
    fireEvent.click(viewDetailsButtons[0]);

    await waitFor(() => {
      expect(screen.getByText('Review Moderation')).toBeInTheDocument();
    });

    // Check modal content
    expect(screen.getByText('John Passenger')).toBeInTheDocument();
    expect(screen.getByText('john@example.com')).toBeInTheDocument();
    expect(screen.getByText('Trip Information')).toBeInTheDocument();
    expect(screen.getByText('Review Content')).toBeInTheDocument();
    expect(screen.getByText('BUS-001')).toBeInTheDocument();
    expect(screen.getByText('John Driver')).toBeInTheDocument();
  });

  it('displays moderation actions for pending reviews', async () => {
    adminService.getReviews.mockResolvedValue(mockReviewsData);
    adminService.getFlaggedReviews.mockResolvedValue(mockFlaggedReviews);

    renderWithQueryClient(<ReviewModeration />);

    await waitFor(() => {
      expect(screen.getAllByText('View Details')).toHaveLength(2);
    });

    // Open modal for pending review
    const viewDetailsButtons = screen.getAllByText('View Details');
    fireEvent.click(viewDetailsButtons[0]);

    await waitFor(() => {
      expect(screen.getByText('Moderation Actions')).toBeInTheDocument();
    });

    // Check moderation buttons
    expect(screen.getByText('✅ Approve')).toBeInTheDocument();
    expect(screen.getByText('❌ Reject')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Enter reason for rejection...')).toBeInTheDocument();
  });

  it('handles review approval', async () => {
    adminService.getReviews.mockResolvedValue(mockReviewsData);
    adminService.getFlaggedReviews.mockResolvedValue(mockFlaggedReviews);
    adminService.moderateReview.mockResolvedValue({ success: true });

    renderWithQueryClient(<ReviewModeration />);

    await waitFor(() => {
      expect(screen.getAllByText('Approve')).toHaveLength(2);
    });

    // Click approve button on card
    const approveButtons = screen.getAllByText('Approve');
    fireEvent.click(approveButtons[0]);

    await waitFor(() => {
      expect(adminService.moderateReview).toHaveBeenCalledWith('1', 'approve', '');
    });
  });

  it('handles review rejection with reason', async () => {
    adminService.getReviews.mockResolvedValue(mockReviewsData);
    adminService.getFlaggedReviews.mockResolvedValue(mockFlaggedReviews);
    adminService.moderateReview.mockResolvedValue({ success: true });

    renderWithQueryClient(<ReviewModeration />);

    await waitFor(() => {
      expect(screen.getAllByText('View Details')).toHaveLength(2);
    });

    // Open modal
    const viewDetailsButtons = screen.getAllByText('View Details');
    fireEvent.click(viewDetailsButtons[0]);

    await waitFor(() => {
      expect(screen.getByText('✅ Approve')).toBeInTheDocument();
    });

    // Enter rejection reason
    const reasonTextarea = screen.getByPlaceholderText('Enter reason for rejection...');
    fireEvent.change(reasonTextarea, { target: { value: 'Inappropriate content' } });

    // Click reject button
    const rejectButton = screen.getByText('❌ Reject');
    fireEvent.click(rejectButton);

    await waitFor(() => {
      expect(adminService.moderateReview).toHaveBeenCalledWith('1', 'reject', 'Inappropriate content');
    });
  });

  it('prevents rejection without reason', async () => {
    adminService.getReviews.mockResolvedValue(mockReviewsData);
    adminService.getFlaggedReviews.mockResolvedValue(mockFlaggedReviews);

    renderWithQueryClient(<ReviewModeration />);

    await waitFor(() => {
      expect(screen.getAllByText('View Details')).toHaveLength(2);
    });

    // Open modal
    const viewDetailsButtons = screen.getAllByText('View Details');
    fireEvent.click(viewDetailsButtons[0]);

    await waitFor(() => {
      expect(screen.getByText('❌ Reject')).toBeInTheDocument();
    });

    // Try to reject without reason
    const rejectButton = screen.getByText('❌ Reject');
    fireEvent.click(rejectButton);

    expect(global.alert).toHaveBeenCalledWith('Please provide a reason for rejection');
    expect(adminService.moderateReview).not.toHaveBeenCalled();
  });

  it('displays flags for flagged reviews in modal', async () => {
    adminService.getReviews.mockResolvedValue(mockReviewsData);
    adminService.getFlaggedReviews.mockResolvedValue(mockFlaggedReviews);

    renderWithQueryClient(<ReviewModeration />);

    await waitFor(() => {
      expect(screen.getAllByText('View Details')).toHaveLength(2);
    });

    // Open modal for flagged review
    const viewDetailsButtons = screen.getAllByText('View Details');
    fireEvent.click(viewDetailsButtons[1]);

    await waitFor(() => {
      expect(screen.getByText('Flags:')).toBeInTheDocument();
    });

    // Check flag badges
    expect(screen.getByText('inappropriate')).toBeInTheDocument();
    expect(screen.getByText('spam')).toBeInTheDocument();
  });

  it('closes modal when close button is clicked', async () => {
    adminService.getReviews.mockResolvedValue(mockReviewsData);
    adminService.getFlaggedReviews.mockResolvedValue(mockFlaggedReviews);

    renderWithQueryClient(<ReviewModeration />);

    await waitFor(() => {
      expect(screen.getAllByText('View Details')).toHaveLength(2);
    });

    // Open modal
    const viewDetailsButtons = screen.getAllByText('View Details');
    fireEvent.click(viewDetailsButtons[0]);

    await waitFor(() => {
      expect(screen.getByText('×')).toBeInTheDocument();
    });

    // Close modal
    const closeButton = screen.getByText('×');
    fireEvent.click(closeButton);

    await waitFor(() => {
      expect(screen.queryByText('Review Moderation')).not.toBeInTheDocument();
    });
  });

  it('truncates long review comments in card view', async () => {
    const longCommentData = {
      ...mockReviewsData,
      reviews: [
        {
          ...mockReviewsData.reviews[0],
          comment: 'This is a very long comment that should be truncated in the card view because it exceeds the maximum length that we want to display in the summary view of the review card.',
        },
      ],
    };

    adminService.getReviews.mockResolvedValue(longCommentData);
    adminService.getFlaggedReviews.mockResolvedValue(mockFlaggedReviews);

    renderWithQueryClient(<ReviewModeration />);

    await waitFor(() => {
      expect(screen.getByText(/This is a very long comment that should be truncated/)).toBeInTheDocument();
    });

    // Check that comment is truncated with ellipsis
    const truncatedText = screen.getByText(/\.\.\./);
    expect(truncatedText).toBeInTheDocument();
  });

  it('handles reviews without comments', async () => {
    const noCommentData = {
      ...mockReviewsData,
      reviews: [
        {
          ...mockReviewsData.reviews[0],
          comment: null,
        },
      ],
    };

    adminService.getReviews.mockResolvedValue(noCommentData);
    adminService.getFlaggedReviews.mockResolvedValue(mockFlaggedReviews);

    renderWithQueryClient(<ReviewModeration />);

    await waitFor(() => {
      expect(screen.getByText('No comment provided')).toBeInTheDocument();
    });
  });

  it('renders loading state', () => {
    adminService.getReviews.mockImplementation(
      () => new Promise(() => {}) // Never resolves
    );
    adminService.getFlaggedReviews.mockResolvedValue(mockFlaggedReviews);

    renderWithQueryClient(<ReviewModeration />);

    expect(screen.getByText('Loading reviews...')).toBeInTheDocument();
  });

  it('renders error state', async () => {
    const errorMessage = 'Failed to fetch reviews';
    adminService.getReviews.mockRejectedValue(new Error(errorMessage));
    adminService.getFlaggedReviews.mockResolvedValue(mockFlaggedReviews);

    renderWithQueryClient(<ReviewModeration />);

    await waitFor(() => {
      expect(screen.getByText(`Error loading reviews: ${errorMessage}`)).toBeInTheDocument();
    });
  });

  it('handles empty reviews data', async () => {
    const emptyData = { reviews: [], stats: { pending: 0, approved: 0, rejected: 0 } };
    adminService.getReviews.mockResolvedValue(emptyData);
    adminService.getFlaggedReviews.mockResolvedValue([]);

    renderWithQueryClient(<ReviewModeration />);

    await waitFor(() => {
      expect(screen.getByText('No reviews found')).toBeInTheDocument();
    });
  });

  it('handles empty flagged reviews', async () => {
    adminService.getReviews.mockResolvedValue(mockReviewsData);
    adminService.getFlaggedReviews.mockResolvedValue([]);

    renderWithQueryClient(<ReviewModeration />);

    // Switch to flagged tab
    const flaggedTab = screen.getByText('Flagged (0)');
    fireEvent.click(flaggedTab);

    await waitFor(() => {
      expect(screen.getByText('No flagged reviews')).toBeInTheDocument();
    });
  });

  it('displays correct star ratings', async () => {
    adminService.getReviews.mockResolvedValue(mockReviewsData);
    adminService.getFlaggedReviews.mockResolvedValue(mockFlaggedReviews);

    renderWithQueryClient(<ReviewModeration />);

    await waitFor(() => {
      expect(screen.getByText('(5/5)')).toBeInTheDocument();
      expect(screen.getByText('(2/5)')).toBeInTheDocument();
    });
  });

  it('formats dates correctly', async () => {
    adminService.getReviews.mockResolvedValue(mockReviewsData);
    adminService.getFlaggedReviews.mockResolvedValue(mockFlaggedReviews);

    renderWithQueryClient(<ReviewModeration />);

    await waitFor(() => {
      // Check that dates are formatted (exact format depends on locale)
      const dateElements = screen.getAllByText(/\d{1,2}\/\d{1,2}\/\d{4}/);
      expect(dateElements.length).toBeGreaterThan(0);
    });
  });

  it('switches between different filter tabs', async () => {
    adminService.getReviews.mockResolvedValue(mockReviewsData);
    adminService.getFlaggedReviews.mockResolvedValue(mockFlaggedReviews);

    renderWithQueryClient(<ReviewModeration />);

    await waitFor(() => {
      expect(screen.getByText('Approved')).toBeInTheDocument();
    });

    // Switch to approved tab
    const approvedTab = screen.getByText('Approved');
    fireEvent.click(approvedTab);

    await waitFor(() => {
      expect(approvedTab).toHaveClass('active');
    });

    // Switch to all reviews tab
    const allTab = screen.getByText('All Reviews');
    fireEvent.click(allTab);

    await waitFor(() => {
      expect(allTab).toHaveClass('active');
    });
  });
});