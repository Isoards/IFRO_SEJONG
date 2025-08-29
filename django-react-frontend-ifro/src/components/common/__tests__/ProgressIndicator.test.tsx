import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { ProgressIndicator } from '../ProgressIndicator';

describe('ProgressIndicator', () => {
  describe('Rendering', () => {
    it('renders progress bar with correct progress value', () => {
      render(<ProgressIndicator progress={50} />);
      
      const progressBar = screen.getByRole('progressbar');
      expect(progressBar).toBeInTheDocument();
      expect(progressBar).toHaveAttribute('aria-valuenow', '50');
      expect(progressBar).toHaveAttribute('aria-valuemin', '0');
      expect(progressBar).toHaveAttribute('aria-valuemax', '100');
    });

    it('renders with percentage by default', () => {
      render(<ProgressIndicator progress={75} />);
      
      expect(screen.getByText('75%')).toBeInTheDocument();
    });

    it('hides percentage when showPercentage is false', () => {
      render(<ProgressIndicator progress={60} showPercentage={false} />);
      
      expect(screen.queryByText('60%')).not.toBeInTheDocument();
    });
  });

  describe('Progress Values', () => {
    it('handles 0% progress', () => {
      render(<ProgressIndicator progress={0} />);
      
      const progressBar = screen.getByRole('progressbar');
      expect(progressBar).toHaveAttribute('aria-valuenow', '0');
      expect(progressBar).toHaveStyle({ width: '0%' });
      expect(screen.getByText('0%')).toBeInTheDocument();
    });

    it('handles 100% progress', () => {
      render(<ProgressIndicator progress={100} />);
      
      const progressBar = screen.getByRole('progressbar');
      expect(progressBar).toHaveAttribute('aria-valuenow', '100');
      expect(progressBar).toHaveStyle({ width: '100%' });
      expect(screen.getByText('100%')).toBeInTheDocument();
    });

    it('clamps progress values above 100', () => {
      render(<ProgressIndicator progress={150} />);
      
      const progressBar = screen.getByRole('progressbar');
      expect(progressBar).toHaveAttribute('aria-valuenow', '100');
      expect(progressBar).toHaveStyle({ width: '100%' });
      expect(screen.getByText('100%')).toBeInTheDocument();
    });

    it('clamps progress values below 0', () => {
      render(<ProgressIndicator progress={-10} />);
      
      const progressBar = screen.getByRole('progressbar');
      expect(progressBar).toHaveAttribute('aria-valuenow', '0');
      expect(progressBar).toHaveStyle({ width: '0%' });
      expect(screen.getByText('0%')).toBeInTheDocument();
    });

    it('handles decimal progress values', () => {
      render(<ProgressIndicator progress={33.33} />);
      
      const progressBar = screen.getByRole('progressbar');
      expect(progressBar).toHaveAttribute('aria-valuenow', '33.33');
      expect(progressBar).toHaveStyle({ width: '33.33%' });
      expect(screen.getByText('33%')).toBeInTheDocument(); // Rounded
    });
  });

  describe('Styling and Variants', () => {
    it('applies default styling', () => {
      render(<ProgressIndicator progress={50} />);
      
      const progressBar = screen.getByRole('progressbar');
      expect(progressBar).toHaveClass('bg-blue-600', 'h-2', 'rounded-full', 'transition-all', 'duration-300');
      expect(progressBar).toHaveStyle({ width: '50%' });
    });

    it('applies custom className', () => {
      render(<ProgressIndicator progress={50} className="custom-class" />);
      
      const container = screen.getByRole('progressbar').parentElement?.parentElement;
      expect(container).toHaveClass('custom-class');
    });

    it('applies custom colors', () => {
      render(<ProgressIndicator progress={50} color="bg-green-500" trackColor="bg-gray-300" />);
      
      const progressBar = screen.getByRole('progressbar');
      expect(progressBar).toHaveClass('bg-green-500');
      
      const track = progressBar.parentElement;
      expect(track).toHaveClass('bg-gray-300');
    });

    it('applies different sizes', () => {
      const { rerender } = render(<ProgressIndicator progress={50} size="sm" />);
      
      let progressBar = screen.getByRole('progressbar');
      expect(progressBar).toHaveClass('h-1');
      
      rerender(<ProgressIndicator progress={50} size="lg" />);
      progressBar = screen.getByRole('progressbar');
      expect(progressBar).toHaveClass('h-3');
    });
  });

  describe('Animation and Transitions', () => {
    it('applies smooth transition classes', () => {
      render(<ProgressIndicator progress={50} />);
      
      const progressBar = screen.getByRole('progressbar');
      expect(progressBar).toHaveClass('transition-all', 'duration-300');
    });
  });

  describe('Accessibility', () => {
    it('has proper ARIA attributes', () => {
      render(<ProgressIndicator progress={75} />);
      
      const progressBar = screen.getByRole('progressbar');
      expect(progressBar).toHaveAttribute('aria-valuenow', '75');
      expect(progressBar).toHaveAttribute('aria-valuemin', '0');
      expect(progressBar).toHaveAttribute('aria-valuemax', '100');
    });
  });

  describe('Edge Cases', () => {
    it('handles NaN progress value', () => {
      render(<ProgressIndicator progress={NaN} />);
      
      const progressBar = screen.getByRole('progressbar');
      expect(progressBar).toHaveAttribute('aria-valuenow', '0');
      expect(progressBar).toHaveStyle({ width: '0%' });
      expect(screen.getByText('0%')).toBeInTheDocument();
    });

    it('handles undefined progress value', () => {
      render(<ProgressIndicator progress={undefined as any} />);
      
      const progressBar = screen.getByRole('progressbar');
      expect(progressBar).toHaveAttribute('aria-valuenow', '0');
    });

    it('handles string progress value', () => {
      render(<ProgressIndicator progress={'50' as any} />);
      
      const progressBar = screen.getByRole('progressbar');
      expect(progressBar).toHaveAttribute('aria-valuenow', '50');
    });
  });

  describe('Performance', () => {
    it('does not re-render unnecessarily', () => {
      const { rerender } = render(<ProgressIndicator progress={50} />);
      
      const progressBar = screen.getByRole('progressbar');
      const initialElement = progressBar;
      
      rerender(<ProgressIndicator progress={50} />);
      
      expect(screen.getByRole('progressbar')).toBe(initialElement);
    });
  });
});