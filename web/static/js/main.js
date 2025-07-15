document.addEventListener('DOMContentLoaded', () => {

    document.querySelectorAll('.close-btn').forEach(button => {
        button.addEventListener('click', () => {
            const messageBox = button.parentElement;
            messageBox.style.opacity = '0';
            setTimeout(() => { messageBox.style.display = 'none'; }, 500);
        });
    });

    document.querySelectorAll('.flashed-message').forEach(message => {
        setTimeout(() => {
            message.style.opacity = '0';
            setTimeout(() => { message.style.display = 'none'; }, 500);
        }, 5000);
    });

    const embedToggle = document.getElementById('embed-toggle-checkbox');
    const submitTypeInput = document.getElementById('submit_type');
    const simpleFields = document.getElementById('simple-fields');
    const embedFields = document.getElementById('embed-fields');

    if (embedToggle && submitTypeInput && simpleFields && embedFields) {
        embedToggle.addEventListener('change', () => {
            if (embedToggle.checked) {
                submitTypeInput.value = 'embed';
                simpleFields.style.display = 'none';
                embedFields.style.display = 'block';
            } else {
                submitTypeInput.value = 'simple';
                simpleFields.style.display = 'block';
                embedFields.style.display = 'none';
            }
        });
    }

    const colorInput = document.getElementById('embed_color_input');
    const colorPreview = document.getElementById('color_preview');

    if (colorInput && colorPreview) {
        const updateColorPreview = () => {
            colorPreview.style.backgroundColor = colorInput.value;
        };
        colorInput.addEventListener('input', updateColorPreview);
        updateColorPreview();
    }
});