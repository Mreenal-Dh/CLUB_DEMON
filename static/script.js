// ===== RIPPLE CANVAS EFFECT =====
(function () {
    // use the existing canvas from the DOM
    const canvas = document.querySelector('.bg-layer .ripple-canvas');
    if (!canvas) {
        console.warn('Ripple canvas not found.');
        return;
    }
    const ctx = canvas.getContext('2d', { alpha: true });

    // HiDPI support
    function resize() {
        const dpr = window.devicePixelRatio || 1;
        canvas.width = Math.max(1, Math.floor(window.innerWidth * dpr));
        canvas.height = Math.max(1, Math.floor(window.innerHeight * dpr));
        canvas.style.width = window.innerWidth + 'px';
        canvas.style.height = window.innerHeight + 'px';
        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    }
    resize();
    window.addEventListener('resize', resize);

    // Simple ripple particle store
    const ripples = [];
    const maxRipples = 12;

    // Throttle pointer events
    let lastAt = 0;
    const throttleMs = 40;

    function spawnRipple(x, y) {
        if (ripples.length >= maxRipples) ripples.shift();
        ripples.push({
            x, y,
            radius: 6,
            maxRadius: 180 + Math.random() * 120,
            alpha: 0.6 + Math.random() * 0.15,
            growth: 0.8 + Math.random() * 0.6,
        });
    }

    function onPointer(e) {
        const now = Date.now();
        if (now - lastAt < throttleMs) return;
        lastAt = now;
        const rect = canvas.getBoundingClientRect();
        const x = (e.clientX !== undefined ? e.clientX : (e.touches && e.touches[0].clientX)) - rect.left;
        const y = (e.clientY !== undefined ? e.clientY : (e.touches && e.touches[0].clientY)) - rect.top;
        spawnRipple(x, y);
    }

    window.addEventListener('pointermove', onPointer, { passive: true });
    window.addEventListener('touchmove', onPointer, { passive: true });

    // Animation loop
    function tick() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        for (let i = ripples.length - 1; i >= 0; i--) {
            const r = ripples[i];
            r.radius += r.growth;
            r.alpha -= 0.006 * (r.growth / 2);

            const grd = ctx.createRadialGradient(r.x, r.y, r.radius * 0.2, r.x, r.y, r.radius);
            grd.addColorStop(0, `rgba(200,230,255,${Math.max(0, r.alpha * 0.08)})`);
            grd.addColorStop(0.5, `rgba(150,190,255,${Math.max(0, r.alpha * 0.04)})`);
            grd.addColorStop(1, `rgba(100,150,255,0)`);

            ctx.beginPath();
            ctx.fillStyle = grd;
            ctx.arc(r.x, r.y, r.radius, 0, Math.PI * 2);
            ctx.fill();
            ctx.closePath();

            if (r.alpha <= 0.01 || r.radius > r.maxRadius) {
                ripples.splice(i, 1);
            }
        }

        requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);

    // Small touch/click burst
    window.addEventListener('pointerdown', (e) => {
        const rect = canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        for (let i = 0; i < 3; i++) spawnRipple(x + (Math.random() * 40 - 20), y + (Math.random() * 40 - 20));
    }, { passive: true });

    // PARALLAX: move .bg-layer background Y based on scroll (smooth)
    const bgLayer = document.querySelector('.bg-layer');
    if (bgLayer) {
        let targetY = 0;
        let currentY = 0;
        const speed = 0.28;        // parallax intensity (0 = no move, 1 = full move)
        const ease = 0.12;         // smoothing (0..1)

        function onScroll() {
            // positive scroll => move background up slightly (negative translate)
            targetY = window.scrollY * speed;
        }
        window.addEventListener('scroll', onScroll, { passive: true });
        onScroll(); // init

        function parallaxTick() {
            // ease toward target
            currentY += (targetY - currentY) * ease;
            // set background-position Y (negative to create depth)
            bgLayer.style.backgroundPosition = `center ${-currentY}px`;
            requestAnimationFrame(parallaxTick);
        }
        requestAnimationFrame(parallaxTick);
    }

    // Cleanup on unload (optional)
    window.addEventListener('beforeunload', () => {
        window.removeEventListener('pointermove', onPointer);
        window.removeEventListener('touchmove', onPointer);
    });
})();

// ===== PROFILE DROPDOWN TOGGLE =====
(function() {
    const profileBtn = document.getElementById('profileBtn');
    const profileMenu = document.getElementById('profileMenu');
    if (!profileBtn || !profileMenu) return;

    profileBtn.addEventListener('click', function (e) {
        e.stopPropagation();
        const open = profileMenu.classList.toggle('open');
        profileBtn.setAttribute('aria-expanded', open ? 'true' : 'false');
        profileMenu.setAttribute('aria-hidden', open ? 'false' : 'true');
    });

    // Close when clicking outside
    document.addEventListener('click', function (e) {
        if (!profileMenu.classList.contains('open')) return;
        if (!profileMenu.contains(e.target) && !profileBtn.contains(e.target)) {
            profileMenu.classList.remove('open');
            profileBtn.setAttribute('aria-expanded', 'false');
            profileMenu.setAttribute('aria-hidden', 'true');
        }
    });

    // Close on Esc
    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') {
            profileMenu.classList.remove('open');
            profileBtn.setAttribute('aria-expanded', 'false');
            profileMenu.setAttribute('aria-hidden', 'true');
        }
    });
})();

