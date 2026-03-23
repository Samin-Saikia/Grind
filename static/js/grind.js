// Auto-dismiss flash messages after 4 seconds
(function() {
  var flashes = document.querySelectorAll('.flash');
  flashes.forEach(function(flash) {
    setTimeout(function() {
      flash.style.transition = 'opacity 0.4s ease';
      flash.style.opacity = '0';
      setTimeout(function() {
        if (flash.parentNode) flash.parentNode.removeChild(flash);
      }, 400);
    }, 4000);
  });
})();

// Task note input - expand on focus
(function() {
  var noteInputs = document.querySelectorAll('.task-note-input');
  noteInputs.forEach(function(input) {
    input.addEventListener('focus', function() {
      this.style.borderColor = 'var(--accent)';
    });
    input.addEventListener('blur', function() {
      if (!this.value) {
        this.style.borderColor = '';
      }
    });
  });
})();

// Confirm before skip/quit forms submit
(function() {
  // Already handled with onclick on buttons, this is a fallback safety
  var dangerForms = document.querySelectorAll('form[data-confirm]');
  dangerForms.forEach(function(form) {
    form.addEventListener('submit', function(e) {
      var msg = form.getAttribute('data-confirm');
      if (!confirm(msg)) {
        e.preventDefault();
      }
    });
  });
})();
