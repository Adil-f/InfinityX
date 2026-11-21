// DOM Elements
const navbar = document.querySelector('.navbar');
const navMenu = document.querySelector('.nav-menu');
const hamburger = document.querySelector('.hamburger');
const navLinks = document.querySelectorAll('.nav-link');
const portfolioFilters = document.querySelectorAll('.filter-btn');
const portfolioItems = document.querySelectorAll('.portfolio-item');
const contactForm = document.getElementById('contactForm');
const modal = document.getElementById('projectModal');
const modalClose = document.querySelector('.modal-close');
const portfolioLinks = document.querySelectorAll('.portfolio-link');
const testimonialSlides = document.querySelectorAll('.testimonial-slide');
const testimonialDots = document.querySelectorAll('.dot');
const faqItems = document.querySelectorAll('.faq-item');
const faqQuestions = document.querySelectorAll('.faq-question');
const statsNumbers = document.querySelectorAll('.stat-number');
const floatingElements = document.querySelectorAll('.floating-element');
const carouselSlides = document.querySelectorAll('.carousel-slide');
const heroTitle = document.querySelector('.hero-title');
const heroName = document.querySelector('.hero-name');

// Loading Screen completamente rimosso

// Interactive Hero Title
if (heroTitle) {
    // Add click sound effect
    heroTitle.addEventListener('click', () => {
        playSound('click');
        
        // Add ripple effect
        createRipple(heroTitle, event);
        
        // Add temporary glow effect
        heroTitle.style.filter = 'brightness(1.6) drop-shadow(0 0 30px rgba(255, 255, 255, 0.8))';
        setTimeout(() => {
            heroTitle.style.filter = 'brightness(1.2)';
        }, 300);
        
        // Add bounce animation
        heroTitle.style.animation = 'none';
        heroTitle.offsetHeight; // Trigger reflow
        heroTitle.style.animation = 'bounce 0.6s ease';
        
        // Reset animation after completion
        setTimeout(() => {
            heroTitle.style.animation = 'titleSlideIn 1.5s cubic-bezier(0.4, 0, 0.2, 1) 0.4s both';
        }, 600);
    });
    
    // Add hover sound effect
    heroTitle.addEventListener('mouseenter', () => {
        playSound('hover');
    });
    
    // Add keyboard support
    heroTitle.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            heroTitle.click();
        }
    });
    
    // Make title focusable
    heroTitle.setAttribute('tabindex', '0');
    heroTitle.setAttribute('role', 'button');
    heroTitle.setAttribute('aria-label', 'Interactive InfinityX title - click for special effects');
}

// Interactive Hero Name
if (heroName) {
    // Add click sound effect
    heroName.addEventListener('click', () => {
        playSound('click');
        
        // Add ripple effect
        createRipple(heroName, event);
        
        // Add temporary glow effect
        heroName.style.filter = 'brightness(1.6) drop-shadow(0 0 30px rgba(255, 255, 255, 0.8))';
        setTimeout(() => {
            heroName.style.filter = 'brightness(1.2)';
        }, 300);
        
        // Add bounce animation
        heroName.style.animation = 'none';
        heroName.offsetHeight; // Trigger reflow
        heroName.style.animation = 'bounce 0.6s ease';
        
        // Reset animation after completion
        setTimeout(() => {
            heroName.style.animation = 'nameSlideIn 1.5s cubic-bezier(0.4, 0, 0.2, 1) 0.6s both';
        }, 600);
    });
    
    // Add hover sound effect
    heroName.addEventListener('mouseenter', () => {
        playSound('hover');
    });
    
    // Add keyboard support
    heroName.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            heroName.click();
        }
    });
    
    // Make name focusable
    heroName.setAttribute('tabindex', '0');
    heroName.setAttribute('role', 'button');
    heroName.setAttribute('aria-label', 'Interactive ADIL FAYYAZ name - click for special effects');
}

// Navigation
hamburger.addEventListener('click', () => {
    hamburger.classList.toggle('active');
    navMenu.classList.toggle('active');
    
    // Update ARIA attributes
    const isExpanded = hamburger.classList.contains('active');
    hamburger.setAttribute('aria-expanded', isExpanded);
});

// Close mobile menu when clicking on a link
navLinks.forEach(link => {
    link.addEventListener('click', () => {
        hamburger.classList.remove('active');
        navMenu.classList.remove('active');
        hamburger.setAttribute('aria-expanded', 'false');
    });
});