// ===== SPARK EFFECT ON CLICK =====
(function() {
    const particles = [];
    const maxParticles = 30;

    const particleCanvas = document.createElement('canvas');
    particleCanvas.className = 'particle-canvas';
    particleCanvas.style.cssText = `
        position: fixed;
        inset: 0;
        z-index: 15;
        pointer-events: none;
    `;
    document.body.appendChild(particleCanvas);

    const pCtx = particleCanvas.getContext('2d', { alpha: true });

    function resizeParticleCanvas() {
        const dpr = window.devicePixelRatio || 1;
        particleCanvas.width = Math.max(1, Math.floor(window.innerWidth * dpr));
        particleCanvas.height = Math.max(1, Math.floor(window.innerHeight * dpr));
        particleCanvas.style.width = window.innerWidth + 'px';
        particleCanvas.style.height = window.innerHeight + 'px';
        pCtx.setTransform(dpr, 0, 0, dpr, 0, 0);
    }
    resizeParticleCanvas();
    window.addEventListener('resize', resizeParticleCanvas);

    function createSpark(x, y, angle) {
        return {
            x: x,
            y: y,
            vx: Math.cos(angle) * 0.6,
            vy: Math.sin(angle) * 0.6,
            life: 1,
            size: 1.5,
            brightness: 200 + Math.random() * 55  // 200-255 shades of white
        };
    }

    window.addEventListener('click', function(e) {
        const sparkCount = 8;
        
        for (let i = 0; i < sparkCount; i++) {
            const angle = (Math.PI * 2 * i) / sparkCount;
            if (particles.length < maxParticles) {
                particles.push(createSpark(e.clientX, e.clientY, angle));
            }
        }
    });

    function animateParticles() {
        pCtx.clearRect(0, 0, particleCanvas.width, particleCanvas.height);

        for (let i = particles.length - 1; i >= 0; i--) {
            const p = particles[i];

            p.x += p.vx;
            p.y += p.vy;
            p.life -= 0.03;

            pCtx.fillStyle = `rgba(${p.brightness}, ${p.brightness}, ${p.brightness}, ${p.life})`;
            pCtx.beginPath();
            pCtx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
            pCtx.fill();

            if (p.life <= 0) {
                particles.splice(i, 1);
            }
        }

        requestAnimationFrame(animateParticles);
    }

    animateParticles();
})();

// ===== LOGIN PAGE ENHANCEMENTS =====
(function() {
    // Only run on login page
    if (!document.querySelector('.login-form')) return;

    const loginForm = document.querySelector('.login-form');
    const submitBtn = document.querySelector('.btn-signin');
    const inputs = document.querySelectorAll('.form-input');

    // Add loading state on submit
    if (loginForm && submitBtn) {
        loginForm.addEventListener('submit', function() {
            submitBtn.classList.add('loading');
            submitBtn.disabled = true;
        });
    }

    // Clear error on input
    inputs.forEach(input => {
        input.addEventListener('input', function() {
            const errorMsg = document.querySelector('.error-message');
            if (errorMsg) {
                errorMsg.style.opacity = '0';
                setTimeout(() => errorMsg.remove(), 300);
            }
        });
    });

    // Keyboard navigation for role selector
    const roleLabels = document.querySelectorAll('.role-label');
    roleLabels.forEach((label, index) => {
        label.setAttribute('tabindex', '0');
        label.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                this.previousElementSibling.checked = true;
            }
        });
    });
})();

