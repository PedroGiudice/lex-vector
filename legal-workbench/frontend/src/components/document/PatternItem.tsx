import React from 'react';
import { PatternMatch, FieldAnnotationInput } from '@/types';
import { useDocumentStore } from '@/store/documentStore';
import { PlusCircle } from 'lucide-react';

interface PatternItemProps {
  patternMatch: PatternMatch;
}

export function PatternItem({ patternMatch }: PatternItemProps) {
  const addAnnotation = useDocumentStore((state) => state.addAnnotation);
  const removeDetectedPattern = useDocumentStore((state) => state.removeDetectedPattern);

  const handleAcceptPattern = () => {
    const fieldName =
      patternMatch.pattern.toLowerCase().replace(/[^a-z0-9_]/g, '_') +
      '_' +
      Math.random().toString(36).substring(7);

    const newAnnotation: FieldAnnotationInput = {
      fieldName: fieldName,
      text: patternMatch.text,
      start: patternMatch.start,
      end: patternMatch.end,
      paragraphIndex: patternMatch.paragraphIndex,
    };
    addAnnotation(newAnnotation);
    removeDetectedPattern(patternMatch);
  };

  return (
    <div className="bg-gh-bg-tertiary border border-gh-border-default rounded px-3 py-2 flex items-center justify-between">
      <div>
        <code className="text-xs font-mono text-gh-accent-success block">
          {patternMatch.pattern}
        </code>
        <p className="text-xs text-gh-text-secondary mt-1 truncate">"{patternMatch.text}"</p>
      </div>
      <button
        onClick={handleAcceptPattern}
        className="text-gh-accent-primary hover:text-gh-accent-success transition-colors duration-200"
        title="Accept pattern as annotation"
      >
        <PlusCircle className="w-4 h-4" />
      </button>
    </div>
  );
}
