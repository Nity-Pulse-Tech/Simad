/**
 * Shopping Cart Management using LocalStorage
 */
class Cart {
    constructor() {
        this.items = JSON.parse(localStorage.getItem('cart')) || [];
        console.log('Cart initialized. Items found in localStorage:', this.items);
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
            // If already in cart, show a different message
            this.notifyAlreadyAdded(product.name);
            return;
        } else {
            this.items.push({
                ...product,
                quantity: 1
            });
            this.save();
            this.updateCartUI();
            this.notifySuccess(product.name);
        }
    }

    /**
     * Saves cart to localStorage
     */
    save() {
        localStorage.setItem('cart', JSON.stringify(this.items));
        // Also trigger an event for other parts of the app to react if needed
        window.dispatchEvent(new CustomEvent('cart-updated', { detail: { items: this.items } }));
    }

    /**
     * Updates the cart count in any element with id="cart-count"
     */
    updateCartUI() {
        const count = this.items.reduce((total, item) => total + (item.quantity || 1), 0);
        const countElements = document.querySelectorAll('#cart-count');
        
        countElements.forEach(el => {
            el.textContent = count;
            
            // Animate only if count > 0
            if (count > 0 && window.anime) {
                window.anime({
                    targets: el,
                    scale: [1, 1.4, 1],
                    duration: 400,
                    easing: 'easeOutBack'
                });
            }
        });

        // If we are on the cart page, we might want to refresh the list
        if (typeof this.renderCartPage === 'function') {
            this.renderCartPage();
        }
    }

    /**
     * Shows a toast notification for success
     * @param {string} productName 
     */
    notifySuccess(productName) {
        if (window.toastManager) {
            window.toastManager.buildToast()
                .setMessage(`${productName} ajouté au panier !`)
                .setType('success')
                .setPosition('bottom-right')
                .setDuration(3000)
                .show();
        }
    }

    /**
     * Shows a toast notification for duplicate item
     * @param {string} productName 
     */
    notifyAlreadyAdded(productName) {
        if (window.toastManager) {
            window.toastManager.buildToast()
                .setMessage(`${productName} est déjà dans votre panier.`)
                .setType('info')
                .setPosition('bottom-right')
                .setDuration(3000)
                .show();
        }
    }

    /**
     * Removes an item from the cart
     * @param {string} productId 
     */
    removeItem(productId) {
        const item = this.items.find(i => i.id === productId);
        const name = item ? item.name : 'Produit';
        
        this.items = this.items.filter(i => i.id !== productId);
        this.save();
        this.updateCartUI();

        if (window.toastManager) {
            window.toastManager.buildToast()
                .setMessage(`${name} retiré du panier.`)
                .setType('warning')
                .setPosition('bottom-right')
                .setDuration(3000)
                .show();
        }
    }

    /**
     * Updates item quantity
     * @param {string} productId 
     * @param {number} delta - +1 or -1
     */
    updateQuantity(productId, delta) {
        const item = this.items.find(i => i.id === productId);
        if (item) {
            item.quantity = Math.max(1, (item.quantity || 1) + delta);
            this.save();
            this.updateCartUI();
        }
    }

    /**
     * Returns the items
     */
    getItems() {
        return this.items;
    }
}

// Initialize Cart immediately so it's available for other scripts
const cart = new Cart();
window.cartManager = cart;
console.log('cartManager exported to window');

// Use event delegation for add-to-cart buttons
document.addEventListener('DOMContentLoaded', () => {
    console.log('cart.js DOMContentLoaded fired');
    
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
