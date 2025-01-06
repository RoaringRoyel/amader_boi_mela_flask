// Function to confirm the deletion of a recipe
document.querySelectorAll('.btn-danger').forEach(button => {
    button.addEventListener('click', function(event) {
        let confirmDelete = confirm('Are you sure you want to delete this recipe?');
        if (!confirmDelete) {
            event.preventDefault();
        }
    });
});
