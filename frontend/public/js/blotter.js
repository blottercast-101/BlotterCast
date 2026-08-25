/**
 * frontend/public/js/blotter.js
 * Legacy CSV/Excel Import Drag & Drop AJAX Handler with Dual Route Dispatch
 */

/**
 * Generates and downloads a standardized CSV template for client import
 * @param {'entry' | 'settlement'} type
 */
function downloadBlotterTemplate(type = 'entry') {
  let csvContent = '';
  let filename = '';

  if (type === 'settlement') {
    csvContent = "DOCKET NO.,HEARING DATE,STAGE,SETTLEMENT STATUS,REMARKS\n" +
      "BLT-2025-0001,2025-06-20,1st Patawag,Ongoing,Parties agreed to return property on next confrontation.\n" +
      "BLT-2025-0002,2025-06-22,2nd Patawag,Settled,Amicably resolved before Barangay Lupon.\n";
    filename = 'blotter_settlement_template.csv';
  } else {
    csvContent = "DOCKET NO.,DATE FILED,NAME OF COMPLAINANT,COMPLAINANT ADDRESS,NAME OF RESPONDENT,RESPONDENT ADDRESS,NATURE OF CASE,CRIM / CIVIL,ZONE\n" +
      "BLT-2025-0001,2025-06-15,\"Marquez, Everlie\",123 Sampaguita St.,\"Dela Cruz, Juan\",456 Rosas St.,Theft,CRIM,Zone 1\n" +
      "BLT-2025-0002,2025-06-18,\"Santos, Maria\",Zone 2,Unknown Suspect,,Physical Assault,CRIM,Zone 2\n";
    filename = 'blotter_entry_template.csv';
  }

  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.setAttribute('href', url);
  link.setAttribute('download', filename);
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

/**
 * Initializes Drag and Drop and File Input listeners for Blotter Import Modal
 */
function initBlotterImportHandler(options = {}) {
  const dropzone = document.getElementById('importDropzone') || document.getElementById('importBlotterModal');
  const fileInput = document.getElementById('blotterImportFile');
  const statusEl = document.getElementById('importStatus');
  const modalId = options.modalId || 'importModal';
  const onSuccess = options.onSuccess || (() => window.location.reload());

  if (!dropzone || !fileInput) return;

  ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    dropzone.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
    }, false);
  });

  ['dragenter', 'dragover'].forEach(eventName => {
    dropzone.addEventListener(eventName, () => {
      dropzone.classList.add('border-emerald-500', 'bg-emerald-50');
    }, false);
  });

  ['dragleave', 'drop'].forEach(eventName => {
    dropzone.addEventListener(eventName, () => {
      dropzone.classList.remove('border-emerald-500', 'bg-emerald-50');
    }, false);
  });

  dropzone.addEventListener('drop', (e) => {
    const dt = e.dataTransfer;
    const files = dt.files;
    if (files && files.length > 0) {
      uploadBlotterFile(files[0]);
    }
  }, false);

  fileInput.addEventListener('change', (e) => {
    if (e.target.files && e.target.files.length > 0) {
      uploadBlotterFile(e.target.files[0]);
    }
  });

  /**
   * Uploads file to either /api/import/blotter-entry or /api/import/blotter-settlement
   */
  async function uploadBlotterFile(file) {
    if (!file) return;
    const ext = file.name.split('.').pop().toLowerCase();
    if (!['csv', 'xlsx', 'xls'].includes(ext)) {
      if (typeof showToast === 'function') {
        showToast('Invalid file format. Please upload a .csv or .xlsx file.', 'error');
      } else {
        alert('Invalid file format. Please upload a .csv or .xlsx file.');
      }
      return;
    }

    const importType = document.querySelector('input[name="blotterImportType"]:checked')?.value || 'blotter-entry';
    const isSettlement = importType === 'blotter-settlement';
    const routeName = isSettlement ? 'Blotter Record (Settlement)' : 'Blotter Entry Record';

    if (statusEl) {
      statusEl.innerHTML = `
        <div class="flex items-center gap-2 text-forest-700 py-2">
          <svg class="animate-spin h-5 w-5 text-emerald-600" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z"></path>
          </svg>
          <span>Uploading and processing <strong>${file.name}</strong> as <em>${routeName}</em>...</span>
        </div>
      `;
    }

    const formData = new FormData();
    formData.append('file', file);
    formData.append('importType', importType);

    try {
      const endpoint = isSettlement ? '/api/import/blotter-settlement' : '/api/import/blotter-entry';
      const response = await fetch(endpoint, {
        method: 'POST',
        body: formData,
      });

      const resData = await response.json();

      if (!response.ok || !resData.ok) {
        throw new Error(resData.error || 'Failed to process import.');
      }

      const successMsg = resData.message || (isSettlement
        ? `Successfully processed ${resData.updated || 0} Blotter Settlement records.`
        : `Successfully imported ${resData.imported || 0} Blotter Entry records with linked incident backfills.`);

      if (statusEl) {
        statusEl.innerHTML = `<span class="text-emerald-600 font-semibold">✓ ${successMsg}</span>`;
      }

      if (typeof showToast === 'function') {
        showToast(successMsg, 'success');
      }

      setTimeout(() => {
        if (typeof closeModal === 'function') closeModal(modalId);
        if (typeof onSuccess === 'function') onSuccess(resData);
      }, 1200);
    } catch (err) {
      console.error('[blotterImport] Error:', err);
      if (statusEl) {
        statusEl.innerHTML = `<span class="text-rose-600 font-semibold">✗ Error: ${err.message}</span>`;
      }
      if (typeof showToast === 'function') {
        showToast(`Import failed: ${err.message}`, 'error');
      }
    } finally {
      fileInput.value = '';
    }
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = {
    initBlotterImportHandler,
    downloadBlotterTemplate,
  };
}
