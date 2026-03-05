import { useState } from 'react';
import './PromptRefinement.css';

export default function PromptRefinement({ query, refinementData, onFinalize, onSkip }) {
  const [answers, setAnswers] = useState({});
  const [roles, setRoles] = useState(refinementData?.suggested_roles || {});

  if (!refinementData) return null;

  const { query_type, questions, suggested_roles } = refinementData;

  const handleAnswer = (question, value) => {
    setAnswers((prev) => ({ ...prev, [question]: value }));
  };

  const handleRoleChange = (model, role) => {
    setRoles((prev) => ({ ...prev, [model]: role }));
  };

  const handleSend = () => {
    onFinalize(answers, roles);
  };

  return (
    <div className="refinement-panel">
      <div className="refinement-header">
        <span className="refinement-type">Query type: <strong>{query_type}</strong></span>
        <button className="skip-btn" onClick={onSkip}>Skip &rarr; Send directly</button>
      </div>

      <div className="refinement-questions">
        <p className="refinement-hint">Answer these to get a better response from the council:</p>
        {questions.map((q, i) => (
          <div key={i} className="question-row">
            <label>{q}</label>
            <input
              type="text"
              placeholder="Your answer..."
              value={answers[q] || ''}
              onChange={(e) => handleAnswer(q, e.target.value)}
            />
          </div>
        ))}
      </div>

      <div className="refinement-roles">
        <p className="refinement-hint">Auto-assigned expert roles:</p>
        {Object.entries(roles).map(([model, role]) => (
          <div key={model} className="role-row-mini">
            <span className="role-model-mini">{model.split('/')[1]}</span>
            <input
              type="text"
              value={role}
              onChange={(e) => handleRoleChange(model, e.target.value)}
            />
          </div>
        ))}
      </div>

      <button className="send-council-btn" onClick={handleSend}>
        Send to Council
      </button>
    </div>
  );
}
