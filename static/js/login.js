/**
 * Login Page JavaScript - Portal IPS COOSALUD
 * Funcionalidades avanzadas para el formulario de login
 */

class LoginManager {
    constructor() {
        this.form = document.getElementById('loginForm');
        this.usernameInput = document.getElementById('username');
        this.passwordInput = document.getElementById('password');
        this.passwordToggle = document.querySelector('.password-toggle');
        this.submitBtn = document.querySelector('.login-btn');
        this.rememberMeCheckbox = document.getElementById('remember_me');
        this.notRobotCheckbox = document.getElementById('notRobot');
        
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadSavedCredentials();
        this.setupFormValidation();
        this.setupAnimations();
        this.checkBrowserSupport();
    }

    bindEvents() {
        // Toggle password visibility
        if (this.passwordToggle) {
            this.passwordToggle.addEventListener('click', () => this.togglePassword());
        }

        // Form submission
        if (this.form) {
            this.form.addEventListener('submit', (e) => this.handleSubmit(e));
        }

        // Real-time validation
        if (this.usernameInput) {
            this.usernameInput.addEventListener('blur', () => this.validateUsername());
            this.usernameInput.addEventListener('input', () => this.clearFieldError(this.usernameInput));
        }

        if (this.passwordInput) {
            this.passwordInput.addEventListener('blur', () => this.validatePassword());
            this.passwordInput.addEventListener('input', () => this.clearFieldError(this.passwordInput));
        }

        // Remember me functionality
        if (this.rememberMeCheckbox) {
            this.rememberMeCheckbox.addEventListener('change', () => this.handleRememberMe());
        }

        // Auto-hide alerts
        this.setupAlertAutoHide();

        // Focus management
        this.setupFocusManagement();

        // Keyboard shortcuts
        this.setupKeyboardShortcuts();
    }

    togglePassword() {
        const type = this.passwordInput.type === 'password' ? 'text' : 'password';
        const icon = this.passwordToggle.querySelector('i');
        
        this.passwordInput.type = type;
        icon.className = type === 'password' ? 'fas fa-eye' : 'fas fa-eye-slash';
        
        // Maintain focus on password input
        this.passwordInput.focus();
        
        // Animate the toggle
        this.passwordToggle.style.transform = 'scale(0.9)';
        setTimeout(() => {
            this.passwordToggle.style.transform = 'scale(1)';
        }, 100);
    }

    validateUsername() {
        const username = this.usernameInput.value.trim();
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        
        if (!username) {
            this.showFieldError(this.usernameInput, 'El correo electrónico es obligatorio');
            return false;
        }

        if (!emailRegex.test(username)) {
            this.showFieldError(this.usernameInput, 'Ingresa un correo electrónico válido');
            return false;
        }

        this.showFieldSuccess(this.usernameInput);
        return true;
    }

    validatePassword() {
        const password = this.passwordInput.value;
        
        if (!password) {
            this.showFieldError(this.passwordInput, 'La contraseña es obligatoria');
            return false;
        }

        if (password.length < 6) {
            this.showFieldError(this.passwordInput, 'La contraseña debe tener al menos 6 caracteres');
            return false;
        }

        this.showFieldSuccess(this.passwordInput);
        return true;
    }

    showFieldError(field, message) {
        this.clearFieldError(field);
        
        field.classList.add('is-invalid');
        field.style.borderColor = '#e74c3c';
        
        const errorDiv = document.createElement('div');
        errorDiv.className = 'invalid-feedback';
        errorDiv.style.display = 'block';
        errorDiv.style.color = '#e74c3c';
        errorDiv.style.fontSize = '0.875rem';
        errorDiv.style.marginTop = '0.25rem';
        errorDiv.textContent = message;
        
        field.parentNode.appendChild(errorDiv);
        
        // Shake animation
        field.style.animation = 'shake 0.5s ease-in-out';
        setTimeout(() => {
            field.style.animation = '';
        }, 500);
    }

    showFieldSuccess(field) {
        this.clearFieldError(field);
        field.classList.add('is-valid');
        field.style.borderColor = '#27ae60';
    }

