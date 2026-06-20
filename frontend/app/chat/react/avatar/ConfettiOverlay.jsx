'use client';

import React, { useEffect, useRef, useState } from 'react';

export default function ConfettiOverlay() {
  const canvasRef = useRef(null);
  const [isActive, setIsActive] = useState(false);

  useEffect(() => {
    let animationFrameId;
    let particles = [];
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    
    const colors = [
      'hsl(217, 91%, 60%)',  // Premium Blue
      'hsl(142, 71%, 45%)',  // Emerald Green
      'hsl(38, 92%, 50%)',   // Amber Gold
      'hsl(327, 90%, 55%)',  // Vibrant Magenta
      'hsl(262, 83%, 58%)',  // Elegant Purple
      'hsl(16, 92%, 54%)'    // Coral Orange
    ];

    function resizeCanvas() {
      if (canvas && canvas.parentElement) {
        canvas.width = canvas.parentElement.clientWidth;
        canvas.height = canvas.parentElement.clientHeight;
      }
    }

    class Particle {
      constructor(w, h) {
        this.x = Math.random() * w;
        this.y = -20 - Math.random() * 100;
        this.size = Math.random() * 8 + 5;
        this.color = colors[Math.floor(Math.random() * colors.length)];
        this.speedX = Math.random() * 4 - 2;
        this.speedY = Math.random() * 3 + 2;
        this.rotation = Math.random() * 360;
        this.rotationSpeed = Math.random() * 4 - 2;
        this.w = w;
        this.h = h;
      }

      update() {
        this.x += this.speedX + Math.sin(this.y / 30) * 0.5;
        this.y += this.speedY;
        this.rotation += this.rotationSpeed;
      }

      draw() {
        ctx.save();
        ctx.translate(this.x, this.y);
        ctx.rotate((this.rotation * Math.PI) / 180);
        ctx.fillStyle = this.color;
        if (Math.random() > 0.5) {
          ctx.fillRect(-this.size / 2, -this.size / 2, this.size, this.size / 2);
        } else {
          ctx.beginPath();
          ctx.arc(0, 0, this.size / 2, 0, Math.PI * 2);
          ctx.fill();
        }
        ctx.restore();
      }
    }

    function initConfetti() {
      resizeCanvas();
      particles = [];
      const numParticles = 80;
      for (let i = 0; i < numParticles; i++) {
        particles.push(new Particle(canvas.width, canvas.height));
      }
      setIsActive(true);
    }

    function animate() {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      let alive = false;
      
      particles.forEach((p) => {
        p.update();
        p.draw();
        if (p.y < canvas.height + 20) {
          alive = true;
        }
      });

      if (alive) {
        animationFrameId = requestAnimationFrame(animate);
      } else {
        setIsActive(false);
        ctx.clearRect(0, 0, canvas.width, canvas.height);
      }
    }

    const handleTrigger = () => {
      initConfetti();
      cancelAnimationFrame(animationFrameId);
      animate();
    };

    window.addEventListener('yelia_correct_answer', handleTrigger);
    window.addEventListener('resize', resizeCanvas);

    return () => {
      window.removeEventListener('yelia_correct_answer', handleTrigger);
      window.removeEventListener('resize', resizeCanvas);
      cancelAnimationFrame(animationFrameId);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      style={{
        position: 'absolute',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        pointerEvents: 'none',
        zIndex: 10,
        display: isActive ? 'block' : 'none'
      }}
    />
  );
}
