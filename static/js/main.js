/**
 * SPEAKUP - Main Vanilla JavaScript
 * Provides client-side helpers: alert auto-dismissal and basic form UX enhancements.
 */

document.addEventListener('DOMContentLoaded', () => {
    // -------------------------------------------------------------------------
    // 1. Auto-dismiss Flash Alerts
    // Automatically fades out informational and success alerts after 5 seconds.
    // -------------------------------------------------------------------------
    const alerts = document.querySelectorAll('.alert-success, .alert-info');
    alerts.forEach((alert) => {
        setTimeout(() => {
            alert.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
            alert.style.opacity = '0';
            alert.style.transform = 'translateY(-6px)';
            setTimeout(() => {
                if (alert.parentElement) {
                    alert.remove();
                }
            }, 500);
        }, 5000);
    });

    // -------------------------------------------------------------------------
    // 2. Client-side Form UX Helper (Password Match Check)
    // Provides immediate visual indicator if passwords don't match on registration.
    // Server-side validation remains the authoritative source of security.
    // -------------------------------------------------------------------------
    const registerForm = document.querySelector('form[action*="register"]');
    if (registerForm) {
        const passwordInput = registerForm.querySelector('#password');
        const confirmInput = registerForm.querySelector('#confirm_password');

        if (passwordInput && confirmInput) {
            const checkMatch = () => {
                if (confirmInput.value && passwordInput.value !== confirmInput.value) {
                    confirmInput.setCustomValidity('Passwords do not match');
                } else {
                    confirmInput.setCustomValidity('');
                }
            };

            passwordInput.addEventListener('input', checkMatch);
            confirmInput.addEventListener('input', checkMatch);
        }
    }
});
