import ReactMarkdown from 'react-markdown';
import './Stage3.css';

export default function Stage3({ finalResponse, consensusType, finalRound, totalRounds }) {
  if (!finalResponse) {
    return null;
  }

  const typeLabels = {
    unanimous: 'Unanimous Consensus',
    majority: '2/3 Majority Consensus',
    chairman: "Chairman's Decision",
    error: 'Error',
  };

  const typeLabel = typeLabels[consensusType] || 'Final Answer';

  return (
    <div className="stage stage3">
      <h3 className="stage-title">Stage 3: Final Council Answer</h3>
      <div className="final-response">
        <div className="final-meta">
          <span className="chairman-label">
            Chairman: {finalResponse.model.split('/')[1] || finalResponse.model}
          </span>
          <span className={`consensus-type-badge ${consensusType || 'unknown'}`}>
            {typeLabel}
            {finalRound && ` (Round ${finalRound})`}
            {consensusType === 'chairman' && totalRounds && ` (after ${totalRounds} rounds)`}
          </span>
        </div>
        <div className="final-text markdown-content">
          <ReactMarkdown>{finalResponse.response}</ReactMarkdown>
        </div>
      </div>
    </div>
  );
}
