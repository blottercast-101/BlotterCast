// ============================================================
// JS LOGIC RESTORATION (clearance.js)
// ============================================================

const residentInput = document.getElementById('residentSearch');
const resultsMenu = document.getElementById('residentResultsMenu');

function selectResidentForClearance(residentId) {
  const numId = Number(residentId);
  const sourceList = Array.isArray(window.censusResidents) 
    ? window.censusResidents 
    : (typeof residentOptions !== 'undefined' && Array.isArray(residentOptions) ? residentOptions : []);
  const r = sourceList.find(x => Number(x.id) === numId);
  if (!r) return;

  const input = document.getElementById('residentSearch') || residentInput;
  if (input) {
    input.value = `${r.last_name || r.lastName}, ${r.first_name || r.firstName} ${r.middle_name || r.middleName || ''}`.trim();
  }

  const hidden = document.getElementById('cl_residentId');
  if (hidden) hidden.value = String(numId);

  // Invoke existing fill and eligibility/blotter validation function
  if (typeof onResidentPicked === 'function') {
    onResidentPicked(r);
  }
}
window.selectResidentForClearance = selectResidentForClearance;

function renderResidentsList(query = '') {
  const menu = resultsMenu || document.getElementById('residentResultsMenu');
  if (!menu) return;

  // Use existing global or cached resident list (e.g., window.censusResidents)
  const sourceList = Array.isArray(window.censusResidents) ? window.censusResidents : [];
  
  // Filter: skip deceased, match query
  const filtered = sourceList.filter(resident => {
    const status = String(resident.status || resident.census_status || '').toLowerCase().trim();
    if (status === 'deceased' || resident.is_deceased === 1 || resident.is_deceased === true) {
      return false; // Skip deceased completely
    }
    
    const fullName = `${resident.first_name || ''} ${resident.last_name || ''}`.toLowerCase();
    const reverseName = `${resident.last_name || ''} ${resident.first_name || ''}`.toLowerCase();
    const q = query.toLowerCase();
    return fullName.includes(q) || reverseName.includes(q);
  });

  if (filtered.length === 0) {
    menu.innerHTML = '<div class="p-3 text-xs text-[#52796f] text-center">No matching residents found</div>';
  } else {
    menu.innerHTML = filtered.map(r => {
      const isTransferred = String(r.status || r.census_status || '').toLowerCase() === 'transferred';
      return `
        <div 
          class="resident-option px-3 py-2 text-sm border-b border-gray-100 flex items-center justify-between ${isTransferred ? 'opacity-40 cursor-not-allowed bg-gray-50' : 'cursor-pointer hover:bg-[#edf5f0] text-[#1e3a2b]'}"
          data-id="${r.id}"
          data-transferred="${isTransferred}"
        >
          <div>
            <div class="font-medium">${r.last_name}, ${r.first_name} ${r.middle_name || ''}</div>
            <div class="text-[11px] text-[#52796f]">Zone ${r.zone || ''} • Household ${r.household_no || ''}</div>
          </div>
          ${isTransferred ? '<span class="text-[10px] bg-amber-100 text-amber-800 px-1.5 py-0.5 rounded font-semibold">TRANSFERRED</span>' : ''}
        </div>
      `;
    }).join('');
  }

  if (resultsMenu) {
    resultsMenu.classList.remove('hidden');
  } else {
    const menu = document.getElementById('residentResultsMenu');
    if (menu) menu.classList.remove('hidden');
  }
}
window.renderResidentsList = renderResidentsList;

// Trigger on typing
if (residentInput) {
  residentInput.addEventListener('input', (e) => {
    const val = e.target.value.trim();
    if (val.length > 0) {
      renderResidentsList(val);
    } else {
      const menu = document.getElementById('residentResultsMenu') || resultsMenu;
      if (menu) menu.classList.add('hidden');
    }
  });

  // Trigger on focus ONLY if there is already text
  residentInput.addEventListener('focus', () => {
    if (residentInput.value.trim().length > 0) {
      renderResidentsList(residentInput.value.trim());
    }
  });
}

// Delegate selection click
if (resultsMenu) {
  resultsMenu.addEventListener('click', (e) => {
    const option = e.target.closest('.resident-option');
    if (!option || option.dataset.transferred === 'true') return;

    const residentId = option.dataset.id;
    selectResidentForClearance(residentId); // Call your existing fill function
    resultsMenu.classList.add('hidden');
  });
}

// Hide on outside click
document.addEventListener('click', (e) => {
  const menu = document.getElementById('residentResultsMenu') || resultsMenu;
  const input = document.getElementById('residentSearch') || residentInput;
  if (menu && !menu.contains(e.target) && e.target !== input) {
    menu.classList.add('hidden');
  }
});

// Re-bind when elements appear dynamically
function initClearanceSearchEvents() {
  const curInput = document.getElementById('residentSearch');
  const curMenu = document.getElementById('residentResultsMenu');

  if (curInput && !curInput.dataset.clearanceSearchBound) {
    curInput.dataset.clearanceSearchBound = '1';
    curInput.addEventListener('input', (e) => {
      const val = e.target.value.trim();
      const menu = document.getElementById('residentResultsMenu') || curMenu;
      if (val.length > 0) {
        renderResidentsList(val);
      } else if (menu) {
        menu.classList.add('hidden');
      }
    });

    curInput.addEventListener('focus', () => {
      if (curInput.value.trim().length > 0) {
        renderResidentsList(curInput.value.trim());
      }
    });
  }

  if (curMenu && !curMenu.dataset.clearanceResultsBound) {
    curMenu.dataset.clearanceResultsBound = '1';
    curMenu.addEventListener('click', (e) => {
      const option = e.target.closest('.resident-option');
      if (!option || option.dataset.transferred === 'true') return;

      const residentId = option.dataset.id;
      selectResidentForClearance(residentId);
      curMenu.classList.add('hidden');
    });
  }
}
window.initClearanceSearchEvents = initClearanceSearchEvents;
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initClearanceSearchEvents);
} else {
  initClearanceSearchEvents();
}
