document.addEventListener('DOMContentLoaded', function () {
    const productList = document.getElementById('product-list');
    const categoryLinks = document.querySelectorAll('.list-group-item a');

    // Function to fetch categories
    async function fetchCategories() {
        try {
            const response = await fetch('/api/categories/?type=product');  // Filter by product type
            if (!response.ok) {
                throw new Error(`Failed to fetch categories: ${response.status} ${response.statusText}`);
            }
            const categories = await response.json();
            console.log('Categories fetched:', categories);
            return categories;
        } catch (error) {
            console.error('Error fetching categories:', error);
            return [];
        }
    }

    // Function to fetch products
    async function fetchProducts(categoryId = null) {
        try {
            const url = categoryId ? `/api/products/?category=${categoryId}` : '/api/products/';
            const response = await fetch(url);
            if (!response.ok) {
                throw new Error(`Failed to fetch products: ${response.status} ${response.statusText}`);
            }
            const products = await response.json();
            console.log('Products fetched:', products);
            return products;
        } catch (error) {
            console.error('Error fetching products:', error);
            return [];
        }
    }

    // Function to render products
    function renderProducts(products) {
        if (!productList) {
            console.error('Product list element not found');
            return;
        }
        productList.innerHTML = ''; // Clear existing products
        if (products.length === 0) {
            console.log('No products to render');
            productList.innerHTML = '<p>Aucun produit disponible.</p>';
            return;
        }

        products.forEach(product => {
            const imageUrl = product.primary_image && product.primary_image.image 
                ? product.primary_image.image 
                : '/static/images/placeholder.jpg';
            console.log(`Rendering product: ${product.name}, Category: ${product.category}, Image URL: ${imageUrl}`);

            const productCard = `
                <div class="col-md-4 mb-4">
                    <div class="card">
                        <img src="${imageUrl}" class="card-img-top" alt="${product.name}" style="height: 200px; object-fit: cover;" loading="lazy" onerror="this.src='/static/images/placeholder.jpg'">
                        <div class="card-body">
                            <h5 class="card-title">${product.name}</h5>
                            <p class="card-text">${parseFloat(product.price).toFixed(2)} FCFA</p>
                            <a href="/ecommerce/product/${product.slug}/" class="btn btn-primary">Voir les détails</a>
                            <a href="/ecommerce/add-to-cart/${product.id}/" class="btn btn-success">Ajouter au panier</a>
                            <a href="/users/favorites/?product_id=${product.id}&action=add" class="btn btn-outline-danger"><i class="fas fa-heart"></i></a>
                        </div>
                    </div>
                </div>
            `;
            productList.insertAdjacentHTML('beforeend', productCard);
        });
    }

    // Function to handle category filter clicks
    categoryLinks.forEach(link => {
        link.addEventListener('click', async function (e) {
            e.preventDefault();
            const url = new URL(this.href);
            const categoryId = url.searchParams.get('category');
            console.log(`Fetching products for category ID: ${categoryId}`);
            const products = await fetchProducts(categoryId);
            renderProducts(products);
        });
    });

    // Initial load of products
    (async function () {
        const urlParams = new URLSearchParams(window.location.search);
        const categoryId = urlParams.get('category');
        console.log(`Initial load, category ID: ${categoryId || 'none'}`);
        const products = await fetchProducts(categoryId);
        renderProducts(products);
    })();

    // Periodically refresh categories (every 30 seconds)
    setInterval(async () => {
        if (!navigator.onLine) {
            console.log('Pas de connexion Internet. Le rafraîchissement des catégories est suspendu.');
            return;
        }
        const categories = await fetchCategories();
        console.log('Periodic category refresh:', categories);
    }, 30000);
});