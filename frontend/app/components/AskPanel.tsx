"""Ask Panel — User interface for research queries.

Allows users to:
1. Enter a ticker symbol
2. Select analysis mode (quick/deep/forecast)
3. Submit research request
4. View snapshot, analysis, and decision results
"""

'use client';

import { useState } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  CircularProgress,
  FormControl,
  FormHelperText,
  Grid,
  InputLabel,
  MenuItem,
  Select,
  Stack,
  Tab,
  Tabs,
  TextField,
  Typography,
  Alert,
  Chip,
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  CheckCircle,
  AlertCircle,
  Info,
} from 'lucide-react';

interface SnapshotData {
  ticker: string;
  company_name?: string;
  current_price: number;
  market_cap_bracket: string;
  sentiment: string;
  confidence_score: number;
  data_freshness_days: number;
  data: Record<string, unknown>;
}

interface AnalysisData {
  ticker: string;
  overall_thesis: string;
  confidence: number;
  investment_rating: string;
  bull_case: string;
  bear_case: string;
  key_catalysts: string[];
  key_risks: string[];
  tokens_used: number;
  time_horizon: string;
}

interface DecisionData {
  ticker: string;
  recommendation: string;
  confidence_pct: number;
  conviction_level: string;
  suggested_entry_price: number;
  target_exit_price: number;
  stop_loss_price: number;
  position_size_pct: number;
  position_size_category: string;
  suggested_quantity?: number;
  expected_return_pct: number;
  key_upside_catalysts: string[];
  key_downside_risks: string[];
  time_horizon: string;
  bull_case: { target_price: number; upside_pct: number; probability_pct: number };
  base_case: { target_price: number; upside_pct: number; probability_pct: number };
  bear_case: { target_price: number; upside_pct: number; probability_pct: number };
}

