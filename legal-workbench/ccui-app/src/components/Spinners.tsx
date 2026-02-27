import React, { useRef, useEffect } from "react";

// Estende Window para incluir p5 (carregado via CDN no index.html)
declare global {
  interface Window {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    p5: any;
  }
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const useP5 = (sketch: (p: any) => void, containerRef: React.RefObject<HTMLDivElement | null>) => {
  useEffect(() => {
    if (!window.p5 || !containerRef.current) return;

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const instance = new window.p5((p: any) => sketch(p), containerRef.current);
    return () => instance.remove();
  }, [sketch, containerRef]);
};

interface SpinnerProps {
  className?: string;
}

export const ReactorSpinner: React.FC<SpinnerProps> = ({ className }) => {
  const ref = useRef<HTMLDivElement>(null);

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const sketch = (p: any) => {
    p.setup = () => {
      p.createCanvas(200, 200);
      p.colorMode(p.RGB);
      p.noFill();
      p.strokeCap(p.ROUND);
    };

    p.draw = () => {
      p.clear();
      p.translate(p.width / 2, p.height / 2);

      const t = p.millis() * 0.001;

      const drawPulseRing = (
        radius: number,
        count: number,
        speed: number,
        baseWeight: number,
        phase: number
      ) => {
        p.push();
        p.rotate(t * speed * 0.5);

        const pulse = p.sin(t * 2 + phase);
        const dynamicWeight = baseWeight + pulse * (baseWeight * 0.3);
        p.strokeWeight(dynamicWeight);

        const sectionSize = p.TWO_PI / count;
        const arcFactor = p.map(pulse, -1, 1, 0.4, 0.6);
        const arcLen = sectionSize * arcFactor;

        for (let i = 0; i < count; i++) {
          const angle = i * sectionSize;
          // Cor coral: #d97757 -> RGB(217, 119, 87)
          p.stroke(217, 119, 87);
          p.arc(0, 0, radius * 2, radius * 2, angle, angle + arcLen);
        }
        p.pop();
      };

      drawPulseRing(70, 3, 0.6, 2.5, 0);
      drawPulseRing(40, 2, -0.8, 3.5, 2);

      p.push();
      p.noStroke();
      p.fill(217, 119, 87);
      const corePulse = 6 + p.sin(t * 3) * 1.5;
      p.circle(0, 0, corePulse);
      p.pop();
    };
  };

  useP5(sketch, ref);
  return <div ref={ref} className={className} />;
};

export const PhyllotaxisSpinner: React.FC<SpinnerProps> = ({ className }) => {
  const ref = useRef<HTMLDivElement>(null);

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const sketch = (p: any) => {
    p.setup = () => {
      p.createCanvas(100, 100);
      p.colorMode(p.RGB);
      p.noStroke();
    };

    p.draw = () => {
      p.clear();
      p.translate(p.width / 2, p.height / 2);
      p.scale(0.25);

      const t = p.millis() * 0.001;
      const numDots = 60;
      const spread = 16;
      const goldenAngle = 137.5 * (Math.PI / 180);

      p.rotate(t * 0.2);

      for (let i = 1; i < numDots; i++) {
        const angle = i * goldenAngle;
        const radius = spread * Math.sqrt(i);
        const x = radius * Math.cos(angle);
        const y = radius * Math.sin(angle);

        const pulse = p.sin(t * 2 - i * 0.1);
        const dotSize = p.map(pulse, -1, 1, 10, 25);

        const alpha = p.map(p.sin(t * 3 + i * 0.2), -1, 1, 100, 255);
        p.fill(217, 119, 87, alpha);

        p.circle(x, y, dotSize);
      }
    };
  };

  useP5(sketch, ref);
  return <div ref={ref} className={className} />;
};
