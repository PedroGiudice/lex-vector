/**
 * Groups sessions by date category (Today, Yesterday, This Week, Older)
 * @param {Array} sessions - Array of session objects with lastModified field
 * @returns {Object} Object with date groups as keys and sessions as values
 */
export function groupSessionsByDate(sessions) {
  if (!sessions || !Array.isArray(sessions)) {
    return {};
  }

  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const yesterday = new Date(today);
  yesterday.setDate(yesterday.getDate() - 1);
  const weekAgo = new Date(today);
  weekAgo.setDate(weekAgo.getDate() - 7);

  const groups = {
    'Today': [],
    'Yesterday': [],
    'This Week': [],
    'Older': []
  };

  sessions.forEach(session => {
    const sessionDate = new Date(session.lastModified || session.createdAt || Date.now());
    const sessionDay = new Date(sessionDate.getFullYear(), sessionDate.getMonth(), sessionDate.getDate());

    if (sessionDay.getTime() === today.getTime()) {
      groups['Today'].push(session);
    } else if (sessionDay.getTime() === yesterday.getTime()) {
      groups['Yesterday'].push(session);
    } else if (sessionDay >= weekAgo) {
      groups['This Week'].push(session);
    } else {
      groups['Older'].push(session);
    }
  });

  // Remove empty groups
  Object.keys(groups).forEach(key => {
    if (groups[key].length === 0) {
      delete groups[key];
    }
  });

  return groups;
}

/**
 * Formats a date/timestamp to a time string
 * @param {Date|string|number} date - Date to format
 * @returns {string} Formatted time string (e.g., "14:30")
 */
export function formatTime(date) {
  if (!date) return '';
  return new Date(date).toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit'
  });
}

/**
 * Formats a date to a relative string (e.g., "2 hours ago")
 * @param {Date|string|number} date - Date to format
 * @returns {string} Relative time string
 */
export function formatRelativeTime(date) {
  if (!date) return '';

  const now = new Date();
  const then = new Date(date);
  const diffMs = now - then;
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  if (diffHours < 24) return `${diffHours}h ago`;
  if (diffDays < 7) return `${diffDays}d ago`;

  return then.toLocaleDateString();
}
