'use client';

import React, { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';

const MODEL_BY_AVATAR = {
  avatar_cat: '/avatar-model/gato.glb',
  avatar_dog: '/avatar-model/perro.glb',
  avatar_owl: '/avatar-model/buho.glb',
};

const FRONT_ROTATION_BY_AVATAR = {
  avatar_cat: -90,
  avatar_dog: -90,
  avatar_owl: -90,
};

const IDLE_MORPHS_BY_AVATAR = {
  avatar_cat: { ojo: 0, boca: 1 },
  avatar_dog: { ojo: 0, boca: 1 },
  avatar_owl: { ojo: 0, boca: 1.0 },
};

const SPEAKING_MOUTH_BY_AVATAR = {
  avatar_cat: 0,
  avatar_dog: 0,
  avatar_owl: 0,
};

const EXPRESSION_STYLE = {
  happy: { tilt: -0.035, nod: 0.018, energy: 1.15 },
  curious: { tilt: 0.06, nod: 0.026, energy: 1.05 },
  explain: { tilt: 0.025, nod: 0.02, energy: 1 },
  supportive: { tilt: -0.06, nod: 0.012, energy: 0.82 },
  concerned: { tilt: 0.08, nod: -0.015, energy: 0.72 },
  error: { tilt: 0.08, nod: -0.015, energy: 0.72 },
  neutral: { tilt: 0, nod: 0, energy: 1 },
};

THREE.Cache.enabled = true;
const PRELOADED_MODELS = new Set();

function preloadAvatarModels() {
  const loader = new GLTFLoader();
  Object.values(MODEL_BY_AVATAR).forEach((modelUrl) => {
    if (PRELOADED_MODELS.has(modelUrl)) return;
    PRELOADED_MODELS.add(modelUrl);
    loader.load(modelUrl, () => {}, undefined, () => {
      PRELOADED_MODELS.delete(modelUrl);
    });
  });
}

function disposeObject(object) {
  object.traverse((child) => {
    if (child.geometry) child.geometry.dispose();
    if (child.material) {
      const materials = Array.isArray(child.material) ? child.material : [child.material];
      materials.forEach((material) => {
        // Se omiten los disposes de material y texturas para evitar el error de carga de texturas (Couldn't load texture blob)
      });
    }
  });
}

function fitModelToStage(model) {
  const box = new THREE.Box3().setFromObject(model);
  const size = new THREE.Vector3();
  const center = new THREE.Vector3();
  box.getSize(size);
  box.getCenter(center);

  model.position.sub(center);
  const maxAxis = Math.max(size.x, size.y, size.z) || 1;
  model.scale.setScalar(2.25 / maxAxis);
  model.position.y -= 0.08;
}

function applyFrontPose(model, avatar, rotationDegrees) {
  const degrees = Number.isFinite(rotationDegrees)
    ? rotationDegrees
    : (FRONT_ROTATION_BY_AVATAR[avatar] ?? -90);
  const baseRotation = THREE.MathUtils.degToRad(degrees);
  model.rotation.set(0, baseRotation, 0);
  model.userData.baseRotationY = baseRotation;
}

function setMorphValue(model, morphName, value) {
  model.traverse((child) => {
    if (!child.morphTargetDictionary || !child.morphTargetInfluences) return;
    const entry = Object.entries(child.morphTargetDictionary)
      .find(([name]) => name.toLowerCase() === morphName);
    if (!entry) return;
    child.morphTargetInfluences[entry[1]] = THREE.MathUtils.clamp(value, -1, 1);
  });
}

function hasMorph(modelPart, morphName) {
  if (!modelPart.morphTargetDictionary) return false;
  return Object.keys(modelPart.morphTargetDictionary)
    .some((name) => name.toLowerCase() === morphName);
}

function configureAvatarLayers(model, avatar) {
  const useMorphLayerOnly = avatar === 'avatar_cat' || avatar === 'avatar_dog' || avatar === 'avatar_owl';
  if (!useMorphLayerOnly) return;

  model.traverse((child) => {
    if (!child.isMesh) return;
    child.visible = hasMorph(child, 'boca') || hasMorph(child, 'ojo');
  });
}

function blinkAmount(now, avatar, duration = 0.18) {
  const interval = avatar === 'avatar_owl' ? 4.2 : 4.8;
  const offset = avatar === 'avatar_dog' ? 1.3 : avatar === 'avatar_owl' ? 0.7 : 0;
  const phase = (now + offset) % interval;
  if (phase > duration) return 0;
  return Math.sin((phase / duration) * Math.PI);
}

function speechMouthAmount(now) {
  const wave = (
    Math.sin(now * 8.5)
    + Math.sin(now * 13.2 + 0.8) * 0.55
    + Math.sin(now * 18.7 + 1.7) * 0.25
  );
  return THREE.MathUtils.smoothstep((wave + 1.8) / 3.6, 0.18, 0.95);
}

function normalizeExpression(expression = 'neutral') {
  const value = String(expression || 'neutral').trim().toLowerCase();
  if (['frustrated', 'anxious', 'confused'].includes(value)) return 'supportive';
  if (['confident', 'satisfied'].includes(value)) return 'happy';
  return EXPRESSION_STYLE[value] ? value : 'neutral';
}

function applyAvatarMorphs(model, avatar, currentState, now) {
  const idleMorphs = IDLE_MORPHS_BY_AVATAR[avatar] || {};
  const speaking = currentState === 'speaking';
  // Reducir la velocidad del pico del búho para que se vea más natural (de 4.5 a 1.8)
  const timeFactor = avatar === 'avatar_owl' ? 1.8 : 1.0;
  const mouthPulse = speaking ? speechMouthAmount(now * timeFactor) : 0;
  const blink = blinkAmount(now, avatar, avatar === 'avatar_owl' ? 0.24 : (speaking ? 0.12 : 0.18));

  if (typeof idleMorphs.ojo === 'number') {
    const eyeValue = THREE.MathUtils.lerp(idleMorphs.ojo, 1, blink);
    setMorphValue(model, 'ojo', eyeValue);

    // Evitar interpenetración de la geometría del ojo durante la animación del párpado (clipping)
    if (avatar === 'avatar_owl' && model.userData.eyeballMesh && model.userData.baseEyeballScale) {
      // Se omite la modificación de escala para evitar que los ojos/cabeza del búho palpiten al hablar o parpadear
    }
  }

  if (typeof idleMorphs.boca === 'number') {
    const targetMouth = SPEAKING_MOUTH_BY_AVATAR[avatar] ?? 0;
    const rawMouthValue = speaking
      ? THREE.MathUtils.lerp(idleMorphs.boca, targetMouth, mouthPulse)
      : idleMorphs.boca;
    const currentMouthValue = Number.isFinite(model.userData.mouthValue)
      ? model.userData.mouthValue
      : idleMorphs.boca;
    const lerpFactor = avatar === 'avatar_owl' ? (speaking ? 0.95 : 1.0) : (speaking ? 0.32 : 0.18);
    const mouthValue = (avatar === 'avatar_owl' && !speaking)
      ? idleMorphs.boca
      : THREE.MathUtils.lerp(currentMouthValue, rawMouthValue, lerpFactor);
    model.userData.mouthValue = mouthValue;
    setMorphValue(model, 'boca', mouthValue);
  }
}

export default function ThreeAvatarCanvas({ avatar = 'avatar_cat', state = 'idle', expression = 'neutral', rotationDegrees }) {
  const mountRef = useRef(null);
  const sceneRef = useRef(null);
  const rendererRef = useRef(null);
  const cameraRef = useRef(null);
  const modelRef = useRef(null);
  const frameRef = useRef(0);
  const stateRef = useRef(state);
  const expressionRef = useRef(expression);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    stateRef.current = state || 'idle';
  }, [state]);

  useEffect(() => {
    expressionRef.current = normalizeExpression(expression);
  }, [expression]);

  useEffect(() => {
    const mount = mountRef.current;
    if (!mount) return undefined;

    const scene = new THREE.Scene();
    sceneRef.current = scene;
    preloadAvatarModels();

    const camera = new THREE.PerspectiveCamera(35, 1, 0.1, 100);
    camera.position.set(0, 0.22, 4.2);
    cameraRef.current = camera;

    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    renderer.setClearColor(0x000000, 0);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.05;
    rendererRef.current = renderer;
    mount.appendChild(renderer.domElement);

    const key = new THREE.HemisphereLight(0xffffff, 0x203040, 2.2);
    scene.add(key);

    const fill = new THREE.DirectionalLight(0xffffff, 2.1);
    fill.position.set(2.5, 4.5, 4);
    scene.add(fill);

    const rim = new THREE.DirectionalLight(0x75e6ff, 1.2);
    rim.position.set(-3, 2, -2);
    scene.add(rim);

    // Lógica de seguimiento del cursor
    let targetMouseX = 0;
    let targetMouseY = 0;
    let currentMouseRotX = 0;
    let currentMouseRotY = 0;
    let lastMouseMoveTime = performance.now();

    const onMouseMove = (event) => {
      // Normalizar coordenadas a rango [-1, 1]
      targetMouseX = (event.clientX / window.innerWidth) * 2 - 1;
      targetMouseY = (event.clientY / window.innerHeight) * 2 - 1;
      lastMouseMoveTime = performance.now();
    };

    const onMouseLeave = () => {
      targetMouseX = 0;
      targetMouseY = 0;
    };

    window.addEventListener('mousemove', onMouseMove);
    document.addEventListener('mouseleave', onMouseLeave);

    const resize = () => {
      const rect = mount.getBoundingClientRect();
      const width = Math.max(1, Math.floor(rect.width));
      const height = Math.max(1, Math.floor(rect.height));
      renderer.setSize(width, height, false);
      camera.aspect = width / height;
      camera.updateProjectionMatrix();
    };

    resize();
    const observer = new ResizeObserver(resize);
    observer.observe(mount);

    const animate = () => {
      frameRef.current = requestAnimationFrame(animate);
      const model = modelRef.current;
      if (model) {
        const now = performance.now() / 1000;
        const nowMs = performance.now();
        const currentState = stateRef.current;
        const currentExpression = expressionRef.current;
        const expressionStyle = EXPRESSION_STYLE[currentExpression] || EXPRESSION_STYLE.neutral;
        const talk = 0;
        const listen = currentState === 'listening' ? Math.sin(now * 4) * 0.055 : 0;
        const think = currentState === 'thinking' ? Math.sin(now * 2.4) * 0.045 : 0;
        const idle = 0;
        const expressionNod = Math.sin(now * 1.25) * expressionStyle.nod;

        // Si el cursor no se mueve en 2.5 segundos, volver lentamente al centro
        if (nowMs - lastMouseMoveTime > 2500) {
          targetMouseX *= 0.98;
          targetMouseY *= 0.98;
        }

        // Interpolar rotaciones suavemente con límites de seguridad
        currentMouseRotX = THREE.MathUtils.lerp(currentMouseRotX, targetMouseY * 0.28, 0.05); // inclinación vertical
        currentMouseRotY = THREE.MathUtils.lerp(currentMouseRotY, targetMouseX * 0.48, 0.05);  // giro horizontal

        const isOwl = avatar === 'avatar_owl';
        applyAvatarMorphs(model, model.userData.avatar || 'avatar_cat', currentState, now);
        model.position.y = idle + talk + 0.03;
        model.rotation.y = (model.userData.baseRotationY || 0) + (isOwl ? 0 : Math.sin(now * 0.8) * 0.035 + listen) + currentMouseRotY;
        model.rotation.x = (isOwl ? 0 : think * 0.35 + expressionNod) + currentMouseRotX;
        model.rotation.z = isOwl ? 0 : expressionStyle.tilt;
        const scalePulse = 1;
        model.scale.setScalar((model.userData.baseScale || 1) * scalePulse);
      }
      renderer.render(scene, camera);
    };

    animate();

    return () => {
      window.removeEventListener('mousemove', onMouseMove);
      document.removeEventListener('mouseleave', onMouseLeave);
      observer.disconnect();
      cancelAnimationFrame(frameRef.current);
      if (modelRef.current) disposeObject(modelRef.current);
      renderer.dispose();
      renderer.domElement.remove();
      scene.clear();
      sceneRef.current = null;
      rendererRef.current = null;
      cameraRef.current = null;
      modelRef.current = null;
    };
  }, []);

  useEffect(() => {
    const scene = sceneRef.current;
    if (!scene) return undefined;

    let cancelled = false;
    setFailed(false);
    const loader = new GLTFLoader();
    const modelUrl = MODEL_BY_AVATAR[avatar] || MODEL_BY_AVATAR.avatar_cat;

    loader.load(
      modelUrl,
      (gltf) => {
        if (cancelled) {
          disposeObject(gltf.scene);
          return;
        }

        if (modelRef.current) {
          scene.remove(modelRef.current);
          disposeObject(modelRef.current);
        }

        const model = gltf.scene;
        fitModelToStage(model);
        applyFrontPose(model, avatar, rotationDegrees);
        configureAvatarLayers(model, avatar);
        model.userData.avatar = avatar;
        model.userData.baseScale = model.scale.x;

        model.traverse((child) => {
          if (child.isMesh) {
            child.castShadow = true;
            child.receiveShadow = true;
            // Identificar la malla de los ojos estáticos (sin morph target de párpados)
            if (avatar === 'avatar_owl' && (!child.morphTargetDictionary || !child.morphTargetDictionary.ojo)) {
              model.userData.eyeballMesh = child;
              model.userData.baseEyeballScale = child.scale.clone();
            }

            // Limpiar y suavizar los desplazamientos del morph target 'boca' en la región de los ojos/cara del búho
            // para evitar líneas visuales, sombras extrañas o deformaciones en la unión del pico
            if (avatar === 'avatar_owl' && child.geometry && child.geometry.morphAttributes) {
              const dict = child.morphTargetDictionary;
              if (dict && typeof dict.boca === 'number') {
                const bocaIndex = dict.boca;
                const posAttr = child.geometry.attributes.position;
                const posMorph = child.geometry.morphAttributes.position ? child.geometry.morphAttributes.position[bocaIndex] : null;
                const normMorph = child.geometry.morphAttributes.normal ? child.geometry.morphAttributes.normal[bocaIndex] : null;
                
                if (posAttr && (posMorph || normMorph)) {
                  const baseArray = posAttr.array;
                  const count = posAttr.count;
                  for (let i = 0; i < count; i++) {
                     const y = baseArray[i * 3 + 1];
                     const z = baseArray[i * 3 + 2];
                     const absY = Math.abs(y);
                     let factor = 1;
                     if (absY >= 0.08 || z >= -0.12) {
                       factor = 0;
                     } else if (absY > 0.05) {
                       factor = (0.08 - absY) / 0.03;
                     }
                    if (factor !== 1) {
                      if (posMorph) {
                        posMorph.array[i * 3] *= factor;
                        posMorph.array[i * 3 + 1] *= factor;
                        posMorph.array[i * 3 + 2] *= factor;
                      }
                      if (normMorph) {
                        normMorph.array[i * 3] *= factor;
                        normMorph.array[i * 3 + 1] *= factor;
                        normMorph.array[i * 3 + 2] *= factor;
                      }
                    }
                  }
                  if (posMorph) posMorph.needsUpdate = true;
                  if (normMorph) normMorph.needsUpdate = true;
                }
              }
            }
          }
        });

        applyAvatarMorphs(model, avatar, 'idle', 0);
        scene.add(model);
        modelRef.current = model;
      },
      undefined,
      () => {
        if (!cancelled) setFailed(true);
      },
    );

    return () => {
      cancelled = true;
    };
  }, [avatar, rotationDegrees]);

  return (
    <div className="yelia-avatar-3d-stage" ref={mountRef}>
      {failed ? <span className="yelia-avatar-3d-fallback">No se pudo cargar el avatar 3D</span> : null}
    </div>
  );
}
