/**
 * frontend/public/js/predictions.js
 * Predictive Insights & ML Model Synchronization Module for BlotterCast
 */

let retrainStepInterval = null;
const RETRAIN_STEPS = [
  'Aggregating live blotter & incident records...',
  'Building spatiotemporal zone features...',
  'Fitting Random Forest & Gradient Boosting models...',
  'Evaluating accuracy & 14-day risk forecasts...',
  'Finalizing predictions...'
];

/**
 * Opens and animates the centered Loading / Progress Modal for model retraining.
 */
function showRetrainModal() {
  const modal = document.getElementById('retrainModal') || document.getElementById('trainModal');
  const content = document.getElementById('retrainModalContent');
  const stepText = document.getElementById('retrainStepText');
  
  if (stepText) stepText.textContent = RETRAIN_STEPS[0];
  
  if (modal) {
    modal.classList.remove('hidden');
    // Trigger reflow for smooth opacity transition
    void modal.offsetWidth;
    modal.classList.remove('opacity-0');
    modal.classList.add('opacity-100');
  }
  if (content) {
    content.classList.remove('scale-95');
    content.classList.add('scale-100');
  }

  let stepIdx = 0;
  clearInterval(retrainStepInterval);
  retrainStepInterval = setInterval(() => {
    stepIdx = (stepIdx + 1) % RETRAIN_STEPS.length;
    if (stepText) stepText.textContent = RETRAIN_STEPS[stepIdx];
  }, 1200);
}

/**
 * Smoothly hides and closes the Retrain Loading Modal.
 */
function hideRetrainModal() {
  clearInterval(retrainStepInterval);
  const modal = document.getElementById('retrainModal') || document.getElementById('trainModal');
  const content = document.getElementById('retrainModalContent');
  
  if (modal) {
    modal.classList.remove('opacity-100');
    modal.classList.add('opacity-0');
  }
  if (content) {
    content.classList.remove('scale-100');
    content.classList.add('scale-95');
  }
  setTimeout(() => {
    if (modal) modal.classList.add('hidden');
  }, 300);
}

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
  module.exports = {
    showRetrainModal,
    hideRetrainModal,
    formatModelTrainedDate,
    updateModelTrainedBadge,
    RETRAIN_STEPS
  };
}
