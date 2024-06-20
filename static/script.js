document.addEventListener('DOMContentLoaded', function() {
    var hamburger = document.getElementById('hamburger');
    var navLinks = document.getElementById('nav-links');
    var closebtn = document.getElementById('closebtn');

    hamburger.addEventListener('click', function() {
        if (navLinks.style.width === '250px') {
            navLinks.style.width = '0';
            closebtn.style.display = 'none';
        } else {
            navLinks.style.width = '250px';
            closebtn.style.display = 'block';
        }
    });

    closebtn.addEventListener('click', function() {
        navLinks.style.width = '0';
        closebtn.style.display = 'none';
    });
});
