/**
 * Lab Demo Manager — client-side helpers
 */

// ---------------------------------------------------------------------------
// Modal helpers
// ---------------------------------------------------------------------------

function openModal(id) {
  const modal = document.getElementById(id);
  if (modal) {
    modal.classList.remove('hidden');
    document.body.style.overflow = 'hidden';
  }
}

function closeModal(id) {
  const modal = document.getElementById(id);
  if (modal) {
    modal.classList.add('hidden');
    document.body.style.overflow = '';
  }
}

// Close modal on Escape key
document.addEventListener('keydown', function (e) {
  if (e.key === 'Escape') {
    document.querySelectorAll('[id]').forEach(function (el) {
      if (el.classList.contains('fixed') && !el.classList.contains('hidden')) {
        el.classList.add('hidden');
        document.body.style.overflow = '';
      }
    });
  }
});

// ---------------------------------------------------------------------------
// Private IP validation (frontend hint for server management form)
// ---------------------------------------------------------------------------

const _PRIVATE_RANGES = [
  { start: ip2int('10.0.0.0'),    end: ip2int('10.255.255.255') },
  { start: ip2int('172.16.0.0'),  end: ip2int('172.31.255.255') },
  { start: ip2int('192.168.0.0'), end: ip2int('192.168.255.255') },
];

function ip2int(ip) {
  return ip.split('.').reduce((acc, octet) => (acc * 256) + parseInt(octet, 10), 0) >>> 0;
}

function isValidIPv4(ip) {
  const parts = ip.split('.');
  if (parts.length !== 4) return false;
  return parts.every(p => /^\d+$/.test(p) && parseInt(p, 10) >= 0 && parseInt(p, 10) <= 255);
}

function isPrivateIP(ip) {
  if (!isValidIPv4(ip)) return false;
  const n = ip2int(ip);
  return _PRIVATE_RANGES.some(r => n >= r.start && n <= r.end);
}

/**
 * Called oninput on IP address fields.  Updates the hint text and border
 * colour so the user gets immediate feedback.
 */
function validatePrivateIP(input) {
  const val = input.value.trim();
  const hintId = input.getAttribute('data-hint') ||
                 (input.id ? input.id + '-hint' : null);
  const hint = hintId ? document.getElementById(hintId) : null;

  if (!val) {
    input.classList.remove('border-red-400', 'border-green-400');
    if (hint) { hint.textContent = 'Must be an internal LAN address (10.x.x.x, 172.16-31.x.x, 192.168.x.x).'; hint.className = 'mt-1 text-xs text-gray-400'; }
    return;
  }

  if (isPrivateIP(val)) {
    input.classList.remove('border-red-400'); input.classList.add('border-green-400');
    if (hint) { hint.textContent = '✓ Valid internal IP address.'; hint.className = 'mt-1 text-xs text-green-600'; }
  } else {
    input.classList.remove('border-green-400'); input.classList.add('border-red-400');
    if (hint) { hint.textContent = '✗ Not a private LAN address. External IPs are not allowed.'; hint.className = 'mt-1 text-xs text-red-500'; }
  }
}

// ---------------------------------------------------------------------------
// Sortable table helper
// ---------------------------------------------------------------------------

const _tableSortState = {};

/**
 * Sort a <table> by the given column index (0-based).
 * Uses data-col-N attributes on <tr> if present, otherwise cell text.
 * @param {string} tableId
 * @param {number} colIndex
 * @param {HTMLElement} thEl   — the clicked <th> element
 */
function sortTable(tableId, colIndex, thEl) {
  const table = document.getElementById(tableId);
  if (!table) return;

  const key = tableId + ':' + colIndex;
  const currentDir = _tableSortState[key] || 'none';
  const newDir = currentDir === 'asc' ? 'desc' : 'asc';
  _tableSortState[key] = newDir;

  // Update sort indicators on all headers
  table.querySelectorAll('thead th .sort-indicator').forEach(el => { el.textContent = ''; });
  const indicator = thEl ? thEl.querySelector('.sort-indicator') : null;
  if (indicator) indicator.textContent = newDir === 'asc' ? ' ↑' : ' ↓';

  const tbody = table.querySelector('tbody');
  const rows = Array.from(tbody.querySelectorAll('tr'));

  rows.sort((a, b) => {
    const aRaw = a.dataset['col' + colIndex] !== undefined
      ? a.dataset['col' + colIndex]
      : (a.cells[colIndex] ? a.cells[colIndex].textContent.trim() : '');
    const bRaw = b.dataset['col' + colIndex] !== undefined
      ? b.dataset['col' + colIndex]
      : (b.cells[colIndex] ? b.cells[colIndex].textContent.trim() : '');

    const aNum = parseFloat(aRaw);
    const bNum = parseFloat(bRaw);
    let cmp;
    if (!isNaN(aNum) && !isNaN(bNum)) {
      cmp = aNum - bNum;
    } else {
      cmp = aRaw.localeCompare(bRaw, undefined, { numeric: true, sensitivity: 'base' });
    }
    return newDir === 'asc' ? cmp : -cmp;
  });

  rows.forEach(row => tbody.appendChild(row));
}

