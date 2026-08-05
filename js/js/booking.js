// ========== CITY TIER PRICING ==========
const TIER1 = ['beijing','shanghai','guangzhou','shenzhen'];     // 1.0
const TIER2 = ['chengdu','hangzhou','wuhan','chongqing','nanjing','suzhou','tianjin','xian','qingdao','xiamen','dalian','changsha','zhengzhou','harbin','jinan']; // 0.85
function getCityTierMultiplier(city) {
  if (!city) return 1.0;
  if (TIER1.includes(city)) return 1.0;
  if (TIER2.includes(city)) return 0.85;
  return 0.70; // Tier 3 — all other cities
}

// ========== BASE PRICES ==========
const basePrices = { economy: 50, business: 80, mpv: 105 };

// Update airport dropdown based on city
function updateAirportInfo() {
  const city = document.getElementById('city').value;
  const airportSelect = document.getElementById('airport');
  const infoEl = document.getElementById('airportDistanceInfo');
  const distRange = document.getElementById('distanceRange');

  if (!airportSelect) return;
  const currentVal = airportSelect.value;

  // Clear existing options
  while (airportSelect.firstChild) {
    airportSelect.removeChild(airportSelect.firstChild);
  }

  // Add default option
  const defaultOpt = document.createElement('option');
  defaultOpt.value = '';
  defaultOpt.disabled = true;
  defaultOpt.selected = true;
  defaultOpt.textContent = 'Select airport';
  airportSelect.appendChild(defaultOpt);

  // Add airport options from distance-db.js
  const airports = getAirportsForCity(city); // from distance-db.js
  airports.forEach(a => {
    const opt = document.createElement('option');
    opt.value = a.code;
    opt.textContent = a.name;
    airportSelect.appendChild(opt);
  });

  // Restore selection if possible
  if (currentVal && airports.find(a => a.code === currentVal)) {
    airportSelect.value = currentVal;
  }

  // Auto-populate distance range based on selected airport
  if (airportSelect.value && distRange) {
    const a = airports.find(x => x.code === airportSelect.value);
    if (a) {
      let range = '0-30';
      if (a.dist > 80) range = '80+';
      else if (a.dist > 50) range = '50-80';
      else if (a.dist > 30) range = '30-50';
      distRange.value = range;
      if (infoEl) {
        infoEl.textContent = a.name + ' — ~' + a.dist + ' km to city center';
      }
    }
  } else if (infoEl) {
    infoEl.textContent = '';
  }
  updateForm();
}

