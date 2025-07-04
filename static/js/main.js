// static/js/main.js

// Main JavaScript file for Bilim Sinovi platform

$(document).ready(function() {
    console.log('Bilim Sinovi platform loaded');
    
    // Initialize all components
    initializeComponents();
    
    // Form validation
    initializeFormValidation();
    
    // Loading states
    initializeLoadingStates();
    
    // Auto-hide alerts
    autoHideAlerts();
});

// Initialize all components
function initializeComponents() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Smooth scrolling for anchor links
    $('a[href^="#"]').on('click', function(event) {
        var target = $(this.getAttribute('href'));
        if( target.length ) {
            event.preventDefault();
            $('html, body').stop().animate({
                scrollTop: target.offset().top - 80
            }, 1000);
        }
    });
}

// Form validation
function initializeFormValidation() {
    // Bootstrap form validation
    var forms = document.querySelectorAll('.needs-validation');
    
    Array.prototype.slice.call(forms).forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });
    
    // Real-time validation for test ID input
    $('#testIdInput').on('input', function() {
        var value = $(this).val().trim();
        var isValid = /^\d+$/.test(value);
        
        if (value.length > 0) {
            if (isValid) {
                $(this).removeClass('is-invalid').addClass('is-valid');
            } else {
                $(this).removeClass('is-valid').addClass('is-invalid');
            }
        } else {
            $(this).removeClass('is-valid is-invalid');
        }
    });
    
    // Student ID validation
    $('input[name="student_id"]').on('input', function() {
        var value = $(this).val().trim();
        var isValid = value.length >= 3;
        
        if (value.length > 0) {
            if (isValid) {
                $(this).removeClass('is-invalid').addClass('is-valid');
            } else {
                $(this).removeClass('is-valid').addClass('is-invalid');
            }
        } else {
            $(this).removeClass('is-valid is-invalid');
        }
    });
    
    // Student name validation
    $('input[name="student_name"]').on('input', function() {
        var value = $(this).val().trim();
        var isValid = value.length >= 2 && /^[a-zA-Z\s]+$/.test(value);
        
        if (value.length > 0) {
            if (isValid) {
                $(this).removeClass('is-invalid').addClass('is-valid');
            } else {
                $(this).removeClass('is-valid').addClass('is-invalid');
            }
        } else {
            $(this).removeClass('is-valid is-invalid');
        }
    });
}

// Loading states for buttons
function initializeLoadingStates() {
    $('form').on('submit', function() {
        var submitBtn = $(this).find('button[type="submit"]');
        if (!submitBtn.hasClass('no-loading')) {
            submitBtn.addClass('loading');
            submitBtn.prop('disabled', true);
            
            // Re-enable after 5 seconds as fallback
            setTimeout(function() {
                submitBtn.removeClass('loading');
                submitBtn.prop('disabled', false);
            }, 5000);
        }
    });
    
    // AJAX loading states
    $(document).ajaxStart(function() {
        showSpinner();
    }).ajaxStop(function() {
        hideSpinner();
    });
}

// Auto-hide alerts after 5 seconds
function autoHideAlerts() {
    setTimeout(function() {
        $('.alert.alert-success, .alert.alert-info').fadeOut('slow');
    }, 5000);
}

// Utility functions
function showSpinner() {
    if ($('#loadingSpinner').length === 0) {
        $('body').append(`
            <div id="loadingSpinner" class="spinner-overlay">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
            </div>
        `);
    }
}

function hideSpinner() {
    $('#loadingSpinner').fadeOut('fast', function() {
        $(this).remove();
    });
}

// Show confirmation dialog
function showConfirmDialog(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

// Format number with commas
function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}

// Copy text to clipboard
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(function() {
        showToast('Copied to clipboard!', 'success');
    }).catch(function(err) {
        console.error('Failed to copy: ', err);
        showToast('Failed to copy', 'error');
    });
}

