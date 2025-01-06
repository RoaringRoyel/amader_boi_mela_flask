// Function to remove a meal
function removeMeal(mealId, date) {
    fetch(`/remove_meal/${mealId}/${date}`, {
      method: 'POST',
    })
    .then(response => response.json())
    .then(data => {
      if (data.success) {
        alert('Meal removed successfully!');
        location.reload(); // Refresh the page to update the meal plan
      } else {
        alert('Failed to remove meal.');
      }
    });
  }
  
  // Function to replace a meal
  function replaceMeal(mealId, date) {
    const newRecipeName = prompt('Enter the new recipe name:');
    if (newRecipeName) {
      fetch(`/replace_meal/${mealId}/${date}`, {
        method: 'POST',
        body: JSON.stringify({ newRecipeName: newRecipeName }),
        headers: {
          'Content-Type': 'application/json'
        }
      })
      .then(response => response.json())
      .then(data => {
        if (data.success) {
          alert('Meal replaced successfully!');
          location.reload(); // Refresh the page to update the meal plan
        } else {
          alert('Failed to replace meal.');
        }
      });
    }
  }
  