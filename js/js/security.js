/**
 * Chinawheely Security Library v1.0
 * Pure JavaScript security utilities for static HTML websites
 * Replaces lib/security.ts from Next.js implementation
 */

(function() {
  'use strict';

  const Security = {
    // === XSS SANITIZATION ===
    sanitizeInput(input) {
      if (typeof input !== 'string') return '';
      return input
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#x27;')
        .replace(/\//g, '&#x2F;');
    },

    // === VALIDATE EMAIL ===
    isValidEmail(email) {
      const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      return re.test(String(email).toLowerCase());
    },

    // === VALIDATE PHONE ===
    isValidPhone(phone) {
      const re = /^[\d\s\-\+\(\)]{7,20}$/;
      return re.test(String(phone));
    },

    // === CHECK INPUT LENGTH (prevent long param attacks) ===
    checkLength(input, max = 500) {
      if (typeof input !== 'string') return false;
      return input.length <= max;
    },

    // === CHECK FOR SUSPICIOUS PATTERNS ===
    hasSuspiciousPattern(input) {
      if (typeof input !== 'string') return false;
      const patterns = [
        /<script/i,
        /javascript:/i,
        /on\w+\s*=/i,
        /eval\s*\(/i,
        /document\.cookie/i,
        /document\.write/i,
        /window\.location/i,
        /union\s+select/i,
        /drop\s+table/i,
        /\.\.\//,
        /\.\.\\/
      ];
      return patterns.some(p => p.test(input));
    },

    // === RATE LIMITING (client-side) ===
    rateLimiter: {
      attempts: {},
      maxAttempts: 5,
      windowMs: 60000, // 1 minute

      check(key) {
        const now = Date.now();
        if (!this.attempts[key]) {
          this.attempts[key] = { count: 1, resetTime: now + this.windowMs };
          return true;
        }
        
        if (now > this.attempts[key].resetTime) {
          this.attempts[key] = { count: 1, resetTime: now + this.windowMs };
          return true;
        }
        
        if (this.attempts[key].count >= this.maxAttempts) {
          return false;
        }
        
        this.attempts[key].count++;
        return true;
      }
    },

    // === FORM VALIDATION ===
    validateForm(formData) {
      const errors = [];
      
      for (const [key, value] of Object.entries(formData)) {
        if (!this.checkLength(value)) {
          errors.push(`${key} exceeds maximum length`);
        }
        if (this.hasSuspiciousPattern(value)) {
          errors.push(`${key} contains invalid characters`);
        }
      }
      
      return errors;
    },

    // === HONEYPOT CHECK ===
    checkHoneypot(fieldName = 'website') {
      const field = document.querySelector(`[name="${fieldName}"]`);
      return !field || !field.value;
    },

    // === ORIGIN CHECK ===
    isValidOrigin() {
      const allowedOrigins = [
        'https://www.Chinawheely.com',
        'https://chinawheely.com'
      ];
      return allowedOrigins.includes(window.location.origin);
    },

    // === SECURE COOKIE SETTER ===
    setSecureCookie(name, value, days = 7) {
      const expires = new Date(Date.now() + days * 864e5).toUTCString();
      document.cookie = `${name}=${encodeURIComponent(value)}; expires=${expires}; path=/; Secure; SameSite=Strict`;
    },

    // === CLEAR SENSITIVE DATA ===
    clearSensitiveData() {
      if (window.console && window.console.clear) {
        console.clear();
      }
    }
  };

  // === PROTECT AGAINST COMMON ATTACKS ===
  
  // 1. Prevent iframe clickjacking
  if (window.self !== window.top) {
    window.top.location = window.self.location;
  }

  // 2. Block right-click on images (optional, can be commented out)
  document.addEventListener('contextmenu', function(e) {
    if (e.target.tagName === 'IMG') {
      e.preventDefault();
    }
  });

  // 3. Detect and warn about DevTools (production only)
  if (window.location.hostname === 'www.Chinawheely.com') {
    const threshold = 160;
    setInterval(() => {
      if (window.outerWidth - window.innerWidth > threshold || 
          window.outerHeight - window.innerHeight > threshold) {
        console.clear();
        console.log('%c🔒 Security Notice', 'color: #e74c3c; font-size: 20px; font-weight: bold;');
        console.log('%cThis is a browser feature intended for developers.', 'color: #333;');
      }
    }, 1000);
  }

  // 4. Sanitize URL parameters
  function sanitizeURL() {
    const url = new URL(window.location.href);
    let hasChange = false;
    
    for (const [key, value] of url.searchParams) {
      if (Security.hasSuspiciousPattern(value)) {
        url.searchParams.delete(key);
        hasChange = true;
      }
    }
    
    if (hasChange) {
      window.history.replaceState({}, '', url.toString());
    }
  }
  
  // Run on load
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', sanitizeURL);
  } else {
    sanitizeURL();
  }

  // Expose Security object globally
  window.ChinawheelySecurity = Security;

})();
