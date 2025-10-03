  
    addEventListener('DOMContentLoaded', function() {
        const productosSelect = document.getElementById('productos');
        const cantidadInput = document.querySelector('input[name="Cantidad"]');
        const TotalInput = document.querySelector('input[name="ped_total"]');


        // productosSelect.addEventListener('change', function() {
        //     console.log('Producto seleccionado:', this.value);
        // });

        // cantidadInput.addEventListener('input', function() {
        //     console.log('Cantidad ingresada:', this.value);
        // });

        document.getElementById('addProducto').addEventListener('click', function() {
            const selectedOption = productosSelect.options[productosSelect.selectedIndex];
            const cantidad = cantidadInput.value;
            const totalActual = parseFloat(TotalInput.value) || 0;
            const precioProducto = parseFloat(selectedOption.text.split('$')[1]) || 0;
            const nuevoTotal = totalActual + (precioProducto * cantidad);
            TotalInput.value = nuevoTotal.toFixed(2);

            if (cantidad > 0) {
                const productoDiv = document.createElement('div');
                productoDiv.textContent = `${selectedOption.text} - Cantidad: ${cantidad} - Total $${(parseFloat(selectedOption.text.split('$')[1]) * cantidad).toFixed(2)}`;;
                document.getElementById('productosList').appendChild(productoDiv);
                TotalInput.value = nuevoTotal.toFixed(2);

                const productoinput = document.createElement('input');
                productoinput.type = 'hidden';
                productoinput.name = 'productos_seleccionados';
                productoinput.value = `${selectedOption.value},${cantidad}`;
                document.getElementById('productosList').appendChild(productoinput);

                
                
                selectedOption.style.display = 'none';
                productosSelect.selectedIndex = 0;
                cantidadInput.value = '';
            } else {
                alert('Por favor, ingresa una cantidad válida.');
            }
        });




    });
