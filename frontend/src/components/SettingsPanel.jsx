import { useState, useEffect } from 'react';
import { api } from '../api';
import './SettingsPanel.css';

const ROLE_PRESETS = [
  '',
  'Security Expert',
  'UX Designer',
  'Backend Engineer',
  'Data Scientist',
  'Product Manager',
  'DevOps Engineer',
  'Technical Writer',
  'Performance Engineer',
  'Architect',
];

export default function SettingsPanel({ isOpen, onClose }) {
  const [settings, setSettings] = useState(null);
  const [availableModels, setAvailableModels] = useState([]);
  const [saving, setSaving] = useState(false);
  const [dirty, setDirty] = useState(false);

  useEffect(() => {
    if (isOpen) loadSettings();
  }, [isOpen]);

  const loadSettings = async () => {
    try {
      const data = await api.getSettings();
      setSettings({
        council_models: data.council_models || [],
        chairman_model: data.chairman_model || '',
        roles: data.roles || {},
        consensus: data.consensus || { max_rounds: 5, unanimous_rounds: 3 },
      });
      setAvailableModels(data.available_models || []);
      setDirty(false);
    } catch (e) {
      console.error('Failed to load settings:', e);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await api.updateSettings(settings);
      setDirty(false);
    } catch (e) {
      console.error('Failed to save settings:', e);
    }
    setSaving(false);
  };

  const toggleModel = (modelId) => {
    setSettings((prev) => {
      const models = prev.council_models.includes(modelId)
        ? prev.council_models.filter((m) => m !== modelId)
        : [...prev.council_models, modelId];
      setDirty(true);
      return { ...prev, council_models: models };
    });
  };

  const setChairman = (modelId) => {
    setSettings((prev) => {
      setDirty(true);
      return { ...prev, chairman_model: modelId };
    });
  };

  const setRole = (modelId, role) => {
    setSettings((prev) => {
      const roles = { ...prev.roles };
      if (role) {
        roles[modelId] = role;
      } else {
        delete roles[modelId];
      }
      setDirty(true);
      return { ...prev, roles };
    });
  };

  const setConsensusField = (field, value) => {
    setSettings((prev) => {
      setDirty(true);
      return { ...prev, consensus: { ...prev.consensus, [field]: parseInt(value) || 0 } };
    });
  };

  if (!isOpen || !settings) return null;

  return (
    <div className="settings-overlay" onClick={onClose}>
      <div className="settings-panel" onClick={(e) => e.stopPropagation()}>
        <div className="settings-header">
          <h2>Council Settings</h2>
          <button className="close-btn" onClick={onClose}>x</button>
        </div>

        <div className="settings-body">
          {/* Council Models */}
          <section className="settings-section">
            <h3>Council Members</h3>
            <p className="settings-hint">Select which models participate in the council</p>
            <div className="model-grid">
              {availableModels.map((m) => (
                <label key={m.id} className={`model-card ${settings.council_models.includes(m.id) ? 'selected' : ''}`}>
                  <input
                    type="checkbox"
                    checked={settings.council_models.includes(m.id)}
                    onChange={() => toggleModel(m.id)}
                  />
                  <div className="model-info">
                    <span className="model-card-name">{m.name}</span>
                    <span className="model-card-provider">{m.provider}</span>
                  </div>
                </label>
              ))}
            </div>
          </section>

          {/* Chairman */}
          <section className="settings-section">
            <h3>Chairman Model</h3>
            <p className="settings-hint">Synthesizes the final answer or breaks ties</p>
            <select
              value={settings.chairman_model}
              onChange={(e) => setChairman(e.target.value)}
              className="settings-select"
            >
              {availableModels.map((m) => (
                <option key={m.id} value={m.id}>{m.name} ({m.provider})</option>
              ))}
            </select>
          </section>

          {/* Expert Roles */}
          <section className="settings-section">
            <h3>Expert Roles</h3>
            <p className="settings-hint">Assign a perspective to each council member</p>
            <div className="roles-list">
              {settings.council_models.map((modelId) => {
                const model = availableModels.find((m) => m.id === modelId);
                const name = model ? model.name : modelId.split('/')[1];
                return (
                  <div key={modelId} className="role-row">
                    <span className="role-model-name">{name}</span>
                    <select
                      value={settings.roles[modelId] || ''}
                      onChange={(e) => setRole(modelId, e.target.value)}
                      className="role-select"
                    >
                      {ROLE_PRESETS.map((r) => (
                        <option key={r} value={r}>{r || '(no role)'}</option>
                      ))}
                    </select>
                    <input
                      type="text"
                      placeholder="Or type custom role..."
                      value={ROLE_PRESETS.includes(settings.roles[modelId] || '') ? '' : (settings.roles[modelId] || '')}
                      onChange={(e) => setRole(modelId, e.target.value)}
                      className="role-custom"
                    />
                  </div>
                );
              })}
            </div>
          </section>

          {/* Consensus Config */}
          <section className="settings-section">
            <h3>Consensus Rules</h3>
            <div className="consensus-fields">
              <div className="consensus-field">
                <label>Max Rounds</label>
                <input
                  type="number"
                  min="1"
                  max="10"
                  value={settings.consensus.max_rounds}
                  onChange={(e) => setConsensusField('max_rounds', e.target.value)}
                  className="consensus-input"
                />
              </div>
              <div className="consensus-field">
                <label>Unanimous Rounds</label>
                <input
                  type="number"
                  min="1"
                  max={settings.consensus.max_rounds}
                  value={settings.consensus.unanimous_rounds}
                  onChange={(e) => setConsensusField('unanimous_rounds', e.target.value)}
                  className="consensus-input"
                />
                <span className="field-hint">First N rounds require unanimous; rest need 2/3</span>
              </div>
            </div>
          </section>
        </div>

        <div className="settings-footer">
          <button className="cancel-btn" onClick={onClose}>Cancel</button>
          <button
            className="save-btn"
            onClick={handleSave}
            disabled={!dirty || saving}
          >
            {saving ? 'Saving...' : 'Save Settings'}
          </button>
        </div>
      </div>
    </div>
  );
}
