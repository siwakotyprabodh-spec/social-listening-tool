// Social Listening Tool - JavaScript Functions

// Global variables
let currentUser = null;
let isLoading = false;

// Initialize app
$(document).ready(function() {
    initializeApp();
});

// Initialize application
function initializeApp() {
    // Check for user session
    checkUserSession();
    
    // Initialize tooltips
    $('[data-bs-toggle="tooltip"]').tooltip();
    
    // Initialize popovers
    $('[data-bs-toggle="popover"]').popover();
    
    // Add fade-in animation to cards
    $('.card').addClass('fade-in');
    
    // Initialize file input
    initializeFileInput();
}

// Check user session
function checkUserSession() {
    // This would typically make an API call to check session
    // For now, we'll assume the user is logged in if we're not on login/register pages
    const currentPath = window.location.pathname;
    if (currentPath !== '/login' && currentPath !== '/register') {
        // User is logged in
        updateUserInterface();
    }
}

// Update user interface based on login status
function updateUserInterface() {
    // Add user-specific features
    $('.user-only').show();
    $('.guest-only').hide();
}

// Initialize file input with drag and drop
function initializeFileInput() {
    const fileInput = document.getElementById('fileInput');
    if (!fileInput) return;
    
    // Add drag and drop functionality
    fileInput.addEventListener('dragover', function(e) {
        e.preventDefault();
        $(this).closest('.card').addClass('drag-over');
    });
    
    fileInput.addEventListener('dragleave', function(e) {
        e.preventDefault();
        $(this).closest('.card').removeClass('drag-over');
    });
    
    fileInput.addEventListener('drop', function(e) {
        e.preventDefault();
        $(this).closest('.card').removeClass('drag-over');
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            this.files = files;
            $(this).trigger('change');
        }
    });
    
    // Add change event listener
    fileInput.addEventListener('change', function() {
        const file = this.files[0];
        if (file) {
            validateFile(file);
        }
    });
}

// Validate uploaded file
function validateFile(file) {
    const allowedTypes = ['text/csv', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'];
    const allowedExtensions = ['.csv', '.xlsx'];
    
    const fileExtension = file.name.toLowerCase().substring(file.name.lastIndexOf('.'));
    
    if (!allowedExtensions.includes(fileExtension)) {
        showAlert('Please upload a CSV or Excel file (.csv, .xlsx)', 'warning');
        return false;
    }
    
    if (file.size > 16 * 1024 * 1024) { // 16MB
        showAlert('File size too large. Please upload a file smaller than 16MB.', 'warning');
        return false;
    }
    
    return true;
}

// Show alert message
function showAlert(message, type = 'info', duration = 5000) {
    const alertId = 'alert-' + Date.now();
    const alertHtml = `
        <div id="${alertId}" class="alert alert-${type} alert-dismissible fade show" role="alert">
            <i class="fas fa-${getAlertIcon(type)}"></i> ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    // Remove existing alerts
    $('.alert').remove();
    
    // Add new alert
    $('.container').first().prepend(alertHtml);
    
    // Auto-dismiss after duration
    if (duration > 0) {
        setTimeout(function() {
            $(`#${alertId}`).fadeOut(function() {
                $(this).remove();
            });
        }, duration);
    }
    
    // Scroll to top to show alert
    $('html, body').animate({ scrollTop: 0 }, 300);
}

// Get alert icon based on type
function getAlertIcon(type) {
    const icons = {
        'success': 'check-circle',
        'danger': 'exclamation-triangle',
        'warning': 'exclamation-circle',
        'info': 'info-circle',
        'primary': 'info-circle'
    };
    return icons[type] || 'info-circle';
}

// Show loading state
function showLoading(element, text = 'Loading...') {
    if (typeof element === 'string') {
        element = $(element);
    }
    
    element.prop('disabled', true);
    element.data('original-text', element.text());
    element.html(`<i class="fas fa-spinner fa-spin"></i> ${text}`);
}

// Hide loading state
function hideLoading(element) {
    if (typeof element === 'string') {
        element = $(element);
    }
    
    element.prop('disabled', false);
    const originalText = element.data('original-text');
    if (originalText) {
        element.text(originalText);
    }
}

// Format file size
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Format date
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Format number with commas
function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

// Debounce function
function debounce(func, wait, immediate) {
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
}

// Throttle function
function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// Copy to clipboard
function copyToClipboard(text) {
    if (navigator.clipboard) {
        navigator.clipboard.writeText(text).then(function() {
            showAlert('Copied to clipboard!', 'success', 2000);
        }).catch(function() {
            fallbackCopyToClipboard(text);
        });
    } else {
        fallbackCopyToClipboard(text);
    }
}

