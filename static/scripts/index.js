
function previewImage(event) {
    const image = document.getElementById("imagePreview");
    const file = event.target.files[0];
    const reader = new FileReader();
    reader.onload = function (e) {
        image.src = e.target.result;
        image.style.display = 'block';
    }
    reader.readAsDataURL(file);
}

async function uploadImage() {
    const imageInput = document.getElementById("imageInput");
    const endpoint = document.getElementById("endpoint").value;
    const resultDiv = document.getElementById("result");

    if (!imageInput.files.length) {
        resultDiv.innerHTML = 'Please select an image.';
        return;
    }

    const file = imageInput.files[0];
    const reader = new FileReader();

    reader.onloadend = async function () {
        const base64Image = reader.result.split(',')[1];
        const body = JSON.stringify({
            "img": base64Image
        });

        try {
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: body
            });

            const data = await response.json();

            // Format and display the result from the response
            let resultHtml = '<h3>Response:</h3><pre>';
            for (const key in data) {
                if (data.hasOwnProperty(key)) {
                    resultHtml += `<span class="key">${key}:</span> <span class="value">${data[key]}</span>\n`;
                }
            }
            resultHtml += '</pre>';
            resultDiv.innerHTML = resultHtml;

        } catch (error) {
            resultDiv.innerHTML = 'Error uploading image: ' + error.message;
        }
    }

    reader.readAsDataURL(file)
}