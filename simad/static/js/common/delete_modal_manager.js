/**
 * Manages a dynamically created delete confirmation modal with customizable message and button texts.
 * Uses Flowbite Modal for display and returns a Promise for confirmation result.
 * Supports internationalization with gettext.
 * @class
 */
class DeleteModalManager {
    constructor() {
        this.modal = null;
        this.modalInstance = null;
        this.isClosing = false; // Prevent recursive calls
    }

    /**
     * Creates the delete confirmation modal DOM element dynamically.
     * @private
     * @param {string} message - The message to display in the modal.
     * @param {string} confirmText - The text for the confirm button.
     * @param {string} cancelText - The text for the cancel button.
     */
    createModal(message, confirmText, cancelText) {
        const modalId = `delete-modal-${Date.now()}`;
        this.modal = document.createElement('div');
        this.modal.id = modalId;
        this.modal.tabIndex = -1;
        this.modal.className = 'hidden overflow-y-auto overflow-x-hidden fixed top-0 right-0 left-0 z-[10000001] justify-center items-center w-full md:inset-0 h-[calc(100%-1rem)] max-h-full';
        this.modal.setAttribute('data-modal', 'true');

        this.modal.innerHTML = `
            <div class="relative w-full h-full max-w-md px-4 md:h-auto">
                <div class="relative bg-white rounded-lg shadow">
                    <div class="flex justify-end p-2">
                        <button type="button" class="text-gray-400 bg-transparent hover:bg-gray-200 hover:text-gray-900 rounded-lg text-sm p-1.5 ml-auto inline-flex items-center" data-modal-hide="${modalId}">
                            <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
                                <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"></path>
                            </svg>
                            <span class="sr-only">${gettext('Close modal')}</span>
                        </button>
                    </div>
                    <div class="p-6 pt-0 text-center">
                        <svg class="w-16 h-16 mx-auto text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                        </svg>
                        <h3 class="mt-5 mb-6 text-lg text-gray-500" id="delete-modal-message">${message || gettext('Are you sure you want to delete this user?')}</h3>
                        <button id="delete-modal-confirm" class="text-white bg-red-600 hover:bg-red-800 focus:ring-4 focus:ring-red-300 font-medium rounded-lg text-base inline-flex items-center px-3 py-2.5 text-center mr-2 cursor-pointer">
                            ${confirmText || gettext("Yes, I'm sure")}
                        </button>
                        <button id="delete-modal-cancel" class="text-gray-900 bg-white hover:bg-gray-100 focus:ring-4 focus:ring-blue-300 border border-gray-200 font-medium inline-flex items-center rounded-lg text-base px-3 py-2.5 text-center cursor-pointer" data-modal-hide="${modalId}">
                            ${cancelText || gettext('No, cancel')}
                        </button>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(this.modal);
        this.modalInstance = new Modal(this.modal, {
            backdrop: 'static',
            backdropClasses: 'bg-gray-900/50 fixed inset-0 z-[10000000]',
            closable: true,
            onHide: () => {
                if (!this.isClosing) {
                    this.isClosing = true;
                    this.closeModal();
                }
            }
        });

        this.initializeEventListeners(modalId);
    }

    /**
     * Initializes event listeners for modal buttons.
     * @private
     * @param {string} modalId - The unique ID of the modal.
     */
    initializeEventListeners(modalId) {
        const confirmButton = this.modal.querySelector('#delete-modal-confirm');
        const cancelButton = this.modal.querySelector('#delete-modal-cancel');
        const closeButton = this.modal.querySelector(`[data-modal-hide="${modalId}"]`);

        const confirmHandler = () => {
            if (this.resolveCallback) {
                this.resolveCallback(true);
                this.modalInstance.hide();
            }
        };
        const cancelHandler = () => {
            if (this.resolveCallback) {
                this.resolveCallback(false);
                this.modalInstance.hide();
            }
        };

        confirmButton.addEventListener('click', confirmHandler);
        cancelButton.addEventListener('click', cancelHandler);
        closeButton.addEventListener('click', cancelHandler);
    }

    /**
     * Closes the modal and cleans up resources.
     * @private
     */
    closeModal() {
        if (this.modal && this.modalInstance && !this.isClosing) {
            this.isClosing = true;
            this.modal.remove();
            this.modal = null;
            this.modalInstance = null;
            this.resolveCallback = null;
            this.isClosing = false;
        }
    }

    /**
     * Shows the delete confirmation modal with custom message and button texts.
     * @param {string} message - The message to display in the modal.
     * @param {string} confirmText - The text for the confirm button.
     * @param {string} cancelText - The text for the cancel button.
     * @returns {Promise<boolean>} Resolves with true if confirmed, false if cancelled or closed.
     */
    show(message, confirmText, cancelText) {
        return new Promise((resolve) => {
            this.resolveCallback = resolve;
            this.createModal(message, confirmText, cancelText);
            this.modalInstance.show();
        });
    }
}

// Export a singleton instance
const deleteModalManager = new DeleteModalManager();
window.deleteModalManager = deleteModalManager;
