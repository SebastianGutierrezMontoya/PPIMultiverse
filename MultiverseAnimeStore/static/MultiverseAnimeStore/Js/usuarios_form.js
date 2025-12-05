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
            const contactoDiv = document.createElement('div');
            const contactoTexto = document.createElement('span');
            let tipoTexto = tipoSelect.options[tipoSelect.selectedIndex].text;
            contactoTexto.textContent = `${tipoTexto}: ${dato} `;
            contactoTexto.classList.add('form-span');
            contactoDiv.appendChild(contactoTexto);

            const removeBtn = document.createElement('button');
            removeBtn.type = 'button';
            removeBtn.textContent = 'Eliminar';
            removeBtn.onclick = removeContacto;
            contactoDiv.appendChild(removeBtn);

            const hiddenInput = document.createElement('input');
            hiddenInput.type = 'hidden';
            hiddenInput.name = 'contactos_relacionados';
            hiddenInput.value = `${tipo},${dato}`;
            contactoDiv.appendChild(hiddenInput);

            contactoDiv.classList.add('form-linear','form-contacto');
            contactosContainer.appendChild(contactoDiv);

            tipoSelect.selectedIndex = 0;
            datoInput.value = '';
        } else {
            alert('Por favor, selecciona el tipo y escribe el dato del contacto.');
        }
    });

    // Actualizar hidden de contactos editados: obtener id desde el atributo name
    function updateHiddenForId(id) {
        const select = document.querySelector('select[name="tipo_contacto_editado_' + id + '"]');
        const input = document.querySelector('input[name="dato_contacto_editado_' + id + '"]');
        const hidden = document.getElementById('contacto_editado_' + id);
        if (!hidden) return;
        const tipoVal = select ? select.value : '';
        const datoVal = input ? input.value : '';
        hidden.value = `${tipoVal},${datoVal},${id}`;
    }

    // attach listeners to existing edited fields
    document.querySelectorAll('.tipo-contacto-editado, .dato-contacto-editado').forEach(function(el) {
        el.addEventListener('change', function() {
            // name expected like 'tipo_contacto_editado_<id>' or 'dato_contacto_editado_<id>'
            const m = el.name.match(/_(\d+)$/);
            if (!m) return;
            const id = m[1];
            updateHiddenForId(id);
        });
    });
});