// ========== MAIN UPDATE FORM ==========
function updateForm() {
  const serviceType = document.querySelector('input[name="serviceType"]:checked').value;
  const city = document.getElementById('city').value;
  const vehicle = document.querySelector('input[name="vehicle"]:checked').value;
  const date = document.getElementById('date').value;
  const time = document.getElementById('time').value;
  const passengers = document.getElementById('passengers').value;
  const hours = document.getElementById('hours').value;
  const fromCity = document.getElementById('fromCity').value;
  const toCity = document.getElementById('toCity').value;
  const airport = document.getElementById('airport').value;
  const transferDirection = document.getElementById('transferDirection').value;
  const hotelAddress = document.getElementById('hotelAddress').value;
  const distanceRange = document.getElementById('distanceRange').value;
  const cityRoute = document.getElementById('cityRoute').value;

  // Toggle fields
  const airportFields = document.getElementById('airportFields');
  const cityFields = document.getElementById('cityFields');
  const intercityFields = document.getElementById('intercityFields');
  const flightGroup = document.getElementById('flightGroup');
  if (airportFields) airportFields.style.display = serviceType === 'airport' ? 'block' : 'none';
  if (cityFields) cityFields.style.display = serviceType === 'city' ? 'block' : 'none';
  if (intercityFields) intercityFields.style.display = serviceType === 'intercity' ? 'block' : 'none';
  if (flightGroup) flightGroup.style.display = serviceType === 'airport' ? 'block' : 'none';

  // ====== SMART DISTANCE ESTIMATION (from distance-db.js) ======
  if (serviceType === 'airport' && city && airport && hotelAddress) {
    const estimate = smartDistanceEstimate(hotelAddress, city, airport);
    if (estimate) {
      const infoEl = document.getElementById('airportDistanceInfo');
      if (infoEl) {
        // Build text content safely (no innerHTML)
        infoEl.textContent = '';
        const checkSpan = document.createElement('span');
        checkSpan.style.color = 'var(--color-primary)';
        checkSpan.textContent = '✓ ';
        infoEl.appendChild(checkSpan);
        infoEl.appendChild(document.createTextNode('Detected: ' + estimate.zone + ' — ~' + estimate.totalDist + ' km total'));
      }
      // Auto-update distance range if not manually changed by user
      const distRange = document.getElementById('distanceRange');
      if (distRange && !distRange.dataset.userChanged) {
        distRange.value = estimate.range;
      }
    }
  }

  // Update airport info when city changes
  if (serviceType === 'airport') {
    const airportSelect = document.getElementById('airport');
    const infoEl = document.getElementById('airportDistanceInfo');
    const airports = getAirportsForCity(city); // from distance-db.js
    if (airport && airportSelect) {
      const a = airports.find(x => x.code === airport);
      if (a && infoEl && !hotelAddress) {
        infoEl.textContent = a.name + ' — ~' + a.dist + ' km to city center';
      }
    }
  }

  // Update summary text
  const summaryService = document.getElementById('summaryService');
  if (summaryService) summaryService.textContent =
    serviceType === 'airport' ? 'Airport Transfer' :
    serviceType === 'city' ? 'City Car Service' : 'Intercity Trip';

  const summaryCity = document.getElementById('summaryCity');
  if (summaryCity) summaryCity.textContent = city ?
    city.charAt(0).toUpperCase() + city.slice(1) : '-';

  let routeText = '-';
  if (serviceType === 'airport' && airport && transferDirection) {
    const dir = transferDirection === 'airport-to-hotel' ? 'Pickup' : 'Drop-off';
    routeText = airport + ' ' + dir;
    if (hotelAddress) routeText += ' → ' + hotelAddress.substring(0, 30) + (hotelAddress.length > 30 ? '...' : '');
    if (distanceRange) routeText += ' (' + getDistanceRangeLabel(distanceRange) + ')';
  } else if (serviceType === 'city') {
    routeText = hours + ' hours';
    const cityDistRange = document.getElementById('cityDistanceRange').value;
    const distLabel = { '0-150': 'Within City', '150-300': 'Suburban', '300-500': 'Outside City' };
    routeText += ' (' + (distLabel[cityDistRange] || 'Within City') + ')';
    if (cityRoute) routeText += ' — ' + cityRoute;
  } else if (serviceType === 'intercity' && fromCity && toCity) {
    routeText = fromCity + ' → ' + toCity;
  }
  const summaryRoute = document.getElementById('summaryRoute');
  if (summaryRoute) summaryRoute.textContent = routeText;

  const summaryDateTime = document.getElementById('summaryDateTime');
  if (summaryDateTime) summaryDateTime.textContent = (date && time) ? (date + ' ' + time) : '-';

  const summaryVehicle = document.getElementById('summaryVehicle');
  if (summaryVehicle) summaryVehicle.textContent = vehicle.charAt(0).toUpperCase() + vehicle.slice(1);

  const summaryPassengers = document.getElementById('summaryPassengers');
  if (summaryPassengers) summaryPassengers.textContent = passengers;

  // ====== PRICE CALCULATION ======
  let price = basePrices[vehicle] || 51;
  const cityMult = getCityTierMultiplier(city);
  price *= cityMult;

  if (serviceType === 'airport') {
    // Airport: base × city × distance multiplier
    price *= getDistanceMultiplier(distanceRange);
  } else if (serviceType === 'city') {
    // City: base × city × hour multiplier × distance multiplier
    const hourMult = { '4': 1.0, '8': 1.8, '12': 2.5, 'custom': 2.0 };
    price *= (hourMult[hours] || 1.8);
    const cityDistRange = document.getElementById('cityDistanceRange').value;
    const distMult = { '0-150': 1.0, '150-300': 2.0, '300-500': 4.0 };
    price *= (distMult[cityDistRange] || 1.0);
  } else if (serviceType === 'intercity') {
    // Intercity: base × 1.5 (fixed)
    price *= 1.5;
  }

  // Round to nearest 5
  price = Math.round(price / 5) * 5;
  const summaryPrice = document.getElementById('summaryPrice');
  if (summaryPrice) summaryPrice.textContent = '$' + price;

  // Update vehicle price labels (show min price for this city & service)
  document.querySelectorAll('.vehicle-price').forEach(el => {
    const base = parseInt(el.dataset.base);
    let vPrice = base * cityMult;
    if (serviceType === 'airport') {
      // Use shortest distance (0-30 = 1.0) for the "From" price label
      vPrice *= 1.0;
    } else if (serviceType === 'city') {
      vPrice *= 1.0; // 4h minimum
      vPrice *= 1.0; // within city (0-150km) minimum
    } else if (serviceType === 'intercity') {
      vPrice *= 1.5;
    }
    vPrice = Math.round(vPrice / 5) * 5;
    el.textContent = 'From $' + vPrice;
  });

  // Extras
  const extras = Array.from(document.querySelectorAll('input[name="extras"]:checked')).map(el => {
    const map = { childseat: 'Child Seat', meetgreet: 'Meet & Greet', wifi: 'WiFi' };
    return map[el.value];
  });
  const summaryExtrasRow = document.getElementById('summaryExtrasRow');
  const summaryExtras = document.getElementById('summaryExtras');
  if (extras.length > 0) {
    if (summaryExtrasRow) summaryExtrasRow.style.display = 'flex';
    if (summaryExtras) summaryExtras.textContent = extras.join(', ');
  } else {
    if (summaryExtrasRow) summaryExtrasRow.style.display = 'none';
  }
}

