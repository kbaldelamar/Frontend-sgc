// Login Page JavaScript - BIOMED
document.addEventListener('DOMContentLoaded', function() {
    console.log('🏢 Login page loaded for BIOMED');
    
    // Verificar si la imagen se carga correctamente
    const heroImg = document.querySelector('.hero-img');
    if (heroImg) {
        heroImg.addEventListener('load', function() {
            console.log('✅ Imagen hero cargada:', this.src);
            // Asegurar que la imagen llene todo el espacio
            this.style.width = '100%';
            this.style.height = '100%';
            this.style.objectFit = 'cover';
        });
        
        heroImg.addEventListener('error', function() {
            console.warn('⚠️ Error cargando imagen hero:', this.src);
            this.style.display = 'none';
            this.parentElement.classList.remove('has-image');
        });
    }
    
    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            alert.style.transform = 'translateY(-20px)';
            setTimeout(() => alert.remove(), 300);
        }, 5000);
    });

    // Focus effects
    document.querySelectorAll('.form-control').forEach(input => {
        input.addEventListener('focus', function() {
            this.parentElement.classList.add('focused');
        });
        
        input.addEventListener('blur', function() {
            this.parentElement.classList.remove('focused');
        });
    });

    // Log tenant info if available
    if (window.TENANT_CONFIG) {
        console.log('🎨 Tenant:', window.TENANT_CONFIG.name);
        console.log('🎨 Colors:', window.TENANT_CONFIG.colors);
    }
});

// Toggle password visibility
function togglePassword() {
    const passwordInput = document.getElementById('password');
    const passwordIcon = document.getElementById('passwordIcon');
    
    if (passwordInput.type === 'password') {
        passwordInput.type = 'text';
        passwordIcon.className = 'fas fa-eye-slash';
    } else {
        passwordInput.type = 'password';
        passwordIcon.className = 'fas fa-eye';
    }
}

// Form validation
document.getElementById('loginForm')?.addEventListener('submit', function(e) {
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const notRobot = document.getElementById('notRobot').checked;

    if (!username || !password) {
        e.preventDefault();
        alert('Por favor completa todos los campos requeridos.');
        return;
    }

    if (!notRobot) {
        e.preventDefault();
        alert('Por favor confirma que no eres un robot.');
        return;
    }

    // Mostrar loading en el botón
    const submitBtn = e.target.querySelector('button[type="submit"]');
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Ingresando...';
    submitBtn.disabled = true;
});