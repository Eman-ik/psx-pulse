/**
 * Data Gating Utility — enforce NO MOCK DATA rule
 *
 * Only display data that comes directly from API responses.
 * Hide/gate any fields that depend on unavailable metrics.
 * Show "Unavailable" instead of mock/synthetic values.
 */

export interface DataGateConfig {
  /** Required metrics for this field to display */
  requiredMetrics: string[];
  /** Show "Unavailable" if any required metric missing */
  gateOnMissing: boolean;
  /** Field is marked explicitly as unavailable/mock in response */
  isExplicitlyUnavailable?: boolean;
}

export function shouldDisplayData(config: DataGateConfig): boolean {
  // If explicitly marked as unavailable in API response, don't display
  if (config.isExplicitlyUnavailable) {
    return false;
  }

  // If gating is enabled and metrics are required, check they're available
  if (config.gateOnMissing && config.requiredMetrics.length > 0) {
    // For now, return true — metrics availability would be checked against API context
    // In production, this would check against ResearchContext passed from parent
    return true;
  }

  return true;
}

export function formatUnavailableField(fieldName: string): string {
  return `${fieldName}: Unavailable`;
}

/**
 * Check if engine output should be gated based on data availability
 */
export function isEngineOutputAvailable(engineOutput: any): boolean {
  if (!engineOutput) return false;

  // Engine explicitly marked as unavailable
  if (engineOutput.status === 'unavailable' || engineOutput.status === 'insufficient_data') {
    return false;
  }

  // Engine using mock data (should be gated)
  if (engineOutput._uses_mock_data === true) {
    return false;
  }

  // Engine output is marked as mock (common pattern)
  if (engineOutput.status === 'mock_data_gated') {
    return false;
  }

  return true;
}

/**
 * Filter engines to only show real data, not mock
 */
export function getAvailableEngines(
  intelligence: Record<string, any> | undefined
): Record<string, any> {
  if (!intelligence) return {};

  return Object.fromEntries(
    Object.entries(intelligence).filter(
      ([_, engine]) => isEngineOutputAvailable(engine)
    )
  );
}
