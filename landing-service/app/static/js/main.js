// Main JavaScript functionality for GrainTrade Landing Pages

document.addEventListener('DOMContentLoaded', function() {
    initializeNavigation();
    initializeAnimations();
    initializeImageLazyLoading();
    initializeScrollEffects();
    initializeLanguageSwitcher();
});

// Navigation functionality
function initializeNavigation() {
    const navToggle = document.getElementById('nav-toggle');
    const navMenu = document.getElementById('nav-menu');
    
    if (navToggle && navMenu) {
        navToggle.addEventListener('click', () => {
            navToggle.classList.toggle('active');
            navMenu.classList.toggle('active');
            document.body.classList.toggle('nav-open');
        });
        
        // Close menu when clicking outside
        document.addEventListener('click', (e) => {
            if (!navToggle.contains(e.target) && !navMenu.contains(e.target)) {
                navToggle.classList.remove('active');
                navMenu.classList.remove('active');
                document.body.classList.remove('nav-open');
            }
        });
        
        // Close menu when clicking on nav links
        const navLinks = navMenu.querySelectorAll('.nav-link');
        navLinks.forEach(link => {
            link.addEventListener('click', () => {
                navToggle.classList.remove('active');
                navMenu.classList.remove('active');
                document.body.classList.remove('nav-open');
            });
        });
    }
}

// Animation functionality
function initializeAnimations() {
    // Intersection Observer for scroll animations
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate-in');
            }
        });
    }, observerOptions);
    
    // Observe elements for animation
    const animateElements = document.querySelectorAll(
        '.advantage-card, .for-whom-card, .step-card, .tip-card, .faq-item, .support-option'
    );
    
    animateElements.forEach((element, index) => {
        element.style.opacity = '0';
        element.style.transform = 'translateY(30px)';
        element.style.transition = `opacity 0.6s ease ${index * 0.1}s, transform 0.6s ease ${index * 0.1}s`;
        observer.observe(element);
    });
    
    // Add animate-in class styling
    const style = document.createElement('style');
    style.textContent = `
        .animate-in {
            opacity: 1 !important;
            transform: translateY(0) !important;
        }
    `;
    document.head.appendChild(style);
}

// Lazy loading for images
function initializeImageLazyLoading() {
    const images = document.querySelectorAll('img[loading="lazy"]');
    
    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src || img.src;
                    img.classList.remove('lazy');
                    imageObserver.unobserve(img);
                }
            });
        });
        
        images.forEach(img => {
            img.classList.add('lazy');
            imageObserver.observe(img);
        });
    }
}

// Scroll effects
function initializeScrollEffects() {
    let ticking = false;
    
    function updateScrollEffects() {
        const scrolled = window.pageYOffset;
        const rate = scrolled * -0.5;
        
        // Parallax effect for hero section
        const hero = document.querySelector('.hero');
        if (hero) {
            hero.style.transform = `translateY(${rate}px)`;
        }
        
        // Header background on scroll
        const header = document.querySelector('.header');
        if (header) {
            if (scrolled > 100) {
                header.classList.add('scrolled');
            } else {
                header.classList.remove('scrolled');
            }
        }
        
        ticking = false;
    }
    
    function requestTick() {
        if (!ticking) {
            requestAnimationFrame(updateScrollEffects);
            ticking = true;
        }
    }
    
    window.addEventListener('scroll', requestTick);
    
    // Add styles for scroll effects
    const style = document.createElement('style');
    style.textContent = `
        .header.scrolled {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
        }
        
        .lazy {
            opacity: 0;
            transition: opacity 0.3s;
        }
        
        .lazy:not([src]) {
            visibility: hidden;
        }
    `;
    document.head.appendChild(style);
}

// Language switcher functionality
function initializeLanguageSwitcher() {
    const langLinks = document.querySelectorAll('.lang-link');
    
    langLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            const newLang = e.target.textContent.toLowerCase().includes('укр') ? 'uk' : 'en';
            const currentUrl = new URL(window.location);
            currentUrl.searchParams.set('lang', newLang);
            
            // Add loading state
            e.target.classList.add('loading');
            
            // Navigate to new language
            window.location.href = currentUrl.toString();
        });
    });
}

// Smooth scroll for anchor links
function initializeSmoothScroll() {
    const anchorLinks = document.querySelectorAll('a[href^="#"]');
    
    anchorLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const targetId = link.getAttribute('href');
            const targetElement = document.querySelector(targetId);
            
            if (targetElement) {
                const headerHeight = document.querySelector('.header').offsetHeight;
                const targetPosition = targetElement.offsetTop - headerHeight - 20;
                
                window.scrollTo({
                    top: targetPosition,
                    behavior: 'smooth'
                });
            }
        });
    });
}

// Image gallery functionality for how-to steps
function initializeImageGallery() {
    const stepImages = document.querySelectorAll('.step-img');
    
    stepImages.forEach(img => {
        img.addEventListener('click', () => {
            openImageModal(img.src, img.alt);
        });
        
        img.style.cursor = 'pointer';
        img.title = 'Click to enlarge';
    });
}

