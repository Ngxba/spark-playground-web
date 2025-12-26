import { useRef, useEffect, useMemo } from 'react';

/**
 * ParticleAnimationEngine - Canvas-based particle renderer for Spark execution visualization
 *
 * Shows particles flowing through stages:
 * - Blue particles: Normal data flow (narrow dependencies)
 * - Orange particles: Shuffle data (wide dependencies)
 */
function ParticleAnimationEngine({
  simulationData,
  currentTime,
  isPlaying,
  playbackSpeed,
  partitionPositions,  // { partitionId: { x, y } }
}) {
  const canvasRef = useRef(null);
  const particlesRef = useRef([]);
  const nextParticleIdRef = useRef(0);
  const animationFrameRef = useRef(null);
  const lastTimeRef = useRef(0);

  // Configuration
  const CONFIG = {
    particlesPerSecond: 10,
    particleSize: 4,
    particleSpeed: 100,
    particleLifetime: 2,  // seconds
    colors: {
      data: '#3b82f6',      // Blue
      shuffle: '#f59e0b',   // Orange
    }
  };

  /**
   * Build particle paths from partition lineage
   * Returns: { pathId: { type, start, end, sourcePartition, destPartition } }
   */
  const particlePaths = useMemo(() => {
    if (!simulationData || !partitionPositions) return {};

    const paths = {};
    const { partitions } = simulationData;

    partitions.forEach(partition => {
      const sourcePos = partitionPositions[partition.id];
      if (!sourcePos) return;

      partition.child_partitions.forEach(childId => {
        const destPos = partitionPositions[childId];
        if (!destPos) return;

        const childPartition = partitions.find(p => p.id === childId);
        const isShuffle = childPartition &&
          childPartition.stage_id !== partition.stage_id;

        const pathId = `${partition.id}-${childId}`;
        paths[pathId] = {
          type: isShuffle ? 'shuffle' : 'data',
          start: sourcePos,
          end: destPos,
          sourcePartition: partition.id,
          destPartition: childId,
        };
      });
    });

    return paths;
  }, [simulationData, partitionPositions]);

  /**
   * Particle class
   */
  class Particle {
    constructor(id, path, spawnTime) {
      this.id = id;
      this.path = path;
      this.spawnTime = spawnTime;
      this.progress = 0;
      this.active = true;
      this.opacity = 1;
    }

    update(currentTime, deltaTime) {
      const age = currentTime - this.spawnTime;
      if (age >= CONFIG.particleLifetime) {
        this.active = false;
        return;
      }

      this.progress += 0.5 * deltaTime;

      if (this.progress > 0.8) {
        this.opacity = (1 - this.progress) / 0.2;
      }

      if (this.progress >= 1) {
        this.active = false;
      }
    }

    draw(ctx) {
      const { start, end, type } = this.path;
      const x = start.x + (end.x - start.x) * this.progress;
      const y = start.y + (end.y - start.y) * this.progress;

      ctx.globalAlpha = this.opacity;
      ctx.fillStyle = CONFIG.colors[type] || CONFIG.colors.data;
      ctx.beginPath();
      ctx.arc(x, y, CONFIG.particleSize, 0, Math.PI * 2);
      ctx.fill();
      ctx.globalAlpha = 1;
    }
  }

  /**
   * Spawn particles based on active tasks
   */
  const spawnParticles = (deltaTime) => {
    if (!isPlaying) return;

    const spawnRate = CONFIG.particlesPerSecond * deltaTime;

    Object.values(particlePaths).forEach(path => {
      if (shouldSpawnParticle(path, currentTime) && Math.random() < spawnRate) {
        particlesRef.current.push(
          new Particle(nextParticleIdRef.current++, path, currentTime)
        );
      }
    });
  };

  /**
   * Check if path should spawn particles at current time
   */
  const shouldSpawnParticle = (path, currentTime) => {
    if (!simulationData) return false;

    const { stages } = simulationData;
    for (const stage of stages) {
      for (const task of stage.tasks) {
        if (task.partition_id === path.sourcePartition &&
            currentTime >= task.start_time &&
            currentTime <= task.end_time) {
          return true;
        }
      }
    }
    return false;
  };

  /**
   * Update all particles
   */
  const updateParticles = (currentTime, deltaTime) => {
    particlesRef.current = particlesRef.current.filter(particle => {
      particle.update(currentTime, deltaTime);
      return particle.active;
    });
  };

  /**
   * Render all particles
   */
  const renderParticles = (ctx) => {
    particlesRef.current.forEach(particle => particle.draw(ctx));
  };

  /**
   * Animation loop
   */
  const animate = (timestamp) => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const deltaTime = lastTimeRef.current
      ? (timestamp - lastTimeRef.current) / 1000 * playbackSpeed
      : 0;

    lastTimeRef.current = timestamp;

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Update and render
    if (isPlaying) {
      spawnParticles(deltaTime);
      updateParticles(currentTime, deltaTime);
    }
    renderParticles(ctx);

    // Continue loop
    animationFrameRef.current = requestAnimationFrame(animate);
  };

  /**
   * Setup canvas and start animation loop
   */
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    // Set canvas size to match parent
    const updateCanvasSize = () => {
      const rect = canvas.parentElement.getBoundingClientRect();
      canvas.width = rect.width;
      canvas.height = rect.height;
    };

    updateCanvasSize();
    window.addEventListener('resize', updateCanvasSize);

    // Start animation loop
    animationFrameRef.current = requestAnimationFrame(animate);

    return () => {
      window.removeEventListener('resize', updateCanvasSize);
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    };
  }, [simulationData, currentTime, isPlaying, playbackSpeed, particlePaths]);

  /**
   * Reset particles when timeline resets
   */
  useEffect(() => {
    if (currentTime === 0) {
      particlesRef.current = [];
      nextParticleIdRef.current = 0;
    }
  }, [currentTime]);

  return (
    <canvas
      ref={canvasRef}
      style={{
        position: 'absolute',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        pointerEvents: 'none',  // Allow clicks to pass through
        zIndex: 10,  // Above visualization, below controls
      }}
    />
  );
}

export default ParticleAnimationEngine;