    clearFieldError(field) {
        field.classList.remove('is-invalid', 'is-valid');
        field.style.borderColor = '';
        
        const errorDiv = field.parentNode.querySelector('.invalid-feedback');
        if (errorDiv) {
            errorDiv.remove();
        }
    }

    handleSubmit(e) {
        e.preventDefault();
        
        // Validate all fields
        const isUsernameValid = this.validateUsername();
        const isPasswordValid = this.validatePassword();
        const isRobotChecked = this.notRobotCheckbox?.checked || false;
        
        if (!isUsernameValid || !isPasswordValid) {
            this.showAlert('Por favor corrige los errores en el formulario', 'error');
            return;
        }

        if (!isRobotChecked) {
            this.showAlert('Por favor confirma que no eres un robot', 'warning');
            return;
        }

        // Show loading state
        this.setLoadingState(true);
        
        // Save credentials if remember me is checked
        if (this.rememberMeCheckbox?.checked) {
            this.saveCredentials();
        } else {
            this.clearSavedCredentials();
        }

        // Submit form
        setTimeout(() => {
            this.form.submit();
        }, 500); // Small delay for UX
    }

    setLoadingState(loading) {
        if (loading) {
            this.submitBtn.disabled = true;
            this.submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Ingresando...';
            this.submitBtn.classList.add('loading');
        } else {
            this.submitBtn.disabled = false;
            this.submitBtn.innerHTML = '<i class="fas fa-sign-in-alt me-2"></i>Ingresar';
            this.submitBtn.classList.remove('loading');
        }
    }

    saveCredentials() {
        if (this.rememberMeCheckbox?.checked) {
            localStorage.setItem('rememberedUsername', this.usernameInput.value);
            localStorage.setItem('rememberMe', 'true');
        }
    }

    loadSavedCredentials() {
        const rememberedUsername = localStorage.getItem('rememberedUsername');
        const rememberMe = localStorage.getItem('rememberMe') === 'true';
        
        if (rememberedUsername && rememberMe) {
            this.usernameInput.value = rememberedUsername;
            if (this.rememberMeCheckbox) {
                this.rememberMeCheckbox.checked = true;
            }
        }
    }

    clearSavedCredentials() {
        localStorage.removeItem('rememberedUsername');
        localStorage.removeItem('rememberMe');
    }

    handleRememberMe() {
        if (!this.rememberMeCheckbox.checked) {
            this.clearSavedCredentials();
        }
    }

    showAlert(message, type = 'info') {
        // Remove existing alerts
        const existingAlerts = document.querySelectorAll('.alert');
        existingAlerts.forEach(alert => alert.remove());
        
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type === 'error' ? 'danger' : type === 'warning' ? 'warning' : 'info'}`;
        
        const icon = type === 'error' ? 'exclamation-triangle' : 
                    type === 'warning' ? 'exclamation-circle' : 
                    type === 'success' ? 'check-circle' : 'info-circle';
        
        alertDiv.innerHTML = `
            <i class="fas fa-${icon} me-2"></i>
            ${message}
        `;
        
        // Insert before form
        this.form.parentNode.insertBefore(alertDiv, this.form);
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.style.opacity = '0';
                alertDiv.style.transform = 'translateY(-20px)';
                setTimeout(() => alertDiv.remove(), 300);
            }
        }, 5000);
    }

    setupAlertAutoHide() {
        const alerts = document.querySelectorAll('.alert');
        alerts.forEach(alert => {
            // Add close button
            const closeBtn = document.createElement('button');
            closeBtn.type = 'button';
            closeBtn.className = 'btn-close';
            closeBtn.style.cssText = `
                position: absolute;
                top: 0.5rem;
                right: 0.5rem;
                background: none;
                border: none;
                font-size: 1.2rem;
                cursor: pointer;
                opacity: 0.6;
                transition: opacity 0.3s ease;
            `;
            closeBtn.innerHTML = '&times;';
            closeBtn.addEventListener('click', () => this.hideAlert(alert));
            
            alert.style.position = 'relative';
            alert.appendChild(closeBtn);
            
            // Auto-hide
            setTimeout(() => this.hideAlert(alert), 5000);
        });
    }

    hideAlert(alert) {
        if (alert && alert.parentNode) {
            alert.style.opacity = '0';
            alert.style.transform = 'translateY(-20px)';
            setTimeout(() => {
                if (alert.parentNode) {
                    alert.remove();
                }
            }, 300);
        }
    }

    setupFormValidation() {
        // Add CSS for validation styles
        const style = document.createElement('style');
        style.textContent = `
            @keyframes shake {
                0%, 100% { transform: translateX(0); }
                10%, 30%, 50%, 70%, 90% { transform: translateX(-5px); }
                20%, 40%, 60%, 80% { transform: translateX(5px); }
            }
            
