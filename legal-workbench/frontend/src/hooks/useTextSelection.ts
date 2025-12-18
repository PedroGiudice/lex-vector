import { useEffect, useState } from 'react';
import type { TextSelection } from '@/types';

interface UseTextSelectionOptions {
  onSelectionChange?: (selection: TextSelection | null) => void;
  containerRef?: React.RefObject<HTMLElement>;
}

export function useTextSelection(options: UseTextSelectionOptions = {}) {
  const [selection, setSelection] = useState<TextSelection | null>(null);

  useEffect(() => {
    const handleMouseUp = () => {
      const sel = window.getSelection();

      if (!sel || sel.isCollapsed || !sel.toString().trim()) {
        setSelection(null);
        options.onSelectionChange?.call(null, null);
        return;
      }

      const selectedText = sel.toString().trim();
      const range = sel.getRangeAt(0);
      const container = options.containerRef?.current;

      // If container is specified, check if selection is within it
      if (container && !container.contains(range.commonAncestorContainer)) {
        return;
      }

      // Find the paragraph index and positions
      const paragraphElement = range.startContainer.parentElement?.closest('[data-paragraph-index]');

      if (!paragraphElement) {
        return;
      }

      const paragraphIndex = parseInt(
        paragraphElement.getAttribute('data-paragraph-index') || '0',
        10
      );

      // Get text content of the paragraph to calculate positions
      const paragraphText = paragraphElement.textContent || '';
      const beforeSelection = range.cloneRange();
      beforeSelection.selectNodeContents(paragraphElement);
      beforeSelection.setEnd(range.startContainer, range.startOffset);
      const start = beforeSelection.toString().length;
      const end = start + selectedText.length;

      const textSelection: TextSelection = {
        text: selectedText,
        start,
        end,
        paragraphIndex,
      };

      setSelection(textSelection);
      options.onSelectionChange?.call(null, textSelection);
    };

    const handleMouseDown = () => {
      // Clear selection when starting a new selection
      setSelection(null);
      options.onSelectionChange?.call(null, null);
    };

    document.addEventListener('mouseup', handleMouseUp);
    document.addEventListener('mousedown', handleMouseDown);

    return () => {
      document.removeEventListener('mouseup', handleMouseUp);
      document.removeEventListener('mousedown', handleMouseDown);
    };
  }, [options.containerRef, options.onSelectionChange]);

  const clearSelection = () => {
    window.getSelection()?.removeAllRanges();
    setSelection(null);
    options.onSelectionChange?.call(null, null);
  };

  return {
    selection,
    clearSelection,
  };
}
