// Re-exports para compatibilidade com imports existentes.
// Os spinners p5.js foram substituidos pelo ApertureSpinner (Canvas 2D nativo).
import { ApertureSpinner } from "./ApertureSpinner";

interface SpinnerProps {
  className?: string;
}

/**
 * Substitui ReactorSpinner (p5.js) pelo ApertureSpinner.
 * Extrai dimensao do className (w-XX h-XX) para o prop size.
 */
export const ReactorSpinner: React.FC<SpinnerProps> = ({ className }) => {
  const size = extractSize(className);
  return (
    <div className={className}>
      <ApertureSpinner size={size} />
    </div>
  );
};

/**
 * Substitui PhyllotaxisSpinner (p5.js) pelo ApertureSpinner.
 */
export const PhyllotaxisSpinner: React.FC<SpinnerProps> = ({ className }) => {
  const size = extractSize(className);
  return (
    <div className={className}>
      <ApertureSpinner size={size} />
    </div>
  );
};

/**
 * Extrai tamanho em pixels a partir de classes Tailwind como "w-16" ou "w-[80px]".
 * Fallback: 64px.
 */
function extractSize(className?: string): number {
  if (!className) return 64;
  // w-[80px] -> 80
  const bracketMatch = className.match(/w-\[(\d+)px\]/);
  if (bracketMatch) return parseInt(bracketMatch[1], 10);
  // w-16 -> 64 (16 * 4)
  const numMatch = className.match(/w-(\d+)/);
  if (numMatch) return parseInt(numMatch[1], 10) * 4;
  return 64;
}