// Fallback copy to clipboard for older browsers
function fallbackCopyToClipboard(text) {
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
        showAlert('Copied to clipboard!', 'success', 2000);
    } catch (err) {
        showAlert('Failed to copy to clipboard', 'warning');
    }
    
    document.body.removeChild(textArea);
}

// Export data to CSV
function exportToCSV(data, filename = 'export.csv') {
    if (!data || data.length === 0) {
        showAlert('No data to export', 'warning');
        return;
    }
    
    const headers = Object.keys(data[0]);
    const csvContent = [
        headers.join(','),
        ...data.map(row => headers.map(header => {
            const value = row[header];
            // Escape commas and quotes in CSV
            if (typeof value === 'string' && (value.includes(',') || value.includes('"'))) {
                return `"${value.replace(/"/g, '""')}"`;
            }
            return value;
        }).join(','))
    ].join('\n');
    
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    
    if (link.download !== undefined) {
        const url = URL.createObjectURL(blob);
        link.setAttribute('href', url);
        link.setAttribute('download', filename);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        showAlert('Data exported successfully!', 'success');
    }
}

// Download data as JSON
function downloadJSON(data, filename = 'export.json') {
    const jsonContent = JSON.stringify(data, null, 2);
    const blob = new Blob([jsonContent], { type: 'application/json;charset=utf-8;' });
    const link = document.createElement('a');
    
    if (link.download !== undefined) {
        const url = URL.createObjectURL(blob);
        link.setAttribute('href', url);
        link.setAttribute('download', filename);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        showAlert('Data exported successfully!', 'success');
    }
}

// Show preferences modal
function showPreferences() {
    // This would open a preferences modal
    // For now, we'll just scroll to the preferences section
    const preferencesCard = $('.preferences-card');
    if (preferencesCard.length) {
        $('html, body').animate({
            scrollTop: preferencesCard.offset().top - 100
        }, 500);
    }
}

// Validate email
function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

// Validate URL
function isValidURL(string) {
    try {
        new URL(string);
        return true;
    } catch (_) {
        return false;
    }
}

// Get sentiment color class
function getSentimentColorClass(score) {
    if (score > 0.1) return 'text-success';
    if (score < -0.1) return 'text-danger';
    return 'text-warning';
}

// Get sentiment badge class
function getSentimentBadgeClass(score) {
    if (score > 0.1) return 'bg-success';
    if (score < -0.1) return 'bg-danger';
    return 'bg-warning';
}

// Get sentiment label
function getSentimentLabel(score) {
    if (score > 0.1) return 'Positive';
    if (score < -0.1) return 'Negative';
    return 'Neutral';
}

// Smooth scroll to element
function scrollToElement(element, offset = 0) {
    if (typeof element === 'string') {
        element = $(element);
    }
    
    $('html, body').animate({
        scrollTop: element.offset().top - offset
    }, 500);
}

// Show confirmation dialog
function showConfirmation(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

// Show loading overlay
function showLoadingOverlay(text = 'Loading...') {
    const overlay = `
        <div id="loadingOverlay" class="loading-overlay">
            <div class="loading-content">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p class="mt-3">${text}</p>
            </div>
        </div>
    `;
    
    $('body').append(overlay);
}

// Hide loading overlay
function hideLoadingOverlay() {
    $('#loadingOverlay').remove();
}

// Add loading overlay CSS if not exists
if (!$('#loadingOverlayStyles').length) {
    $('head').append(`
        <style id="loadingOverlayStyles">
            .loading-overlay {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.5);
                display: flex;
                justify-content: center;
                align-items: center;
                z-index: 9999;
            }
            
            .loading-content {
                background: white;
                padding: 2rem;
                border-radius: 10px;
                text-align: center;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
            }
        </style>
    `);
}

// Initialize tooltips on dynamic content
$(document).on('mouseenter', '[data-bs-toggle="tooltip"]', function() {
    $(this).tooltip();
});

// Handle form submissions with loading states
$(document).on('submit', 'form', function() {
    const submitBtn = $(this).find('button[type="submit"]');
    if (submitBtn.length) {
        showLoading(submitBtn);
    }
});

// Handle AJAX errors globally
$(document).ajaxError(function(event, xhr, settings, thrownError) {
    let errorMessage = 'An error occurred';
    
    if (xhr.responseJSON && xhr.responseJSON.error) {
        errorMessage = xhr.responseJSON.error;
    } else if (xhr.status === 0) {
        errorMessage = 'Network error. Please check your connection.';
    } else if (xhr.status === 404) {
        errorMessage = 'Requested resource not found.';
    } else if (xhr.status === 500) {
        errorMessage = 'Server error. Please try again later.';
    }
    
    showAlert(errorMessage, 'danger');
});

// Add fade-in animation to new elements
$(document).on('DOMNodeInserted', function(e) {
    if ($(e.target).hasClass('card')) {
        $(e.target).addClass('fade-in');
    }
});
