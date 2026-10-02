/* ============================================
   Nestoria - Frontend Interactions
   ============================================ */

document.addEventListener('DOMContentLoaded', () => {

    // ---------- Mobile Navigation ----------
    const menuToggle = document.getElementById('menuToggle');
    const mainNav = document.getElementById('mainNav');

    if (menuToggle && mainNav) {
        menuToggle.addEventListener('click', () => {
            mainNav.classList.toggle('open');
            const icon = menuToggle.querySelector('i');
            if (mainNav.classList.contains('open')) {
                icon.classList.remove('fa-bars');
                icon.classList.add('fa-xmark');
            } else {
                icon.classList.remove('fa-xmark');
                icon.classList.add('fa-bars');
            }
        });

        // Close on nav link click
        mainNav.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', () => {
                mainNav.classList.remove('open');
                const icon = menuToggle.querySelector('i');
                icon.classList.remove('fa-xmark');
                icon.classList.add('fa-bars');
            });
        });
    }

    // ---------- Nav Active State ----------
    const navLinks = document.querySelectorAll('.main-nav a');
    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            navLinks.forEach(l => l.classList.remove('active'));
            link.classList.add('active');
        });
    });

    // ---------- Favorite Buttons ----------
    document.querySelectorAll('.fav-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            btn.classList.toggle('active');
            const icon = btn.querySelector('i');
            if (btn.classList.contains('active')) {
                icon.classList.remove('fa-regular');
                icon.classList.add('fa-solid');
            } else {
                icon.classList.remove('fa-solid');
                icon.classList.add('fa-regular');
            }
        });
    });

    // ---------- Search Form ----------
    const searchBar = document.getElementById('searchBar');
    if (searchBar) {
        searchBar.addEventListener('submit', (e) => {
            e.preventDefault();
            const btn = searchBar.querySelector('.btn-search');
            const originalHTML = btn.innerHTML;

            btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Searching...';
            btn.disabled = true;

            setTimeout(() => {
                btn.innerHTML = originalHTML;
                btn.disabled = false;
                // Demo: scroll to properties
                const props = document.querySelector('.featured-properties');
                if (props) props.scrollIntoView({ behavior: 'smooth' });
            }, 1200);
        });
    }

    // ---------- Header Scroll Shadow ----------
    const header = document.querySelector('.site-header');
    window.addEventListener('scroll', () => {
        if (window.scrollY > 10) {
            header.style.boxShadow = '0 4px 20px rgba(31, 27, 75, 0.08)';
        } else {
            header.style.boxShadow = '0 1px 0 var(--border)';
        }
    });

    // ---------- Simple Fade-In on Scroll ----------
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.1 });

    document.querySelectorAll('.feature-card, .property-card, .step-card, .testimonial-card').forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(24px)';
        el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(el);
    });

});

    // ---------- Jobs Page: Search Filter ----------
    const jobSearch = document.getElementById('jobSearch');
    const jobsGrid = document.getElementById('jobsGrid');
    const jobsEmpty = document.getElementById('jobsEmpty');

    if (jobSearch && jobsGrid && jobsEmpty) {
        const jobCards = jobsGrid.querySelectorAll('.job-card');

        jobSearch.addEventListener('input', () => {
            const query = jobSearch.value.trim().toLowerCase();
            let visibleCount = 0;

            jobCards.forEach(card => {
                const title = card.dataset.title || '';
                const location = card.dataset.location || '';
                const matches = title.includes(query) || location.includes(query);

                card.style.display = matches ? '' : 'none';
                if (matches) visibleCount++;
            });

            jobsEmpty.hidden = visibleCount > 0;
            jobsGrid.style.display = visibleCount > 0 ? '' : 'none';
        });
    }

        // ---------- Apply Modal Wizard ----------
    const applyModal = document.getElementById('applyModal');
    const applyForm = document.getElementById('applyForm');
    const applyStepsTrack = document.getElementById('applyStepsTrack');
    const applySteps = document.querySelectorAll('.apply-step');
    const applyProgressBar = document.getElementById('applyProgressBar');
    const applyStepLabel = document.getElementById('applyStepLabel');
    const applyStepName = document.getElementById('applyStepName');
    const applyBackBtn = document.getElementById('applyBackBtn');
    const applyNextBtn = document.getElementById('applyNextBtn');
    const applySubmitBtn = document.getElementById('applySubmitBtn');
    const applySuccess = document.getElementById('applySuccess');
    const applyJobTitle = document.getElementById('applyJobTitle');

    const stepNames = [
        'Personal Information',
        'Contact Information',
        'Identification & Verification',
        'Educational Background',
        'Employment History',
        'Professional Information',
        'Salary & Payroll Information',
        'Emergency & Other Information'
    ];

    let currentStep = 0;
    const totalSteps = applySteps.length;

    function showStep(index) {
        applySteps.forEach((step, i) => {
            step.classList.remove('active', 'exit-left');
            if (i === index) {
                step.classList.add('active');
            } else if (i < index) {
                step.classList.add('exit-left');
            }
        });

        // Progress
        const percent = ((index + 1) / totalSteps) * 100;
        applyProgressBar.style.width = percent + '%';
        applyStepLabel.textContent = `Step ${index + 1} of ${totalSteps}`;
        applyStepName.textContent = stepNames[index];

        // Buttons
        applyBackBtn.disabled = index === 0;
        const isLast = index === totalSteps - 1;
        applyNextBtn.hidden = isLast;
        applySubmitBtn.hidden = !isLast;

        // Reset scroll within the step
        applySteps[index].scrollTop = 0;
    }

    function validateCurrentStep() {
        const step = applySteps[currentStep];
        const fields = step.querySelectorAll('input[required], select[required], textarea[required]');
        let valid = true;

        fields.forEach(field => {
            field.classList.remove('invalid');
            if (field.type === 'file') {
                if (!field.files || field.files.length === 0) {
                    field.classList.add('invalid');
                    valid = false;
                }
            } else if (!field.value.trim()) {
                field.classList.add('invalid');
                valid = false;
            }
        });

        if (!valid) {
            // Shake the footer for feedback
            const footer = document.querySelector('.apply-modal-footer');
            footer.classList.add('shake');
            setTimeout(() => footer.classList.remove('shake'), 400);
        }
        return valid;
    }

    // Shake animation injection
    const shakeStyle = document.createElement('style');
    shakeStyle.textContent = `
        @keyframes shake-x {
            0%, 100% { transform: translateX(0); }
            25% { transform: translateX(-6px); }
            75% { transform: translateX(6px); }
        }
        .apply-modal-footer.shake { animation: shake-x 0.35s ease; }
    `;
    document.head.appendChild(shakeStyle);

    // Open modal
    document.querySelectorAll('.job-apply-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const title = btn.dataset.jobTitle || 'this position';
            applyJobTitle.textContent = title;

            currentStep = 0;
            applyForm.reset();
            applySuccess.hidden = true;
            applyForm.style.display = 'flex';
            applySteps.forEach(s => s.classList.remove('invalid'));
            showStep(0);

            applyModal.classList.add('open');
            applyModal.setAttribute('aria-hidden', 'false');
            document.body.classList.add('modal-open');
        });
    });

    // Close modal
    document.querySelectorAll('[data-close-modal]').forEach(el => {
        el.addEventListener('click', () => {
            applyModal.classList.remove('open');
            applyModal.setAttribute('aria-hidden', 'true');
            document.body.classList.remove('modal-open');
        });
    });

    // ESC key to close
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && applyModal.classList.contains('open')) {
            applyModal.classList.remove('open');
            applyModal.setAttribute('aria-hidden', 'true');
            document.body.classList.remove('modal-open');
        }
    });

    // Next / Back
    applyNextBtn.addEventListener('click', () => {
        if (!validateCurrentStep()) return;
        if (currentStep < totalSteps - 1) {
            currentStep++;
            showStep(currentStep);
        }
    });

    applyBackBtn.addEventListener('click', () => {
        if (currentStep > 0) {
            currentStep--;
            showStep(currentStep);
        }
    });

    // Submit
        // ---------- Submit — POST to backend which sends email ----------
    applyForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        if (!validateCurrentStep()) return;

        // Show loading state on button
        const originalHTML = applySubmitBtn.innerHTML;
        applySubmitBtn.disabled = true;
        applySubmitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Submitting...';

        try {
            const formData = new FormData(applyForm);

            // Include which job they're applying for
            formData.append('applied_for', applyJobTitle.textContent.trim());

            const response = await fetch('/jobs/apply', {
                method: 'POST',
                body: formData,
            });

            const result = await response.json();

            if (!response.ok || !result.success) {
                throw new Error(result.message || 'Submission failed.');
            }

            // Success — show the success screen
            applyForm.style.display = 'none';
            applySuccess.hidden = false;

        } catch (err) {
            console.error('Application error:', err);
            alert('Sorry, something went wrong sending your application.\n\n' + err.message);
        } finally {
            applySubmitBtn.disabled = false;
            applySubmitBtn.innerHTML = originalHTML;
        }
    });