// Smooth scrolling for navigation links
navLinks.forEach(link => {
    link.addEventListener('click', (e) => {
        e.preventDefault();
        const targetId = link.getAttribute('href');
        const targetSection = document.querySelector(targetId);
        
        if (targetSection) {
            targetSection.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// Active navigation link on scroll
window.addEventListener('scroll', () => {
    const sections = document.querySelectorAll('section[id]');
    const scrollPos = window.scrollY + 100;

    sections.forEach(section => {
        const sectionTop = section.offsetTop;
        const sectionHeight = section.offsetHeight;
        const sectionId = section.getAttribute('id');
        const navLink = document.querySelector(`.nav-link[href="#${sectionId}"]`);

        if (scrollPos >= sectionTop && scrollPos < sectionTop + sectionHeight) {
            navLinks.forEach(link => link.classList.remove('active'));
            if (navLink) navLink.classList.add('active');
        }
    });
});

// Navbar background on scroll
window.addEventListener('scroll', () => {
    if (window.scrollY > 100) {
        navbar.style.background = 'rgba(0, 0, 0, 0.98)';
        navbar.style.boxShadow = '0 2px 20px rgba(0, 0, 0, 0.3)';
    } else {
        navbar.style.background = 'rgba(0, 0, 0, 0.95)';
        navbar.style.boxShadow = 'none';
    }
});

// Portfolio Filtering
portfolioFilters.forEach(filter => {
    filter.addEventListener('click', () => {
        // Remove active class from all filters
        portfolioFilters.forEach(f => {
            f.classList.remove('active');
            f.setAttribute('aria-selected', 'false');
        });
        // Add active class to clicked filter
        filter.classList.add('active');
        filter.setAttribute('aria-selected', 'true');
        
        const filterValue = filter.getAttribute('data-filter');
        
        portfolioItems.forEach(item => {
            const category = item.getAttribute('data-category');
            
            if (filterValue === 'all' || category === filterValue) {
                item.style.display = 'block';
                item.style.animation = 'fadeInUp 0.6s ease-out';
            } else {
                item.style.display = 'none';
            }
        });
    });
    
    // Add keyboard support
    filter.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            filter.click();
        }
    });
});

// Contact Form Validation and Submission
contactForm.addEventListener('submit', (e) => {
    e.preventDefault();
    
    const name = document.getElementById('name').value;
    const email = document.getElementById('email').value;
    const subject = document.getElementById('subject').value;
    const message = document.getElementById('message').value;
    
    // Basic validation
    if (!name || !email || !subject || !message) {
        showNotification('Please fill in all fields', 'error');
        return;
    }
    
    if (!isValidEmail(email)) {
        showNotification('Please enter a valid email address', 'error');
        return;
    }
    
    // Simulate form submission
    showNotification('Message sent successfully!', 'success');
    contactForm.reset();
});

// Email validation function
function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

// Notification system
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <i class="fas fa-${type === 'success' ? 'check-circle' : type === 'error' ? 'exclamation-circle' : 'info-circle'}"></i>
            <span>${message}</span>
        </div>
    `;
    
    // Add styles
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${type === 'success' ? 'var(--gradient-success)' : type === 'error' ? 'var(--gradient-error)' : 'var(--gradient-primary)'};
        color: white;
        padding: 1rem 1.5rem;
        border-radius: 10px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
        z-index: 10000;
        transform: translateX(100%);
        transition: transform 0.3s ease;
        max-width: 300px;
    `;
    
    document.body.appendChild(notification);
    
    // Animate in
    setTimeout(() => {
        notification.style.transform = 'translateX(0)';
    }, 100);
    
    // Remove after 5 seconds
    setTimeout(() => {
        notification.style.transform = 'translateX(100%)';
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, 5000);
}

// Enhanced Stats Counter Animation
function animateStats() {
    statsNumbers.forEach((stat, index) => {
        const target = parseInt(stat.getAttribute('data-target'));
        const duration = 2000;
        const increment = target / (duration / 16);
        let current = 0;
        
        // Add staggered animation delay
        setTimeout(() => {
            const timer = setInterval(() => {
                current += increment;
                if (current >= target) {
                    current = target;
                    clearInterval(timer);
                    // Add completion effect
                    stat.style.transform = 'scale(1.1)';
                    setTimeout(() => {
                        stat.style.transform = 'scale(1)';
                    }, 200);
                }
                stat.textContent = Math.floor(current);
            }, 16);
        }, index * 200); // Stagger each stat by 200ms
    });
}

// Intersection Observer for animations
const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('fade-in-up');
            
            // Trigger stats animation when about section is visible
            if (entry.target.id === 'about') {
                animateStats();
            }
        }
    });
}, observerOptions);

