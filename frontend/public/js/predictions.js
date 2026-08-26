/**
 * frontend/public/js/predictions.js
 * Predictive Insights & ML Model Synchronization Module for BlotterCast
 */

/**
 * Parses an ISO trainedAt timestamp and formats it in the client's local timezone (Asia/Manila)
 * with the evaluated record count.
 *
 * @param {string} isoString - ISO formatted timestamp string (e.g. '2026-08-26T14:49:00.000Z')
 * @param {number} [recordCount=0] - Number of incident records evaluated
 * @returns {string} Formatted label string (e.g. "Model trained: Aug 26, 2026, 11:49 PM · 79 records")
 */
function formatModelTrainedDate(isoString, recordCount) {
  if (!isoString) return 'Not trained yet';
  const date = new Date(isoString);
  if (isNaN(date.getTime())) return 'Not trained yet';

  const formattedDate = date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric'
  });

  const formattedTime = date.toLocaleTimeString('en-US', {
    hour: 'numeric',
    minute: '2-digit',
    hour12: true
  });

  const count = (recordCount !== undefined && recordCount !== null) ? recordCount : 0;
  return `Model trained: ${formattedDate}, ${formattedTime} · ${count} records`;
}

/**
 * Updates the Model Trained badge in the UI given trainedAt and recordCount.
 * Supports both #modelTrainedBadge and #trainedStamp.
 *
 * @param {string} isoString
 * @param {number} [recordCount=0]
 */
function updateModelTrainedBadge(isoString, recordCount) {
  const text = formatModelTrainedDate(isoString, recordCount);
  const stamp = document.getElementById('trainedStamp');
  if (stamp) {
    stamp.textContent = text;
  }
  const badge = document.getElementById('modelTrainedBadge');
  if (badge && !stamp) {
    badge.innerHTML = `<span class="pulse-dot"></span><span>${text}</span>`;
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { formatModelTrainedDate, updateModelTrainedBadge };
}
