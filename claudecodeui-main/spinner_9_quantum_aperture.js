p.setup = () => {
  p.createCanvas(400, 400);
  p.colorMode(p.HSB, 360, 100, 100);
  p.noFill();
  p.strokeCap(p.ROUND);
};

p.draw = () => {
  p.clear();
  p.translate(p.width / 2, p.height / 2);

  const t = p.millis() * 0.001;
  const baseHue = (t * 40) % 360;

  // Function to draw pulsing rings with dynamic weight
  const drawPulseRing = (radius, count, speed, baseWeight, phase) => {
    p.push();
    p.rotate(t * speed);
    
    // Evolved logic: Modulate stroke weight dynamically using sine waves
    // This creates a 'pumping' visual that makes the cursor feel alive
    const pulse = p.sin(t * 4 + phase);
    const dynamicWeight = baseWeight + pulse * (baseWeight * 0.35);
    p.strokeWeight(dynamicWeight);
    
    // Calculate arc length based on the same pulse for synchronized breathing
    const sectionSize = p.TWO_PI / count;
    // Map pulse to arc length: Closed vs Open
    const arcFactor = p.map(pulse, -1, 1, 0.3, 0.85);
    const arcLen = sectionSize * arcFactor;

    for (let i = 0; i < count; i++) {
      const angle = i * sectionSize;
      // High contrast colors cycling through HSB
      p.stroke((baseHue + phase * 60 + i * 40) % 360, 90, 100);
      p.arc(0, 0, radius * 2, radius * 2, angle, angle + arcLen);
    }
    p.pop();
  };

  // Outer Shell: Thick, slow moving, forms the main silhouette
  // Radius 130 + (70/2) = 165px extent. Fits safely in 400px.
  drawPulseRing(130, 3, 1.2, 50, 0);

  // Inner Interlock: Counter-rotating, fills the negative space
  // Radius 65 + (50/2) = 90px extent. Touches the outer ring's inner edge.
  drawPulseRing(65, 2, -2.0, 40, 2);

  // Core Reactor: A solid oscillating anchor point
  p.push();
  p.noStroke();
  p.fill((baseHue + 180) % 360, 100, 100);
  const corePulse = 35 + p.sin(t * 8) * 8;
  p.circle(0, 0, corePulse);
  p.pop();
};