// Observe all sections
document.querySelectorAll('section').forEach(section => {
    observer.observe(section);
});

// Modern Floating Elements Animation
function animateFloatingElements() {
    floatingElements.forEach((element, index) => {
        const speed = parseFloat(element.getAttribute('data-speed')) || 1;
        const time = Date.now() * 0.001 * speed;
        const x = Math.sin(time + index) * 40;
        const y = Math.cos(time * 0.8 + index) * 35;
        const rotation = Math.sin(time * 0.6) * 20;
        const scale = 1 + Math.sin(time * 0.4) * 0.2;
        
        element.style.transform = `translate(${x}px, ${y}px) rotate(${rotation}deg) scale(${scale})`;
        
        // Enhanced dynamic glow effect
        const glowIntensity = Math.abs(Math.sin(time)) * 0.7 + 0.5;
        const glowSize = 25 + glowIntensity * 40;
        element.style.boxShadow = `0 0 ${glowSize}px rgba(255, 255, 255, ${glowIntensity})`;
        
        // Add subtle brightness variation
        const brightness = 1 + Math.sin(time * 0.5) * 0.3;
        element.style.filter = `brightness(${brightness})`;
        
        // Add subtle border animation
        const borderOpacity = Math.abs(Math.sin(time * 0.3)) * 0.5 + 0.3;
        element.style.borderColor = `rgba(255, 255, 255, ${borderOpacity})`;
    });
    requestAnimationFrame(animateFloatingElements);
}

animateFloatingElements();

// Enhanced Hero Carousel
let currentSlide = 0;
function nextSlide() {
    // Add exit animation
    const currentSlideElement = carouselSlides[currentSlide];
    currentSlideElement.style.transform = 'scale(0.8) rotateY(-90deg)';
    currentSlideElement.style.opacity = '0';
    
    setTimeout(() => {
        currentSlideElement.classList.remove('active');
        currentSlide = (currentSlide + 1) % carouselSlides.length;
        
        // Add entrance animation
        const nextSlideElement = carouselSlides[currentSlide];
        nextSlideElement.classList.add('active');
        nextSlideElement.style.transform = 'scale(0.8) rotateY(90deg)';
        nextSlideElement.style.opacity = '0';
        
        setTimeout(() => {
            nextSlideElement.style.transform = 'scale(1) rotateY(0deg)';
            nextSlideElement.style.opacity = '1';
        }, 50);
    }, 300);
}

setInterval(nextSlide, 4000);

// Testimonials Slider
let currentTestimonial = 0;
function nextTestimonial() {
    testimonialSlides[currentTestimonial].classList.remove('active');
    testimonialDots[currentTestimonial].classList.remove('active');
    testimonialDots[currentTestimonial].setAttribute('aria-selected', 'false');
    
    currentTestimonial = (currentTestimonial + 1) % testimonialSlides.length;
    
    testimonialSlides[currentTestimonial].classList.add('active');
    testimonialDots[currentTestimonial].classList.add('active');
    testimonialDots[currentTestimonial].setAttribute('aria-selected', 'true');
}

setInterval(nextTestimonial, 5000);

// Testimonial dots click
testimonialDots.forEach((dot, index) => {
    dot.addEventListener('click', () => {
        testimonialSlides[currentTestimonial].classList.remove('active');
        testimonialDots[currentTestimonial].classList.remove('active');
        testimonialDots[currentTestimonial].setAttribute('aria-selected', 'false');
        
        currentTestimonial = index;
        
        testimonialSlides[currentTestimonial].classList.add('active');
        testimonialDots[currentTestimonial].classList.add('active');
        testimonialDots[currentTestimonial].setAttribute('aria-selected', 'true');
    });
    
    // Add keyboard support
    dot.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            dot.click();
        }
    });
});

