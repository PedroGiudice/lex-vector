import React, { useRef, useEffect } from 'react';

// Extend Window interface to include p5
declare global {
  interface Window {
    p5: any;
  }
}

const useP5 = (sketch: (p: any) => void, containerRef: React.RefObject<HTMLDivElement>) => {
  useEffect(() => {
    if (!window.p5 || !containerRef.current) return;

    const wrapper = (p: any) => {
      sketch(p);
    };

    const instance = new window.p5(wrapper, containerRef.current);
    return () => instance.remove();
  }, [sketch]);
};

interface SpinnerProps {
  className?: string;
}

export const ReactorSpinner: React.FC<SpinnerProps> = ({ className }) => {
  const ref = useRef<HTMLDivElement>(null);

  const sketch = (p: any) => {
    p.setup = () => {
      p.createCanvas(200, 200); // Smaller canvas (was 300)
      p.colorMode(p.RGB); // Use RGB for exact hex matching
      p.noFill();
      p.strokeCap(p.ROUND);
    };

    p.draw = () => {
      p.clear();
      p.translate(p.width / 2, p.height / 2);

      const t = p.millis() * 0.001;

      // Thinner, Slower Pulse Ring
      const drawPulseRing = (radius: number, count: number, speed: number, baseWeight: number, phase: number) => {
        p.push();
        p.rotate(t * speed * 0.5); // 50% slower rotation

        const pulse = p.sin(t * 2 + phase); // Slower pulse frequency
        // Drastically reduced weight for "thinner" look (2px - 4px range)
        const dynamicWeight = baseWeight + pulse * (baseWeight * 0.3);
        p.strokeWeight(dynamicWeight);

        const sectionSize = p.TWO_PI / count;
        // Less dramatic expansion for a more stable, technical feel
        const arcFactor = p.map(pulse, -1, 1, 0.4, 0.6);
        const arcLen = sectionSize * arcFactor;

        for (let i = 0; i < count; i++) {
          const angle = i * sectionSize;
          // Coral Color: #d97757 -> RGB(217, 119, 87)
          p.stroke(217, 119, 87);
          p.arc(0, 0, radius * 2, radius * 2, angle, angle + arcLen);
        }
        p.pop();
      };

      // Outer Shell: Radius 70, thinner weight
      drawPulseRing(70, 3, 0.6, 2.5, 0);

      // Inner Interlock: Radius 40, slightly thicker weight
      drawPulseRing(40, 2, -0.8, 3.5, 2);

      // Core Reactor
      p.push();
      p.noStroke();
      p.fill(217, 119, 87);
      const corePulse = 6 + p.sin(t * 3) * 1.5; // Smaller core
      p.circle(0, 0, corePulse);
      p.pop();
    };
  };

  useP5(sketch, ref);
  return <div ref={ref} className={className} />;
};

export const PhyllotaxisSpinner: React.FC<SpinnerProps> = ({ className }) => {
  const ref = useRef<HTMLDivElement>(null);
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

      p.rotate(t * 0.2); // Slower rotation

      for (let i = 1; i < numDots; i++) {
        const angle = i * goldenAngle;
        const radius = spread * Math.sqrt(i);
        const x = radius * Math.cos(angle);
        const y = radius * Math.sin(angle);

        const pulse = p.sin(t * 2 - i * 0.1); // Slower wave
        const dotSize = p.map(pulse, -1, 1, 10, 25); // Smaller dots

        // Coral Color with Alpha for depth
        const alpha = p.map(p.sin(t * 3 + i * 0.2), -1, 1, 100, 255);
        p.fill(217, 119, 87, alpha);

        p.circle(x, y, dotSize);
      }
    };
  };
  useP5(sketch, ref);
  return <div ref={ref} className={className} />;
};
