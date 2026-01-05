document.addEventListener('DOMContentLoaded', function() {
    // Handle formset add more
    document.querySelectorAll('.add-form-row').forEach(button => {
        button.addEventListener('click', function() {
            const formsetContainer = this.previousElementSibling;
            const totalForms = formsetContainer.querySelector('[name$="-TOTAL_FORMS"]');
            const currentFormCount = parseInt(totalForms.value);
            
            // Clone the last form
            const lastForm = formsetContainer.querySelector('.formset-row:last-child');
            const newForm = lastForm.cloneNode(true);
            
            // Update form indices
            newForm.innerHTML = newForm.innerHTML.replace(
                new RegExp(`-${currentFormCount - 1}-`, 'g'),
                `-${currentFormCount}-`
            );
            
            // Clear input values
            newForm.querySelectorAll('input, textarea, select').forEach(input => {
                if (input.type !== 'hidden') input.value = '';
            });
            
            formsetContainer.appendChild(newForm);
            totalForms.value = currentFormCount + 1;
        });
    });
    
    // Handle formset delete
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('delete-form-row')) {
            const formRow = e.target.closest('.formset-row');
            const deleteCheckbox = formRow.querySelector('[name$="-DELETE"]');
            
            if (deleteCheckbox) {
                deleteCheckbox.checked = true;
                formRow.style.display = 'none';
            }
        }
    });
});
