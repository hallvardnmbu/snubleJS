document.addEventListener("DOMContentLoaded", function() {
  // Now, query for tab links and attach the click event listeners
  document.querySelectorAll('.tab-link').forEach(link => {
    link.addEventListener('click', function (e) {
      e.preventDefault();

      // Get the target item id
      const targetId = this.getAttribute('data-target');
      const parentContainer = this.closest('.item-information-container');

      // Remove 'active' class from all tabs and sections within the same container
      parentContainer.querySelectorAll('.tab-link').forEach(tab => tab.classList.remove('active'));
      parentContainer.querySelectorAll('.content-section').forEach(section => section.classList.remove('active'));

      // Add 'active' class to the clicked tab and corresponding section
      this.classList.add('active');
      parentContainer.querySelector(`#${targetId}`).classList.add('active');
    });
  });
});
