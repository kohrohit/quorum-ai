import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import './Stage2.css';

export default function Stage2({ rounds }) {
  const [activeRound, setActiveRound] = useState(null);
  const [activeModel, setActiveModel] = useState(0);

  if (!rounds || rounds.length === 0) {
    return null;
  }

  const selectedRound = activeRound !== null ? activeRound : rounds.length - 1;
  const round = rounds[selectedRound];

  return (
    <div className="stage stage2">
      <h3 className="stage-title">Stage 2: Consensus Deliberation</h3>

      {/* Round tabs */}
      <div className="round-tabs">
        {rounds.map((r, idx) => {
          const yesCount = r.votes?.filter(v => v.vote === 'YES').length || 0;
          const total = r.votes?.length || 0;
          return (
            <button
              key={idx}
              className={`round-tab ${selectedRound === idx ? 'active' : ''} ${r.consensus_reached ? 'consensus' : ''}`}
              onClick={() => { setActiveRound(idx); setActiveModel(0); }}
            >
              Round {r.round}
              <span className={`vote-badge ${r.consensus_reached ? 'agreed' : 'disagreed'}`}>
                {yesCount}/{total}
              </span>
            </button>
          );
        })}
      </div>

      {/* Round details */}
      <div className="round-details">
        <div className="round-header">
          <span className="threshold-label">
            Threshold: {round.threshold}
          </span>
          {round.consensus_reached && (
            <span className="consensus-badge">Consensus Reached</span>
          )}
        </div>

        {/* Model response tabs */}
        {round.responses && round.responses.length > 0 && (
          <>
            <h4 className="subsection-title">
              {round.round === 1 ? 'Initial Responses' : 'Revised Responses'}
            </h4>
            <div className="tabs">
              {round.responses.map((r, idx) => (
                <button
                  key={idx}
                  className={`tab ${activeModel === idx ? 'active' : ''}`}
                  onClick={() => setActiveModel(idx)}
                >
                  {r.model.split('/')[1] || r.model}
                </button>
              ))}
            </div>
            <div className="tab-content">
              <div className="ranking-content markdown-content">
                <ReactMarkdown>
                  {round.responses[activeModel]?.response || ''}
                </ReactMarkdown>
              </div>
            </div>
          </>
        )}

        {/* Votes */}
        {round.votes && round.votes.length > 0 && (
          <>
            <h4 className="subsection-title">Agreement Votes</h4>
            <div className="votes-grid">
              {round.votes.map((v, idx) => (
                <div key={idx} className={`vote-card ${v.vote === 'YES' ? 'vote-yes' : 'vote-no'}`}>
                  <div className="vote-model">{v.model.split('/')[1] || v.model}</div>
                  <div className="vote-result">{v.vote}</div>
                  {v.explanation && (
                    <div className="vote-explanation">{v.explanation}</div>
                  )}
                </div>
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  );
}