// Image modal functionality
function openImageModal(src, alt) {
    // Create modal
    const modal = document.createElement('div');
    modal.className = 'image-modal';
    modal.innerHTML = `
        <div class="modal-backdrop">
            <div class="modal-content">
                <button class="modal-close">&times;</button>
                <img src="${src}" alt="${alt}" class="modal-image">
                <div class="modal-caption">${alt}</div>
            </div>
        </div>
    `;
    
    // Add modal styles
    const style = document.createElement('style');
    style.textContent = `
        .image-modal {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: 10000;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .modal-backdrop {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.9);
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 2rem;
        }
        
        .modal-content {
            position: relative;
            max-width: 90vw;
            max-height: 90vh;
            text-align: center;
        }
        
        .modal-close {
            position: absolute;
            top: -40px;
            right: -40px;
            width: 40px;
            height: 40px;
            background: rgba(255, 255, 255, 0.1);
            border: 2px solid rgba(255, 255, 255, 0.3);
            border-radius: 50%;
            color: white;
            font-size: 24px;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.3s ease;
        }
        
        .modal-close:hover {
            background: rgba(255, 255, 255, 0.2);
            border-color: rgba(255, 255, 255, 0.5);
        }
        
        .modal-image {
            max-width: 100%;
            max-height: 80vh;
            object-fit: contain;
            border-radius: 8px;
        }
        
        .modal-caption {
            color: white;
            margin-top: 1rem;
            font-size: 1.1rem;
        }
        
        @media (max-width: 768px) {
            .modal-close {
                top: -30px;
                right: -30px;
                width: 30px;
                height: 30px;
                font-size: 18px;
            }
        }
    `;
    document.head.appendChild(style);
    
    document.body.appendChild(modal);
    document.body.style.overflow = 'hidden';
    
    // Close modal functionality
    const closeModal = () => {
        document.body.removeChild(modal);
        document.body.style.overflow = '';
        document.head.removeChild(style);
    };
    
    modal.querySelector('.modal-close').addEventListener('click', closeModal);
    modal.querySelector('.modal-backdrop').addEventListener('click', (e) => {
        if (e.target === modal.querySelector('.modal-backdrop')) {
            closeModal();
        }
    });
    
    // Close on escape key
    const handleEscape = (e) => {
        if (e.key === 'Escape') {
            closeModal();
            document.removeEventListener('keydown', handleEscape);
        }
    };
    document.addEventListener('keydown', handleEscape);
}

// Form validation (if needed for future contact forms)
function initializeFormValidation() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            
            const formData = new FormData(form);
            const errors = validateForm(formData);
            
            if (errors.length === 0) {
                submitForm(form, formData);
            } else {
                showFormErrors(errors);
            }
        });
    });
}

function validateForm(formData) {
    const errors = [];
    
    // Email validation
    const email = formData.get('email');
    if (email && !isValidEmail(email)) {
        errors.push('Please enter a valid email address');
    }
    
    // Required fields validation
    const requiredFields = ['name', 'email', 'message'];
    requiredFields.forEach(field => {
        if (!formData.get(field)) {
            errors.push(`${field.charAt(0).toUpperCase() + field.slice(1)} is required`);
        }
    });
    
    return errors;
}

function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

function submitForm(form, formData) {
    // Add loading state
    const submitButton = form.querySelector('button[type="submit"]');
    const originalText = submitButton.textContent;
    submitButton.textContent = 'Sending...';
    submitButton.disabled = true;
    
    // Simulate form submission (replace with actual API call)
    setTimeout(() => {
        showSuccessMessage('Thank you! Your message has been sent successfully.');
        form.reset();
        submitButton.textContent = originalText;
        submitButton.disabled = false;
    }, 2000);
}

function showFormErrors(errors) {
    const errorContainer = document.createElement('div');
    errorContainer.className = 'form-errors';
    errorContainer.innerHTML = `
        <div class="error-message">
            <h4>Please fix the following errors:</h4>
            <ul>
                ${errors.map(error => `<li>${error}</li>`).join('')}
            </ul>
        </div>
    `;
    
    // Insert before form
    const form = document.querySelector('form');
    form.parentNode.insertBefore(errorContainer, form);
    
    // Remove after 5 seconds
    setTimeout(() => {
        if (errorContainer.parentNode) {
            errorContainer.parentNode.removeChild(errorContainer);
        }
    }, 5000);
}

function showSuccessMessage(message) {
    const successContainer = document.createElement('div');
    successContainer.className = 'success-message';
    successContainer.innerHTML = `
        <div class="success-content">
            <i class="fas fa-check-circle"></i>
            <p>${message}</p>
        </div>
    `;
    
    // Add styles
    const style = document.createElement('style');
    style.textContent = `
        .success-message {
            position: fixed;
            top: 20px;
            right: 20px;
            background: var(--primary-color);
            color: white;
            padding: 1rem 2rem;
            border-radius: var(--border-radius);
            box-shadow: var(--shadow-hover);
            z-index: 9999;
            animation: slideInRight 0.3s ease;
        }
        
        .success-content {
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        .success-content i {
            font-size: 1.2rem;
        }
        
        .success-content p {
            margin: 0;
            color: white;
        }
        
        .form-errors {
            background: #f8d7da;
            color: #721c24;
            padding: 1rem;
            border-radius: var(--border-radius);
            margin-bottom: 1rem;
            border: 1px solid #f1aeb5;
        }
        
        .error-message h4 {
            margin: 0 0 0.5rem 0;
            color: #721c24;
        }
        
        .error-message ul {
            margin: 0;
            padding-left: 1.5rem;
        }
    `;
    document.head.appendChild(style);
    
    document.body.appendChild(successContainer);
    
    // Remove after 5 seconds
    setTimeout(() => {
        if (successContainer.parentNode) {
            successContainer.parentNode.removeChild(successContainer);
            document.head.removeChild(style);
        }
    }, 5000);
}

// Initialize all functionality when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeNavigation();
    initializeAnimations();
    initializeImageLazyLoading();
    initializeScrollEffects();
    initializeLanguageSwitcher();
    initializeSmoothScroll();
    initializeImageGallery();
    initializeFormValidation();
});

// Export functions for testing or external use
window.GrainTradeLanding = {
    initializeNavigation,
    initializeAnimations,
    initializeImageLazyLoading,
    initializeScrollEffects,
    initializeLanguageSwitcher,
    openImageModal
};