// FAQ Accordion
faqQuestions.forEach(question => {
    question.addEventListener('click', () => {
        const faqItem = question.parentElement;
        const isActive = faqItem.classList.contains('active');
        const answer = faqItem.querySelector('.faq-answer');
        
        // Close all FAQ items
        faqItems.forEach(item => {
            item.classList.remove('active');
            const itemQuestion = item.querySelector('.faq-question');
            const itemAnswer = item.querySelector('.faq-answer');
            itemQuestion.setAttribute('aria-expanded', 'false');
            itemAnswer.style.display = 'none';
        });
        
        // Open clicked item if it wasn't active
        if (!isActive) {
            faqItem.classList.add('active');
            question.setAttribute('aria-expanded', 'true');
            answer.style.display = 'block';
        }
    });
    
    // Add keyboard support
    question.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            question.click();
        }
    });
});

// Project Modal
portfolioLinks.forEach(link => {
    link.addEventListener('click', (e) => {
        e.preventDefault();
        const modalId = link.getAttribute('data-modal');
        
        // Show modal
        modal.style.display = 'flex';
        modal.setAttribute('aria-hidden', 'false');
        
        // Set modal content based on project
        const modalTitle = modal.querySelector('.modal-title');
        const modalDescription = modal.querySelector('.modal-description');
        const modalImage = modal.querySelector('.modal-image img');
        const clientName = modal.querySelector('.client-name');
        const categoryName = modal.querySelector('.category-name');
        const technologies = modal.querySelector('.technologies');
        const duration = modal.querySelector('.duration');
        
        // Project data (you can expand this)
        const projectData = {
            project1: {
                title: 'E-Commerce Platform',
                description: 'A modern e-commerce platform built with React and Node.js, featuring advanced product management, secure payment processing, and responsive design.',
                image: 'https://via.placeholder.com/800x400/333333/ffffff?text=E-Commerce+Platform',
                client: 'TechCorp',
                category: 'Web Development',
                tech: 'React, Node.js, MongoDB',
                duration: '3 months'
            },
            project2: {
                title: 'Fitness App',
                description: 'A comprehensive fitness tracking application with workout plans, progress monitoring, and social features.',
                image: 'https://via.placeholder.com/800x400/666666/ffffff?text=Fitness+App',
                client: 'FitLife',
                category: 'Mobile Development',
                tech: 'React Native, Firebase',
                duration: '4 months'
            },
            project3: {
                title: 'Brand Identity',
                description: 'Complete brand redesign including logo, color palette, typography, and marketing materials.',
                image: 'https://via.placeholder.com/800x400/999999/ffffff?text=Brand+Identity',
                client: 'StartupXYZ',
                category: 'UI/UX Design',
                tech: 'Figma, Adobe Creative Suite',
                duration: '2 months'
            },
            project4: {
                title: 'Dashboard System',
                description: 'Analytics dashboard with real-time data visualization, reporting tools, and customizable widgets.',
                image: 'https://via.placeholder.com/800x400/cccccc/333333?text=Dashboard+System',
                client: 'DataCorp',
                category: 'Web Development',
                tech: 'Vue.js, D3.js, Python',
                duration: '5 months'
            },
            project5: {
                title: 'Social App',
                description: 'Community building platform with user profiles, messaging, and content sharing features.',
                image: 'https://via.placeholder.com/800x400/eeeeee/333333?text=Social+App',
                client: 'ConnectHub',
                category: 'Mobile Development',
                tech: 'Flutter, Firebase, AWS',
                duration: '6 months'
            },
            project6: {
                title: 'AI Assistant',
                description: 'Intelligent chatbot solution with natural language processing and machine learning capabilities.',
                image: 'https://via.placeholder.com/800x400/ffffff/333333?text=AI+Assistant',
                client: 'AI Solutions',
                category: 'AI & Machine Learning',
                tech: 'Python, TensorFlow, NLP',
                duration: '4 months'
            }
        };
        
        const data = projectData[modalId];
        if (data) {
            modalTitle.textContent = data.title;
            modalDescription.textContent = data.description;
            modalImage.src = data.image;
            modalImage.alt = data.title;
            clientName.textContent = data.client;
            categoryName.textContent = data.category;
            technologies.textContent = data.tech;
            duration.textContent = data.duration;
        }
        
        modal.classList.add('show');
        modal.setAttribute('aria-hidden', 'false');
        document.body.style.overflow = 'hidden';
    });
});

// Close modal
modalClose.addEventListener('click', () => {
    modal.classList.remove('show');
    modal.setAttribute('aria-hidden', 'true');
    document.body.style.overflow = 'auto';
});

