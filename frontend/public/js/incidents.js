/**
 * BlotterCast Incident Helpers & Status Badges
 * Centralized status badge color mapping and elevation helpers.
 */

function getStatusBadge(status) {
  const s = String(status || '').toUpperCase().trim();

  switch (s) {
    case 'UNDER INVESTIGATION':
      return 'bg-amber-100 text-amber-800 border border-amber-300';

    case 'ELEVATED':
    case 'ELEVATED TO BLOTTER':
      // Enforce consistent soft red styling
      return 'bg-red-100 text-red-700 border border-red-200';

    case 'SETTLED':
    case 'RESOLVED':
      return 'bg-emerald-100 text-emerald-800 border border-emerald-300';

    default:
      return 'bg-gray-100 text-gray-700 border border-gray-200';
  }
}

if (typeof window !== 'undefined') {
  window.getStatusBadge = getStatusBadge;
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { getStatusBadge };
}
