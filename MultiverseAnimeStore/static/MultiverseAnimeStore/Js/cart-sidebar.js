const cartSidebar = document.getElementById('cart-sidebar');
const cartOverlay = document.getElementById('cart-overlay');

let cart = [];

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
  if (cart.length === 0) {
    cartSidebar.classList.remove('open');
    cartOverlay.classList.remove('open');
    document.body.style.overflow = '';
  }
}

function addToCart(name, price, id) {
  const existing = cart.find(item => item.name === name);

  if (existing) {
    existing.qty = (existing.qty || 1) + 1;
  } else {
    cart.push({ name, price, qty: 1 });
  }

  
  renderCart();

  cartSidebar.classList.add('open');
  cartOverlay.classList.add('open');
  document.body.style.overflow = 'hidden';
}


function removeFromCart(index) {
  changeQty(index, -cart[index].qty);
}