// Show toast notification
function showToast(message, type = 'info') {
    var toastClass = 'bg-' + (type === 'error' ? 'danger' : type);
    var toastHtml = `
        <div class="toast align-items-center text-white ${toastClass} border-0" role="alert">
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        </div>
    `;
    
    // Create toast container if it doesn't exist
    if ($('#toastContainer').length === 0) {
        $('body').append('<div id="toastContainer" class="toast-container position-fixed top-0 end-0 p-3"></div>');
    }
    
    var $toast = $(toastHtml);
    $('#toastContainer').append($toast);
    
    var toast = new bootstrap.Toast($toast[0]);
    toast.show();
    
    // Remove toast element after it's hidden
    $toast.on('hidden.bs.toast', function() {
        $(this).remove();
    });
}

// Time formatting
function formatTime(timeStr) {
    var time = new Date('1970-01-01T' + timeStr + 'Z');
    return time.toLocaleTimeString('en-US', { 
        hour: '2-digit', 
        minute: '2-digit',
        hour12: true 
    });
}

// Date formatting
function formatDate(dateStr) {
    var date = new Date(dateStr);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

// Calculate percentage
function calculatePercentage(correct, total) {
    if (total === 0) return 0;
    return Math.round((correct / total) * 100 * 100) / 100; // Round to 2 decimal places
}

// Get grade suffix
function getGradeSuffix(grade) {
    var suffixes = ['th', 'st', 'nd', 'rd'];
    var v = grade % 100;
    return grade + (suffixes[(v - 20) % 10] || suffixes[v] || suffixes[0]);
}

// Debounce function for search inputs
function debounce(func, wait, immediate) {
    var timeout;
    return function() {
        var context = this, args = arguments;
        var later = function() {
            timeout = null;
            if (!immediate) func.apply(context, args);
        };
        var callNow = immediate && !timeout;
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
        if (callNow) func.apply(context, args);
    };
}

// Search functionality
function initializeSearch() {
    var searchInput = $('#searchInput');
    if (searchInput.length > 0) {
        var debouncedSearch = debounce(function() {
            var searchTerm = searchInput.val().toLowerCase();
            performSearch(searchTerm);
        }, 300);
        
        searchInput.on('input', debouncedSearch);
    }
}

function performSearch(searchTerm) {
    $('.searchable-item').each(function() {
        var itemText = $(this).data('name').toLowerCase();
        if (itemText.includes(searchTerm)) {
            $(this).show();
        } else {
            $(this).hide();
        }
    });
}

// Print functionality
function printResults() {
    window.print();
}

// Export functionality (if needed)
function exportToCSV(data, filename) {
    var csv = convertArrayToCSV(data);
    var blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    var link = document.createElement("a");
    var url = URL.createObjectURL(blob);
    link.setAttribute("href", url);
    link.setAttribute("download", filename);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

function convertArrayToCSV(data) {
    if (!data || !data.length) return '';
    
    var headers = Object.keys(data[0]);
    var csvContent = headers.join(',') + '\n';
    
    data.forEach(function(row) {
        var values = headers.map(function(header) {
            var value = row[header];
            return typeof value === 'string' && value.includes(',') ? '"' + value + '"' : value;
        });
        csvContent += values.join(',') + '\n';
    });
    
    return csvContent;
}

// Keyboard shortcuts
$(document).on('keydown', function(e) {
    // Ctrl+Enter to submit forms
    if (e.ctrlKey && e.keyCode === 13) {
        var activeForm = $('form:visible').first();
        if (activeForm.length > 0) {
            activeForm.submit();
        }
    }
    
    // Escape key to close modals
    if (e.keyCode === 27) {
        $('.modal.show').modal('hide');
    }
});

// Performance monitoring
function logPerformance(action, startTime) {
    var endTime = performance.now();
    var duration = endTime - startTime;
    console.log(`${action} took ${duration.toFixed(2)} milliseconds`);
}

// Error handling
window.addEventListener('error', function(e) {
    console.error('JavaScript Error:', e.error);
    // Could send error to analytics service here
});

// Online/offline status
window.addEventListener('online', function() {
    showToast('Internet tiklendi', 'success');
});

window.addEventListener('offline', function() {
    showToast('Internet óshti', 'warning');
});

// Initialize on page load
$(window).on('load', function() {
    // Hide any loading spinners
    hideSpinner();
    
    // Initialize search if present
    initializeSearch();
    
    // Log page load time
    var loadTime = performance.now();
    logPerformance('Page load', 0);
});

// Bulk Questions specific functionality
var questionCount = 0;

function addQuestionRow(questionText = '', options = { A: '', B: '', C: '', D: '', correct: '' }) {
    questionCount++;
    var newRow = `
        <div class="question-row" id="question-${questionCount}">
            <div class="d-flex justify-content-between align-items-center mb-3">
                <h6 class="mb-0">Question ${questionCount}</h6>
                <button type="button" class="btn btn-sm btn-outline-danger remove-question-btn" onclick="removeQuestionRow(${questionCount})">
                    <i class="bi bi-trash"></i> Remove
                </button>
            </div>
            
            <div class="mb-3">
                <label class="form-label">Question Text:</label>
                <textarea class="form-control question-text" rows="3" placeholder="Enter question text" required>${questionText}</textarea>
            </div>
            
            <div class="row g-2 mb-3">
                <div class="col-md-6">
                    <label class="form-label">Option A:</label>
                    <input type="text" class="form-control option-a" placeholder="Option A" required value="${options.A}">
                </div>
                <div class="col-md-6">
                    <label class="form-label">Option B:</label>
                    <input type="text" class="form-control option-b" placeholder="Option B" required value="${options.B}">
                </div>
                <div class="col-md-6">
                    <label class="form-label">Option C:</label>
                    <input type="text" class="form-control option-c" placeholder="Option C" required value="${options.C}">
                </div>
                <div class="col-md-6">
                    <label class="form-label">Option D:</label>
                    <input type="text" class="form-control option-d" placeholder="Option D" required value="${options.D}">
                </div>
            </div>
            
            <div class="mb-3">
                <label class="form-label">Correct Answer:</label>
                <select class="form-control correct-answer" required>
                    <option value="">Select correct answer</option>
                    <option value="A" ${options.correct == 0 ? 'selected' : ''}>A</option>
                    <option value="B" ${options.correct == 1 ? 'selected' : ''}>B</option>
                    <option value="C" ${options.correct == 2 ? 'selected' : ''}>C</option>
                    <option value="D" ${options.correct == 3 ? 'selected' : ''}>D</option>
                </select>
            </div>
        </div>
    `;
    
    $('#questionsContainer').append(newRow);
    
    // Animate the new row
    // $('#question-' + questionCount).hide().fadeIn('slow');
    
    // Scroll to the new question
    // $('html, body').animate({
    //     scrollTop: $('#question-' + questionCount).offset().top - 100
    // }, 500);
}

function removeQuestionRow(questionId) {
    $('#question-' + questionId).addClass('removing');
    setTimeout(function() {
        $('#question-' + questionId).fadeOut('fast', function() {
            $(this).remove();
            updateQuestionNumbers();
        });
    }, 200);
}

function updateQuestionNumbers() {
    $('.question-row').each(function(index) {
        $(this).find('h6').text('Question ' + (index + 1));
    });
}

function collectQuestionsData() {
    var questionsData = [];
    
    $('.question-row').each(function() {
        var questionText = $(this).find('.question-text').val().trim();
        var optionA = $(this).find('.option-a').val().trim();
        var optionB = $(this).find('.option-b').val().trim();
        var optionC = $(this).find('.option-c').val().trim();
        var optionD = $(this).find('.option-d').val().trim();
        var correctAnswer = $(this).find('.correct-answer').val();
        
        // Only include if all fields are filled
        if (questionText && optionA && optionB && optionC && optionD && correctAnswer) {
            questionsData.push({
                question_text: questionText,
                option_a: optionA,
                option_b: optionB,
                option_c: optionC,
                option_d: optionD,
                correct_answer: correctAnswer
            });
        }
    });
    
    return questionsData;
}

// Export global functions
window.addQuestionRow = addQuestionRow;
window.removeQuestionRow = removeQuestionRow;
window.collectQuestionsData = collectQuestionsData;
window.showConfirmDialog = showConfirmDialog;
window.copyToClipboard = copyToClipboard;
window.showToast = showToast;
window.printResults = printResults;