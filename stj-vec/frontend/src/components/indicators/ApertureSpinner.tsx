import { useRef, useEffect } from 'react';

interface ApertureSpinnerProps {
  size?: number;
  palette?: {
    red: string;
    light: string;
    dark: string;
  };
}

function easeInOutExpo(x: number): number {
  if (x === 0) return 0;
  if (x === 1) return 1;
  return x < 0.5
    ? Math.pow(2, 20 * x - 10) / 2
    : (2 - Math.pow(2, -20 * x + 10)) / 2;
}

const DEFAULT_PALETTE = {
  red: 'rgb(91, 141, 239)',
  light: 'rgb(60, 62, 68)',
  dark: 'rgb(39, 40, 45)',
};

export const ApertureSpinner: React.FC<ApertureSpinnerProps> = ({
  size = 40,
  palette = DEFAULT_PALETTE,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const rafRef = useRef<number>(0);
  const startRef = useRef<number>(0);

  useEffect(() => {
    function draw(timestamp: number): void {
      if (!startRef.current) startRef.current = timestamp;
      const canvas = canvasRef.current;
      if (!canvas) return;
      const ctx = canvas.getContext('2d');
      if (!ctx) return;

      const dpr = window.devicePixelRatio || 1;
      const w = size * dpr;
      const h = size * dpr;

      if (canvas.width !== w || canvas.height !== h) {
        canvas.width = w;
        canvas.height = h;
      }

      ctx.clearRect(0, 0, w, h);
      ctx.save();
      ctx.scale(dpr, dpr);
      ctx.translate(size / 2, size / 2);

      const totalDuration = 2500;
      const elapsed = (timestamp - startRef.current) % totalDuration;
      const progress = elapsed / totalDuration;

      let animState = 0;
      if (progress < 0.4) {
        animState = easeInOutExpo(progress / 0.4);
      } else if (progress < 0.6) {
        animState = 1;
      } else {
        animState = easeInOutExpo((1 - progress) / 0.4);
      }

      const slowRot = (timestamp - startRef.current) * 0.0002;
      ctx.rotate(slowRot);

      const numShapes = 4;
      const scale = size / 400;
      const baseSize = 60 * scale;
      const expandDist = 40 * scale;

      for (let i = 0; i < numShapes; i++) {
        ctx.save();
        const baseAngle = (Math.PI * 2 / numShapes) * i;
        const snapRotation = animState * (Math.PI / 2);
        ctx.rotate(baseAngle + snapRotation);
        const currentDist = expandDist * animState;

        if (currentDist > 2 * scale) {
          ctx.strokeStyle = palette.dark;
          ctx.lineWidth = 2 * scale;
          ctx.beginPath();
          ctx.moveTo(0, 0);
          ctx.lineTo(currentDist, 0);
          ctx.stroke();
        }

        ctx.translate(currentDist, 0);
        const currentRound = animState * (baseSize / 2);
        ctx.fillStyle = i % 2 === 0 ? palette.red : palette.light;

        const half = baseSize / 2;
        ctx.beginPath();
        ctx.moveTo(-half + currentRound, -half);
        ctx.lineTo(half - currentRound, -half);
        ctx.arcTo(half, -half, half, -half + currentRound, currentRound);
        ctx.lineTo(half, half - currentRound);
        ctx.arcTo(half, half, half - currentRound, half, currentRound);
        ctx.lineTo(-half + currentRound, half);
        ctx.arcTo(-half, half, -half, half - currentRound, currentRound);
        ctx.lineTo(-half, -half + currentRound);
        ctx.arcTo(-half, -half, -half + currentRound, -half, currentRound);
        ctx.closePath();
        ctx.fill();

        ctx.fillStyle = palette.dark;
        ctx.save();
        ctx.rotate(-(baseAngle + snapRotation));
        const screwSize = animState * 8 * scale;
        if (screwSize > 1 * scale) {
          ctx.fillRect(-screwSize / 2, -1 * scale, screwSize, 2 * scale);
          ctx.fillRect(-1 * scale, -screwSize / 2, 2 * scale, screwSize);
        }
        ctx.restore();
        ctx.restore();
      }

      ctx.fillStyle = palette.dark;
      const centerSize = (10 + 10 * animState) * scale;
      ctx.beginPath();
      ctx.arc(0, 0, centerSize / 2, 0, Math.PI * 2);
      ctx.fill();
      ctx.restore();

      rafRef.current = requestAnimationFrame(draw);
    }

    rafRef.current = requestAnimationFrame(draw);
    return () => cancelAnimationFrame(rafRef.current);
  }, [size, palette]);

  return (
    <canvas
      ref={canvasRef}
      style={{
        width: size,
        height: size,
        display: 'block',
      }}
    />
  );
};

export default ApertureSpinner;
