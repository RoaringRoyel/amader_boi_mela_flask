$(document).ready(function () {
    $('#search-form').submit(function (event) {
        event.preventDefault();

        const ingredient = $('#ingredient').val();

        $.ajax({
            url: `/api/recipes/search/ingredient`,
            type: 'GET',
            data: { ingredient: ingredient },
            success: function (recipes) {
                displayRecipes(recipes);
            },
            error: function (error) {
                console.error('Error fetching recipes:', error);
            }
        });
    });

    function displayRecipes(recipes) {
        const container = $('#results-container');
        container.empty();

        if (recipes.length === 0) {
            container.append('<p>No recipes found.</p>');
            return;
        }

        recipes.forEach(recipe => {
            const recipeCard = `
                <div class="recipe-card">
                    <h3>${recipe.title}</h3>
                    <p><strong>Prep Time:</strong> ${recipe.prepTime} mins</p>
                    <p><strong>Cook Time:</strong> ${recipe.cookTime} mins</p>
                    <p><strong>Yields:</strong> ${recipe.yields}</p>
                    <p><strong>Ingredients:</strong> ${recipe.ingredients.join(', ')}</p>
                    <button onclick="viewDetails('${recipe.id}')">View Details</button>
                </div>
            `;
            container.append(recipeCard);
        });
    }

    window.viewDetails = function (recipeId) {
        alert(`Details for recipe ID: ${recipeId}`);
    };
});
