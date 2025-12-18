document.addEventListener('DOMContentLoaded', () => {
    const uploadBtn = document.getElementById('uploadBtn');
    const jsonBtn = document.getElementById('jsonBtn');
    const analyzeBtn = document.getElementById('analyzeBtn');
    const imageUpload = document.getElementById('imageUpload');
    const jsonUpload = document.getElementById('jsonUpload');
    const imagePreview = document.getElementById('imagePreview');
    const imageContainer = document.getElementById('imageContainer');
    const resultContainer = document.getElementById('resultContainer');
    const placeholderText = document.getElementById('placeholderText');
    const gravityValue = document.getElementById('gravityValue');
    const patientForm = document.getElementById('patientForm');

    uploadBtn.addEventListener('click', () => imageUpload.click());
    jsonBtn.addEventListener('click', () => jsonUpload.click());

    analyzeBtn.addEventListener('click', async () => {
        if (imagePreview.src && imagePreview.style.display === 'block') {
            await processImage(imagePreview.src);
        }
    });

    function setFormData(data) {
        Object.keys(data).forEach(key => {
            const input = patientForm.querySelector(`[name="${key}"]`);
            if (input) {
                if (input.type === 'checkbox') {
                    input.checked = data[key];
                } else {
                    input.value = data[key];
                }
            }
        });
    }

    function getFormData() {
        const formData = new FormData(patientForm);
        const data = {};
        
        for (let [key, value] of formData.entries()) {
            if (value !== '') {
                if (['idade_paciente', 'altura', 'peso', 'intensidade_dor_exame', 'intensidade_dor_indicacao'].includes(key)) {
                    data[key] = parseFloat(value);
                } else {
                    data[key] = value;
                }
            }
        }
        
        const checkboxes = patientForm.querySelectorAll('input[type="checkbox"]');
        checkboxes.forEach(cb => {
            data[cb.name] = cb.checked;
        });
        
        return data;
    }

    async function processImage(dataUrl) {
        const base64 = dataUrl.split(',')[1];
        const tabularData = getFormData();
        
        const requiredFields = {
            'idade_paciente': 'Idade do paciente',
            'sexo_paciente': 'Sexo',
            'altura': 'Altura',
            'peso': 'Peso',
            'intensidade_dor_exame': 'Intensidade da dor no exame',
            'intensidade_dor_indicacao': 'Intensidade da dor na indicação'
        };
        
        const missingFields = [];
        for (const [field, label] of Object.entries(requiredFields)) {
            const value = tabularData[field];
            if (value === undefined || value === null || value === '' || 
                (typeof value === 'number' && value === 0 && field !== 'intensidade_dor_exame' && field !== 'intensidade_dor_indicacao')) {
                missingFields.push(label);
            }
        }
        
        if (missingFields.length > 0) {
            alert('⚠️ Dados incompletos!\n\nPor favor, preencha os seguintes campos:\n• ' + missingFields.join('\n• '));
            return;
        }
    
        document.getElementById('loadingSpinner').style.display = 'flex';
        resultContainer.style.display = 'none';
        gravityValue.textContent = '';
        placeholderText.style.display = 'none';
    
        try {
            const res = await fetch('/ecg-descritores', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    img: base64,
                    tabular_data: tabularData
                })
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
    }

    function renderResults(data) {
        placeholderText.style.display = 'none';
        resultContainer.style.display = 'block';

        if (data.gravidade && data.gravidade !== 'None') {
            if (Array.isArray(data.gravidade)) {
                const filteredLabels = data.gravidade.filter(label => label !== 'None');
                if (filteredLabels.length > 0) {
                    gravityValue.innerHTML = filteredLabels.join('<br>');
                } else {
                    gravityValue.textContent = 'Não Identificado';
                }
            } else {
                gravityValue.textContent = data.gravidade;
            }
        } else {
            gravityValue.textContent = 'Não Identificado';
        }
    }
    
    imageUpload.addEventListener('change', () => {
        const file = imageUpload.files[0];
        if (!file) return;
    
        if (file.type === "application/pdf") {
            const reader = new FileReader();
            reader.onload = async (e) => {
                const typedarray = new Uint8Array(e.target.result);
    
                const pdf = await pdfjsLib.getDocument({ data: typedarray }).promise;
                const page = await pdf.getPage(1);
    
                const viewport = page.getViewport({ scale: 2.0 });
                const canvas = document.createElement("canvas");
                const context = canvas.getContext("2d");
    
                canvas.width = viewport.width;
                canvas.height = viewport.height;
    
                await page.render({ canvasContext: context, viewport }).promise;
    
                const dataUrl = canvas.toDataURL("image/png");
    
                imagePreview.src = dataUrl;
                imagePreview.style.display = 'block';
                imageContainer.classList.add('has-image');
                analyzeBtn.style.display = 'block';
            };
            reader.readAsArrayBuffer(file);
        } else {
            const reader = new FileReader();
            reader.onload = (e) => {
                const dataUrl = e.target.result;
                imagePreview.src = dataUrl;
                imagePreview.style.display = 'block';
                imageContainer.classList.add('has-image');
                analyzeBtn.style.display = 'block';
            };
            reader.readAsDataURL(file);
        }
    });

    jsonUpload.addEventListener('change', async () => {
        const file = jsonUpload.files[0];
        if (!file) return;

        try {
            const text = await file.text();
            const jsonData = JSON.parse(text);

            if (jsonData.patient_data) {
                setFormData(jsonData.patient_data);
            } else if (jsonData) {
                setFormData(jsonData);
            }
            alert('Dados do paciente carregados com sucesso!');
        } catch (err) {
            console.error('Erro ao carregar JSON:', err);
            alert('Erro ao carregar arquivo JSON. Verifique o console para detalhes.');
        }
    });

    imageContainer.addEventListener('click', e => {
        if (e.target === imagePreview && imagePreview.style.display === 'block') {
            imageUpload.value = '';
            imagePreview.style.display = 'none';
            imageContainer.classList.remove('has-image');
            resultContainer.style.display = 'none';
            placeholderText.style.display = 'block';
            analyzeBtn.style.display = 'none';
        }
    });
});
