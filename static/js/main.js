// Main JavaScript functionality for RAG Assistant

document.addEventListener('DOMContentLoaded', function() {
    // Initialize theme
    initializeTheme();
    
    // Initialize tooltips
    initializeTooltips();
    
    // Initialize file upload enhancements
    initializeFileUpload();
    
    // Initialize auto-refresh for processing documents
    initializeAutoRefresh();
});

// Theme Management
function initializeTheme() {
    const themeToggle = document.getElementById('themeToggle');
    const htmlElement = document.documentElement;
    
    // Get saved theme or default to light
    const savedTheme = localStorage.getItem('theme') || 'light';
    setTheme(savedTheme);
    
    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            const currentTheme = htmlElement.getAttribute('data-bs-theme');
            const newTheme = currentTheme === 'light' ? 'dark' : 'light';
            setTheme(newTheme);
        });
    }
    
    function setTheme(theme) {
        htmlElement.setAttribute('data-bs-theme', theme);
        localStorage.setItem('theme', theme);
        
        if (themeToggle) {
            const icon = themeToggle.querySelector('i');
            if (theme === 'dark') {
                icon.className = 'bi bi-moon-fill';
                themeToggle.title = 'Switch to light mode';
            } else {
                icon.className = 'bi bi-sun-fill';
                themeToggle.title = 'Switch to dark mode';
            }
        }
    }
}

// Tooltip Initialization
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// File Upload Enhancements
function initializeFileUpload() {
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');
    
    if (!uploadArea || !fileInput) return;
    
    // Prevent default drag behaviors
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, preventDefaults, false);
        document.body.addEventListener(eventName, preventDefaults, false);
    });
    
    // Highlight drop area when item is dragged over it
    ['dragenter', 'dragover'].forEach(eventName => {
        uploadArea.addEventListener(eventName, highlight, false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, unhighlight, false);
    });
    
    // Handle dropped files
    uploadArea.addEventListener('drop', handleDrop, false);
    
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    function highlight(e) {
        uploadArea.classList.add('border-success');
    }
    
    function unhighlight(e) {
        uploadArea.classList.remove('border-success');
    }
    
    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        
        if (files.length > 0) {
            fileInput.files = files;
            
            // Trigger change event
            const event = new Event('change', { bubbles: true });
            fileInput.dispatchEvent(event);
        }
    }
}

// Auto-refresh for processing documents
function initializeAutoRefresh() {
    // Check if we're on the documents page with processing documents
    const processingBadges = document.querySelectorAll('.badge.bg-warning');
    
    if (processingBadges.length > 0) {
        console.log(`Found ${processingBadges.length} processing documents. Starting auto-refresh.`);
        
        // Refresh every 5 seconds
        const refreshInterval = setInterval(() => {
            location.reload();
        }, 5000);
        
        // Stop refreshing after 5 minutes to prevent infinite loops
        setTimeout(() => {
            clearInterval(refreshInterval);
            console.log('Auto-refresh stopped after 5 minutes.');
        }, 300000);
    }
}

