import React, { useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import './LandingPage.css';

const LandingPage = () => {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;

    // Particle system for data flow effect
    class Particle {
      constructor() {
        this.reset();
      }

      reset() {
        this.x = Math.random() * canvas.width;
        this.y = Math.random() * canvas.height;
        this.vx = (Math.random() - 0.5) * 0.5;
        this.vy = (Math.random() - 0.5) * 0.5;
        this.life = Math.random() * 100;
        this.maxLife = 100;
        this.hue = Math.random() > 0.5 ? 180 : 30; // Cyan or amber
      }

      update() {
        this.x += this.vx;
        this.y += this.vy;
        this.life--;

        if (this.life <= 0 || this.x < 0 || this.x > canvas.width || this.y < 0 || this.y > canvas.height) {
          this.reset();
        }
      }

      draw() {
        const alpha = this.life / this.maxLife;
        ctx.fillStyle = `hsla(${this.hue}, 100%, 50%, ${alpha * 0.6})`;
        ctx.fillRect(this.x, this.y, 2, 2);

        // Glow effect
        ctx.shadowBlur = 10;
        ctx.shadowColor = `hsl(${this.hue}, 100%, 50%)`;
        ctx.fillRect(this.x, this.y, 1, 1);
        ctx.shadowBlur = 0;
      }
    }

    const particles = Array.from({ length: 100 }, () => new Particle());

    function drawGrid() {
      ctx.strokeStyle = 'rgba(0, 217, 255, 0.1)';
      ctx.lineWidth = 1;

      const gridSize = 50;
      for (let x = 0; x < canvas.width; x += gridSize) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, canvas.height);
        ctx.stroke();
      }

      for (let y = 0; y < canvas.height; y += gridSize) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(canvas.width, y);
        ctx.stroke();
      }
    }

    function animate() {
      ctx.fillStyle = 'rgba(10, 14, 20, 0.1)';
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      drawGrid();

      particles.forEach(particle => {
        particle.update();
        particle.draw();
      });

      requestAnimationFrame(animate);
    }

    animate();

    const handleResize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
    };

    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
    };
  }, []);

  return (
    <div className="landing-page">
      <canvas ref={canvasRef} className="background-canvas" />

      {/* Scanline overlay */}
      <div className="scanline-overlay" />

      {/* Hero Section */}
      <section className="hero-section">
        <div className="hero-content">
          {/* System status indicator */}
          <div className="system-status">
            <span className="status-dot"></span>
            <span className="status-text">SYSTEM ONLINE</span>
          </div>

          {/* Main title */}
          <h1 className="hero-title">
            <span className="title-line">SPARK</span>
            <span className="title-line">PLAYGROUND</span>
          </h1>

          {/* Glitch subtitle */}
          <div className="hero-subtitle-wrapper">
            <p className="hero-subtitle" data-text="MASTER DATA PROCESSING THROUGH INDUSTRIAL-SCALE CHALLENGES">
              MASTER DATA PROCESSING THROUGH INDUSTRIAL-SCALE CHALLENGES
            </p>
          </div>

          {/* Technical specs bar */}
          <div className="tech-specs">
            <div className="spec-item">
              <span className="spec-icon">⚡</span>
              <span className="spec-label">REAL-TIME EXECUTION</span>
            </div>
            <div className="spec-divider"></div>
            <div className="spec-item">
              <span className="spec-icon">🎯</span>
              <span className="spec-label">HANDS-ON PUZZLES</span>
            </div>
            <div className="spec-divider"></div>
            <div className="spec-item">
              <span className="spec-icon">🏭</span>
              <span className="spec-label">FACTORY VISUALIZATION</span>
            </div>
          </div>

          {/* CTA Button */}
          <Link to="/puzzles" className="cta-button">
            <span className="cta-text">ENTER PLAYGROUND</span>
            <span className="cta-arrow">→</span>
            <div className="cta-glow"></div>
          </Link>

          {/* Version info */}
          <div className="version-info">
            <span className="version-label">VERSION</span>
            <span className="version-number">1.0.0-BETA</span>
          </div>
        </div>

        {/* Animated brackets */}
        <div className="hero-bracket hero-bracket-left">[</div>
        <div className="hero-bracket hero-bracket-right">]</div>
      </section>

      {/* Features Section */}
      <section className="features-section">
        <div className="section-header">
          <div className="header-line"></div>
          <h2 className="section-title">FACILITY CAPABILITIES</h2>
          <div className="header-line"></div>
        </div>

        <div className="features-grid">
          {/* Feature 1: Interactive Puzzles */}
          <div className="feature-card" style={{ animationDelay: '0.1s' }}>
            <div className="feature-icon-wrapper">
              <div className="feature-icon">🧩</div>
              <div className="icon-glow"></div>
            </div>
            <h3 className="feature-title">INTERACTIVE PUZZLES</h3>
            <p className="feature-description">
              Solve real-world Spark challenges in a hands-on environment.
              Write code, execute transformations, and see results instantly.
            </p>
            <div className="feature-metric">
              <span className="metric-value">50+</span>
              <span className="metric-label">CHALLENGES</span>
            </div>
          </div>

          {/* Feature 2: Real-time Execution */}
          <div className="feature-card" style={{ animationDelay: '0.2s' }}>
            <div className="feature-icon-wrapper">
              <div className="feature-icon">⚡</div>
              <div className="icon-glow"></div>
            </div>
            <h3 className="feature-title">REAL-TIME EXECUTION</h3>
            <p className="feature-description">
              Execute your Spark code against live data pipelines.
              Instant feedback with detailed execution metrics and performance analysis.
            </p>
            <div className="feature-metric">
              <span className="metric-value">&lt;2s</span>
              <span className="metric-label">RESPONSE TIME</span>
            </div>
          </div>

          {/* Feature 3: Progressive Hints */}
          <div className="feature-card" style={{ animationDelay: '0.3s' }}>
            <div className="feature-icon-wrapper">
              <div className="feature-icon">💡</div>
              <div className="icon-glow"></div>
            </div>
            <h3 className="feature-title">PROGRESSIVE HINTS</h3>
            <p className="feature-description">
              Get unstuck with our intelligent hint system.
              Layered guidance from gentle nudges to detailed solutions.
            </p>
            <div className="feature-metric">
              <span className="metric-value">4</span>
              <span className="metric-label">HINT LEVELS</span>
            </div>
          </div>

          {/* Feature 4: Factory Visualization */}
          <div className="feature-card" style={{ animationDelay: '0.4s' }}>
            <div className="feature-icon-wrapper">
              <div className="feature-icon">🏭</div>
              <div className="icon-glow"></div>
            </div>
            <h3 className="feature-title">FACTORY VISUALIZATION</h3>
            <p className="feature-description">
              See your Spark jobs come to life with industrial-grade visualizations.
              Track stages, workers, and data flow in real-time.
            </p>
            <div className="feature-metric">
              <span className="metric-value">100%</span>
              <span className="metric-label">VISIBILITY</span>
            </div>
          </div>
        </div>
      </section>

      {/* Footer Section */}
      <footer className="landing-footer">
        <div className="footer-content">
          <div className="footer-branding">
            <div className="footer-logo">SPARK PLAYGROUND</div>
            <div className="footer-tagline">Industrial-Scale Data Education</div>
          </div>

          <div className="footer-divider"></div>

          <div className="footer-info">
            <div className="info-item">
              <span className="info-icon">🔧</span>
              <span className="info-text">Built for Data Engineers</span>
            </div>
            <div className="info-item">
              <span className="info-icon">📚</span>
              <span className="info-text">Learn by Doing</span>
            </div>
            <div className="info-item">
              <span className="info-icon">🚀</span>
              <span className="info-text">Production-Ready Skills</span>
            </div>
          </div>
        </div>

        <div className="footer-bottom">
          <div className="terminal-prompt">
            <span className="prompt-symbol">$</span>
            <span className="prompt-text">Ready to process data at scale?</span>
            <span className="cursor-blink">_</span>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