// ===== HOME PAGE SPECIFIC FUNCTIONALITY =====
(function() {
    // Only run on home page
    if (!document.querySelector('.hero')) return;

    // ===== SECTION NAVIGATION DOTS =====
    const sections = document.querySelectorAll('.scroll-section');
    const navDots = document.querySelectorAll('.nav-dot');
    const scrollContainer = document.querySelector('.scroll-container');
    
    // Update active dot based on scroll position
    function updateActiveDot() {
        if (window.innerWidth <= 768) return; // Disable on mobile
        
        const scrollPos = scrollContainer ? scrollContainer.scrollTop : window.scrollY;
        const windowHeight = window.innerHeight;
        
        let currentSection = 0;
        sections.forEach((section, index) => {
            const sectionTop = section.offsetTop;
            const sectionHeight = section.offsetHeight;
            
            if (scrollPos >= sectionTop - windowHeight / 3) {
                currentSection = index;
            }
        });
        
        navDots.forEach((dot, index) => {
            if (index === currentSection) {
                dot.classList.add('active');
            } else {
                dot.classList.remove('active');
            }
        });
    }
    
    // Click handler for navigation dots
    navDots.forEach(dot => {
        dot.addEventListener('click', () => {
            const sectionIndex = parseInt(dot.getAttribute('data-section'));
            const targetSection = document.getElementById(`section-${sectionIndex}`);
            
            if (targetSection) {
                if (scrollContainer) {
                    scrollContainer.scrollTo({
                        top: targetSection.offsetTop,
                        behavior: 'smooth'
                    });
                } else {
                    targetSection.scrollIntoView({ behavior: 'smooth' });
                }
            }
        });
    });
    
    // Listen to scroll events
    if (scrollContainer) {
        scrollContainer.addEventListener('scroll', updateActiveDot, { passive: true });
    } else {
        window.addEventListener('scroll', updateActiveDot, { passive: true });
    }
    
    // Initial update
    updateActiveDot();

    // ===== STATS COUNTER ANIMATION =====
    const statNumbers = document.querySelectorAll('.stat-number');
    let statsAnimated = false;
    
    const animateStats = (entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting && !statsAnimated) {
                statsAnimated = true;
                
                statNumbers.forEach(stat => {
                    const target = parseInt(stat.getAttribute('data-target'));
                    const duration = 2000; // 2 seconds
                    const increment = target / (duration / 16); // 60fps
                    let current = 0;
                    
                    const updateCounter = () => {
                        current += increment;
                        if (current < target) {
                            stat.textContent = Math.floor(current) + '+';
                            requestAnimationFrame(updateCounter);
                        } else {
                            stat.textContent = target + '+';
                        }
                    };
                    
                    updateCounter();
                });
            }
        });
    };
    
    const statsObserver = new IntersectionObserver(animateStats, {
        threshold: 0.5
    });
    
    const heroStats = document.querySelector('.hero-stats');
    if (heroStats) {
        statsObserver.observe(heroStats);
    }

    // ===== STAGGER ANIMATION FOR CARDS =====
    const cards = document.querySelectorAll('.square-card');
    
    const animateCards = (entries) => {
        entries.forEach((entry, index) => {
            if (entry.isIntersecting) {
                setTimeout(() => {
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                }, index * 100);
                cardObserver.unobserve(entry.target);
            }
        });
    };
    
    const cardObserver = new IntersectionObserver(animateCards, {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    });
    
    cards.forEach(card => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(30px)';
        card.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        cardObserver.observe(card);
    });

    // ===== FEATURE ITEMS ANIMATION =====
    const featureItems = document.querySelectorAll('.feature-item');
    
    const animateFeatures = (entries) => {
        entries.forEach((entry, index) => {
            if (entry.isIntersecting) {
                const items = Array.from(entry.target.parentElement.children);
                const itemIndex = items.indexOf(entry.target);
                
                setTimeout(() => {
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                }, itemIndex * 100);
                
                featureObserver.unobserve(entry.target);
            }
        });
    };
    
    const featureObserver = new IntersectionObserver(animateFeatures, {
        threshold: 0.2,
        rootMargin: '0px 0px -50px 0px'
    });

    featureItems.forEach(item => {
        item.style.opacity = '0';
        item.style.transform = 'translateY(20px)';
        item.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
        featureObserver.observe(item);
    });

    // ===== PARALLAX EFFECT FOR HERO (DISABLED TO PREVENT OVERLAP) =====
    // Hero parallax disabled - caused overlapping issues with scroll snap
    // Keeping code commented for future reference
    /*
    const hero = document.querySelector('.hero');
    if (hero && window.innerWidth > 768) {
        const parallaxHero = () => {
            const scrolled = scrollContainer ? scrollContainer.scrollTop : window.scrollY;
            const rate = scrolled * 0.3;
            hero.style.transform = `translateY(${rate}px)`;
        };
        
        if (scrollContainer) {
            scrollContainer.addEventListener('scroll', parallaxHero, { passive: true });
        } else {
            window.addEventListener('scroll', parallaxHero, { passive: true });
        }
    }
    */

    // ===== SCROLL INDICATOR HIDE ON SCROLL =====
    const scrollIndicator = document.querySelector('.scroll-indicator');
    if (scrollIndicator) {
        const hideIndicator = () => {
            const scrollPos = scrollContainer ? scrollContainer.scrollTop : window.scrollY;
            if (scrollPos > 100) {
                scrollIndicator.style.opacity = '0';
            } else {
                scrollIndicator.style.opacity = '0.7';
            }
        };
        
        if (scrollContainer) {
            scrollContainer.addEventListener('scroll', hideIndicator, { passive: true });
        } else {
            window.addEventListener('scroll', hideIndicator, { passive: true });
        }
    }

    // ===== RESPONSIVE HANDLING =====
    const handleResize = () => {
        if (window.innerWidth <= 768) {
            // Disable scroll snapping on mobile
            if (scrollContainer) {
                scrollContainer.style.scrollSnapType = 'none';
            }
            // Hide nav dots on mobile
            const sectionNav = document.querySelector('.section-nav');
            if (sectionNav) {
                sectionNav.style.display = 'none';
            }
        } else {
            if (scrollContainer) {
                scrollContainer.style.scrollSnapType = 'y mandatory';
            }
            const sectionNav = document.querySelector('.section-nav');
            if (sectionNav) {
                sectionNav.style.display = 'flex';
            }
        }
    };
    
    window.addEventListener('resize', handleResize);
    handleResize(); // Initial call
})();