// ecommerce/static/js/product_list.js
document.addEventListener('DOMContentLoaded', function () {
    // Ajouter des écouteurs d'événements pour les clics sur les catégories
    const categoryLinks = document.querySelectorAll('#category-list a');
    categoryLinks.forEach(link => {
        link.addEventListener('click', function (e) {
            e.preventDefault(); // Empêche le rechargement de la page
            const categoryId = this.getAttribute('data-category-id');
            fetchProducts(categoryId);

            // Mettre à jour la classe active
            categoryLinks.forEach(l => l.classList.remove('fw-bold'));
            this.classList.add('fw-bold');
        });
    });

    // Fonction pour récupérer et afficher les produits
    function fetchProducts(categoryId) {
        const url = categoryId === 'all' ? '/api/products/' : `/api/products/?category=${categoryId}`;
        fetch(url)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Erreur HTTP ${response.status}`);
                }
                return response.json();
            })
            .then(products => {
                console.log('Products fetched:', products);
                const productList = document.getElementById('product-list');
                productList.innerHTML = ''; // Vider la liste actuelle
                if (products.length === 0) {
                    productList.innerHTML = '<p class="text-muted">Aucun produit disponible pour le moment.</p>';
                } else {
                    products.forEach(product => {
                        const productDiv = document.createElement('div');
                        productDiv.classList.add('col-md-4', 'mb-4');
                        productDiv.innerHTML = `
                            <div class="card h-100">
                                <img src="${product.image || 'https://via.placeholder.com/150'}" alt="${product.name}" class="card-img-top" style="height: 200px; object-fit: cover;">
                                <div class="card-body">
                                    <h5 class="card-title">${product.name}</h5>
                                    <p class="card-text">${product.description ? product.description.substring(0, 45) + '...' : ''}</p>
                                    <p class="card-text"><strong>${product.price} FCFA</strong></p>
                                    <a href="/ecommerce/product/${product.slug}/" class="btn btn-primary">Voir les détails</a>
                                    <a href="/ecommerce/add-to-cart/${product.id}/" class="btn btn-success mt-2">Ajouter au panier</a>
                                </div>
                            </div>
                        `;
                        productList.appendChild(productDiv);
                    });
                }
            })
            .catch(error => {
                console.error('Erreur lors de la récupération des produits :', error);
                const productList = document.getElementById('product-list');
                productList.innerHTML = '<p class="text-danger">Erreur lors du chargement des produits. Veuillez réessayer plus tard.</p>';
            });
    }

    // Fonction pour rafraîchir les catégories
    function fetchCategories() {
        fetch('/api/categories/?type=product')
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Erreur HTTP ${response.status}`);
                }
                return response.json();
            })
            .then(categories => {
                console.log('Categories fetched:', categories);
                const categoryList = document.getElementById('category-list');
                if (categories.length === 0) {
                    console.warn('Aucune catégorie renvoyée par l’API.');
                    categoryList.innerHTML = '<li class="text-muted">Aucune catégorie disponible.</li>';
                    return;
                }
                categoryList.innerHTML = ''; // Vider la liste actuelle
                // Ajouter "Toutes les catégories"
                const allCategoriesItem = document.createElement('li');
                allCategoriesItem.innerHTML = `<a href="${productListUrl}" class="text-dark" data-category-id="all">Toutes les catégories</a>`;
                categoryList.appendChild(allCategoriesItem);
                // Ajouter les catégories dynamiquement
                categories.forEach(category => {
                    const listItem = document.createElement('li');
                    listItem.innerHTML = `<a href="${productListUrl}?category=${category.id}" class="text-dark" data-category-id="${category.id}">${category.name}</a>`;
                    categoryList.appendChild(listItem);
                });
                // Réappliquer les écouteurs d'événements
                const newCategoryLinks = document.querySelectorAll('#category-list a');
                newCategoryLinks.forEach(link => {
                    link.addEventListener('click', function (e) {
                        e.preventDefault();
                        const categoryId = this.getAttribute('data-category-id');
                        fetchProducts(categoryId);
                        newCategoryLinks.forEach(l => l.classList.remove('fw-bold'));
                        this.classList.add('fw-bold');
                    });
                });
            })
            .catch(error => {
                console.error('Erreur lors de la récupération des catégories :', error);
                const categoryList = document.getElementById('category-list');
                categoryList.innerHTML = '<li class="text-danger">Erreur lors du chargement des catégories. Veuillez réessayer plus tard.</li>';
            });
    }

    // Rafraîchir les catégories toutes les 10 secondes
    setInterval(() => {
        if (navigator.onLine) {
            fetchCategories();
        } else {
            console.warn('Pas de connexion Internet. Le rafraîchissement des catégories est suspendu.');
        }
    }, 10000);

    // Appeler fetchCategories au chargement initial
    fetchCategories();
});