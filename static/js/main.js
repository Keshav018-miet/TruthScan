document.addEventListener('DOMContentLoaded', () => {
    const uploadForms = document.querySelectorAll('form[enctype="multipart/form-data"]');
    
    uploadForms.forEach(form => {
        form.addEventListener('submit', function() {
            const btn = this.querySelector('button[type="submit"]');
            if (btn) {
                const originalText = btn.innerHTML;
                btn.innerHTML = 'Processing... <span class="spinner"></span>';
                btn.disabled = true;
                
                // Slight delay to allow UI to update before blocking thread
                setTimeout(() => {
                    this.submit();
                }, 50);
            }
        });
    });

    const fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach(input => {
        input.addEventListener('change', function() {
            const label = this.nextElementSibling;
            if (label && label.classList.contains('file-label')) {
                if (this.files && this.files.length > 1) {
                    label.innerHTML = (this.getAttribute('data-multiple-caption') || '').replace('{count}', this.files.length);
                } else if (this.files && this.files[0]) {
                    label.innerHTML = this.files[0].name;
                }
            }
        });
    });
});
