// web/static/js/main.js
document.addEventListener('DOMContentLoaded', () => {
    // --- Lógica para las notificaciones (mensajes flash) ---
    // Botón de cierre manual
    document.querySelectorAll('.close-btn').forEach(button => {
        button.addEventListener('click', () => {
            const messageBox = button.parentElement;
            messageBox.style.opacity = '0';
            setTimeout(() => messageBox.style.display = 'none', 500);
        });
    });

    // Cierre automático después de 5 segundos
    document.querySelectorAll('.flashed-message').forEach(message => {
        setTimeout(() => {
            message.style.opacity = '0';
            setTimeout(() => message.style.display = 'none', 500);
        }, 5000);
    });

    // --- Lógica para el panel de envío unificado (Simple/Embed) ---
    const toggleBtn = document.getElementById('toggle-mode-btn');
    const submitTypeInput = document.getElementById('submit_type');
    const simpleFields = document.getElementById('simple-fields');
    const embedFields = document.getElementById('embed-fields');

    if (toggleBtn) {
        toggleBtn.addEventListener('click', () => {
            const isSimpleMode = submitTypeInput.value === 'simple';
            if (isSimpleMode) {
                // Cambiar a modo Embed
                submitTypeInput.value = 'embed';
                toggleBtn.textContent = '> CAMBIAR A MENSAJE SIMPLE';
                simpleFields.style.display = 'none';
                embedFields.style.display = 'block';
            } else {
                // Cambiar a modo Simple
                submitTypeInput.value = 'simple';
                toggleBtn.textContent = '> CREAR MENSAJE EMBED';
                simpleFields.style.display = 'block';
                embedFields.style.display = 'none';
            }
        });
    }

    // --- Lógica para el selector de color con vista previa ---
    const colorInput = document.getElementById('embed_color_input');
    const colorPreview = document.getElementById('color_preview');

    if (colorInput && colorPreview) {
        // Sincroniza la vista previa cuando cambia el color
        colorInput.addEventListener('input', (event) => {
            colorPreview.style.backgroundColor = event.target.value;
        });
        // Establece el color inicial al cargar la página
        colorPreview.style.backgroundColor = colorInput.value;
    }
});