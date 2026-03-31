/**
 * Modal helpers for Lab Demo Manager
 */

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
