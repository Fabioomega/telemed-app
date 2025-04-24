document.addEventListener('DOMContentLoaded', function () {
    const uploadBtn = document.getElementById('uploadBtn');
    const imageUpload = document.getElementById('imageUpload');
    const imagePreview = document.getElementById('imagePreview');
    const imageContainer = document.getElementById('imageContainer');
    const resultContainer = document.getElementById('resultContainer');
    const gravityValue = document.getElementById('gravityValue');
    const descriptionContainer = document.getElementById('descriptionContainer');
    const descriptionList = document.getElementById('descriptionList');
    const placeholderText = document.getElementById('placeholderText');

    // Mock AI response for demo purposes
    const mockAiResponse = {
        gravity: "very grave",
        description: ["Hello", "World"]
    };

    uploadBtn.addEventListener('click', function () {
        imageUpload.click();
    });

    imageUpload.addEventListener('change', function () {
        const file = this.files[0];
        if (file) {
            const reader = new FileReader();

            reader.onload = function (e) {
                // Display the image
                imagePreview.src = e.target.result;
                imagePreview.style.display = 'block';
                imageContainer.classList.add('has-image');

                // In a real app, you would send the image to your AI service here
                // For this demo, we'll just show the mock response after a short delay
                setTimeout(showResults, 500);
            };

            reader.readAsDataURL(file);
        }
    });

    function showResults() {
        // Display the mock AI results
        placeholderText.style.display = 'none';
        resultContainer.style.display = 'block';

        // Set gravity value
        gravityValue.textContent = mockAiResponse.gravity;

        // Handle description if available
        if (mockAiResponse.description && mockAiResponse.description.length > 0) {
            descriptionContainer.style.display = 'block';
            descriptionList.innerHTML = '';

            mockAiResponse.description.forEach(item => {
                const listItem = document.createElement('li');
                listItem.className = 'description-item';
                listItem.textContent = item;
                descriptionList.appendChild(listItem);
            });
        } else {
            descriptionContainer.style.display = 'none';
        }
    }

    // For demo purposes, let's add the ability to reset by clicking on the image
    imageContainer.addEventListener('click', function (e) {
        if (e.target === imagePreview && imagePreview.style.display === 'block') {
            imageUpload.value = '';
            imagePreview.style.display = 'none';
            imageContainer.classList.remove('has-image');
            resultContainer.style.display = 'none';
            placeholderText.style.display = 'block';
        }
    });
});