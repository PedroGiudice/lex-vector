import React from 'react';
import type { FieldAnnotation as FieldAnnotationType } from '@/types';

interface FieldAnnotationProps {
  annotation: FieldAnnotationType;
  text: string;
  onClick?: () => void;
}

export function FieldAnnotation({ annotation, text, onClick }: FieldAnnotationProps) {
  return (
    <span
      className="field-annotation"
      onClick={onClick}
      title={`Field: ${annotation.fieldName}`}
      data-field-name={annotation.fieldName}
    >
      {text}
    </span>
  );
}
