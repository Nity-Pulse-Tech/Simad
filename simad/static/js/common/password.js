class PasswordToggle {
    constructor() {
        this.eyeOpenSVG = `
            <svg class="w-5 h-5 text-gray-800" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="none" viewBox="0 0 24 24">
                <path stroke="currentColor" stroke-width="2" d="M21 12c0 1.2-4.03 6-9 6s-9-4.8-9-6c0-1.2 4.03-6 9-6s9 4.8 9 6Z"/>
                <path stroke="currentColor" stroke-width="2" d="M15 12a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z"/>
            </svg>
        `;
        this.eyeClosedSVG = `
            <svg class="w-5 h-5 text-gray-800" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="none" viewBox="0 0 24 24">
                <path stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3.933 13.909A4.357 4.357 0 0 1 3 12c0-1 4-6 9-6m7.6 3.8A5.068 5.068 0 0 1 21 12c0 1-3 6-9 6-.314 0-.62-.014-.918-.04M5 19 19 5m-4 7a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z"/>
            </svg>
        `;
        this.init();
    }

    init() {
        console.log('PasswordToggle: Initializing');
        const inputs = [
            document.getElementById('password'),
            document.getElementById('password2')
        ].filter(input => input !== null); // Filter out null inputs

        if (inputs.length === 0) {
            console.warn('PasswordToggle: No password inputs found');
            return;
        }

        inputs.forEach(input => {
            console.log('PasswordToggle: Setting up toggle for', input.id);
            this.setupToggle(input);
        });
    }

    setupToggle(input) {
        // Skip if already initialized
        if (input.dataset.toggleInitialized) {
            console.log('PasswordToggle: Input already initialized', input.id);
            return;
        }

        // Mark as initialized
        input.dataset.toggleInitialized = 'true';

        // Create wrapper
        const wrapper = document.createElement('div');
        wrapper.className = 'password-toggle-wrapper';
        wrapper.style.position = 'relative';

        // Move input into wrapper
        input.parentElement.insertBefore(wrapper, input);
        wrapper.appendChild(input);

        // Create toggle button
        const toggle = document.createElement('button');
        toggle.type = 'button';
        toggle.className = 'password-toggle-btn';
        toggle.style.position = 'absolute';
        toggle.style.right = '0.75rem';
        toggle.style.top = '50%';
        toggle.style.transform = 'translateY(-50%)';
        toggle.style.cursor = 'pointer';
        toggle.style.background = 'none';
        toggle.style.border = 'none';
        toggle.style.padding = '0';
        toggle.innerHTML = this.eyeClosedSVG;

        // Hover effects
        toggle.addEventListener('mouseover', () => {
            toggle.style.color = '#0b5e65';
        });
        toggle.addEventListener('mouseout', () => {
            toggle.style.color = '#6b7280';
        });

        // Toggle event
        toggle.addEventListener('click', () => {
            console.log('PasswordToggle: Toggling', input.id);
            const isPassword = input.type === 'password';
            input.type = isPassword ? 'text' : 'password';
            toggle.innerHTML = isPassword ? this.eyeOpenSVG : this.eyeClosedSVG;
        });

        wrapper.appendChild(toggle);
        console.log('PasswordToggle: Setup complete for', input.id);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    console.log('PasswordToggle: DOM loaded, starting');
    new PasswordToggle();
});