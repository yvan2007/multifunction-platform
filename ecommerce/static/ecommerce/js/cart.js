document.addEventListener('DOMContentLoaded', function() {
    const checkoutForm = document.querySelector('#checkout-form');
    if (checkoutForm) {
        checkoutForm.addEventListener('submit', function(e) {
            e.preventDefault();

            // Show loading animation
            const loadingOverlay = document.querySelector('.loading-overlay');
            loadingOverlay.style.display = 'flex';

            // Simulate payment processing (replace with actual API call)
            setTimeout(() => {
                loadingOverlay.style.display = 'none';

                // Show success animation
                const successAnimation = document.querySelector('.success-animation');
                successAnimation.style.display = 'block';

                // Redirect to order confirmation page after animation
                setTimeout(() => {
                    window.location.href = '/ecommerce/order-history/';
                }, 2000);
            }, 3000); // Simulate 3-second processing
        });
    }
});