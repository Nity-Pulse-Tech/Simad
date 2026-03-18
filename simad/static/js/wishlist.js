/**
 * Wishlist Management
 */
window.toggleWishlist = async function(button, alpineData) {
    const productId = button.getAttribute('data-product-id');
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;

    if (!csrfToken) {
        console.error('CSRF token not found. Please ensure {% csrf_token %} is present on the page.');
        return;
    }

    try {
        const response = await fetch('/wishlist/toggle/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': csrfToken,
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: new URLSearchParams({
                'product_id': productId
            })
        });

        if (response.status === 401) {
            if (window.toastManager) {
                window.toastManager.buildToast()
                    .setMessage('Veuillez vous connecter pour ajouter des favoris.')
                    .setType('warning')
                    .setPosition('bottom-right')
                    .setDuration(4000)
                    .show();
            }
            return;
        }

        const data = await response.json();
        if (data.success) {
            // Update Alpine.js state
            alpineData.isFavorite = (data.status === 'added');
            
            // Show toast
            if (window.toastManager) {
                window.toastManager.buildToast()
                    .setMessage(data.message)
                    .setType('success')
                    .setPosition('bottom-right')
                    .setDuration(3000)
                    .show();
            }
        } else {
            if (window.toastManager) {
                window.toastManager.buildToast()
                    .setMessage(data.message || 'Une erreur est survenue.')
                    .setType('danger')
                    .setPosition('bottom-right')
                    .setDuration(4000)
                    .show();
            }
        }
    } catch (error) {
        console.error('Wishlist error:', error);
        if (window.toastManager) {
            window.toastManager.buildToast()
                .setMessage('Erreur de connexion au serveur.')
                .setType('danger')
                .setPosition('bottom-right')
                .setDuration(4000)
                .show();
        }
    }
};
