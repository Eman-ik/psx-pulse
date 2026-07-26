/**
 * Triggers interactive actions such as showing a modal or redirecting the user.
 */
function triggerAction() {
    console.log("Button clicked, initializing onboarding workflow...");
    alert("Thank you for your interest! Redirecting to the cohort onboarding flow...");
}

// Add scroll transformation effects if desired
window.addEventListener('scroll', () => {
    const navbar = document.querySelector('.navbar');
    if (window.scrollY > 50) {
        navbar.style.background = 'rgba(4, 9, 20, 0.85)';
        navbar.style.backdropFilter = 'blur(10px)';
    } else {
        navbar.style.background = 'transparent';
        navbar.style.backdropFilter = 'none';
    }
});