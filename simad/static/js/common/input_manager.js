/**
 * Manages error display for a single input element, including feedback divs and optional error icons.
 */
class InputValidationManager {
    constructor(inputElement, options = {}) {
        this.input = inputElement;
        // this.isTextInput = this.input.tagName.toLowerCase() === 'input' && this.input.type.toLowerCase() === 'text';
        this.options = {
            showIcon: false,
            iconErrors: options.iconErrors || ['required', 'format', 'maxlength', 'server'], // Errors that trigger the icon
            feedbackId: options.feedbackId || `${inputElement.id}_feedback`, // ID for error feedback div
            ...options
        };
        this.feedbackContainer = null;
        this.iconContainer = null;
        this.init();
    }

    /**
     * Initializes the feedback container and icon for error display.
     */
    init() {
        // Create or find feedback container
        this.feedbackContainer = document.getElementById(this.options.feedbackId);
        if (!this.feedbackContainer) {
            this.feedbackContainer = document.createElement('div');
            this.feedbackContainer.id = this.options.feedbackId;
            this.feedbackContainer.className = 'text-xs mt-1 text-red-500';
            this.input.parentElement.insertAdjacentElement('afterend', this.feedbackContainer);
        }

        // Create icon container only for <input type="text">
        if (this.options.showIcon) {
            this.iconContainer = document.createElement('span');
            this.iconContainer.className = 'absolute top-1/2 right-3.5 -translate-y-1/2';
            this.iconContainer.style.display = 'none';
            this.iconContainer.innerHTML = `
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path fill-rule="evenodd" clip-rule="evenodd"
                          d="M2.58325 7.99967C2.58325 5.00813 5.00838 2.58301 7.99992 2.58301C10.9915 2.58301 13.4166 5.00813 13.4166 7.99967C13.4166 10.9912 10.9915 13.4163 7.99992 13.4163C5.00838 13.4163 2.58325 10.9912 2.58325 7.99967ZM7.99992 1.08301C4.17995 1.08301 1.08325 4.17971 1.08325 7.99967C1.08325 11.8196 4.17995 14.9163 7.99992 14.9163C11.8199 14.9163 14.9166 11.8196 14.9166 7.99967C14.9166 4.17971 11.8199 1.08301 7.99992 1.08301ZM7.09932 5.01639C7.09932 5.51345 7.50227 5.91639 7.99932 5.91639H7.99999C8.49705 5.91639 8.89999 5.51345 8.89999 5.01639C8.89999 4.51933 8.49705 4.11639 7.99999 4.11639H7.99932C7.50227 4.11639 7.09932 4.51933 7.09932 5.01639ZM7.99998 11.8306C7.58576 11.8306 7.24998 11.4948 7.24998 11.0806V7.29627C7.24998 6.88206 7.58576 6.54627 7.99998 6.54627C8.41419 6.54627 8.74998 6.88206 8.74998 7.29627V11.0806C8.74998 11.4948 8.41419 11.8306 7.99998 11.8306Z"
                          fill="#F04438"></path>
                </svg>
            `;
            this.input.parentElement.appendChild(this.iconContainer);
        }
    }

    /**
     * Updates the UI to reflect validation errors.
     * @param {Array} errors - List of error objects with type and message.
     */
    updateUI(errors) {
        // Clear previous state
        this.input.classList.remove('public-dashboard-invalid-input');
        this.feedbackContainer.innerHTML = '';
        if (this.iconContainer) {
            this.iconContainer.style.display = 'none';
        }

        // Apply error state
        if (errors.length > 0) {
            this.input.classList.add('public-dashboard-invalid-input');
            errors.forEach(error => {
                const errorElement = document.createElement('p');
                errorElement.className = 'feedback text-xs text-red-500 mt-1.5';
                errorElement.textContent = error.message;
                this.feedbackContainer.appendChild(errorElement);
            });

            // Show icon for specified error types if applicable
            if (this.options.showIcon && errors.some(e => this.options.iconErrors.includes(e.type))) {
                this.iconContainer.style.display = 'block';
            }
        }
    }

    /**
     * Clears any validation errors.
     */
    clearErrors() {
        this.input.classList.remove('public-dashboard-invalid-input');
        this.feedbackContainer.innerHTML = '';
        if (this.iconContainer) {
            this.iconContainer.style.display = 'none';
        }
    }

    /**
     * Marks the input as valid, clearing any errors and feedback.
     */
    setValid() {
        this.clearErrors();
        this.input.classList.remove('public-dashboard-invalid-input');
        this.feedbackContainer.classList.add('hidden');
    }

    /**
     * Marks the input as valid and displays a success message.
     * @param {string} message - The success message to display.
     */
    setValidWithMessage(message) {
        this.clearErrors();
        this.input.classList.remove('public-dashboard-invalid-input');
        this.feedbackContainer.classList.remove('hidden');
        this.feedbackContainer.innerHTML = '';
        const successElement = document.createElement('p');
        successElement.className = 'feedback text-xs text-green-500 mt-1.5';
        successElement.textContent = message;
        this.feedbackContainer.appendChild(successElement);
    }

    /**
     * Marks the input as invalid and displays validation errors.
     * @param {Array} errors - List of error objects with type and message.
     */
    setInvalid(errors) {
        this.input.classList.add('public-dashboard-invalid-input');
        this.feedbackContainer.classList.remove('hidden');
        this.feedbackContainer.innerHTML = '';
        errors.forEach(error => {
            const errorElement = document.createElement('p');
            errorElement.className = 'feedback text-xs text-red-500 mt-1.5';
            errorElement.textContent = error instanceof Object ? error.message : error;
            this.feedbackContainer.appendChild(errorElement);
        });

        // Show icon for specified error types if applicable
        if (this.options.showIcon && errors.some(e => this.options.iconErrors.includes(e.type))) {
            this.iconContainer.style.display = 'block';
        }
    }
}
