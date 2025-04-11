document.addEventListener('DOMContentLoaded', function() {
    const countrySelect = document.querySelector('#id_country');
    const citySelect = document.querySelector('#id_city');

    const citiesByCountry = {
        'Côte d\'Ivoire': ['Abidjan', 'Yamoussoukro', 'Bouaké'],
        'France': ['Paris', 'Lyon', 'Marseille'],
        'Sénégal': ['Dakar', 'Thiès', 'Saint-Louis'],
        // Add more countries and cities as needed
    };

    countrySelect.addEventListener('change', function() {
        const selectedCountry = this.value;
        citySelect.innerHTML = '<option value="">Sélectionnez une ville</option>';

        if (selectedCountry && citiesByCountry[selectedCountry]) {
            citiesByCountry[selectedCountry].forEach(city => {
                const option = document.createElement('option');
                option.value = city;
                option.textContent = city;
                citySelect.appendChild(option);
            });
        }
    });
});