// Utility Functions
const Utils = {
    // Format file size
    formatFileSize: function(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },
    
    // Show loading spinner
    showLoading: function(message = 'Loading...') {
        const existingOverlay = document.querySelector('.loading-overlay');
        if (existingOverlay) return;
        
        const overlay = document.createElement('div');
        overlay.className = 'loading-overlay';
        overlay.innerHTML = `
            <div class="text-center text-white">
                <div class="spinner-border mb-3" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <div>${message}</div>
            </div>
        `;
        document.body.appendChild(overlay);
    },
    
    // Hide loading spinner
    hideLoading: function() {
        const overlay = document.querySelector('.loading-overlay');
        if (overlay) {
            overlay.remove();
        }
    },
    
    // Show toast notification
    showToast: function(message, type = 'info') {
        // Create toast container if it doesn't exist
        let toastContainer = document.querySelector('.toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
            document.body.appendChild(toastContainer);
        }
        
        const toastId = 'toast-' + Date.now();
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${type} border-0`;
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');
        toast.id = toastId;
        
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;
        
        toastContainer.appendChild(toast);
        
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
        
        // Remove toast element after it's hidden
        toast.addEventListener('hidden.bs.toast', function() {
            toast.remove();
        });
    },
    
    // Debounce function
    debounce: function(func, wait, immediate) {
        let timeout;
        return function executedFunction() {
            const context = this;
            const args = arguments;
            const later = function() {
                timeout = null;
                if (!immediate) func.apply(context, args);
            };
            const callNow = immediate && !timeout;
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
            if (callNow) func.apply(context, args);
        };
    },
    
    // Copy text to clipboard
    copyToClipboard: function(text) {
        if (navigator.clipboard && window.isSecureContext) {
            return navigator.clipboard.writeText(text).then(() => {
                this.showToast('Copied to clipboard!', 'success');
            }).catch(err => {
                console.error('Failed to copy: ', err);
                this.showToast('Failed to copy to clipboard', 'danger');
            });
        } else {
            // Fallback for older browsers
            const textArea = document.createElement('textarea');
            textArea.value = text;
            textArea.style.position = 'fixed';
            textArea.style.left = '-999999px';
            textArea.style.top = '-999999px';
            document.body.appendChild(textArea);
            textArea.focus();
            textArea.select();
            
            try {
                document.execCommand('copy');
                textArea.remove();
                this.showToast('Copied to clipboard!', 'success');
            } catch (err) {
                console.error('Fallback: Oops, unable to copy', err);
                textArea.remove();
                this.showToast('Failed to copy to clipboard', 'danger');
            }
        }
    },
    
    // Validate file type and size
    validateFile: function(file, allowedTypes, maxSize) {
        const errors = [];
        
        // Check file type
        const fileExtension = file.name.split('.').pop().toLowerCase();
        const mimeType = file.type.toLowerCase();
        
        const isValidType = allowedTypes.some(type => {
            if (type.startsWith('.')) {
                return fileExtension === type.substring(1);
            } else {
                return mimeType.includes(type);
            }
        });
        
        if (!isValidType) {
            errors.push(`File type not supported. Allowed types: ${allowedTypes.join(', ')}`);
        }
        
        // Check file size
        if (file.size > maxSize) {
            errors.push(`File too large. Maximum size: ${this.formatFileSize(maxSize)}`);
        }
        
        return {
            isValid: errors.length === 0,
            errors: errors
        };
    }
};

// Global error handler
window.addEventListener('error', function(e) {
    console.error('Global error:', e.error);
    
    // Don't show error toast for minor issues
    if (e.error && e.error.message && !e.error.message.includes('Script error')) {
        Utils.showToast('An unexpected error occurred. Please refresh the page.', 'danger');
    }
});

// API Helper
const API = {
    // Generic API call wrapper
    call: async function(url, options = {}) {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
            },
        };
        
        const mergedOptions = { ...defaultOptions, ...options };
        
        try {
            const response = await fetch(url, mergedOptions);
            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || `HTTP error! status: ${response.status}`);
            }
            
            return data;
        } catch (error) {
            console.error('API call failed:', error);
            throw error;
        }
    },
    
    // Check document status
    checkDocumentStatus: async function(documentId) {
        return this.call(`/documents/status/${documentId}`);
    },
    
    // Send chat message
    sendMessage: async function(question, documentNames = null) {
        return this.call('/chat/ask', {
            method: 'POST',
            body: JSON.stringify({
                question: question,
                document_names: documentNames
            })
        });
    },
    
    // Clear chat
    clearChat: async function() {
        return this.call('/chat/clear', {
            method: 'POST'
        });
    }
};

// Make utilities available globally
window.Utils = Utils;
window.API = API;

// Auto-focus on first input when page loads
document.addEventListener('DOMContentLoaded', function() {
    const firstInput = document.querySelector('input[type="text"], input[type="email"], textarea');
    if (firstInput && !firstInput.disabled) {
        // Small delay to ensure page is fully rendered
        setTimeout(() => {
            firstInput.focus();
        }, 100);
    }
});

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + K to focus search/chat input
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        const searchInput = document.getElementById('questionInput') || document.querySelector('input[type="text"]');
        if (searchInput) {
            searchInput.focus();
        }
    }
    
    // Escape to clear focus
    if (e.key === 'Escape') {
        document.activeElement.blur();
    }
});

// Performance monitoring
if ('performance' in window) {
    window.addEventListener('load', function() {
        setTimeout(() => {
            const perfData = performance.getEntriesByType('navigation')[0];
            if (perfData) {
                console.log(`Page load time: ${perfData.loadEventEnd - perfData.loadEventStart}ms`);
            }
        }, 0);
    });
}
