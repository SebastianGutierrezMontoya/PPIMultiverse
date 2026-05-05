document.addEventListener('DOMContentLoaded', function() {
  var form = document.getElementById('registerForm');
  if (!form) return;

  var username = document.getElementById('id_usuario');
  var nombre = document.getElementById('id_nombre');
  var apellido = document.getElementById('id_primer_apellido');
  var password = document.getElementById('id_password_hash');
  var confirmPass = document.getElementById('id_confirmar_contraseña');
  var sexo = document.getElementById('id_usuario_id_sexo');
  var telefono = document.getElementById('id_telefono');
  var calle = document.getElementById('id_direccion_calle');
  var ciudad = document.getElementById('id_direccion_ciudad');
  var pais = document.getElementById('id_direccion_pais');
  var direccionHidden = document.getElementById('id_direccion');
  var submitBtn = document.getElementById('registerSubmitBtn');
  var matchError = document.getElementById('err-password-match');

  function showError(inputId, msg) {
    var el = document.getElementById(inputId);
    if (el) {
      el.textContent = msg || 'Campo obligatorio';
      el.classList.add('visible');
    }
  }

  function hideError(inputId) {
    var el = document.getElementById(inputId);
    if (el) {
      el.classList.remove('visible');
    }
  }

  function markError(input) {
    input.classList.add('error');
  }

  function clearError(input) {
    input.classList.remove('error');
  }

  function clearErrors(inputIds) {
    inputIds.forEach(function(id) {
      hideError(id);
      var el = document.getElementById(id.replace('err-', 'id_'));
      if (el) clearError(el);
    });
  }

  function validateField(input, errorId, condition, msg) {
    if (!condition) {
      markError(input);
      showError(errorId, msg);
      return false;
    }
    clearError(input);
    hideError(errorId);
    return true;
  }

  function checkPasswordsMatch() {
    if (confirmPass.value && password.value !== confirmPass.value) {
      markError(confirmPass);
      matchError.classList.add('visible');
      return false;
    }
    clearError(confirmPass);
    matchError.classList.remove('visible');
    return true;
  }

  function clearAllInputErrors() {
    [username, nombre, apellido, password, confirmPass, sexo, telefono, calle, ciudad, pais].forEach(function(el) {
      if (el) clearError(el);
    });
    matchError.classList.remove('visible');
  }

  password.addEventListener('input', function() {
    if (confirmPass.value) checkPasswordsMatch();
  });

  confirmPass.addEventListener('input', checkPasswordsMatch);

  form.addEventListener('submit', function(e) {
    var valid = true;

    clearAllInputErrors();

    valid = validateField(username, 'err-usuario', username.value.trim().length > 0) && valid;
    valid = validateField(nombre, 'err-nombre', nombre.value.trim().length > 0) && valid;
    valid = validateField(apellido, 'err-primer_apellido', apellido.value.trim().length > 0) && valid;
    valid = validateField(password, 'err-password', password.value.length >= 6, 'Mínimo 6 caracteres') && valid;
    valid = validateField(confirmPass, 'err-confirm', confirmPass.value.trim().length > 0) && valid;
    valid = validateField(sexo, 'err-sexo', sexo.value !== '') && valid;
    valid = validateField(telefono, 'err-telefono', telefono.value.trim().length > 0) && valid;
    valid = validateField(calle, 'err-direccion_calle', calle.value.trim().length > 0) && valid;
    valid = validateField(ciudad, 'err-direccion_ciudad', ciudad.value.trim().length > 0) && valid;
    valid = validateField(pais, 'err-direccion_pais', pais.value.trim().length > 0) && valid;

    if (confirmPass.value && password.value !== confirmPass.value) {
      markError(confirmPass);
      matchError.classList.add('visible');
      valid = false;
    }

    if (valid) {
      var barrio = document.getElementById('id_direccion_barrio');
      var parts = [calle.value.trim(), ciudad.value.trim(), pais.value.trim()];
      if (barrio && barrio.value.trim()) parts.push(barrio.value.trim());
      direccionHidden.value = parts.join(' | ');
    } else {
      e.preventDefault();
    }
  });
});
