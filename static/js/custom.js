// Attendre que le DOM soit chargé
document.addEventListener('DOMContentLoaded', function() {
    // to get current year
    function getYear() {
        var currentDate = new Date();
        var currentYear = currentDate.getFullYear();
        var yearElement = document.querySelector("#displayYear");
        if (yearElement) {
            yearElement.innerHTML = currentYear;
        } else {
            console.error("L'élément avec id='displayYear' n'a pas été trouvé.");
        }
    }
    getYear();

    // Réinitialiser l'opacité de <main> et appliquer l'animation d'entrée
    gsap.set('main', { opacity: 0 }); // S'assurer que l'opacité est à 0 au départ
    gsap.to('main', {
        opacity: 1,
        duration: 0.5,
    });

    // client section owl carousel (si Owl Carousel est utilisé)
    if (typeof jQuery !== 'undefined' && jQuery.fn.owlCarousel) {
        $(".client_owl-carousel").owlCarousel({
            loop: true,
            margin: 0,
            dots: false,
            nav: true,
            navText: [
                '<i class="fa fa-angle-left" aria-hidden="true"></i>',
                '<i class="fa fa-angle-right" aria-hidden="true"></i>'
            ],
            autoplay: true,
            autoplayHoverPause: true,
            responsive: {
                0: {
                    items: 1
                },
                768: {
                    items: 2
                },
                1000: {
                    items: 2
                }
            }
        });
    } else {
        console.warn("Owl Carousel n'est pas chargé ou jQuery est manquant.");
    }

    // Navbar Scroll Effect
    window.addEventListener('scroll', () => {
        const navbar = document.querySelector('.navbar');
        if (navbar) {
            if (window.scrollY > 50) {
                navbar.classList.add('scrolled');
            } else {
                navbar.classList.remove('scrolled');
            }
        }
    });

    // Page Transition on Navigation
    document.querySelectorAll('a.nav-link').forEach(link => {
        link.addEventListener('click', (e) => {
            const href = link.getAttribute('href');
            // Vérifier si le lien est valide et différent de la page actuelle
            if (href && href !== window.location.pathname) {
                e.preventDefault();
                gsap.to('main', {
                    opacity: 0,
                    duration: 0.5,
                    onComplete: () => {
                        window.location.href = href;
                    }
                });
            }
        });
    });

    // Scroll-Triggered Animations for Portfolio Items
    gsap.utils.toArray('.portfolio-item').forEach(item => {
        gsap.from(item, {
            opacity: 0,
            y: 50,
            duration: 1,
            scrollTrigger: {
                trigger: item,
                start: 'top 80%',
                end: 'bottom 20%',
                toggleActions: 'play none none none',
            }
        });
    });

    // Form Input Animation
    document.querySelectorAll('.form-control').forEach(input => {
        input.addEventListener('focus', () => {
            gsap.to(input, { scale: 1.02, duration: 0.3 });
        });
        input.addEventListener('blur', () => {
            gsap.to(input, { scale: 1, duration: 0.3 });
        });
    });

    // Charger l'API Google Maps dynamiquement
    function loadGoogleMapsAPI() {
        return new Promise((resolve, reject) => {
            // Vérifier si l'API est déjà chargée
            if (window.google && window.google.maps) {
                resolve();
                return;
            }

            // Créer un élément script pour charger l'API
            const script = document.createElement('script');
            script.src = 'https://maps.googleapis.com/maps/api/js?key=AIzaSyDt7pzn6sOx-S1EeMGrh8ogaf2JYa5iCm8&loading=async';
            script.async = true;
            script.defer = true;

            // Résoudre la promesse une fois que l'API est chargée
            script.onload = () => resolve();
            script.onerror = () => reject(new Error('Erreur lors du chargement de l\'API Google Maps'));

            // Ajouter le script au DOM
            document.head.appendChild(script);
        });
    }

    // Fonction pour initialiser la carte
    function initMap() {
        const mapElement = document.getElementById("googleMap");
        if (mapElement) {
            const map = new google.maps.Map(mapElement, {
                center: { lat: 48.8566, lng: 2.3522 }, // Coordonnées de Paris, France
                zoom: 18,
            });
        } else {
            console.warn("L'élément avec id='googleMap' n'a pas été trouvé.");
        }
    }

    // Charger l'API Google Maps et initialiser la carte si nécessaire
    loadGoogleMapsAPI()
        .then(() => {
            // L'API est chargée, on peut maintenant initialiser la carte
            initMap();
        })
        .catch((error) => {
            console.error('Erreur lors du chargement de l\'API Google Maps :', error);
        });
});

// Preloader Animation
window.addEventListener('load', () => {
    gsap.to('#preloader', {
        opacity: 0,
        duration: 1,
        onComplete: () => {
            const preloader = document.getElementById('preloader');
            if (preloader) {
                preloader.style.display = 'none';
            }
        }
    });
});

// Solution de secours pour le preloader
setTimeout(() => {
    const preloader = document.getElementById('preloader');
    if (preloader && preloader.style.display !== 'none') {
        gsap.to('#preloader', {
            opacity: 0,
            duration: 1,
            onComplete: () => {
                preloader.style.display = 'none';
            }
        });
    }
}, 5000);