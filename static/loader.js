// static/loader.js
// Muestra un loader cuando se hace submit en formularios con botones demorados

document.addEventListener('DOMContentLoaded', function() {
    // Crea el overlay del loader si no existe
    if (!document.getElementById('loader-overlay')) {
        const loaderOverlay = document.createElement('div');
        loaderOverlay.id = 'loader-overlay';
        loaderOverlay.innerHTML = `
            <div class="loader-spinner"></div>
            <div class="loader-text">Cargando... Por favor espera.</div>
        `;
        document.body.appendChild(loaderOverlay);
    }

    // Oculta el loader al inicio
    document.getElementById('loader-overlay').style.display = 'none';

    // Selecciona los formularios de los botones demorados
    const forms = document.querySelectorAll('form[action="/select_channels"], form[action="/select_video"], form[action="/channels"]');
    forms.forEach(form => {
        form.addEventListener('submit', function() {
            const loader = document.getElementById('loader-overlay');
            // Mensaje personalizado según el formulario
            if (form.getAttribute('action') === '/select_channels') {
                loader.querySelector('.loader-text').textContent = 'Buscando canales... Por favor espera.';
            } else if (form.getAttribute('action') === '/select_video') {
                loader.querySelector('.loader-text').textContent = 'Buscando video... Por favor espera.';
            } else if (form.getAttribute('action') === '/channels') {
                loader.querySelector('.loader-text').textContent = 'Comparando canales... Por favor espera.';
            } else {
                loader.querySelector('.loader-text').textContent = 'Cargando... Por favor espera.';
            }
            loader.style.display = 'flex';
        });
    });

    // También para el formulario de análisis de comentarios
    const analisisForms = document.querySelectorAll('form.ver-analisis-form');
    analisisForms.forEach(form => {
        form.addEventListener('submit', function() {
            const loader = document.getElementById('loader-overlay');
            loader.querySelector('.loader-text').textContent = 'Cargando análisis de comentarios... Por favor espera.';
            loader.style.display = 'flex';
        });
    });
});
