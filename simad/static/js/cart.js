/**
 * Shopping Cart Management using LocalStorage
 */
class Cart {
    constructor() {
        this.items = JSON.parse(localStorage.getItem('cart')) || [];
        this.init();
    }

    init() {
        // Initial update on page load
        this.updateCartUI();
    }

    /**
     * Adds a product to the cart
     * @param {Object} product - Product details (id, name, price, image)
     */
    addItem(product) {
        const existingItem = this.items.find(item => item.id === product.id);
        
        if (existingItem) {
            existingItem.quantity = (existingItem.quantity || 1) + 1;
        } else {
            this.items.push({
                ...product,
                quantity: 1
            });
        }

        this.save();
        this.updateCartUI();
        this.notifySuccess(product.name);
    }

    /**
     * Saves cart to localStorage
     */
    save() {
        localStorage.setItem('cart', JSON.stringify(this.items));
    }

    /**
     * Updates the cart count in the navbar
     */
    updateCartUI() {
        const count = this.items.reduce((total, item) => total + (item.quantity || 1), 0);
        const countElement = document.getElementById('cart-count');
        
        if (countElement) {
            countElement.textContent = count;
            
            // Animate only if count > 0 to avoid animation on page load with 0
            if (count > 0 && window.anime) {
                window.anime({
                    targets: countElement,
                    scale: [1, 1.4, 1],
                    duration: 400,
                    easing: 'easeOutBack'
                });
            }
        }
    }

    /**
     * Shows a toast notification
     * @param {string} productName 
     */
    notifySuccess(productName) {
        if (window.toastManager) {
            window.toastManager.buildToast()
                .setMessage(`${productName} ajouté au panier !`)
                .setType('success')
                .setPosition('top-right')
                .setDuration(3000)
                .show();
        } else {
            console.warn('ToastManager not found on window');
        }
    }

    /**
     * Returns the number of unique items in the cart
     */
    getItemCount() {
        return this.items.length;
    }
}

// Initialize Cart on DOMContentLoaded
document.addEventListener('DOMContentLoaded', () => {
    const cart = new Cart();
    
    // Export to window for global access if needed
    window.cartManager = cart;

    // Use event delegation for add-to-cart buttons
    document.addEventListener('click', (event) => {
        const target = event.target.closest('.add-to-cart-btn');
        if (target) {
            event.preventDefault();
            
            const product = {
                id: target.dataset.id,
                name: target.dataset.name,
                price: target.dataset.price,
                image: target.dataset.image
            };
            
            cart.addItem(product);
        }
    });
});
