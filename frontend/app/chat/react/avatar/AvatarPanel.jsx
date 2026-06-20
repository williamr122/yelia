'use client';

import React, { useLayoutEffect, useState } from 'react';
import { readStorage, writeStorage } from '../core/storage.js';
import ThreeAvatarCanvas from './ThreeAvatarCanvas.jsx';
import ConfettiOverlay from './ConfettiOverlay.jsx';

const STATE_LABELS = {
  idle: 'En reposo',
  thinking: 'YELIA esta respondiendo',
  listening: 'Escuchando tu voz',
  speaking: 'YELIA esta hablando',
  muted: 'Voz desactivada',
  error: 'Necesita revision',
};

export default function AvatarPanel({ state = 'idle', voiceEnabled, setVoiceEnabled }) {
  const [avatar, setAvatar] = useState('avatar_cat');
  const contract = typeof state === 'object' && state ? state : { state };
  const avatarState = STATE_LABELS[contract.state] ? contract.state : 'idle';
  const expression = contract.expression || contract.emotion || 'neutral';

  function change(value) {
    setAvatar(value);
    writeStorage('yelia_avatar', value);
  }

  useLayoutEffect(() => {
    setAvatar(readStorage('yelia_avatar', 'avatar_cat'));
  }, []);

  return (
    <aside className={`yelia-panel yelia-avatar-panel is-${avatarState}`}>
      <h2 className="yelia-section-title mb-2 d-flex align-items-center gap-2">
        Avatar
        {setVoiceEnabled && (
          <button 
            className="yelia-icon-button" 
            onClick={() => setVoiceEnabled(!voiceEnabled)} 
            type="button" 
            title={voiceEnabled ? "Silenciar voz" : "Activar voz"} 
            aria-label={voiceEnabled ? "Silenciar voz" : "Activar voz"}
            style={{ background: 'none', border: 'none', color: '#fff', cursor: 'pointer', padding: 0, display: 'inline-flex', alignItems: 'center' }}
          >
            <i className={`bi ${voiceEnabled ? 'bi-volume-up-fill' : 'bi-volume-mute-fill'}`} style={{ fontSize: '1.1rem' }}></i>
          </button>
        )}
        <span className={`yelia-avatar-state-indicator is-${avatarState}`} title={STATE_LABELS[avatarState]}>
          <i className="bi bi-circle-fill"></i>
        </span>
        <span className={`yelia-avatar-speaking-icon ${avatarState === 'speaking' ? '' : 'yelia-hidden'}`}><i className="bi bi-volume-up-fill"></i></span>
      </h2>
      <div className={`yelia-avatar-status-pill is-${avatarState}`}>
        <span></span>{STATE_LABELS[avatarState]}
      </div>
      <div className="mb-3">
        <label className="form-label yelia-label">Seleccionar avatar</label>
        <select className="form-select" value={avatar} onChange={(event) => change(event.target.value)}>
          <option value="avatar_cat">Gatito</option>
          <option value="avatar_dog">Perrito</option>
          <option value="avatar_owl">Buho</option>
        </select>
      </div>
      <div className={`yelia-avatar-placeholder yelia-avatar-state-${avatarState}`} style={{ position: 'relative' }}>
        <ThreeAvatarCanvas avatar={avatar} state={avatarState} expression={expression} />
        <ConfettiOverlay />
      </div>
      <div className="yelia-tts-captions" aria-live="polite" data-expression={expression} data-gesture={contract.gesture || 'none'}></div>
    </aside>
  );
}
