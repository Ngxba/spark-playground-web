import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import RunReport from './RunReport';

describe('RunReport Component', () => {
  const mockOnClose = vi.fn();

  const mockResult = {
    correct: true,
    output: [{ id: 1, name: 'test' }],
    metrics: {
      time_simulated: 2.5,
      shuffles: 1,
      stages: 2,
      skew_detected: false,
      cache_used: false,
      broadcast_used: true,
    },
    stars: 3,
    hint: null,
    error: null,
  };

  it('should render nothing when result is null', () => {
    const { container } = render(<RunReport result={null} onClose={mockOnClose} />);
    expect(container.firstChild).toBeNull();
  });

  it('should render correct output indicator', () => {
    render(<RunReport result={mockResult} onClose={mockOnClose} />);
    expect(screen.getByText(/Correct Output!/i)).toBeInTheDocument();
  });

  it('should render 3 stars when stars is 3', () => {
    render(<RunReport result={mockResult} onClose={mockOnClose} />);
    const stars = screen.getAllByText('★');
    // 3 filled + 0 empty from our 3-star result
    expect(stars.length).toBeGreaterThanOrEqual(3);
  });

  it('should render metrics correctly', () => {
    render(<RunReport result={mockResult} onClose={mockOnClose} />);
    expect(screen.getByText('2.5s')).toBeInTheDocument();
    expect(screen.getByText('1')).toBeInTheDocument(); // shuffles
    expect(screen.getByText('2')).toBeInTheDocument(); // stages
  });

  it('should show broadcast indicator when used', () => {
    render(<RunReport result={mockResult} onClose={mockOnClose} />);
    expect(screen.getByText(/Broadcast/i)).toBeInTheDocument();
  });

  it('should render error message when present', () => {
    const errorResult = {
      ...mockResult,
      correct: false,
      error: 'Syntax error: missing parenthesis',
    };
    render(<RunReport result={errorResult} onClose={mockOnClose} />);
    expect(screen.getByText(/Output Incorrect/i)).toBeInTheDocument();
    expect(screen.getByText(/Syntax error/i)).toBeInTheDocument();
  });

  it('should render hint when present', () => {
    const hintResult = {
      ...mockResult,
      stars: 2,
      hint: 'Try using broadcast join for better performance',
    };
    render(<RunReport result={hintResult} onClose={mockOnClose} />);
    expect(screen.getByText(/Try using broadcast join/i)).toBeInTheDocument();
  });

  it('should call onClose when close button is clicked', () => {
    render(<RunReport result={mockResult} onClose={mockOnClose} />);
    const closeButton = screen.getByText('×');
    fireEvent.click(closeButton);
    expect(mockOnClose).toHaveBeenCalled();
  });

  it('should call onClose when overlay is clicked', () => {
    render(<RunReport result={mockResult} onClose={mockOnClose} />);
    const overlay = screen.getByText(/Correct Output!/i).closest('.run-report-overlay');
    fireEvent.click(overlay);
    expect(mockOnClose).toHaveBeenCalled();
  });

  it('should not close when modal content is clicked', () => {
    const localOnClose = vi.fn();
    const { container } = render(<RunReport result={mockResult} onClose={localOnClose} />);
    const modal = container.querySelector('.run-report-modal');
    fireEvent.click(modal);
    // onClose should not be called when clicking inside modal (stopPropagation)
    expect(localOnClose).not.toHaveBeenCalled();
  });

  it('should show execution log when present', () => {
    const logResult = {
      ...mockResult,
      execution_log: 'Processing data...\nCompleted!',
    };
    render(<RunReport result={logResult} onClose={mockOnClose} />);
    expect(screen.getByText(/Execution Log/i)).toBeInTheDocument();
    expect(screen.getByText(/Processing data/i)).toBeInTheDocument();
  });

  it('should show skew warning when detected', () => {
    const skewResult = {
      ...mockResult,
      metrics: {
        ...mockResult.metrics,
        skew_detected: true,
      },
    };
    render(<RunReport result={skewResult} onClose={mockOnClose} />);
    expect(screen.getByText(/Skew/i)).toBeInTheDocument();
  });

  it('should show cache indicator when used', () => {
    const cacheResult = {
      ...mockResult,
      metrics: {
        ...mockResult.metrics,
        cache_used: true,
      },
    };
    render(<RunReport result={cacheResult} onClose={mockOnClose} />);
    expect(screen.getByText(/Cache/i)).toBeInTheDocument();
  });
});
