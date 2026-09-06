import { useState } from 'react';
import { ThermalEvent } from '../../../types';

export function Advisory({ event }: { event: ThermalEvent }) {
  const [advisoryLang, setAdvisoryLang] = useState<'en' | 'hi'>('en');

  if (!event.advisory) return null;

  return (
    <div className="tab-content">
      <div className="section-card sitrep-card">
        <div className="section-card-header">
          <h4>📋 AI Situation Report (SitRep)</h4>
          <span className="card-badge-muted">INTELLIGENCE BRIEF</span>
        </div>
        <div className="sitrep-text">{event.advisory.situation_report}</div>
      </div>

      <div className="section-card">
        <div className="section-card-header">
          <h4>✅ Priority Action Directives</h4>
          <span className="card-badge-alert">{event.advisory.action_items?.length || 0} Directives</span>
        </div>
        <div className="action-items">
          {event.advisory.action_items?.map((item, i) => (
            <div className={`action-item priority-${item.priority?.toLowerCase()}`} key={i}>
              <span className="action-priority">{item.priority}</span>
              <div className="action-detail">
                <span className="action-text">{item.action}</span>
                <span className="action-responsible">Assigned: {item.responsible}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Bilingual Public Advisory with Language Selector */}
      <div className="section-card">
        <div className="section-card-header">
          <h4>📢 Public Safety Advisory</h4>
          <div className="lang-pill-group">
            <button
              className={`lang-pill ${advisoryLang === 'en' ? 'active' : ''}`}
              onClick={() => setAdvisoryLang('en')}
            >
              English (EN)
            </button>
            <button
              className={`lang-pill ${advisoryLang === 'hi' ? 'active' : ''}`}
              onClick={() => setAdvisoryLang('hi')}
            >
              हिन्दी (HI)
            </button>
          </div>
        </div>

        {advisoryLang === 'en' ? (
          <div className="advisory-text">{event.advisory.public_advisory_en}</div>
        ) : (
          <div className="advisory-text hindi-font">{event.advisory.public_advisory_hi}</div>
        )}
      </div>

      <div className="section-card">
        <div className="section-card-header">
          <h4>📱 Emergency SMS Broadcast Template</h4>
          <span className="card-badge-muted">160 CHARS</span>
        </div>
        <div className="sms-template">{event.advisory.sms_alert}</div>
      </div>

      <div className="section-card psych-guidance-card">
        <h4>🧠 Psychological First-Aid Guidance</h4>
        <div className="guidance-grid">
          <div className="guidance-section">
            <h5>For First Responders:</h5>
            <ul>{event.advisory.psych_guidance_responders?.map((g, i) => <li key={i}>{g}</li>)}</ul>
          </div>
          <div className="guidance-section">
            <h5>For Affected Families:</h5>
            <ul>{event.advisory.psych_guidance_families?.map((g, i) => <li key={i}>{g}</li>)}</ul>
          </div>
        </div>

        {event.advisory.psych_helplines?.length > 0 && (
          <div className="guidance-section helplines">
            <h5>📞 Emergency Crisis Support Lines:</h5>
            <div className="helpline-grid">
              {event.advisory.psych_helplines.map((h, i) => (
                <div className="helpline-row" key={i}>
                  <span>{h.name}</span>
                  <strong>{h.number}</strong>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
