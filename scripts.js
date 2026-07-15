// Chinawheely — Main Scripts
// Handles: navigation, FAQ accordion, mobile menu, scroll animations, toast notifications

document.addEventListener('DOMContentLoaded', function() {
  initNav();
  initFAQ();
  initMobileMenu();
  initScrollAnimations();
});

// ===== Navigation =====
function initNav() {
  const navbar = document.getElementById('navbar');
  if (!navbar) return;

  let lastScroll = 0;
  window.addEventListener('scroll', function() {
    const currentScroll = window.pageYOffset;
    if (currentScroll > 50) {
      navbar.classList.add('scrolled');
    } else {
      navbar.classList.remove('scrolled');
    }
    lastScroll = currentScroll;
  });

  // Smooth scroll for anchor links
  document.querySelectorAll('a[href^="#"]').forEach(link => {
    link.addEventListener('click', function(e) {
      const target = document.querySelector(this.getAttribute('href'));
      if (target) {
        e.preventDefault();
        const offset = 80;
        const targetPosition = target.getBoundingClientRect().top + window.pageYOffset - offset;
        window.scrollTo({ top: targetPosition, behavior: 'smooth' });
      }
    });
  });
}

// ===== FAQ Accordion =====
function initFAQ() {
  document.querySelectorAll('.faq-item').forEach(item => {
    const question = item.querySelector('.faq-question');
    if (question) {
      question.addEventListener('click', function() {
        const isActive = item.classList.contains('active');
        // Close all
        document.querySelectorAll('.faq-item').forEach(i => i.classList.remove('active'));
        // Open clicked if it wasn't active
        if (!isActive) {
          item.classList.add('active');
        }
      });
    }
  });
}

// ===== Mobile Menu =====
function initMobileMenu() {
  const toggle = document.getElementById('mobileToggle');
  const menu = document.getElementById('mobileMenu');
  if (!toggle || !menu) return;

  toggle.addEventListener('click', function() {
    const isOpen = menu.style.display === 'flex';
    menu.style.display = isOpen ? 'none' : 'flex';
    document.body.style.overflow = isOpen ? '' : 'hidden';
  });

  menu.querySelectorAll('a').forEach(link => {
    link.addEventListener('click', function() {
      menu.style.display = 'none';
      document.body.style.overflow = '';
    });
  });
}

// ===== Scroll Animations =====
function initScrollAnimations() {
  const observerOptions = {
    root: null,
    rootMargin: '0px',
    threshold: 0.1
  };

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('animate-fade-in-up');
        observer.unobserve(entry.target);
      }
    });
  }, observerOptions);

  document.querySelectorAll('.card, .process-step, .testimonial-card').forEach(el => {
    el.style.opacity = '0';
    observer.observe(el);
  });
}

// ===== Toast Notifications =====
function showToast(message, type = 'success') {
  const toast = document.getElementById('toast');
  const toastIcon = document.getElementById('toastIcon');
  const toastMessage = document.getElementById('toastMessage');
  if (!toast) return;

  toastMessage.textContent = message;
  toastIcon.textContent = type === 'success' ? '✓' : '✕';
  toast.className = 'toast show toast-' + type;

  setTimeout(() => {
    toast.classList.remove('show');
  }, 4000);
}

// ===== Service Option Selection =====
function initServiceOptions() {
  document.querySelectorAll('.service-option').forEach(label => {
    const input = label.querySelector('input[type="radio"]');
    const box = label.querySelector('.service-option-box');
    if (!input || !box) return;

    function update() {
      document.querySelectorAll('.service-option-box').forEach(b => {
        b.style.borderColor = 'var(--color-gray-200)';
      });
      if (input.checked) {
        box.style.borderColor = 'var(--color-primary)';
      }
    }

    input.addEventListener('change', update);
    update();
  });
}

// ===== Vehicle Option Selection =====
function initVehicleOptions() {
  document.querySelectorAll('.vehicle-option').forEach(label => {
    const input = label.querySelector('input[type="radio"]');
    const box = label.querySelector('.vehicle-option-box');
    if (!input || !box) return;

    function update() {
      document.querySelectorAll('.vehicle-option-box').forEach(b => {
        b.style.borderColor = 'var(--color-gray-200)';
      });
      if (input.checked) {
        box.style.borderColor = 'var(--color-primary)';
      }
    }

    input.addEventListener('change', update);
    update();
  });
}

// ===== WhatsApp Modal =====
function openWhatsappModal() {
  const modal = document.getElementById('whatsappModal');
  if (modal) modal.classList.add('active');
}
function closeWhatsappModal() {
  const modal = document.getElementById('whatsappModal');
  if (modal) modal.classList.remove('active');
}

document.addEventListener('DOMContentLoaded', function() {
  const waModal = document.getElementById('whatsappModal');
  if (waModal) {
    waModal.addEventListener('click', function(e) {
      if (e.target === this) closeWhatsappModal();
    });
  }
});

// ============================================================
// Global event delegation for data-action attributes
// Replaces inline onclick handlers (CSP compliance)
// ============================================================
document.addEventListener('click', function(e) {
  const target = e.target.closest('[data-action]');
  if (!target) return;

  const action = target.dataset.action;

  switch (action) {
    case 'open-whatsapp':
      e.preventDefault();
      openWhatsappModal();
      break;
    case 'close-whatsapp':
      e.preventDefault();
      closeWhatsappModal();
      break;
    case 'switch-payment':
      e.preventDefault();
      const tab = target.dataset.tab;
      if (typeof switchPaymentTab === 'function') switchPaymentTab(tab);
      break;
    case 'submit-booking':
      e.preventDefault();
      if (typeof submitBooking === 'function') submitBooking();
      break;
    case 'close-payment':
      e.preventDefault();
      if (typeof closePaymentModal === 'function') closePaymentModal();
      break;
    case 'stop-propagation':
      e.stopPropagation();
      break;
  }
});
