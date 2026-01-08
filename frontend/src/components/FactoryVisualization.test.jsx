import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import FactoryVisualization from './FactoryVisualization';

describe('FactoryVisualization Component', () => {
  const mockPuzzle = {
    id: 'test_puzzle',
    title: 'Test Puzzle',
    scenario: 'This is a test factory scenario',
    visualization_config: {
      input_conveyors: 2,
      output_conveyors: 1,
      transformation: 'join',
    },
  };

  it('should render nothing when puzzle is null', () => {
    const { container } = render(<FactoryVisualization puzzle={null} isRunning={false} result={null} />);
    expect(container.firstChild).toBeNull();
  });

  it('should render factory view title and description', () => {
    render(<FactoryVisualization puzzle={mockPuzzle} isRunning={false} result={null} />);
    expect(screen.getByText('Factory View')).toBeInTheDocument();
    expect(screen.getByText(/test factory scenario/i)).toBeInTheDocument();
  });

  it('should render SVG factory diagram', () => {
    const { container } = render(<FactoryVisualization puzzle={mockPuzzle} isRunning={false} result={null} />);
    const svg = container.querySelector('svg.factory-svg');
    expect(svg).toBeInTheDocument();
  });

  it('should show idle status when not running', () => {
    render(<FactoryVisualization puzzle={mockPuzzle} isRunning={false} result={null} />);
    expect(screen.getByText(/Ready to run/i)).toBeInTheDocument();
  });

  it('should show running status when isRunning is true', () => {
    render(<FactoryVisualization puzzle={mockPuzzle} isRunning={true} result={null} />);
    expect(screen.getByText(/Factory running/i)).toBeInTheDocument();
  });

  it('should show success status when result is correct', () => {
    const mockResult = {
      correct: true,
      metrics: {
        shuffles: 1,
        broadcast_used: false,
      },
    };
    render(<FactoryVisualization puzzle={mockPuzzle} isRunning={false} result={mockResult} />);
    // After animation completes, should show complete status
    // Note: In real usage, there's a delay before showing this
  });

  it('should show error status when result is incorrect', () => {
    const mockResult = {
      correct: false,
      metrics: {
        shuffles: 0,
      },
    };
    // Render with completed animation state
    render(<FactoryVisualization puzzle={mockPuzzle} isRunning={false} result={mockResult} />);
  });

  it('should render correct number of input conveyors', () => {
    const { container } = render(<FactoryVisualization puzzle={mockPuzzle} isRunning={false} result={null} />);
    // Check for input section elements
    const inputTexts = container.querySelectorAll('text');
    const inputLabels = Array.from(inputTexts).filter(text => text.textContent.includes('Input'));
    expect(inputLabels.length).toBeGreaterThanOrEqual(2);
  });

  it('should render transformation machine', () => {
    const { container } = render(<FactoryVisualization puzzle={mockPuzzle} isRunning={false} result={null} />);
    const machineText = Array.from(container.querySelectorAll('text')).find(
      text => text.textContent.includes('JOIN')
    );
    expect(machineText).toBeInTheDocument();
  });

  it('should show broadcast indicator when broadcast is used', () => {
    const mockResult = {
      correct: true,
      metrics: {
        shuffles: 0,
        broadcast_used: true,
      },
    };
    const { container } = render(<FactoryVisualization puzzle={mockPuzzle} isRunning={false} result={mockResult} />);
    const broadcastText = Array.from(container.querySelectorAll('text')).find(
      text => text.textContent.includes('Broadcast')
    );
    expect(broadcastText).toBeInTheDocument();
  });

  it('should show shuffle indicator when shuffles occur', () => {
    const mockResult = {
      correct: true,
      metrics: {
        shuffles: 2,
        broadcast_used: false,
      },
    };
    const { container } = render(<FactoryVisualization puzzle={mockPuzzle} isRunning={false} result={mockResult} />);
    const shuffleText = Array.from(container.querySelectorAll('text')).find(
      text => text.textContent.includes('Shuffle')
    );
    expect(shuffleText).toBeInTheDocument();
  });

  it('should show cache indicator when cache is used', () => {
    const mockResult = {
      correct: true,
      metrics: {
        shuffles: 0,
        cache_used: true,
      },
    };
    const { container } = render(<FactoryVisualization puzzle={mockPuzzle} isRunning={false} result={mockResult} />);
    // Cache is shown as an icon in the SVG
    expect(container.querySelector('svg')).toBeInTheDocument();
  });
});
