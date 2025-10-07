addEventListener('DOMContentLoaded', function() {
    const addContactoBtn = document.getElementById('addContacto');
    const contactosContainer = document.getElementById('contactosContainer');
    const tipoSelect = contactosContainer.querySelector('select[name="tipo_contacto"]');
    const datoInput = contactosContainer.querySelector('input[name="dato_contacto"]');

    function removeContacto(e) {
        e.target.parentElement.remove();
    }

    addContactoBtn.addEventListener('click', function() {
        const tipo = tipoSelect.value;
        const dato = datoInput.value;

        if (tipo && dato) {
            // Muestra el contacto agregado con botón eliminar
            const contactoDiv = document.createElement('div');
            let tipoTexto = tipoSelect.options[tipoSelect.selectedIndex].text;
            contactoDiv.textContent = `${tipoTexto}: ${dato} `;

            // Botón eliminar
            const removeBtn = document.createElement('button');
            removeBtn.type = 'button';
            removeBtn.textContent = 'Eliminar';
            removeBtn.onclick = removeContacto;
            contactoDiv.appendChild(removeBtn);

            // Input oculto para enviar al backend
            const hiddenInput = document.createElement('input');
            hiddenInput.type = 'hidden';
            hiddenInput.name = 'contactos_relacionados';
            hiddenInput.value = `${tipo},${dato}`;
            contactoDiv.appendChild(hiddenInput);

            contactosContainer.appendChild(contactoDiv);

            // Limpia los campos
            tipoSelect.selectedIndex = 0;
            datoInput.value = '';
        } else {
            alert('Por favor, selecciona el tipo y escribe el dato del contacto.');
        }
    });


    document.querySelectorAll('.tipo-contacto-editado, .dato-contacto-editado').forEach(function(el) {
                el.addEventListener('change', function() {
                    var li = el.closest('li');
                    var select = li.querySelector('.tipo-contacto-editado');
                    var input = li.querySelector('.dato-contacto-editado');
                    var hidden = li.querySelector('input[type="hidden"][name="contactos_relacionados_editados"]');
                    var id = hidden.id.split('_')[2];
                    hidden.value = select.value + ',' + input.value + ',' + id;
                });
            });
});