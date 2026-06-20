'use client';

import { useEffect, useRef, useState } from 'react';
import { notify } from '../core/notify.js';
import { readStorage, writeStorage } from '../core/storage.js';

function cleanSpeechText(text = '') {
  return String(text || '')
    .replace(/```[\s\S]*?```/g, ' bloque de codigo. ')
    .replace(/`([^`]+)`/g, '$1')
    .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
    .replace(/<[^>]+>/g, ' ')
    .replace(/^#{1,6}\s+/gm, '')
    .replace(/^\s*[-*]\s+/gm, '')
    .replace(/^\s*\d+[.)]\s+/gm, '')
    .replace(/\*\*([^*]+)\*\*/g, '$1')
    .replace(/[_*~>#|]+/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();
}

function splitTextIntoChunks(text, maxChunkLength = 250) {
  if (!text) return [];
  const words = text.split(/\s+/);
  const chunks = [];
  let currentChunk = "";
  
  for (const word of words) {
    if (!word) continue;
    const testChunk = currentChunk ? `${currentChunk} ${word}` : word;
    if (testChunk.length > maxChunkLength) {
      if (currentChunk) {
        chunks.push(currentChunk);
        currentChunk = word;
      } else {
        chunks.push(word);
        currentChunk = "";
      }
    } else {
      currentChunk = testChunk;
    }
  }
  
  if (currentChunk) {
    chunks.push(currentChunk);
  }
  
  return chunks;
}

export function useSpeech() {
  const [listening, setListening] = useState(false);
  const [speaking, setSpeaking] = useState(false);
  const [voiceEnabled, setVoiceEnabledState] = useState(true);
  const voiceEnabledRef = useRef(voiceEnabled);
  const pausedByToggleRef = useRef(false);
  const audioRef = useRef(null);
  const audioUrlRef = useRef('');
  const speakingTimerRef = useRef(null);

  const chunksRef = useRef([]);
  const chunkIndexRef = useRef(0);

  function clearSpeakingTimer() {
    if (!speakingTimerRef.current) return;
    window.clearTimeout(speakingTimerRef.current);
    speakingTimerRef.current = null;
  }

  function finishSpeaking() {
    clearSpeakingTimer();
    pausedByToggleRef.current = false;
    setSpeaking(false);
  }

  function armSpeakingFallback(text = '') {
    clearSpeakingTimer();
    const seconds = Math.min(90, Math.max(5, Math.ceil(String(text || '').length / 14)));
    speakingTimerRef.current = window.setTimeout(finishSpeaking, seconds * 1000);
  }

  useEffect(() => {
    const next = readStorage('yelia_voice_enabled', '1') !== '0';
    setVoiceEnabledState(next);
    voiceEnabledRef.current = next;
  }, []);

  useEffect(() => {
    voiceEnabledRef.current = voiceEnabled;
  }, [voiceEnabled]);

  useEffect(() => {
    const stopSpeech = () => stop();
    window.addEventListener('beforeunload', stopSpeech);
    window.addEventListener('pagehide', stopSpeech);
    return () => {
      stop();
      clearSpeakingTimer();
      window.removeEventListener('beforeunload', stopSpeech);
      window.removeEventListener('pagehide', stopSpeech);
    };
  }, []);

  function setVoiceEnabled(value) {
    const next = Boolean(value);
    setVoiceEnabledState(next);
    writeStorage('yelia_voice_enabled', next ? '1' : '0');
    voiceEnabledRef.current = next;
    if (!('speechSynthesis' in window)) return;
    if (!next) {
      if (window.speechSynthesis.speaking && !window.speechSynthesis.paused) {
        window.speechSynthesis.pause();
        pausedByToggleRef.current = true;
        clearSpeakingTimer();
        setSpeaking(false);
      }
      return;
    }
    if (pausedByToggleRef.current && window.speechSynthesis.paused) {
      window.speechSynthesis.resume();
      pausedByToggleRef.current = false;
      setSpeaking(true);
      armSpeakingFallback(chunksRef.current[chunkIndexRef.current] || '');
    }
  }

  function playNextChunk() {
    if (chunksRef.current.length === 0 || chunkIndexRef.current >= chunksRef.current.length) {
      finishSpeaking();
      return;
    }

    const chunk = chunksRef.current[chunkIndexRef.current];
    const provider = readStorage('yelia_tts_provider', process.env.NEXT_PUBLIC_TTS_PROVIDER || 'browser');
    if (provider === 'google') {
      playGoogleTtsChunk(chunk);
    } else {
      playBrowserTtsChunk(chunk);
    }
  }

  function playBrowserTtsChunk(text) {
    if (!('speechSynthesis' in window)) {
      chunkIndexRef.current += 1;
      playNextChunk();
      return;
    }
    try {
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.lang = 'es-EC';
      utterance.rate = 0.95;
      utterance.onstart = () => {
        setSpeaking(true);
        armSpeakingFallback(text);
      };
      utterance.onend = () => {
        chunkIndexRef.current += 1;
        playNextChunk();
      };
      utterance.onerror = (e) => {
        console.warn("SpeechSynthesis error handled:", e);
        chunksRef.current = [];
        chunkIndexRef.current = 0;
        finishSpeaking();
      };
      window.speechSynthesis.speak(utterance);
    } catch (err) {
      console.warn("SpeechSynthesis speak failed synchronously:", err);
      chunksRef.current = [];
      chunkIndexRef.current = 0;
      finishSpeaking();
    }
  }

  async function playGoogleTtsChunk(text) {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
    }
    if (audioUrlRef.current) {
      URL.revokeObjectURL(audioUrlRef.current);
      audioUrlRef.current = '';
    }
    if (!text) {
      chunkIndexRef.current += 1;
      playNextChunk();
      return;
    }
    try {
      setSpeaking(true);
      armSpeakingFallback(text);
      const response = await fetch('/api/voice/tts', {
        method: 'POST',
        credentials: 'include',
        headers: { 'Content-Type': 'application/json', Accept: 'audio/mpeg' },
        body: JSON.stringify({ text, lang: 'es' }),
      });
      if (!response.ok) throw new Error(`TTS ${response.status}`);
      const blob = await response.blob();
      if (audioUrlRef.current) URL.revokeObjectURL(audioUrlRef.current);
      audioUrlRef.current = URL.createObjectURL(blob);
      const audio = new Audio(audioUrlRef.current);
      audioRef.current = audio;
      audio.onended = () => {
        chunkIndexRef.current += 1;
        playNextChunk();
      };
      audio.onerror = () => {
        playBrowserTtsChunk(text);
      };
      await audio.play();
    } catch {
      playBrowserTtsChunk(text);
    }
  }

  function speak(text, options = {}) {
    if (!options.force && !voiceEnabledRef.current) return false;
    
    stop();

    const cleaned = cleanSpeechText(text);
    if (!cleaned) return false;

    const chunks = splitTextIntoChunks(cleaned, 250);
    if (chunks.length === 0) return false;

    chunksRef.current = chunks;
    chunkIndexRef.current = 0;

    playNextChunk();
    return true;
  }

  function stop() {
    chunksRef.current = [];
    chunkIndexRef.current = 0;
    if ('speechSynthesis' in window) window.speechSynthesis.cancel();
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
      audioRef.current = null;
    }
    if (audioUrlRef.current) {
      URL.revokeObjectURL(audioUrlRef.current);
      audioUrlRef.current = '';
    }
    pausedByToggleRef.current = false;
    finishSpeaking();
  }

  function listen(onResult) {
    const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!Recognition) {
      notify('Tu navegador no soporta reconocimiento de voz. Prueba en Chrome o Edge actualizado.', 'error');
      return false;
    }
    try {
      const recognition = new Recognition();
      recognition.lang = 'es-ES';
      recognition.interimResults = false;
      recognition.onstart = () => setListening(true);
      recognition.onend = () => setListening(false);
      recognition.onerror = () => {
        setListening(false);
        notify('No pude activar el microfono. Revisa permisos del navegador.', 'error');
      };
      recognition.onresult = (event) => onResult?.(event.results?.[0]?.[0]?.transcript || '');
      recognition.start();
      return true;
    } catch {
      setListening(false);
      notify('No pude iniciar el dictado por voz. Revisa permisos del microfono.', 'error');
      return false;
    }
  }

  return { listening, speaking, voiceEnabled, setVoiceEnabled, speak, stop, listen };
}
