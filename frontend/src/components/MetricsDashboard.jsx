import './MetricsDashboard.css';

export default function MetricsDashboard({ stage1Metrics, finalMetrics }) {
  if (!stage1Metrics && !finalMetrics) return null;

  const metrics = finalMetrics || {};
  const perModel = metrics.per_model || {};
  const totalCost = metrics.total_cost_usd || 0;
  const totalTokens = metrics.total_tokens || { input: 0, output: 0 };
  const totalLatency = metrics.total_latency_ms || 0;

  // Merge stage1 metrics into per-model if final metrics not available yet
  const displayModels = Object.keys(perModel).length > 0
    ? perModel
    : (stage1Metrics || {});

  if (Object.keys(displayModels).length === 0) return null;

  return (
    <div className="metrics-dashboard">
      <h4 className="metrics-title">Cost & Performance</h4>

      {/* Summary bar */}
      <div className="metrics-summary">
        <div className="metric-chip">
          <span className="metric-label">Total Cost</span>
          <span className="metric-value">${totalCost.toFixed(4)}</span>
        </div>
        <div className="metric-chip">
          <span className="metric-label">Tokens</span>
          <span className="metric-value">
            {(totalTokens.input + totalTokens.output).toLocaleString()}
          </span>
        </div>
        <div className="metric-chip">
          <span className="metric-label">Total Latency</span>
          <span className="metric-value">{(totalLatency / 1000).toFixed(1)}s</span>
        </div>
      </div>

      {/* Per-model breakdown */}
      <div className="metrics-table">
        <div className="metrics-row metrics-header-row">
          <span className="metrics-col model-col">Model</span>
          <span className="metrics-col">Calls</span>
          <span className="metrics-col">In Tokens</span>
          <span className="metrics-col">Out Tokens</span>
          <span className="metrics-col">Cost</span>
          <span className="metrics-col">Latency</span>
        </div>
        {Object.entries(displayModels).map(([model, m]) => (
          <div key={model} className="metrics-row">
            <span className="metrics-col model-col">
              {model.split('/')[1] || model}
            </span>
            <span className="metrics-col">{m.calls || 1}</span>
            <span className="metrics-col">{(m.tokens?.input || 0).toLocaleString()}</span>
            <span className="metrics-col">{(m.tokens?.output || 0).toLocaleString()}</span>
            <span className="metrics-col">${(m.cost_usd || 0).toFixed(4)}</span>
            <span className="metrics-col">{((m.latency_ms || 0) / 1000).toFixed(1)}s</span>
          </div>
        ))}
      </div>
    </div>
  );
}
