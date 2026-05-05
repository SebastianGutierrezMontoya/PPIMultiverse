const cartSidebar = document.getElementById('cart-sidebar');
const cartOverlay = document.getElementById('cart-overlay');

const CART_CACHE_KEY = 'multiverse_cart_items';
let cart = [];

function loadCartFromCache() {
  try {
    const cached = localStorage.getItem(CART_CACHE_KEY);
    if (!cached) return [];
    const parsed = JSON.parse(cached);
    return Array.isArray(parsed) ? parsed : [];
  } catch (error) {
    console.warn('Error cargando carrito desde cache:', error);
    return [];
  }
}

function saveCartToCache() {
  try {
    localStorage.setItem(CART_CACHE_KEY, JSON.stringify(cart));
  } catch (error) {
    console.warn('Error guardando carrito en cache:', error);
  }
}

function clearCartCache() {
  try {
    localStorage.removeItem(CART_CACHE_KEY);
  } catch (error) {
    console.warn('Error borrando carrito de cache:', error);
  }
}

function toggleCart() {
  const isOpen = cartSidebar.classList.contains('open');

  if (isOpen) {
    cartSidebar.classList.remove('open');
    cartOverlay.classList.remove('open');
    document.body.style.overflow = '';
  } else {
    cartSidebar.classList.add('open');
    cartOverlay.classList.add('open');
    document.body.style.overflow = 'hidden';
  }
}






function renderCart() {
  const container = document.getElementById('cart-items');
  const totalEl = document.getElementById('cart-total');

  container.innerHTML = '';

  if (cart.length === 0) {
    container.innerHTML = `
      <div style="text-align:center; padding:80px 0;">
        <i class="fas fa-shopping-bag" style="font-size:60px; color:#1e293b; margin-bottom:16px;"></i>
        <p style="color:#475569; font-weight:700; text-transform:uppercase; font-size:10px; letter-spacing:0.2em;">
          Carrito vacío
        </p>
      </div>
    `;
    totalEl.textContent = '$ 0';
    updateHiddenCartFields(0);
    saveCartToCache();
    return;
  }

  let total = 0;

  cart.forEach((item, index) => {
    total += item.price * item.qty;

    const itemHTML = `
      <div class="cart-item">
        <div class="cart-item-info">
          <span class="cart-price">$${formatPrice(item.price * item.qty)}</span>
          <span class="cart-name">${item.name}</span>
        </div>
        <div class="cart-qty-controls">
          <button onclick="changeQty(${index}, -1)" class="cart-qty-btn">-</button>
          <span class="cart-qty">${item.qty}</span>
          <button onclick="changeQty(${index}, 1)" class="cart-qty-btn">+</button>
        </div>
        <button onclick="removeFromCart(${index})" class="cart-remove">
          <i class="fas fa-trash-can">X</i>
        </button>
      </div>
    `;

    container.innerHTML += itemHTML;
  });

  totalEl.textContent = '$ ' + formatPrice(total);
  updateHiddenCartFields(total);
}

function updateHiddenCartFields(total) {
  const cartItemsInput = document.getElementById('cart_items_input');
  const cartQuantityInput = document.getElementById('cart_quantity_input');
  const cartTotalInput = document.getElementById('cart_total_input');

  if (!cartItemsInput) return;

  cartItemsInput.value = JSON.stringify(cart);
  cartQuantityInput.value = cart.reduce((sum, item) => sum + item.qty, 0);
  cartTotalInput.value = total.toFixed(2);
}

function formatPrice(value) {
  return value.toLocaleString('es-CO');
}

function changeQty(index, delta) {
  cart[index].qty += delta;
  if (cart[index].qty <= 0) {
    cart.splice(index, 1);
  }
  renderCart();
  saveCartToCache();
  if (cart.length === 0) {
    cartSidebar.classList.remove('open');
    cartOverlay.classList.remove('open');
    document.body.style.overflow = '';
  }
}

function addToCart(name, price, id) {
  const unitPrice = parseFloat(price) || 0;
  const existing = cart.find(item => item.id === id);

  if (existing) {
    existing.qty = (existing.qty || 1) + 1;
  } else {
    cart.push({ id, name, price: unitPrice, qty: 1 });
  }

  renderCart();
  saveCartToCache();

  cartSidebar.classList.add('open');
  cartOverlay.classList.add('open');
  document.body.style.overflow = 'hidden';
}


