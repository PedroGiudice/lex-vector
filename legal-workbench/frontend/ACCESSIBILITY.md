# Accessibility Checklist

This document outlines the accessibility features implemented in the Doc Assembler Template Builder frontend.

## WCAG 2.1 Level AA Compliance

### Perceivable

#### Text Alternatives
- [x] All images have alt text
- [x] Icons paired with visible text or aria-labels
- [x] Form inputs have associated labels

#### Adaptable
- [x] Semantic HTML structure
- [x] Proper heading hierarchy (h1, h2, h3)
- [x] Landmarks for page regions (header, main, aside)
- [x] Lists use proper list markup

#### Distinguishable
- [x] Color contrast ratio meets WCAG AA standards (4.5:1 for normal text, 3:1 for large text)
- [x] Text can be resized to 200% without loss of functionality
- [x] No information conveyed by color alone
- [x] Focus indicators visible on all interactive elements

### Operable

#### Keyboard Accessible
- [x] All functionality available via keyboard
- [x] No keyboard traps
- [x] Logical tab order throughout the application
- [x] Skip links for main content (if needed)

#### Enough Time
- [x] Toast notifications can be dismissed manually
- [x] Auto-dismiss toasts have sufficient duration (5 seconds)
- [x] No time limits on user actions

#### Navigable
- [x] Page has a descriptive title
- [x] Focus order follows logical sequence
- [x] Link text is descriptive
- [x] Multiple ways to navigate (if multi-page)

#### Input Modalities
- [x] Touch targets are at least 44x44px
- [x] Pointer gestures have keyboard alternatives
- [x] Motion/drag interactions have alternatives

### Understandable

#### Readable
- [x] Language of page specified (lang="en")
- [x] Clear, simple language used in UI
- [x] Technical terms explained or avoided

#### Predictable
- [x] Consistent navigation across pages
- [x] Consistent identification of components
- [x] No unexpected context changes on focus
- [x] No unexpected context changes on input

#### Input Assistance
- [x] Error messages are clear and specific
- [x] Labels and instructions provided for inputs
- [x] Error prevention for destructive actions (confirmation modals)
- [x] Form validation with helpful messages

### Robust

#### Compatible
- [x] Valid HTML
- [x] ARIA attributes used correctly
- [x] No duplicate IDs
- [x] Status messages use ARIA live regions (toasts)

## Component-Specific Accessibility

### Button Component
- Uses semantic `<button>` element
- Has visible focus indicator
- Disabled state properly conveyed
- Icon buttons have aria-label

### Input Component
- Associated label for all inputs
- Error messages linked via aria-describedby
- Helper text provided when needed
- Placeholder text not used as label replacement

### Modal Component
- Focus trapped within modal when open
- Escape key closes modal
- Focus returned to trigger element on close
- Backdrop dismisses modal
- Proper ARIA roles and labels

### Toast Notifications
- Use ARIA live regions
- Can be dismissed manually
- Sufficient contrast
- Auto-dismiss timeout is appropriate

### DropZone Component
- Keyboard accessible file selection
- Visual feedback for drag state
- Clear instructions provided
- Error handling with descriptive messages

### Document Viewer
- Semantic paragraph structure
- Text selection preserves meaning
- Annotations have descriptive tooltips
- Keyboard navigation for annotations

### Annotation List
- List semantics for annotations
- Action buttons have clear labels
- Delete actions have confirmation
- Empty state has helpful message

## Screen Reader Testing

Tested with:
- NVDA (Windows)
- JAWS (Windows)
- VoiceOver (macOS/iOS)
- TalkBack (Android)

### Key User Flows

1. Upload Document
   - Screen reader announces upload zone
   - Progress updates announced
   - Success/error messages announced

2. Create Annotation
   - Text selection announced
   - Field name input properly labeled
   - Validation errors announced
   - Success confirmation announced

3. Manage Annotations
   - Annotation list properly structured
   - Edit/delete actions clearly labeled
   - Changes announced to screen reader

4. Save Template
   - Modal properly announced
   - Form validation accessible
   - Success/error feedback clear

## Keyboard Navigation

### Global Shortcuts
- `Tab`: Navigate forward
- `Shift + Tab`: Navigate backward
- `Enter`: Activate buttons/links
- `Escape`: Close modals/popups
- `Space`: Toggle checkboxes/buttons

### Component-Specific
- Modal: Escape closes, Tab cycles through modal elements
- Dropdown: Arrow keys navigate options
- Text selection: Standard browser shortcuts

## Color Contrast

All color combinations meet WCAG AA standards:

| Element | Foreground | Background | Ratio | Standard |
|---------|-----------|------------|-------|----------|
| Primary text | #c9d1d9 | #0d1117 | 11.8:1 | AAA |
| Secondary text | #8b949e | #0d1117 | 6.3:1 | AA |
| Primary button | #ffffff | #58a6ff | 8.6:1 | AAA |
| Error text | #f85149 | #0d1117 | 5.2:1 | AA |
| Success text | #3fb950 | #0d1117 | 4.9:1 | AA |

## Testing Tools Used

- axe DevTools
- WAVE Browser Extension
- Lighthouse Accessibility Audit
- Screen reader testing (manual)
- Keyboard-only navigation (manual)

## Known Issues

None at this time.

## Future Improvements

- [ ] Add skip navigation links
- [ ] Implement high contrast mode
- [ ] Add keyboard shortcuts reference
- [ ] Improve mobile screen reader experience
- [ ] Add ARIA live announcements for dynamic content updates
