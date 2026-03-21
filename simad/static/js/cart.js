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
     * @param {Object} product - Product details (id, name, price, image, stock)
     * @param {number} quantity - Quantity to add (default 1)
     */
    addItem(product, quantity = 1) {
        const qtyToAdd = parseInt(quantity) || 1;
        // Validation: Stock check
        const stock = parseInt(product.stock) || 0;
        if (stock <= 0) {
            this.notifyError(`Désolé, ${product.name} est en rupture de stock.`);
            return;
        }

        const existingItem = this.items.find(item => item.id === product.id);
        
        if (existingItem) {
            // Check if we can add more
            if (existingItem.quantity + qtyToAdd <= stock) {
                existingItem.quantity += qtyToAdd;
                this.save();
                this.updateCartUI();
                this.notifySuccess(`${qtyToAdd} x ${product.name} ajouté au panier !`);
            } else {
                const available = stock - existingItem.quantity;
                if (available > 0) {
                    existingItem.quantity = stock;
                    this.save();
                    this.updateCartUI();
                    this.notifyError(`Stock maximum atteint. Nous avons ajouté les ${available} restants.`);
                } else {
                    this.notifyError(`Stock maximum atteint pour ${product.name} (${stock}).`);
                }
            }
            return;
        } else {
            // Limit first add to stock
            const finalQty = Math.min(qtyToAdd, stock);
            this.items.push({
                ...product,
                quantity: finalQty,
                stock: stock 
            });
            this.save();
            this.updateCartUI();
            if (finalQty < qtyToAdd) {
                this.notifyError(`Seulement ${finalQty} unités ajoutées (stock limité).`);
            } else {
                this.notifySuccess(`${finalQty} x ${product.name} ajouté au panier !`);
            }
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
        // USER REQUEST: Count unique products, not total quantity
        const count = this.items.length; 
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
     * @param {string} message 
     */
    notifySuccess(message) {
        if (window.toastManager) {
            window.toastManager.buildToast()
                .setMessage(message)
                .setType('success')
                .setPosition('bottom-right')
                .setDuration(3000)
                .show();
        }
    }

    /**
     * Shows a toast notification for errors/stock limits
     * @param {string} message 
     */
    notifyError(message) {
        if (window.toastManager) {
            window.toastManager.buildToast()
                .setMessage(message)
                .setType('warning')
                .setPosition('bottom-right')
                .setDuration(4000)
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
                .setType('info')
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
            const newQty = (item.quantity || 1) + delta;
            
            // Stock Validation
            if (delta > 0 && newQty > (item.stock || 999)) {
                this.notifyError(`Désolé, seulement ${item.stock} unités disponibles pour ${item.name}.`);
                return;
            }

            if (newQty <= 0) {
                this.removeItem(productId);
            } else {
                item.quantity = newQty;
                this.save();
                this.updateCartUI();
            }
        }
    }

    /**
     * Returns the items
     */
    getItems() {
        return this.items;
    }
}

// Initialize Cart immediately
const cart = new Cart();
window.cartManager = cart;

// Use event delegation for add-to-cart buttons
document.addEventListener('DOMContentLoaded', () => {
    document.addEventListener('click', (event) => {
        const target = event.target.closest('.add-to-cart-btn');
        if (target) {
            event.preventDefault();
            
            const product = {
                id: target.dataset.id,
                name: target.dataset.name,
                price: target.dataset.price,
                image: target.dataset.image,
                stock: target.dataset.stock
            };
            
            const quantity = parseInt(target.dataset.quantity || 1);
            cart.addItem(product, quantity);
        }
    });
});
