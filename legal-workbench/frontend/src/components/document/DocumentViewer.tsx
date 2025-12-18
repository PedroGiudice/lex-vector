import React, { useRef, useMemo, useEffect } from 'react';
import { useDocumentStore } from '@/store/documentStore';
import { useTextSelection } from '@/hooks/useTextSelection';
import { useAnnotations } from '@/hooks/useAnnotations';
import { TextSelectionPopup } from './TextSelection';
import { FieldAnnotation as FieldAnnotationComponent } from './FieldAnnotation';
import { FileText } from 'lucide-react';
import type { FieldAnnotation, PatternMatch } from '@/types';

export function DocumentViewer() {
  const containerRef = useRef<HTMLDivElement>(null);

  const paragraphs = useDocumentStore(state => state.paragraphs);
  const selectedText = useDocumentStore(state => state.selectedText);
  const setSelectedText = useDocumentStore(state => state.setSelectedText);
  const detectedPatterns = useDocumentStore(state => state.detectedPatterns);

  const { getAnnotationsForParagraph } = useAnnotations();

  useTextSelection({
    containerRef,
    onSelectionChange: setSelectedText,
  });

  // Keyboard shortcut: Escape to cancel selection
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setSelectedText(null);
      }
    };
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [setSelectedText]);

  // Render a paragraph with annotations and patterns
  const renderParagraph = (paragraph: string, paragraphIndex: number) => {
    const annotations = getAnnotationsForParagraph(paragraphIndex);
    const patterns = detectedPatterns.filter(p => p.paragraphIndex === paragraphIndex);

    if (annotations.length === 0 && patterns.length === 0) {
      return <p key={paragraphIndex}>{paragraph}</p>;
    }

    interface Segment {
      start: number;
      end: number;
      type: 'text' | 'annotation' | 'pattern';
      data?: FieldAnnotation | PatternMatch;
    }

    const segments: Segment[] = [];
    let lastIndex = 0;

    const allEvents = [
      ...annotations.map(a => ({ type: 'annotationStart', index: a.start, data: a as FieldAnnotation })),
      ...annotations.map(a => ({ type: 'annotationEnd', index: a.end, data: a as FieldAnnotation })),
      ...patterns.map(p => ({ type: 'patternStart', index: p.start, data: p as PatternMatch })),
      ...patterns.map(p => ({ type: 'patternEnd', index: p.end, data: p as PatternMatch })),
    ].sort((a, b) => a.index - b.index);

    let activeAnnotations: FieldAnnotation[] = [];
    let activePatterns: PatternMatch[] = [];

    for (const event of allEvents) {
      if (event.index > lastIndex) {
        // Add text segment before the current event
        const textSegment = paragraph.slice(lastIndex, event.index);
        if (textSegment.length > 0) {
          if (activeAnnotations.length > 0) {
            segments.push({ start: lastIndex, end: event.index, type: 'annotation', data: activeAnnotations[0] });
          } else if (activePatterns.length > 0) {
            segments.push({ start: lastIndex, end: event.index, type: 'pattern', data: activePatterns[0] });
          } else {
            segments.push({ start: lastIndex, end: event.index, type: 'text' });
          }
        }
      }

      if (event.type === 'annotationStart') {
        activeAnnotations.push(event.data as FieldAnnotation);
      } else if (event.type === 'annotationEnd') {
        activeAnnotations = activeAnnotations.filter(a => a.fieldName !== (event.data as FieldAnnotation).fieldName);
      } else if (event.type === 'patternStart') {
        // Only add if not already covered by an annotation
        if (activeAnnotations.length === 0) {
          activePatterns.push(event.data as PatternMatch);
        }
      } else if (event.type === 'patternEnd') {
        activePatterns = activePatterns.filter(p =>
          !(p.pattern === (event.data as PatternMatch).pattern &&
            p.start === (event.data as PatternMatch).start &&
            p.end === (event.data as PatternMatch).end &&
            p.paragraphIndex === (event.data as PatternMatch).paragraphIndex)
        );
      }
      lastIndex = event.index;
    }

    // Add any remaining text after the last event
    if (lastIndex < paragraph.length) {
      const textSegment = paragraph.slice(lastIndex);
      if (textSegment.length > 0) {
        if (activeAnnotations.length > 0) {
          segments.push({ start: lastIndex, end: paragraph.length, type: 'annotation', data: activeAnnotations[0] });
        } else if (activePatterns.length > 0) {
          segments.push({ start: lastIndex, end: paragraph.length, type: 'pattern', data: activePatterns[0] });
        } else {
          segments.push({ start: lastIndex, end: paragraph.length, type: 'text' });
        }
      }
    }

    const parts: React.ReactNode[] = [];
    segments.forEach((segment, i) => {
      const text = paragraph.slice(segment.start, segment.end);
      if (segment.type === 'annotation' && segment.data) {
        parts.push(
          <FieldAnnotationComponent
            key={`seg-annotation-${i}`}
            annotation={segment.data as FieldAnnotation}
            text={text}
          />
        );
      } else if (segment.type === 'pattern' && segment.data) {
        parts.push(
          <span key={`seg-pattern-${i}`} className="bg-yellow-700 bg-opacity-30 rounded-sm">
            {text}
          </span>
        );
      } else {
        parts.push(<span key={`seg-text-${i}`}>{text}</span>);
      }
    });

    return <p key={paragraphIndex}>{parts}</p>;
  };

  if (paragraphs.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-center px-8">
        <FileText className="w-16 h-16 text-gh-text-secondary mb-4" />
        <h3 className="text-lg font-semibold text-gh-text-primary mb-2">
          No Document Loaded
        </h3>
        <p className="text-sm text-gh-text-secondary max-w-md">
          Upload a .docx document to start creating your template. Select text to create
          field annotations.
        </p>
      </div>
    );
  }

  return (
    <div className="relative h-full">
      <div
        ref={containerRef}
        className="h-full overflow-y-auto px-8 py-6 bg-gh-bg-primary"
      >
        <div className="max-w-4xl mx-auto">
          <div className="prose prose-invert prose-sm max-w-none">
            {paragraphs.map((paragraph, index) => (
              <div
                key={index}
                data-paragraph-index={index}
                className="mb-4 text-gh-text-primary leading-relaxed"
              >
                {renderParagraph(paragraph, index)}
              </div>
            ))}
          </div>
        </div>
      </div>

      {selectedText && (
        <TextSelectionPopup
          selection={selectedText}
          onClose={() => setSelectedText(null)}
        />
      )}
    </div>
  );
}