            .form-control.is-invalid {
                border-color: #e74c3c !important;
                box-shadow: 0 0 0 3px rgba(231, 76, 60, 0.1) !important;
            }
            
            .form-control.is-valid {
                border-color: #27ae60 !important;
                box-shadow: 0 0 0 3px rgba(39, 174, 96, 0.1) !important;
            }
            
            .invalid-feedback {
                animation: fadeInUp 0.3s ease-out;
            }
            
            @keyframes fadeInUp {
                from {
                    opacity: 0;
                    transform: translateY(10px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }
        `;
        document.head.appendChild(style);
    }

    setupAnimations() {
        // Intersection Observer for animations
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animate-in');
                }
            });
        }, observerOptions);

        // Observe elements for animation
        document.querySelectorAll('.form-group, .login-btn, .register-link').forEach(el => {
            observer.observe(el);
        });

        // Add animation styles
        const animationStyle = document.createElement('style');
        animationStyle.textContent = `
            .form-group, .login-btn, .register-link {
                opacity: 0;
                transform: translateY(20px);
                transition: all 0.6s ease-out;
            }
            
            .animate-in {
                opacity: 1 !important;
                transform: translateY(0) !important;
            }
        `;
        document.head.appendChild(animationStyle);
    }

    setupFocusManagement() {
        // Focus first empty field on load
        setTimeout(() => {
            if (!this.usernameInput.value) {
                this.usernameInput.focus();
            } else if (!this.passwordInput.value) {
                this.passwordInput.focus();
            }
        }, 500);

        // Enhanced focus indicators
        const focusElements = [this.usernameInput, this.passwordInput, this.submitBtn];
        
        focusElements.forEach(element => {
            if (element) {
                element.addEventListener('focus', () => {
                    element.parentElement?.classList.add('focused');
                });
                
                element.addEventListener('blur', () => {
                    element.parentElement?.classList.remove('focused');
                });
            }
        });
    }

    setupKeyboardShortcuts() {
        document.addEventListener('keydown', (e) => {
            // Alt + L to focus username
            if (e.altKey && e.key.toLowerCase() === 'l') {
                e.preventDefault();
                this.usernameInput.focus();
            }
            
            // Alt + P to focus password
            if (e.altKey && e.key.toLowerCase() === 'p') {
                e.preventDefault();
                this.passwordInput.focus();
            }
            
            // Alt + T to toggle password visibility
            if (e.altKey && e.key.toLowerCase() === 't') {
                e.preventDefault();
                this.togglePassword();
            }
            
            // Enter to submit from any field
            if (e.key === 'Enter' && (e.target === this.usernameInput || e.target === this.passwordInput)) {
                e.preventDefault();
                this.handleSubmit(e);
            }
        });
    }

    checkBrowserSupport() {
        // Check for required features
        const requiredFeatures = [
            'localStorage',
            'addEventListener',
            'querySelector',
            'classList'
        ];

        const unsupportedFeatures = requiredFeatures.filter(feature => {
            switch (feature) {
                case 'localStorage':
                    return typeof Storage === 'undefined';
                case 'addEventListener':
                    return !document.addEventListener;
                case 'querySelector':
                    return !document.querySelector;
                case 'classList':
                    return !document.createElement('div').classList;
                default:
                    return false;
            }
        });

        if (unsupportedFeatures.length > 0) {
            console.warn('Algunas funcionalidades pueden no estar disponibles en este navegador:', unsupportedFeatures);
            this.showAlert('Tu navegador puede no soportar todas las funcionalidades. Considera actualizarlo.', 'warning');
        }

        // Check for WebAuthn support (for future biometric login)
        if (window.PublicKeyCredential) {
            console.log('WebAuthn soportado - Login biométrico disponible para futuras versiones');
        }
    }

    // Utility methods
    static debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    static throttle(func, limit) {
        let inThrottle;
        return function() {
            const args = arguments;
            const context = this;
            if (!inThrottle) {
                func.apply(context, args);
                inThrottle = true;
                setTimeout(() => inThrottle = false, limit);
            }
        };
    }

    // Method to handle network errors
    handleNetworkError() {
        this.setLoadingState(false);
        this.showAlert('Error de conexión. Por favor verifica tu conexión a internet.', 'error');
    }

    // Method to validate form before submission
    validateForm() {
        const isValid = this.validateUsername() && this.validatePassword();
        const isRobotChecked = this.notRobotCheckbox?.checked || false;
        
        return isValid && isRobotChecked;
    }

    // Method to reset form
    resetForm() {
        this.form.reset();
        this.clearFieldError(this.usernameInput);
        this.clearFieldError(this.passwordInput);
        this.setLoadingState(false);
    }

    // Method to handle successful login
    handleLoginSuccess() {
        this.showAlert('¡Login exitoso! Redirigiendo...', 'success');
        this.setLoadingState(false);
    }

    // Method to handle login error
    handleLoginError(message) {
        this.showAlert(message || 'Error en el login. Verifica tus credenciales.', 'error');
        this.setLoadingState(false);
        this.passwordInput.focus();
        this.passwordInput.select();
    }
}

// Additional utility functions
class SecurityUtils {
    static detectSuspiciousActivity() {
        // Basic detection for multiple failed attempts
        const failedAttempts = parseInt(sessionStorage.getItem('failedLoginAttempts') || '0');
        return failedAttempts > 3;
    }

    static logFailedAttempt() {
        const current = parseInt(sessionStorage.getItem('failedLoginAttempts') || '0');
        sessionStorage.setItem('failedLoginAttempts', (current + 1).toString());
    }

    static clearFailedAttempts() {
        sessionStorage.removeItem('failedLoginAttempts');
    }

    static isSecureContext() {
        return window.isSecureContext || location.protocol === 'https:' || location.hostname === 'localhost';
    }
}

// Performance monitoring
class PerformanceMonitor {
    static measureLoadTime() {
        if (window.performance && window.performance.timing) {
            const loadTime = window.performance.timing.loadEventEnd - window.performance.timing.navigationStart;
            console.log(`Página cargada en ${loadTime}ms`);
            return loadTime;
        }
    }

    static measureFormSubmissionTime() {
        const startTime = performance.now();
        return () => {
            const endTime = performance.now();
            console.log(`Formulario procesado en ${endTime - startTime}ms`);
        };
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Initialize login manager
    const loginManager = new LoginManager();
    
    // Make it globally accessible for debugging
    window.loginManager = loginManager;
    
    // Measure page load performance
    PerformanceMonitor.measureLoadTime();
    
    // Add security warnings if not in secure context
    if (!SecurityUtils.isSecureContext()) {
        console.warn('La página no está siendo servida a través de HTTPS. Algunas funcionalidades de seguridad pueden no estar disponibles.');
    }
    
    // Setup service worker for offline functionality (if available)
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/sw.js').catch(err => {
            console.log('Service Worker no disponible:', err);
        });
    }
    
    console.log('Portal IPS Login inicializado correctamente');
});

// Handle page visibility changes
document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        // Page is hidden - could implement session timeout warning
        console.log('Página oculta - considerando timeout de sesión');
    } else {
        // Page is visible again
        console.log('Página visible - reanudando actividad normal');
    }
});

// Handle network status changes
window.addEventListener('online', () => {
    console.log('Conexión restaurada');
    document.querySelector('.login-form')?.classList.remove('offline');
});

window.addEventListener('offline', () => {
    console.log('Conexión perdida');
    document.querySelector('.login-form')?.classList.add('offline');
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { LoginManager, SecurityUtils, PerformanceMonitor };
}