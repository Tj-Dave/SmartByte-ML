// /Documents/flood-predictor_v1/static/ui-enhancements.js
// // UI Enhancements for modern design - keeps main.js functionality intact

document.addEventListener('DOMContentLoaded', function() {
    // Enhanced modal functionality for the new design
    const modals = document.querySelectorAll('.modal');
    
    // Close modals when clicking outside
    modals.forEach(modal => {
        modal.addEventListener('click', function(e) {
            if (e.target === modal) {
                modal.classList.remove('show');
            }
        });
    });

    // Enhanced form submission with loading state
    const searchForm = document.getElementById('search-form');
    const originalSubmitHandler = searchForm.onsubmit;
    
    searchForm.addEventListener('submit', function(e) {
        // Add modern loading state
        const submitButton = this.querySelector('.btn-primary');
        const originalText = submitButton.innerHTML;
        
        submitButton.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating...';
        submitButton.disabled = true;
        
        // Reset button after a delay (this will be handled by main.js fetch completion)
        setTimeout(() => {
            submitButton.innerHTML = originalText;
            submitButton.disabled = false;
        }, 3000);
    });

    // Add smooth scroll animations for sidebar cards
    const cards = document.querySelectorAll('.card');
    cards.forEach((card, index) => {
        card.style.animationDelay = `${index * 0.1}s`;
    });

    // Enhanced responsive behavior
    function handleResize() {
        const sidebar = document.getElementById('sidebar');
        const toggleButton = document.querySelector('.toggle-sidebar');
        
        if (window.innerWidth > 768) {
            sidebar.classList.remove('active');
        }
    }

    window.addEventListener('resize', handleResize);

    // Enhance the legend styling when it's created by main.js
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.type === 'childList') {
                const legend = document.getElementById('legend');
                if (legend && !legend.classList.contains('enhanced')) {
                    legend.classList.add('enhanced');
                    // Style enhancements are handled by CSS
                }
            }
        });
    });

    observer.observe(document.body, {
        childList: true,
        subtree: true
    });

    // Add keyboard navigation for modals
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            modals.forEach(modal => {
                if (modal.classList.contains('show')) {
                    modal.classList.remove('show');
                }
            });
        }
    });

    // Enhance theme switching with transition effects
    const themeInputs = document.querySelectorAll('input[name="theme"]');
    themeInputs.forEach(input => {
        input.addEventListener('change', function() {
            // Add transition class
            document.body.style.transition = 'all 0.3s ease';
            
            setTimeout(() => {
                document.body.style.transition = '';
            }, 300);
        });
    });

    // Add focus management for accessibility
    const focusableElements = 'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])';
    
    modals.forEach(modal => {
        modal.addEventListener('keydown', function(e) {
            if (e.key === 'Tab') {
                const focusable = modal.querySelectorAll(focusableElements);
                const firstFocusable = focusable[0];
                const lastFocusable = focusable[focusable.length - 1];

                if (e.shiftKey) {
                    if (document.activeElement === firstFocusable) {
                        lastFocusable.focus();
                        e.preventDefault();
                    }
                } else {
                    if (document.activeElement === lastFocusable) {
                        firstFocusable.focus();
                        e.preventDefault();
                    }
                }
            }
        });
    });
});