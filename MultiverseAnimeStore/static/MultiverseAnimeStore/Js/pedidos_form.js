addEventListener('DOMContentLoaded', function() {
        const productosSelect = document.getElementById('productos');
        const cantidadInput = document.querySelector('input[name="Cantidad"]');
        const TotalInput = document.querySelector('input[name="ped_total"]');

        function parseNumber(v) {
            const n = parseFloat(v);
            return isNaN(n) ? 0 : n;
        }

        document.getElementById('addProducto').addEventListener('click', function() {
            const selectedOption = productosSelect.options[productosSelect.selectedIndex];
            if (!selectedOption || !selectedOption.value) {
                alert('Por favor, selecciona un producto.');
                return;
            }
            const cantidad = parseInt(cantidadInput.value, 10) || 0;
            if (cantidad <= 0) {
                alert('Por favor, ingresa una cantidad válida.');
                return;
            }

            // obtener precio y descuento desde atributos data-*
            const precioBruto = parseNumber(selectedOption.dataset.price);
            const descuentoPct = parseNumber(selectedOption.dataset.discount);
            const precioConDescuento = precioBruto * (1 - (descuentoPct / 100));
            const subtotalLinea = precioConDescuento * cantidad;

            const totalActual = parseNumber(TotalInput ? TotalInput.value : 0);
            const nuevoTotal = totalActual + subtotalLinea;
            if (TotalInput) TotalInput.value = nuevoTotal.toFixed(2);

            // crear representación visual
            const productoDiv = document.createElement('div');
            productoDiv.textContent = `${selectedOption.text} - Cantidad: ${cantidad} - Subtotal: $${subtotalLinea.toFixed(2)}`;
            document.getElementById('productosList').appendChild(productoDiv);

            // input oculto que envía id y cantidad (siguiendo formato actual)
            const productoinput = document.createElement('input');
            productoinput.type = 'hidden';
            productoinput.name = 'productos_seleccionados';
            productoinput.value = `${selectedOption.value},${cantidad}`;
            document.getElementById('productosList').appendChild(productoinput);

            // ocultar opción ya agregada para evitar duplicados
            selectedOption.style.display = 'none';
            productosSelect.selectedIndex = 0;
            cantidadInput.value = '';
        });
    });
