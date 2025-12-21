p.setup = () => {
  p.createCanvas(400, 400);
  p.colorMode(p.HSB, 360, 100, 100);
  p.noStroke();
};

p.draw = () => {
  p.clear();
  p.translate(p.width / 2, p.height / 2);

  const t = p.millis() * 0.001;
  const numDots = 60;
  const spread = 16; // Space between dots
  const goldenAngle = 137.5 * (Math.PI / 180);

  // Rotate the entire system for the primary spinner movement
  p.rotate(t * 0.5);

  for (let i = 1; i < numDots; i++) {
    // Calculate Phyllotaxis position
    const angle = i * goldenAngle;
    const radius = spread * Math.sqrt(i);
    
    // Cartesian coordinates
    const x = radius * Math.cos(angle);
    const y = radius * Math.sin(angle);

    // Dynamic sizing based on wave pulse
    // Uses the index 'i' to offset the wave, creating a ripple from center to edge
    const pulse = p.sin(t * 3 - i * 0.15);
    const dotSize = p.map(pulse, -1, 1, 10, 35);

    // Color calculation: Hue shifts based on radius and time
    const hue = (i * 4 + t * 50) % 360;
    
    p.fill(hue, 85, 100);
    
    // Draw particle
    // Using circle for clear legibility at small sizes
    p.circle(x, y, dotSize);
  }
};