import React from 'react';
import { render, screen, fireEvent, act } from '@testing-library/react';
import '@testing-library/jest-dom';
import { FeedbackMessage } from '../FeedbackMessage';

// Mock lucide-react icons
jest.mock('lucide-react', () => ({
  X: ({ size, className }: any) => <div data-testid="close-icon" className={className} />,
  CheckCircle: ({ size, className }: any) => <div data-testid="success-icon" className={className} />,
  AlertCircle: ({ size, className }: any) => <div data-testid="error-icon" className={className} />,
  Info: ({ size, className }: any) => <div data-testid="info-icon" className={className} />,
  AlertTriangle: ({ size, className }: any) => <div data-testid="warning-icon" className={className} />
}));

describe('FeedbackMessage', () => {
  const defaultProps = {
    type: 'info' as const,
    message: 'Test message',
    isVisible: true
  };

  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  describe('Rendering', () => {
    it('renders message when visible', () => {
      render(<FeedbackMessage {...defaultProps} />);
      
      expect(screen.getByText('Test message')).toBeInTheDocument();
      expect(screen.getByTestId('info-icon')).toBeInTheDocument();
    });

    it('does not render when not visible', () => {
      render(<FeedbackMessage {...defaultProps} isVisible={false} />);
      
      expect(screen.queryByText('Test message')).not.toBeInTheDocument();
    });

    it('renders success type with correct icon', () => {
      render(<FeedbackMessage {...defaultProps} type="success" />);
      
      expect(screen.getByTestId('success-icon')).toBeInTheDocument();
      expect(screen.getByRole('alert')).toHaveClass('bg-green-50', 'border-green-200');
    });

    it('renders error type with correct icon', () => {
      render(<FeedbackMessage {...defaultProps} type="error" />);
      
      expect(screen.getByTestId('error-icon')).toBeInTheDocument();
      expect(screen.getByRole('alert')).toHaveClass('bg-red-50', 'border-red-200');
    });

    it('renders warning type with correct icon', () => {
      render(<FeedbackMessage {...defaultProps} type="warning" />);
      
      expect(screen.getByTestId('warning-icon')).toBeInTheDocument();
      expect(screen.getByRole('alert')).toHaveClass('bg-yellow-50', 'border-yellow-200');
    });

    it('renders info type with correct icon', () => {
      render(<FeedbackMessage {...defaultProps} type="info" />);
      
      expect(screen.getByTestId('info-icon')).toBeInTheDocument();
      expect(screen.getByRole('alert')).toHaveClass('bg-blue-50', 'border-blue-200');
    });
  });

  describe('Close Functionality', () => {
    it('shows close button by default', () => {
      const onDismiss = jest.fn();
      render(<FeedbackMessage {...defaultProps} onDismiss={onDismiss} />);
      
      expect(screen.getByRole('button')).toBeInTheDocument();
    });

    it('hides close button when showCloseButton is false', () => {
      render(<FeedbackMessage {...defaultProps} showCloseButton={false} />);
      
      expect(screen.queryByTestId('close-icon')).not.toBeInTheDocument();
    });

    it('calls onDismiss when close button is clicked', () => {
      const onDismiss = jest.fn();
      render(<FeedbackMessage {...defaultProps} onDismiss={onDismiss} />);
      
      fireEvent.click(screen.getByRole('button'));
      expect(onDismiss).toHaveBeenCalledTimes(1);
    });
  });

  describe('Auto Hide Functionality', () => {
    it('auto hides after specified duration', () => {
      const onDismiss = jest.fn();
      render(
        <FeedbackMessage 
          {...defaultProps} 
          onDismiss={onDismiss}
          autoHideDuration={3000}
        />
      );
      
      expect(onDismiss).not.toHaveBeenCalled();
      
      act(() => {
        jest.advanceTimersByTime(3000);
      });
      
      expect(onDismiss).toHaveBeenCalledTimes(1);
    });

    it('does not auto hide when autoHideDuration is not provided', () => {
      const onDismiss = jest.fn();
      render(<FeedbackMessage {...defaultProps} onDismiss={onDismiss} />);
      
      act(() => {
        jest.advanceTimersByTime(5000);
      });
      
      expect(onDismiss).not.toHaveBeenCalled();
    });

    it('clears timeout when component unmounts', () => {
      const onDismiss = jest.fn();
      const { unmount } = render(
        <FeedbackMessage 
          {...defaultProps} 
          onDismiss={onDismiss}
          autoHideDuration={3000}
        />
      );
      
      unmount();
      
      act(() => {
        jest.advanceTimersByTime(3000);
      });
      
      expect(onDismiss).not.toHaveBeenCalled();
    });

    it('resets timer when isVisible changes', () => {
      const onDismiss = jest.fn();
      const { rerender } = render(
        <FeedbackMessage 
          {...defaultProps} 
          onDismiss={onDismiss}
          autoHideDuration={3000}
        />
      );
      
      act(() => {
        jest.advanceTimersByTime(1500);
      });
      
      // Change visibility to reset timer
      rerender(
        <FeedbackMessage 
          {...defaultProps} 
          isVisible={false}
          onDismiss={onDismiss}
          autoHideDuration={3000}
        />
      );
      
      rerender(
        <FeedbackMessage 
          {...defaultProps} 
          isVisible={true}
          onDismiss={onDismiss}
          autoHideDuration={3000}
        />
      );
      
      act(() => {
        jest.advanceTimersByTime(1500);
      });
      
      expect(onDismiss).not.toHaveBeenCalled();
      
      act(() => {
        jest.advanceTimersByTime(1500);
      });
      
      expect(onDismiss).toHaveBeenCalledTimes(1);
    });
  });

  describe('Accessibility', () => {
    it('has proper role attribute', () => {
      render(<FeedbackMessage {...defaultProps} />);
      
      expect(screen.getByRole('alert')).toBeInTheDocument();
    });

    it('has proper aria-live attribute', () => {
      render(<FeedbackMessage {...defaultProps} />);
      
      expect(screen.getByRole('alert')).toHaveAttribute('aria-live', 'polite');
    });

    it('close button has proper aria-label', () => {
      const onDismiss = jest.fn();
      render(<FeedbackMessage {...defaultProps} onDismiss={onDismiss} />);
      
      expect(screen.getByRole('button')).toHaveAttribute('aria-label', 'Close');
    });
  });

  describe('Custom Styling', () => {
    it('applies custom className', () => {
      render(<FeedbackMessage {...defaultProps} className="custom-class" />);
      
      expect(screen.getByRole('alert')).toHaveClass('custom-class');
    });

    it('applies correct styling for each message type', () => {
      const types = ['success', 'error', 'warning', 'info'] as const;
      const expectedClasses = {
        success: ['bg-green-50', 'border-green-200', 'text-green-700'],
        error: ['bg-red-50', 'border-red-200', 'text-red-700'],
        warning: ['bg-yellow-50', 'border-yellow-200', 'text-yellow-700'],
        info: ['bg-blue-50', 'border-blue-200', 'text-blue-700']
      };

      types.forEach(type => {
        const { unmount } = render(<FeedbackMessage {...defaultProps} type={type} />);
        
        const alert = screen.getByRole('alert');
        expectedClasses[type].forEach(className => {
          expect(alert).toHaveClass(className);
        });
        
        unmount();
      });
    });
  });

  describe('Edge Cases', () => {
    it('handles empty message', () => {
      render(<FeedbackMessage {...defaultProps} message="" />);
      
      expect(screen.getByRole('alert')).toBeInTheDocument();
      expect(screen.getByRole('alert')).toHaveTextContent('');
    });

    it('handles long messages', () => {
      const longMessage = 'This is a very long message that should still be displayed correctly and not break the layout or functionality of the component';
      render(<FeedbackMessage {...defaultProps} message={longMessage} />);
      
      expect(screen.getByText(longMessage)).toBeInTheDocument();
    });

    it('handles null type gracefully', () => {
      render(<FeedbackMessage {...defaultProps} type={null as any} />);
      
      // Should not render when type is null
      expect(screen.queryByRole('alert')).not.toBeInTheDocument();
    });
  });
});