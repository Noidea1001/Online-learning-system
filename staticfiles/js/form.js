// form
document.addEventListener('DOMContentLoaded', function() {
  
  const fileInputs = document.querySelectorAll("input[type='file']");
  
  fileInputs.forEach(fileInput => {
    fileInput.addEventListener('change', function() {
      if (this.files && this.files[0]) {
        const file = this.files[0];
        const maxSizeBytes = (this.dataset.maxSize || 25) * 1024 * 1024; // យកតាម dataset ឬលំនាំដើម 25MB
        const dropzoneBox = this.closest('.premium-dropzone-box');
        const titleEl = dropzoneBox ? dropzoneBox.querySelector('.dropzone-title') : null;

        if (file.size > maxSizeBytes) {
          this.classList.add('is-invalid');
          if (dropzoneBox) {
            dropzoneBox.style.borderColor = '#dc3545';
            dropzoneBox.style.backgroundColor = '#fff5f5';
          }
          if (titleEl) titleEl.innerHTML = `<span class="text-danger"><i class="bi bi-x-circle-fill me-1"></i> File size over than limit! (Max ${this.dataset.maxSize || 25}MB)</span>`;
        } else {
          this.classList.remove('is-invalid');
          if (dropzoneBox) {
            dropzoneBox.style.borderColor = '#10b981';
            dropzoneBox.style.backgroundColor = '#f0fdf4';
          }
          if (titleEl) titleEl.innerHTML = `<span class="text-success"><i class="bi bi-check-circle-fill me-1"></i>Success!</span><br><small class="text-muted">${file.name}</small>`;
        }
      }
    });
  });

  const forms = document.querySelectorAll('.needs-validation');
  Array.prototype.slice.call(forms).forEach(function(form) {
    form.addEventListener('submit', function(event) {
      if (!form.checkValidity()) {
        event.preventDefault();
        event.stopPropagation();
      }
      form.classList.add('was-validated');
    }, false);
  });
});