interface FlowResponse {
  ticker: string;
  snapshot: SnapshotData;
  analysis: AnalysisData;
  decision: DecisionData;
  flow_status: 'complete' | 'partial' | 'failed';
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`research-tabpanel-${index}`}
      aria-labelledby={`research-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 2 }}>{children}</Box>}
    </div>
  );
}

export default function AskPanel() {
  const [ticker, setTicker] = useState('FFC');
  const [mode, setMode] = useState('quick');
  const [portfolioSize, setPortfolioSize] = useState(100);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<FlowResponse | null>(null);
  const [tabValue, setTabValue] = useState(0);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `http://localhost:8000/api/research/${ticker.toUpperCase()}/unified-flow?analysis_mode=${mode}&portfolio_size_thousands=${portfolioSize}`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        throw new Error(`API Error: ${response.status} ${response.statusText}`);
      }

      const data: FlowResponse = await response.json();
      setResult(data);
      setTabValue(0);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error occurred');
    } finally {
      setLoading(false);
    }
  };

  const getRecommendationColor = (recommendation: string) => {
    switch (recommendation) {
      case 'Strong Buy':
        return 'success';
      case 'Buy':
        return 'info';
      case 'Hold':
        return 'warning';
      case 'Sell':
        return 'error';
      case 'Strong Sell':
        return 'error';
      default:
        return 'default';
    }
  };

  const getThesisIcon = (thesis: string) => {
    if (thesis.includes('Bullish')) return <TrendingUp className="text-green-600" />;
    if (thesis.includes('Bearish'))
      return <TrendingDown className="text-red-600" />;
    return <Info className="text-blue-600" />;
  };

  return (
    <Box sx={{ width: '100%', maxWidth: 1200, mx: 'auto', p: 2 }}>
      <Stack spacing={3}>
        {/* Input Section */}
        <Card>
          <CardContent>
            <Typography variant="h5" gutterBottom>
              📊 Investment Research
            </Typography>
            <Typography variant="body2" color="textSecondary" gutterBottom>
              Enter a ticker to analyze with PSX Pulse LLM integration
            </Typography>

            <Box component="form" onSubmit={handleSubmit} sx={{ mt: 3 }}>
              <Stack spacing={2}>
                <Grid container spacing={2}>
                  <Grid item xs={12} sm={6}>
                    <TextField
                      fullWidth
                      label="Ticker Symbol"
                      value={ticker}
                      onChange={(e) => setTicker(e.target.value.toUpperCase())}
                      placeholder="e.g., FFC, EFERT"
                      disabled={loading}
                    />
                  </Grid>

                  <Grid item xs={12} sm={3}>
                    <FormControl fullWidth disabled={loading}>
                      <InputLabel>Analysis Mode</InputLabel>
                      <Select
                        value={mode}
                        label="Analysis Mode"
                        onChange={(e) => setMode(e.target.value)}
                      >
                        <MenuItem value="quick">Quick (3-5 signals)</MenuItem>
                        <MenuItem value="deep">Deep (multi-angle)</MenuItem>
                        <MenuItem value="forecast">Forecast (targets)</MenuItem>
                      </Select>
                      <FormHelperText>
                        Processing depth
                      </FormHelperText>
                    </FormControl>
                  </Grid>

                  <Grid item xs={12} sm={3}>
                    <TextField
                      fullWidth
                      type="number"
                      label="Portfolio (K PKR)"
                      value={portfolioSize}
                      onChange={(e) =>
                        setPortfolioSize(parseInt(e.target.value) || 100)
                      }
                      disabled={loading}
                      helperText="For position sizing"
                    />
                  </Grid>
                </Grid>

                {error && (
                  <Alert severity="error">
                    <AlertCircle className="inline mr-2" size={20} />
                    {error}
                  </Alert>
                )}

                <Button
                  variant="contained"
                  size="large"
                  type="submit"
                  disabled={loading || !ticker}
                  fullWidth
                  sx={{
                    py: 1.5,
                    background: loading
                      ? 'rgba(33, 150, 243, 0.5)'
                      : 'linear-gradient(135deg, #2196F3 0%, #1976D2 100%)',
                  }}
                >
                  {loading ? (
                    <>
                      <CircularProgress size={20} sx={{ mr: 1 }} />
                      Analyzing...
                    </>
                  ) : (
                    '🔍 Analyze'
                  )}
                </Button>
              </Stack>
            </Box>
          </CardContent>
        </Card>

        {/* Results Section */}
        {result && (
          <>
            <Card>
              <CardContent>
                <Stack direction="row" spacing={2} alignItems="center" sx={{ mb: 2 }}>
                  <Typography variant="h6">
                    {result.snapshot?.company_name || result.ticker}
                  </Typography>
                  {result.flow_status === 'complete' && (
                    <Chip
                      icon={<CheckCircle size={16} />}
                      label="Complete"
                      color="success"
                      variant="outlined"
                      size="small"
                    />
                  )}
                  {result.flow_status === 'partial' && (
                    <Chip
                      icon={<AlertCircle size={16} />}
                      label="Partial"
                      color="warning"
                      variant="outlined"
                      size="small"
                    />
                  )}
                </Stack>

                <Tabs
                  value={tabValue}
                  onChange={(_, value) => setTabValue(value)}
                  aria-label="research tabs"
                >
                  <Tab label="📈 Snapshot" id="research-tab-0" />
                  <Tab label="🧠 Analysis" id="research-tab-1" />
                  <Tab label="💰 Decision" id="research-tab-2" />
                </Tabs>

                {/* Snapshot Tab */}
                <TabPanel value={tabValue} index={0}>
                  <Stack spacing={2}>
                    <Grid container spacing={2}>
                      <Grid item xs={6} sm={3}>
                        <Box>
                          <Typography variant="body2" color="textSecondary">
                            Current Price
                          </Typography>
                          <Typography variant="h6">
                            ₨{result.snapshot?.current_price?.toFixed(2)}
                          </Typography>
                        </Box>
                      </Grid>

                      <Grid item xs={6} sm={3}>
                        <Box>
                          <Typography variant="body2" color="textSecondary">
                            Market Cap
                          </Typography>
                          <Typography variant="h6">
                            {result.snapshot?.market_cap_bracket}
                          </Typography>
                        </Box>
                      </Grid>

                      <Grid item xs={6} sm={3}>
                        <Box>
                          <Typography variant="body2" color="textSecondary">
                            Sentiment
                          </Typography>
                          <Chip
                            label={result.snapshot?.sentiment}
                            color={
                              result.snapshot?.sentiment === 'positive'
                                ? 'success'
                                : result.snapshot?.sentiment === 'negative'
                                  ? 'error'
                                  : 'default'
                            }
                            size="small"
                          />
                        </Box>
                      </Grid>

                      <Grid item xs={6} sm={3}>
                        <Box>
                          <Typography variant="body2" color="textSecondary">
                            Confidence
                          </Typography>
                          <Typography variant="h6">
                            {result.snapshot?.confidence_score?.toFixed(0)}%
                          </Typography>
                        </Box>
                      </Grid>
                    </Grid>
                  </Stack>
                </TabPanel>

                {/* Analysis Tab */}
                <TabPanel value={tabValue} index={1}>
                  <Stack spacing={2}>
                    <Box
                      sx={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: 2,
                        p: 2,
                        bgcolor: 'background.paper',
                        borderRadius: 1,
                        border: '1px solid',
                        borderColor: 'divider',
                      }}
                    >
                      {getThesisIcon(result.analysis?.overall_thesis)}
                      <Box flex={1}>
                        <Typography variant="body2" color="textSecondary">
                          Thesis
                        </Typography>
                        <Typography variant="h6">
                          {result.analysis?.overall_thesis}
                        </Typography>
                      </Box>
                      <Chip
                        label={`${result.analysis?.confidence?.toFixed(0)}%`}
                        color={
                          result.analysis?.confidence >= 75
                            ? 'success'
                            : result.analysis?.confidence >= 50
                              ? 'warning'
                              : 'default'
                        }
                      />
                    </Box>

                    <Grid container spacing={2}>
                      <Grid item xs={12} sm={6}>
                        <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
                          ✅ Bull Case
                        </Typography>
                        <Typography variant="body2">
                          {result.analysis?.bull_case}
                        </Typography>
                      </Grid>

                      <Grid item xs={12} sm={6}>
                        <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
                          ⚠️ Bear Case
                        </Typography>
                        <Typography variant="body2">
                          {result.analysis?.bear_case}
                        </Typography>
                      </Grid>
                    </Grid>

                    {result.analysis?.key_catalysts && result.analysis.key_catalysts.length > 0 && (
                      <Box>
                        <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
                          Catalysts
                        </Typography>
                        <Stack direction="row" spacing={1} flexWrap="wrap">
                          {result.analysis.key_catalysts.map((catalyst, i) => (
                            <Chip
                              key={i}
                              label={catalyst}
                              variant="outlined"
                              size="small"
                            />
                          ))}
                        </Stack>
                      </Box>
                    )}

                    {result.analysis?.key_risks && result.analysis.key_risks.length > 0 && (
                      <Box>
                        <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 1 }}>
                          Risks
                        </Typography>
                        <Stack direction="row" spacing={1} flexWrap="wrap">
                          {result.analysis.key_risks.map((risk, i) => (
                            <Chip
                              key={i}
                              label={risk}
                              variant="outlined"
                              size="small"
                              color="error"
                            />
                          ))}
                        </Stack>
                      </Box>
                    )}
                  </Stack>
                </TabPanel>

                {/* Decision Tab */}
                <TabPanel value={tabValue} index={2}>
                  <Stack spacing={2}>
                    <Box
                      sx={{
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'space-between',
                        p: 2,
                        bgcolor: 'background.paper',
                        borderRadius: 1,
                        border: '2px solid',
                        borderColor:
                          getRecommendationColor(result.decision?.recommendation) ===
                          'success'
                            ? '#4caf50'
                            : getRecommendationColor(result.decision?.recommendation) ===
                                'error'
                              ? '#f44336'
                              : '#2196f3',
                      }}
                    >
                      <Box>
                        <Typography variant="body2" color="textSecondary">
                          Recommendation
                        </Typography>
                        <Typography variant="h6">
                          {result.decision?.recommendation}
                        </Typography>
                        <Typography variant="caption" color="textSecondary">
                          {result.decision?.conviction_level} Conviction
                        </Typography>
                      </Box>
                      <Chip
                        label={`${result.decision?.confidence_pct?.toFixed(0)}%`}
                        color={getRecommendationColor(result.decision?.recommendation) as any}
                        variant="filled"
                      />
                    </Box>

                    <Grid container spacing={2}>
                      <Grid item xs={6} sm={3}>
                        <Box>
                          <Typography variant="caption" color="textSecondary">
                            Entry Price
                          </Typography>
                          <Typography variant="body1" sx={{ fontWeight: 600 }}>
                            ₨{result.decision?.suggested_entry_price?.toFixed(2)}
                          </Typography>
                        </Box>
                      </Grid>

                      <Grid item xs={6} sm={3}>
                        <Box>
                          <Typography variant="caption" color="textSecondary">
                            Exit Target
                          </Typography>
                          <Typography variant="body1" sx={{ fontWeight: 600 }}>
                            ₨{result.decision?.target_exit_price?.toFixed(2)}
                          </Typography>
                        </Box>
                      </Grid>

                      <Grid item xs={6} sm={3}>
                        <Box>
                          <Typography variant="caption" color="textSecondary">
                            Stop Loss
                          </Typography>
                          <Typography
                            variant="body1"
                            sx={{ fontWeight: 600, color: '#f44336' }}
                          >
                            ₨{result.decision?.stop_loss_price?.toFixed(2)}
                          </Typography>
                        </Box>
                      </Grid>

                      <Grid item xs={6} sm={3}>
                        <Box>
                          <Typography variant="caption" color="textSecondary">
                            Position Size
                          </Typography>
                          <Typography variant="body1" sx={{ fontWeight: 600 }}>
                            {result.decision?.position_size_pct?.toFixed(1)}%
                          </Typography>
                        </Box>
                      </Grid>
                    </Grid>

                    <Box
                      sx={{
                        display: 'grid',
                        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                        gap: 2,
                      }}
                    >
                      <Box sx={{ p: 2, bgcolor: '#f5f5f5', borderRadius: 1 }}>
                        <Typography variant="caption" color="textSecondary">
                          🚀 Bull Case
                        </Typography>
                        <Typography variant="h6" sx={{ color: '#4caf50' }}>
                          ₨{result.decision?.bull_case?.target_price?.toFixed(2)}
                        </Typography>
                        <Typography variant="caption">
                          +{result.decision?.bull_case?.upside_pct?.toFixed(1)}% ({result.decision?.bull_case?.probability_pct?.toFixed(0)}% prob)
                        </Typography>
                      </Box>

                      <Box sx={{ p: 2, bgcolor: '#f5f5f5', borderRadius: 1 }}>
                        <Typography variant="caption" color="textSecondary">
                          📊 Base Case
                        </Typography>
                        <Typography variant="h6">
                          ₨{result.decision?.base_case?.target_price?.toFixed(2)}
                        </Typography>
                        <Typography variant="caption">
                          +{result.decision?.base_case?.upside_pct?.toFixed(1)}% ({result.decision?.base_case?.probability_pct?.toFixed(0)}% prob)
                        </Typography>
                      </Box>

                      <Box sx={{ p: 2, bgcolor: '#f5f5f5', borderRadius: 1 }}>
                        <Typography variant="caption" color="textSecondary">
                          📉 Bear Case
                        </Typography>
                        <Typography variant="h6" sx={{ color: '#f44336' }}>
                          ₨{result.decision?.bear_case?.target_price?.toFixed(2)}
                        </Typography>
                        <Typography variant="caption">
                          {result.decision?.bear_case?.upside_pct?.toFixed(1)}% ({result.decision?.bear_case?.probability_pct?.toFixed(0)}% prob)
                        </Typography>
                      </Box>
                    </Box>

                    <Box sx={{ p: 2, bgcolor: '#e3f2fd', borderRadius: 1 }}>
                      <Typography variant="body2" sx={{ fontWeight: 600 }}>
                        Expected Return: {result.decision?.expected_return_pct?.toFixed(1)}%
                      </Typography>
                      <Typography variant="caption" color="textSecondary">
                        Probability-weighted across scenarios
                      </Typography>
                    </Box>
                  </Stack>
                </TabPanel>
              </CardContent>
            </Card>

            {/* Disclaimer */}
            <Alert severity="info">
              ℹ️ This analysis is generated by Claude LLM based on structured evidence.
              Not a financial recommendation. Do your own research before investing.
            </Alert>
          </>
        )}
      </Stack>
    </Box>
  );
}
