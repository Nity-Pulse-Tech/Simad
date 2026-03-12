/**
 * Base class for handling common functionality like CSRF tokens and errors
 */
class BaseHandler {
    handleError(error, context, genericMessage) {
        let message;
        if (error.name === "TypeError") {
            message = gettext('Server not reachable. Please check your connection or try again later.');
        } else if (error.name === "TimeoutError") {
            message = gettext('The request timed out. Please try again.');
        } else if (error.message) {
            message = error.message;
        } else if (error instanceof SyntaxError) {
            message = gettext('Server error occurred. Please try again later.');
        } else {
            message = genericMessage || gettext("An Unexpected Error occur, please try again later.");
        }

        window.toastManager.buildToast()
            .setMessage(message)
            .setType(message === "Coming soon." ? 'info' : 'danger')
            .setPosition('top-right')
            .setDuration(4000)
            .show();

        console.error(`${context}:`, error);
    }
}

// Base API class for common functionality
class BaseAPI {
    // Base request configuration
    _requestConfig(method, body = null) {
        const config = {
            method,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value
            }
        };

        if (body) {
            if (body instanceof FormData) {
                config.body = body;
            } else {
                config.headers['Content-Type'] = 'application/json';
                config.body = JSON.stringify(body);
            }
        }

        return config;
    }

    async _sendRequest(url, method, body = null) {
        try {
            return await fetch(url, this._requestConfig(method, body));
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    }
}