// Set default date to tomorrow
const tomorrow = new Date();
tomorrow.setDate(tomorrow.getDate() + 1);
const dateEl = document.getElementById('date');
if (dateEl) dateEl.value = tomorrow.toISOString().split('T')[0];
const timeEl = document.getElementById('time');
if (timeEl) timeEl.value = '10:00';

// ========== FORM SUBMISSION ==========
let currentPrice = 0;
let exchangeRate = 7.25;

const bookingForm = document.getElementById('bookingForm');
if (bookingForm) {
  bookingForm.addEventListener('submit', function(e) {
    e.preventDefault();

    // Honeypot
    const honeypot = document.getElementById('website');
    if (honeypot && honeypot.value) {
      showToast('An error occurred. Please try again.', 'error');
      return;
    }
    // Rate limit
    if (window.ChinawheelySecurity && !window.ChinawheelySecurity.rateLimiter.check('booking')) {
      showToast('Too many attempts. Please wait a minute.', 'error');
      return;
    }
    // Required fields validation
    const serviceType = document.querySelector('input[name="serviceType"]:checked').value;
    if (!document.getElementById('city').value) {
      showToast('Please select a city', 'error');
      return;
    }
    if (serviceType === 'airport') {
      if (!document.getElementById('airport').value) {
        showToast('Please select an airport', 'error');
        return;
      }
      if (!document.getElementById('transferDirection').value) {
        showToast('Please select transfer direction', 'error');
        return;
      }
      if (!document.getElementById('hotelAddress').value) {
        showToast('Please enter your hotel address', 'error');
        return;
      }
      if (!document.getElementById('distanceRange').value) {
        showToast('Please select approximate distance', 'error');
        return;
      }
    }
    if (serviceType === 'intercity') {
      if (!document.getElementById('fromCity').value || !document.getElementById('toCity').value) {
        showToast('Please enter both origin and destination cities', 'error');
        return;
      }
    }
    if (!document.getElementById('firstName').value || !document.getElementById('lastName').value) {
      showToast('Please enter your full name', 'error');
      return;
    }
    if (!document.getElementById('email').value || !document.getElementById('phone').value) {
      showToast('Please enter your contact details', 'error');
      return;
    }

    // Security checks
    const formFields = ['firstName','lastName','email','phone','hotelAddress','fromCity','toCity','cityRoute','cityDistanceRange'];
    for (const fieldId of formFields) {
      const field = document.getElementById(fieldId);
      if (field && field.value && window.ChinawheelySecurity && window.ChinawheelySecurity.hasSuspiciousPattern(field.value)) {
        showToast('Invalid characters detected. Please check your input.', 'error');
        return;
      }
    }
    const emailField = document.getElementById('email');
    if (emailField && window.ChinawheelySecurity && !window.ChinawheelySecurity.isValidEmail(emailField.value)) {
      showToast('Please enter a valid email address', 'error');
      return;
    }

    // === Compute price ===
    const city = document.getElementById('city').value;
    const vehicle = document.querySelector('input[name="vehicle"]:checked').value;
    const date = document.getElementById('date').value;
    const time = document.getElementById('time').value;
    const passengers = document.getElementById('passengers').value;
    const hours = document.getElementById('hours').value;
    const fromCity = document.getElementById('fromCity').value;
    const toCity = document.getElementById('toCity').value;
    const airport = document.getElementById('airport').value;
    const transferDirection = document.getElementById('transferDirection').value;
    const hotelAddress = document.getElementById('hotelAddress').value;
    const distanceRange = document.getElementById('distanceRange').value;
    const cityRoute = document.getElementById('cityRoute').value;

    let price = basePrices[vehicle] || 51;
    const cityMult = getCityTierMultiplier(city);
    price *= cityMult;

    if (serviceType === 'airport') {
      price *= getDistanceMultiplier(distanceRange);
    } else if (serviceType === 'city') {
      const hourMult = { '4': 1.0, '8': 1.8, '12': 2.5, 'custom': 2.0 };
      price *= (hourMult[hours] || 1.8);
      const cityDistRange = document.getElementById('cityDistanceRange').value;
      const distMult = { '0-150': 1.0, '150-300': 2.0, '300-500': 4.0 };
      price *= (distMult[cityDistRange] || 1.0);
    } else if (serviceType === 'intercity') {
      price *= 1.5;
    }
    currentPrice = Math.round(price / 5) * 5;

    // Populate modal
    const modalService = document.getElementById('modalService');
    if (modalService) modalService.textContent =
      serviceType === 'airport' ? 'Airport Transfer' :
      serviceType === 'city' ? 'City Car Service' : 'Intercity Trip';

    const modalCity = document.getElementById('modalCity');
    if (modalCity) modalCity.textContent = city ? city.charAt(0).toUpperCase() + city.slice(1) : '-';

    let routeText = '-';
    if (serviceType === 'airport' && airport && transferDirection) {
      const dir = transferDirection === 'airport-to-hotel' ? 'Pickup' : 'Drop-off';
      routeText = airport + ' ' + dir;
      if (hotelAddress) routeText += ' → ' + hotelAddress.substring(0, 30) + (hotelAddress.length > 30 ? '...' : '');
      if (distanceRange) routeText += ' (' + getDistanceRangeLabel(distanceRange) + ')';
    } else if (serviceType === 'city') {
      routeText = hours + ' hours';
      const cityDistRange = document.getElementById('cityDistanceRange').value;
      const distLabel = { '0-150': 'Within City', '150-300': 'Suburban', '300-500': 'Outside City' };
      routeText += ' (' + (distLabel[cityDistRange] || 'Within City') + ')';
      if (cityRoute) routeText += ' — ' + cityRoute;
    } else if (serviceType === 'intercity' && fromCity && toCity) {
      routeText = fromCity + ' → ' + toCity;
    }
    const modalRoute = document.getElementById('modalRoute');
    if (modalRoute) modalRoute.textContent = routeText;

    const modalDateTime = document.getElementById('modalDateTime');
    if (modalDateTime) modalDateTime.textContent = (date && time) ? (date + ' ' + time) : '-';

    const modalVehicle = document.getElementById('modalVehicle');
    if (modalVehicle) modalVehicle.textContent = vehicle.charAt(0).toUpperCase() + vehicle.slice(1);

    const modalPassengers = document.getElementById('modalPassengers');
    if (modalPassengers) modalPassengers.textContent = passengers;

    const modalPrice = document.getElementById('modalPrice');
    if (modalPrice) modalPrice.textContent = '$' + currentPrice;

    const modalPriceUsd = document.getElementById('modalPriceUsd');
    if (modalPriceUsd) modalPriceUsd.textContent = '$' + currentPrice;

    const modalPriceCny = document.getElementById('modalPriceCny');
    if (modalPriceCny) modalPriceCny.textContent = '¥' + Math.round(currentPrice * exchangeRate);

    fetch('https://open.er-api.com/v6/latest/USD')
      .then(function(r) { return r.json(); })
      .then(function(data) {
        if (data && data.rates && data.rates.CNY) {
          exchangeRate = data.rates.CNY;
          if (modalPriceCny) modalPriceCny.textContent = '¥' + Math.round(currentPrice * exchangeRate);
        }
      })
      .catch(function() {});

    const paymentModal = document.getElementById('paymentModal');
    if (paymentModal) {
      paymentModal.classList.add('active');
      document.body.style.overflow = 'hidden';
    }
  });
}