// Close modal when clicking outside
modal.addEventListener('click', (e) => {
    if (e.target === modal) {
        modal.classList.remove('show');
        modal.setAttribute('aria-hidden', 'true');
        document.body.style.overflow = 'auto';
    }
});

// Keyboard navigation
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && modal.classList.contains('show')) {
        modal.classList.remove('show');
        modal.setAttribute('aria-hidden', 'true');
        document.body.style.overflow = 'auto';
    }
});

// Enhanced Scroll Progress Indicator
function updateScrollProgress() {
    const scrollTop = window.pageYOffset;
    const docHeight = document.body.offsetHeight - window.innerHeight;
    const scrollPercent = (scrollTop / docHeight) * 100;
    
    // Create progress bar if it doesn't exist
    let progressBar = document.querySelector('.scroll-progress');
    if (!progressBar) {
        progressBar = document.createElement('div');
        progressBar.className = 'scroll-progress';
        progressBar.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 0%;
            height: 4px;
            background: linear-gradient(90deg, #000000, #333333, #666666);
            z-index: 10000;
            transition: width 0.1s ease;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.3);
        `;
        document.body.appendChild(progressBar);
    }
    
    progressBar.style.width = scrollPercent + '%';
    
    // Add glow effect based on scroll position
    const glowIntensity = Math.min(scrollPercent / 50, 1);
    progressBar.style.boxShadow = `0 0 ${10 + glowIntensity * 20}px rgba(0, 0, 0, ${0.3 + glowIntensity * 0.4})`;
}

window.addEventListener('scroll', updateScrollProgress);

// Ripple Effect for Buttons
function createRipple(event) {
    const button = event.currentTarget;
    const ripple = document.createElement('span');
    const rect = button.getBoundingClientRect();
    const size = Math.max(rect.width, rect.height);
    const x = event.clientX - rect.left - size / 2;
    const y = event.clientY - rect.top - size / 2;
    
    ripple.style.cssText = `
        position: absolute;
        width: ${size}px;
        height: ${size}px;
        left: ${x}px;
        top: ${y}px;
        background: rgba(255, 255, 255, 0.3);
        border-radius: 50%;
        transform: scale(0);
        animation: ripple 0.6s linear;
        pointer-events: none;
    `;
    
    button.style.position = 'relative';
    button.style.overflow = 'hidden';
    button.appendChild(ripple);
    
    setTimeout(() => {
        ripple.remove();
    }, 600);
}

// Add ripple effect to all buttons
document.querySelectorAll('.btn').forEach(button => {
    button.addEventListener('click', createRipple);
});

// Add ripple animation
const style = document.createElement('style');
style.textContent = `
    @keyframes ripple {
        to {
            transform: scale(4);
            opacity: 0;
        }
    }
`;
document.head.appendChild(style);

// Lazy Loading for Images
const imageObserver = new IntersectionObserver((entries, observer) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            const img = entry.target;
            img.src = img.dataset.src;
            img.classList.remove('lazy');
            observer.unobserve(img);
        }
    });
});

document.querySelectorAll('img[data-src]').forEach(img => {
    imageObserver.observe(img);
});

// Sound Effects (optional)
function playSound(type) {
    // Create audio context for sound effects
    const audioContext = new (window.AudioContext || window.webkitAudioContext)();
    const oscillator = audioContext.createOscillator();
    const gainNode = audioContext.createGain();
    
    oscillator.connect(gainNode);
    gainNode.connect(audioContext.destination);
    
    oscillator.frequency.setValueAtTime(type === 'click' ? 800 : 600, audioContext.currentTime);
    gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
    gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.1);
    
    oscillator.start(audioContext.currentTime);
    oscillator.stop(audioContext.currentTime + 0.1);
}

// Add sound effects to interactive elements
document.querySelectorAll('.btn, .nav-link, .filter-btn').forEach(element => {
    element.addEventListener('click', () => playSound('click'));
});

// Parallax Effect for Hero Section
window.addEventListener('scroll', () => {
    const scrolled = window.pageYOffset;
    const hero = document.querySelector('.hero');
    const heroContent = document.querySelector('.hero-content');
    
    if (hero && heroContent) {
        const rate = scrolled * -0.5;
        heroContent.style.transform = `translateY(${rate}px)`;
    }
});

// Typing Effect for Hero Title
function typeWriter(element, text, speed = 100) {
    let i = 0;
    element.innerHTML = '';
    
    function type() {
        if (i < text.length) {
            element.innerHTML += text.charAt(i);
            i++;
            setTimeout(type, speed);
        }
    }
    
    type();
}

// Initialize typing effect when page loads
window.addEventListener('load', () => {
    const heroTitle = document.querySelector('.hero-title');
    if (heroTitle) {
        const originalText = heroTitle.textContent;
        setTimeout(() => {
            typeWriter(heroTitle, originalText, 50);
        }, 1000);
    }
});

// Smooth reveal animations for sections
const revealElements = document.querySelectorAll('.service-card, .team-member, .portfolio-item, .pricing-card');

const revealObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.style.opacity = '1';
            entry.target.style.transform = 'translateY(0)';
        }
    });
}, {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
});

revealElements.forEach(element => {
    element.style.opacity = '0';
    element.style.transform = 'translateY(30px)';
    element.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
    revealObserver.observe(element);
});

// Enhanced mobile menu
let isMenuOpen = false;

hamburger.addEventListener('click', () => {
    isMenuOpen = !isMenuOpen;
    
    if (isMenuOpen) {
        hamburger.classList.add('active');
        navMenu.classList.add('active');
        document.body.style.overflow = 'hidden';
    } else {
        hamburger.classList.remove('active');
        navMenu.classList.remove('active');
        document.body.style.overflow = 'auto';
    }
});

// Close menu when clicking outside
document.addEventListener('click', (e) => {
    if (isMenuOpen && !hamburger.contains(e.target) && !navMenu.contains(e.target)) {
        isMenuOpen = false;
        hamburger.classList.remove('active');
        navMenu.classList.remove('active');
        document.body.style.overflow = 'auto';
    }
});

// Newsletter form submission
document.querySelector('.newsletter-form').addEventListener('submit', (e) => {
    e.preventDefault();
    const email = e.target.querySelector('input[type="email"]').value;
    
    if (isValidEmail(email)) {
        showNotification('Successfully subscribed to newsletter!', 'success');
        e.target.reset();
    } else {
        showNotification('Please enter a valid email address', 'error');
    }
});

// Enhanced scroll animations
const scrollAnimations = {
    fadeIn: (element) => {
        element.style.opacity = '0';
        element.style.transform = 'translateY(30px)';
        
        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                    entry.target.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
                }
            });
        });
        
        observer.observe(element);
    }
};

// Apply scroll animations to elements
document.querySelectorAll('.service-card, .team-member, .portfolio-item, .pricing-card, .timeline-item').forEach(element => {
    scrollAnimations.fadeIn(element);
});

// Performance optimization
let ticking = false;

function updateOnScroll() {
    if (!ticking) {
        requestAnimationFrame(() => {
            // Update scroll-based animations here
            ticking = false;
        });
        ticking = true;
    }
}

window.addEventListener('scroll', updateOnScroll);

// Initialize all animations and interactions
document.addEventListener('DOMContentLoaded', () => {
    // Add loading animation to all sections
    document.querySelectorAll('section').forEach(section => {
        section.style.opacity = '0';
        section.style.transform = 'translateY(30px)';
        
        const sectionObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                    entry.target.style.transition = 'opacity 0.8s ease, transform 0.8s ease';
                }
            });
        });
        
        sectionObserver.observe(section);
    });
    
    // Initialize tooltips (if needed)
    document.querySelectorAll('[data-tooltip]').forEach(element => {
        element.addEventListener('mouseenter', (e) => {
            const tooltip = document.createElement('div');
            tooltip.className = 'tooltip';
            tooltip.textContent = e.target.dataset.tooltip;
            tooltip.style.cssText = `
                position: absolute;
                background: var(--bg-dark);
                color: white;
                padding: 0.5rem 1rem;
                border-radius: 5px;
                font-size: 0.9rem;
                z-index: 1000;
                pointer-events: none;
                white-space: nowrap;
            `;
            
            document.body.appendChild(tooltip);
            
            const rect = e.target.getBoundingClientRect();
            tooltip.style.left = rect.left + rect.width / 2 - tooltip.offsetWidth / 2 + 'px';
            tooltip.style.top = rect.top - tooltip.offsetHeight - 10 + 'px';
        });
        
        element.addEventListener('mouseleave', () => {
            const tooltip = document.querySelector('.tooltip');
            if (tooltip) tooltip.remove();
        });
    });
}); 