function removeFromCart(index) {
  changeQty(index, -cart[index].qty);
}


function openCheckoutModal() {
  const modal = document.getElementById('checkout-modal');
  const overlay = document.getElementById('checkout-overlay');
  const error = document.getElementById('checkout-error');
  if (modal) modal.style.display = 'flex';
  if (overlay) overlay.style.display = 'block';
  if (error) error.classList.add('hidden');
}

function closeCheckoutModal() {
  const modal = document.getElementById('checkout-modal');
  const overlay = document.getElementById('checkout-overlay');
  if (modal) modal.style.display = 'none';
  if (overlay) overlay.style.display = 'none';
}

function submitCheckoutForm() {
  const notesInput = document.getElementById('checkout_notes');
  const nameInput = document.getElementById('checkout_name');
  const phoneInput = document.getElementById('checkout_phone');
  const calleInput = document.getElementById('checkout_calle');
  const ciudadInput = document.getElementById('checkout_ciudad');
  const paisInput = document.getElementById('checkout_pais');
  const barrioInput = document.getElementById('checkout_barrio');
  const addressHidden = document.getElementById('ped_direccion_envio_input');
  const notesHidden = document.getElementById('ped_notas_input');
  const nameHidden = document.getElementById('nombre_invitado_input');
  const phoneHidden = document.getElementById('telefono_invitado_input');
  const form = document.getElementById('checkout-form');
  const error = document.getElementById('checkout-error');
  const isAuthenticated = window.isAuthenticated;

  if (!notesInput || !addressHidden || !notesHidden || !form) {
    return;
  }

  const calleVal = calleInput ? calleInput.value.trim() : '';
  const ciudadVal = ciudadInput ? ciudadInput.value.trim() : '';
  const paisVal = paisInput ? paisInput.value.trim() : '';
  const barrioVal = barrioInput ? barrioInput.value.trim() : '';

  if (!calleVal || !ciudadVal || !paisVal) {
    if (error) {
      error.textContent = 'Completa la dirección: calle, ciudad y país son obligatorios.';
      error.classList.remove('hidden');
    }
    if (calleInput && !calleVal) calleInput.classList.add('error');
    if (ciudadInput && !ciudadVal) ciudadInput.classList.add('error');
    if (paisInput && !paisVal) paisInput.classList.add('error');
    return;
  }

  const parts = [calleVal, ciudadVal, paisVal];
  if (barrioVal) parts.push(barrioVal);
  addressHidden.value = parts.join(' | ');

  if (!isAuthenticated) {
    const nameVal = nameInput ? nameInput.value.trim() : '';
    const phoneVal = phoneInput ? phoneInput.value.trim() : '';
    if (!nameVal || !phoneVal) {
      if (error) {
        error.textContent = 'Debes ingresar tu nombre y teléfono para continuar.';
        error.classList.remove('hidden');
      }
      if (nameInput && !nameVal) nameInput.classList.add('error');
      if (phoneInput && !phoneVal) phoneInput.classList.add('error');
      return;
    }
    if (nameHidden) nameHidden.value = nameVal;
    if (phoneHidden) phoneHidden.value = phoneVal;
  }

  notesHidden.value = notesInput.value.trim();

  form.submit();
  clearCartCache();
}

function clearInputError(input) {
  if (input) input.classList.remove('error');
}

function initCart() {
  cart = loadCartFromCache();
  renderCart();

  var nameGroup = document.getElementById('checkout-name-group');
  var phoneGroup = document.getElementById('checkout-phone-group');
  var nameInput = document.getElementById('checkout_name');
  var phoneInput = document.getElementById('checkout_phone');

  if (window.isAuthenticated) {
    if (nameGroup) nameGroup.style.display = 'none';
    if (phoneGroup) phoneGroup.style.display = 'none';
  } else {
    if (nameInput) nameInput.addEventListener('input', function() { clearInputError(this); });
    if (phoneInput) phoneInput.addEventListener('input', function() { clearInputError(this); });
  }
}

document.addEventListener('DOMContentLoaded', initCart);