function closePaymentModal() {
  const paymentModal = document.getElementById('paymentModal');
  if (paymentModal) {
    paymentModal.classList.remove('active');
    document.body.style.overflow = '';
  }
}

function switchPaymentTab(tab) {
  document.querySelectorAll('.payment-tab').forEach(function(t) { t.classList.remove('active'); });
  document.querySelectorAll('.payment-tab-content').forEach(function(c) { c.classList.remove('active'); });
  const activeTab = document.querySelector('.payment-tab[data-action="switch-payment"][data-tab="' + tab + '"]');
  if (activeTab) activeTab.classList.add('active');
  const tabContent = document.getElementById('tab-' + tab);
  if (tabContent) tabContent.classList.add('active');
}

function openWhatsappModal() {
  const modal = document.getElementById('whatsappModal');
  if (modal) {
    modal.classList.add('active');
    document.body.style.overflow = 'hidden';
  }
}

function closeWhatsappModal() {
  const modal = document.getElementById('whatsappModal');
  if (modal) {
    modal.classList.remove('active');
    document.body.style.overflow = '';
  }
}

function submitBooking() {
  // Populate hidden fields with computed data so formsubmit.co email includes full details
  const formPrice = document.getElementById('formPrice');
  if (formPrice) formPrice.value = '$' + currentPrice + ' USD';

  const formRouteSummary = document.getElementById('formRouteSummary');
  if (formRouteSummary) {
    const modalRoute = document.getElementById('modalRoute');
    formRouteSummary.value = modalRoute ? modalRoute.textContent : '';
  }

  const formServiceType = document.getElementById('formServiceType');
  if (formServiceType) {
    const modalService = document.getElementById('modalService');
    formServiceType.value = modalService ? modalService.textContent : '';
  }

  const formVehicleLabel = document.getElementById('formVehicleLabel');
  if (formVehicleLabel) {
    const modalVehicle = document.getElementById('modalVehicle');
    const modalPassengers = document.getElementById('modalPassengers');
    formVehicleLabel.value = (modalVehicle ? modalVehicle.textContent : '') + ' (' + (modalPassengers ? modalPassengers.textContent : '') + ' pax)';
  }

  if (bookingForm) bookingForm.submit();
}

// Close modals on overlay click
const paymentModal = document.getElementById('paymentModal');
if (paymentModal) {
  paymentModal.addEventListener('click', function(e) {
    if (e.target === this) closePaymentModal();
  });
}

const whatsappModal = document.getElementById('whatsappModal');
if (whatsappModal) {
  whatsappModal.addEventListener('click', function(e) {
    if (e.target === this) closeWhatsappModal();
  });
}

// Close modals on Escape key
document.addEventListener('keydown', function(e) {
  if (e.key === 'Escape') {
    closePaymentModal();
    closeWhatsappModal();
  }
});

// Initialize
if (typeof updateForm === 'function') updateForm();
