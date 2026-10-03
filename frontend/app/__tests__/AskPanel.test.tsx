/**
 * Step 12: Frontend Ask Panel tests
 *
 * Tests for the investment research query interface:
 * - Input validation
 * - API integration
 * - Result display
 * - Tab navigation
 * - Error handling
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import AskPanel from '@/app/components/AskPanel';
import '@testing-library/jest-dom';

// Mock fetch
global.fetch = jest.fn();

const mockFlowResponse = {
  ticker: 'FFC',
  snapshot: {
    ticker: 'FFC',
    company_name: 'Fauji Fertilizer',
    current_price: 305.5,
    market_cap_bracket: 'mid',
    sentiment: 'positive',
    confidence_score: 85,
    data_freshness_days: 0,
    data: {},
  },
  analysis: {
    ticker: 'FFC',
    overall_thesis: 'Bullish',
    confidence: 75,
    investment_rating: 'Buy',
    bull_case: 'Strong revenue growth and dividend increase',
    bear_case: 'Market volatility and economic slowdown risks',
    key_catalysts: ['Q4 earnings', 'Dividend announcement'],
    key_risks: ['Market correction', 'Input cost inflation'],
    tokens_used: 2500,
    time_horizon: '6-12 months',
  },
  decision: {
    ticker: 'FFC',
    recommendation: 'Buy',
    confidence_pct: 75,
    conviction_level: 'Medium',
    suggested_entry_price: 308.0,
    target_exit_price: 385.0,
    stop_loss_price: 277.2,
    position_size_pct: 4.0,
    position_size_category: 'Standard',
    suggested_quantity: 1305,
    expected_return_pct: 8.5,
    key_upside_catalysts: ['Q4 earnings'],
    key_downside_risks: ['Market correction'],
    time_horizon: '6-12 months',
    bull_case: {
      target_price: 385,
      upside_pct: 25,
      probability_pct: 40,
    },
    base_case: {
      target_price: 321.4,
      upside_pct: 5,
      probability_pct: 35,
    },
    bear_case: {
      target_price: 259.25,
      upside_pct: -15,
      probability_pct: 25,
    },
  },
  flow_status: 'complete' as const,
};

describe('AskPanel Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders input form', () => {
    render(<AskPanel />);

    expect(screen.getByDisplayValue('FFC')).toBeInTheDocument();
    expect(screen.getByLabelText('Analysis Mode')).toBeInTheDocument();
    expect(screen.getByLabelText('Portfolio (K PKR)')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Analyze/i })).toBeInTheDocument();
  });

  test('submits form with correct data', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockFlowResponse,
    });

    render(<AskPanel />);

    const analyzeButton = screen.getByRole('button', { name: /Analyze/i });
    await userEvent.click(analyzeButton);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('FFC'),
        expect.any(Object)
      );
    });
  });

  test('changes ticker input', async () => {
    render(<AskPanel />);

    const tickerInput = screen.getByDisplayValue('FFC') as HTMLInputElement;
    await userEvent.clear(tickerInput);
    await userEvent.type(tickerInput, 'EFERT');

    expect(tickerInput.value).toBe('EFERT');
  });

  test('changes analysis mode', async () => {
    render(<AskPanel />);

    const modeSelect = screen.getByLabelText('Analysis Mode');
    await userEvent.click(modeSelect);

    const deepOption = screen.getByText('Deep (multi-angle)');
    await userEvent.click(deepOption);

    expect(modeSelect).toHaveTextContent('Deep');
  });

  test('displays results after successful submission', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockFlowResponse,
    });

    render(<AskPanel />);

    const analyzeButton = screen.getByRole('button', { name: /Analyze/i });
    await userEvent.click(analyzeButton);

    await waitFor(() => {
      expect(screen.getByText('Fauji Fertilizer')).toBeInTheDocument();
    });

    expect(screen.getByText('Bullish')).toBeInTheDocument();
    expect(screen.getByText('Buy')).toBeInTheDocument();
  });

  test('displays snapshot data', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockFlowResponse,
    });

    render(<AskPanel />);

    const analyzeButton = screen.getByRole('button', { name: /Analyze/i });
    await userEvent.click(analyzeButton);

    await waitFor(() => {
      expect(screen.getByText('Snapshot')).toBeInTheDocument();
    });

    expect(screen.getByText('Current Price')).toBeInTheDocument();
    expect(screen.getByText('305.50')).toBeInTheDocument();
  });

  test('displays analysis data', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockFlowResponse,
    });

    render(<AskPanel />);

    const analyzeButton = screen.getByRole('button', { name: /Analyze/i });
    await userEvent.click(analyzeButton);

    await waitFor(() => {
      expect(screen.getByText('Analysis')).toBeInTheDocument();
    });

    const analysisTab = screen.getByRole('tab', { name: /Analysis/ });
    await userEvent.click(analysisTab);

    expect(
      screen.getByText('Strong revenue growth and dividend increase')
    ).toBeInTheDocument();
  });

  test('displays decision data', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockFlowResponse,
    });

    render(<AskPanel />);

    const analyzeButton = screen.getByRole('button', { name: /Analyze/i });
    await userEvent.click(analyzeButton);

    await waitFor(() => {
      expect(screen.getByText('Decision')).toBeInTheDocument();
    });

    const decisionTab = screen.getByRole('tab', { name: /Decision/ });
    await userEvent.click(decisionTab);

    expect(screen.getByText('Entry Price')).toBeInTheDocument();
    expect(screen.getByText('308.00')).toBeInTheDocument();
    expect(screen.getByText('Exit Target')).toBeInTheDocument();
  });

  test('displays scenarios in decision tab', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockFlowResponse,
    });

    render(<AskPanel />);

    const analyzeButton = screen.getByRole('button', { name: /Analyze/i });
    await userEvent.click(analyzeButton);

    await waitFor(() => {
      const decisionTab = screen.getByRole('tab', { name: /Decision/ });
      expect(decisionTab).toBeInTheDocument();
    });

    const decisionTab = screen.getByRole('tab', { name: /Decision/ });
    await userEvent.click(decisionTab);

    expect(screen.getByText('Bull Case')).toBeInTheDocument();
    expect(screen.getByText('Base Case')).toBeInTheDocument();
    expect(screen.getByText('Bear Case')).toBeInTheDocument();
  });

  test('handles API error', async () => {
    (global.fetch as jest.Mock).mockRejectedValueOnce(new Error('API Error'));

    render(<AskPanel />);

    const analyzeButton = screen.getByRole('button', { name: /Analyze/i });
    await userEvent.click(analyzeButton);

    await waitFor(() => {
      expect(screen.getByText(/API Error/i)).toBeInTheDocument();
    });
  });

  test('handles 404 not found', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: false,
      status: 404,
      statusText: 'Not Found',
    });

    render(<AskPanel />);

    const analyzeButton = screen.getByRole('button', { name: /Analyze/i });
    await userEvent.click(analyzeButton);

    await waitFor(() => {
      expect(screen.getByText(/404/i)).toBeInTheDocument();
    });
  });

  test('disables submit button while loading', async () => {
    (global.fetch as jest.Mock).mockImplementationOnce(
      () =>
        new Promise((resolve) =>
          setTimeout(
            () => resolve({ ok: true, json: async () => mockFlowResponse }),
            100
          )
        )
    );

    render(<AskPanel />);

    const analyzeButton = screen.getByRole('button', { name: /Analyze/i });
    await userEvent.click(analyzeButton);

    // Button should be disabled during loading
    expect(analyzeButton).toBeDisabled();

    await waitFor(() => {
      expect(analyzeButton).not.toBeDisabled();
    });
  });

  test('tabs navigate between snapshot, analysis, and decision', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockFlowResponse,
    });

    render(<AskPanel />);

    const analyzeButton = screen.getByRole('button', { name: /Analyze/i });
    await userEvent.click(analyzeButton);

    await waitFor(() => {
      expect(screen.getByText('Snapshot')).toBeInTheDocument();
    });

    // Check Snapshot tab
    let snapshotTab = screen.getByRole('tab', { name: /Snapshot/ });
    expect(snapshotTab).toHaveAttribute('aria-selected', 'true');

    // Click Analysis tab
    const analysisTab = screen.getByRole('tab', { name: /Analysis/ });
    await userEvent.click(analysisTab);
    expect(analysisTab).toHaveAttribute('aria-selected', 'true');

    // Click Decision tab
    const decisionTab = screen.getByRole('tab', { name: /Decision/ });
    await userEvent.click(decisionTab);
    expect(decisionTab).toHaveAttribute('aria-selected', 'true');
  });

  test('displays confidence percentage correctly', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockFlowResponse,
    });

    render(<AskPanel />);

    const analyzeButton = screen.getByRole('button', { name: /Analyze/i });
    await userEvent.click(analyzeButton);

    await waitFor(() => {
      expect(screen.getByText('75%')).toBeInTheDocument();
    });
  });

  test('displays recommendation with correct styling', async () => {
    (global.fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => mockFlowResponse,
    });

    render(<AskPanel />);

    const analyzeButton = screen.getByRole('button', { name: /Analyze/i });
    await userEvent.click(analyzeButton);

    await waitFor(() => {
      const decisionTab = screen.getByRole('tab', { name: /Decision/ });
      expect(decisionTab).toBeInTheDocument();
    });

    const decisionTab = screen.getByRole('tab', { name: /Decision/ });
    await userEvent.click(decisionTab);

    const buyRecommendation = screen.getByText('Buy');
    expect(buyRecommendation).toBeInTheDocument();
  });
});
