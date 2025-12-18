import React, { useState } from 'react';
import { useDocumentStore } from '@/store/documentStore';
import { PatternItem } from './PatternItem';
import { Sparkles } from 'lucide-react';
import { PatternMatch } from '@/types';

export function PatternList() {
  const detectedPatterns = useDocumentStore((state) => state.detectedPatterns);
  const documentId = useDocumentStore((state) => state.documentId);
  const [showAllPatterns, setShowAllPatterns] = useState(false);

  // Group patterns by paragraph index for easier rendering
  const patternsByParagraph: { [key: number]: PatternMatch[] } = detectedPatterns.reduce((acc, pattern) => {
    const paragraphIndex = pattern.paragraphIndex;
    if (!acc[paragraphIndex]) {
      acc[paragraphIndex] = [];
    }
    acc[paragraphIndex].push(pattern);
    return acc;
  }, {} as { [key: number]: PatternMatch[] });

  const paragraphsWithPatterns = Object.keys(patternsByParagraph).sort((a, b) => parseInt(a) - parseInt(b));

  if (!documentId || detectedPatterns.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-center px-4 py-8">
        <Sparkles className="w-12 h-12 text-gh-text-secondary mb-4" />
        <h3 className="text-md font-semibold text-gh-text-primary mb-2">
          No Patterns Detected
        </h3>
        <p className="text-xs text-gh-text-secondary max-w-md">
          Upload a document to automatically detect common patterns like CPF, dates, and more.
        </p>
      </div>
    );
  }

  const patternsToShow = showAllPatterns ? detectedPatterns : detectedPatterns.slice(0, 5);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-gh-accent-success" />
          <h2 className="text-sm font-semibold text-gh-text-primary">Detected Patterns</h2>
        </div>
        {detectedPatterns.length > 5 && (
          <button
            onClick={() => setShowAllPatterns(!showAllPatterns)}
            className="text-xs text-gh-accent-primary hover:underline"
          >
            {showAllPatterns ? 'Show Less' : `Show All (${detectedPatterns.length})`}
          </button>
        )}
      </div>
      <div className="space-y-2">
        {paragraphsWithPatterns.map((paragraphIndexStr) => {
          const paragraphIndex = parseInt(paragraphIndexStr);
          const patterns = patternsByParagraph[paragraphIndex];
          const visiblePatterns = showAllPatterns ? patterns : patterns.filter((_, idx) => idx < 5);

          if (visiblePatterns.length === 0) return null;

          return (
            <div key={paragraphIndexStr} className="space-y-2">
              <h3 className="text-xs font-semibold text-gh-text-secondary">
                Paragraph {paragraphIndex + 1}
              </h3>
              {visiblePatterns.map((pattern, index) => (
                <PatternItem
                  key={`${paragraphIndex}-${index}`}
                  patternMatch={pattern}
                />
              ))}
            </div>
          );
        })}
      </div>
    </div>
  );
}
