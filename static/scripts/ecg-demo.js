document.addEventListener('DOMContentLoaded', () => {
    const uploadBtn = document.getElementById('uploadBtn');
    const imageUpload = document.getElementById('imageUpload');
    const imagePreview = document.getElementById('imagePreview');
    const imageContainer = document.getElementById('imageContainer');
    const resultContainer = document.getElementById('resultContainer');
    const placeholderText = document.getElementById('placeholderText');
    const gravityValue = document.getElementById('gravityValue');
    const descriptionContainer = document.getElementById('descriptionContainer');
    const descriptionList = document.getElementById('descriptionList');

    uploadBtn.addEventListener('click', () => imageUpload.click());

    imageUpload.addEventListener('change', () => {
        const file = imageUpload.files[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = async (e) => {
            const dataUrl = e.target.result;
            imagePreview.src = dataUrl;
            imagePreview.style.display = 'block';
            imageContainer.classList.add('has-image');
        
            document.getElementById('loadingSpinner').style.display = 'flex';
        
            resultContainer.style.display = 'none';
            descriptionContainer.style.display = 'none';
            gravityValue.textContent = '';
            placeholderText.style.display = 'none';
            try {
                const base64 = dataUrl.split(',')[1];
                const res = await fetch('/ecg-descritores', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ img: base64 })
                });
        
                const json = await res.json();
                renderResults(json);
            } catch (err) {
                console.error(err);
                placeholderText.textContent = 'Erro ao processar a imagem.';
                placeholderText.style.display = 'block';
            } finally {
                document.getElementById('loadingSpinner').style.display = 'none';
            }
        };
        reader.readAsDataURL(file);
    });

    function renderResults(data) {
        placeholderText.style.display = 'none';
        resultContainer.style.display = 'block';

        if (data.gravidade) {
            gravityValue.textContent = data.gravidade;
        } else {
            gravityValue.textContent = 'N/A';
        }

        const details = data.grave_classification || [];
        if (Array.isArray(details) && details.length) {
            descriptionContainer.style.display = 'block';
            descriptionList.innerHTML = '';
            details.forEach(item => {
                const li = document.createElement('li');
                li.className = 'description-item';
                li.textContent = item;
                descriptionList.appendChild(li);
            });
        } else {
            descriptionContainer.style.display = 'none';
        }
    }

    imageContainer.addEventListener('click', e => {
        if (e.target === imagePreview && imagePreview.style.display === 'block') {
            imageUpload.value = '';
            imagePreview.style.display = 'none';
            imageContainer.classList.remove('has-image');
            resultContainer.style.display = 'none';
            placeholderText.style.display = 'block';
        }
    });
});
