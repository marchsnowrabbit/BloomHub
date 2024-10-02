document.addEventListener('DOMContentLoaded', function() {
    let cards = document.querySelectorAll('.card');
    cards.forEach(card => {
        card.addEventListener('mouseover', function() {
            card.style.transform = 'scale(1.1)';
            card.style.transition = 'transform 0.3s';
        });
        card.addEventListener('mouseout', function() {
            card.style.transform = 'scale(1)';
        });
    });
});