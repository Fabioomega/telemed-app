document.addEventListener('DOMContentLoaded', () => {
    // Get DOM Elements
    const imageUpload = document.getElementById('imageUpload');
    const uploadBtnTrigger = document.getElementById('uploadBtnTrigger'); // Button to trigger input
    const imagePreviewBox = document.getElementById('imagePreviewBox'); // The container div
    const uploadedImage = document.getElementById('uploadedImage');
    const interestingRegionsPreviewImage = document.getElementById('interestingRegionsPreview');

    const analysisPlaceholder = document.getElementById('analysisPlaceholder');
    const aiOutputContainer = document.getElementById('aiOutputContainer'); // Holds all results cards

    const modalitySpan = document.getElementById('modality');
    const regionSpan = document.getElementById('region');
    const diseaseCheckboxesContainer = document.getElementById('diseaseCheckboxes');
    const reportOutput = document.getElementById('reportOutput');

    const generateBtn = document.getElementById('generateBtn');
    const completeBtn = document.getElementById('completeBtn');

    const conditionsCard = document.getElementById('conditionsCard');
    const reportCard = document.getElementById('reportCard');
    const regionsPreviewCard = document.getElementById('regionsPreviewCard');


    // --- Variables ---
    let currentB64ImageFile = null; // Store the uploaded file reference

    const modalityEndpoint = '/modalidade';
    const regionEndpoint = '/regiao';
    const diseasesEndpoint = '/raio-x-doencas';
    const fractureEndpoint = '/fracture';
    const completeReportEndpoint = "/completar-laudo";
    const generateReportEndpoint = "/gerar-laudo";

    // --- Event Listeners ---

    // Trigger hidden file input when the styled button is clicked
    uploadBtnTrigger.addEventListener('click', () => {
        imageUpload.click();
    });

    // Image Upload Listener (on the hidden input)
    imageUpload.addEventListener('change', (event) => {
        const file = event.target.files[0];
        if (file) {
            const reader = new FileReader();

            reader.onload = (e) => {
                currentB64ImageFile = e.target.result.split(',')[1];

                uploadedImage.src = e.target.result;
                uploadedImage.style.display = 'block'; // Show the image element
                imagePreviewBox.classList.add('has-image'); // Add class to hide placeholder/border

                hidePlaceholder();

                populateAnalysis(currentB64ImageFile);
            }
            reader.readAsDataURL(file);

            // Reset file input value so the 'change' event fires even if the same file is selected again
            imageUpload.value = null;
        }
    });

    // Generate Report Button Listener
    generateBtn.addEventListener('click', async () => {
        if (!currentB64ImageFile) {
            alert('Please upload an image first.');
            return;
        }
        setLoadingState(true, 'generate');

        report = await getReport(currentB64ImageFile);
        populateReport(report);

        setLoadingState(false);
    });

    // Complete Text Button Listener
    completeBtn.addEventListener('click', async () => {
        const currentText = reportOutput.value;
        if (!currentText.trim()) {
            alert('Please type something in the report area for the AI to complete, or generate an initial report.');
            return;
        }
        setLoadingState(true, 'complete');

        let start = reportOutput.value;
        report = await getCompleteReport(start, currentB64ImageFile);
        populateReport(report);

        setLoadingState(false);
    });


    // --- Fetch Functions ---

    async function fetchImageEndpoint(endpoint, base64Image) {
        const body = JSON.stringify({
            "img": base64Image
        });

        try {
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: body,
                signal: AbortSignal.timeout(300000)
            });

            const data = await response.json();

            return data;
        } catch (error) {
            console.warn(`While fetching from ${endpoint} an error happened!`);
            console.warn(`The error: ${error.message}`);
            return {};
        }
    }

    async function fetchImageEndpointAsBlob(endpoint, base64Image) {
        const body = JSON.stringify({
            "img": base64Image
        });

        try {
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: body,
                signal: AbortSignal.timeout(300000)
            });

            const blob = await response.blob();
            return blob;
        } catch (error) {
            console.warn(`While fetching from ${endpoint} an error happened!`);
            console.warn(`The error: ${error.message}`);
            return {};
        }
    }

    async function fetchCompleteEndpoint(endpoint, text, base64Image) {
        const body = JSON.stringify({
            "start": text,
            "img": base64Image,
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

            return data;
        } catch (error) {
            console.warn(`While fetching from ${endpoint} an error happened!`);
            console.warn(`The error: ${error.message}`);
            return {};
        }
    }

    async function getFractureRegion(base64Image) {
        let blob = await fetchImageEndpointAsBlob(fractureEndpoint, base64Image);
        return URL.createObjectURL(blob);
    }

    async function getRegion(base64Image) {
        let data = await fetchImageEndpoint(regionEndpoint, base64Image);

        for (const [key, value] of Object.entries(data)) {
            if (value) {
                if (value === true) {
                    return key;
                } else {
                    console.warn(`The endpoint ${regionEndpoint} has probably changed! The output type was not expected!`);
                }
            }
        }

        return "";
    }

    async function getModality(base64Image) {
        let data = await fetchImageEndpoint(modalityEndpoint, base64Image);

        for (const [key, value] of Object.entries(data)) {
            if (value) {
                if (value === true) {
                    return key;
                } else {
                    console.warn(`The endpoint ${modalityEndpoint} has probably changed! The output type was not expected!`);
                }
            }
        }

        return "";
    }

    async function getAnalysisHeader(base64Image) {
        const [region, modality] = await Promise.all([
            getRegion(base64Image),
            getModality(base64Image)
        ]);
        return { 'region': region, 'modality': modality };
    }

    async function getDiseases(base64Image) {
        return await fetchImageEndpoint(diseasesEndpoint, base64Image);
    }

    async function getReport(base64Image) {
        let output = await fetchImageEndpoint(generateReportEndpoint, base64Image);
        if ("generated_text" in output) {
            return output['generated_text'];
        } else {
            return "";
        }
    }

    async function getCompleteReport(start, base64Image) {
        let output = await fetchCompleteEndpoint(completeReportEndpoint, start, base64Image);
        if ("generated_text" in output) {
            return output['generated_text'];
        } else {
            return "";
        }
    }

    async function createHeader(base64Image) {
        let output = await getAnalysisHeader(base64Image);
        populateHeader(output);
    }

    async function createFractureImagePreview(base64Image) {
        let url = await getFractureRegion(base64Image);
        console.log(url);
        populateFracturePreview(url);
        unsetHidden(regionsPreviewCard);
    }

    async function createCheckboxes(base64Image) {
        let output = await getDiseases(base64Image);
        populateCheckboxes(output);
        unsetHidden(conditionsCard);
    }

    async function createReport(base64Image) {
        let output = await getReport(base64Image);
        populateReport(output);
        unsetHidden(reportCard);
    }

    async function populateAnalysis(base64Image) {
        let analysisType = getSelectedAnalysisType();

        resetAIOutputs();
        setLoadingState(true);

        let promises = [
            createHeader(base64Image),
            createReport(base64Image)
        ]

        if (analysisType === 'general') {
            promises.push(createCheckboxes(base64Image));
        } else if (analysisType === 'mammography') {

        } else if (analysisType === 'fracture') {
            promises.push(createFractureImagePreview(base64Image));
        }

        await Promise.all(promises);

        setLoadingState(false);
    }

    // --- UI Helper Functions ---

    function setHidden(element) {
        element.classList.add('hidden');
    }

    function unsetHidden(element) {
        element.classList.remove('hidden');
    }


    function getSelectedAnalysisType() {
        const selected = document.querySelector('input[name="analysisType"]:checked');
        return selected ? selected.value : 'general';
    }

    const hidePlaceholder = () => {
        // Hide the main analysis placeholder and show the results area
        setHidden(analysisPlaceholder);
        unsetHidden(aiOutputContainer);
    }

    function populateFracturePreview(url) {
        interestingRegionsPreviewImage.onload = () => URL.revokeObjectURL(url);
        interestingRegionsPreviewImage.src = url;
    }

    function populateCheckboxes(diseases) {
        diseaseCheckboxesContainer.innerHTML = ''; // Clear previous checkboxes or placeholder

        if (!diseases || diseases.length === 0) {
            diseaseCheckboxesContainer.innerHTML = '<span class="placeholder-value">No specific conditions flagged.</span>';
            return;
        }

        let index = 0;
        for (const [disease, detected] of Object.entries(diseases)) {
            const div = document.createElement('div');
            div.className = 'checkbox-item';

            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.id = `disease_${index}`;
            checkbox.name = 'diseases';
            checkbox.value = disease;
            checkbox.checked = detected;

            const label = document.createElement('label');
            label.htmlFor = `disease_${index}`;
            label.textContent = disease;

            div.appendChild(checkbox);
            div.appendChild(label);
            diseaseCheckboxesContainer.appendChild(div);

            index++;
        }
    }

    function populateHeader(headers) {
        if (headers.modality.length != 0) {
            modalitySpan.textContent = headers.modality;
            modalitySpan.classList.remove('placeholder-value');
        }

        if (headers.region.length != 0) {
            regionSpan.textContent = headers.region;
            regionSpan.classList.remove('placeholder-value');
        }
    }

    function populateReport(report) {
        if (report.length != 0) {
            reportOutput.value = report;
            reportOutput.placeholder = 'AI report draft generated. You can edit this text.';
        }
    }

    function getCheckedDiseases() {
        const checkedBoxes = diseaseCheckboxesContainer.querySelectorAll('input[type="checkbox"]:checked');
        return Array.from(checkedBoxes).map(cb => cb.value);
    }

    function setLoadingState(isLoading, buttonType = null) {
        const buttons = [generateBtn, completeBtn];

        if (isLoading) {
            if (buttonType === 'generate') {
                generateBtn.disabled = true;
                generateBtn.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" width="16" height="16" class="spin"><path stroke-linecap="round" stroke-linejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0 0 13.803-3.7M4.031 9.865a8.25 8.25 0 0 1 13.803-3.7l3.181 3.182m0-4.991v4.99" /></svg> Generating...`;
            } else if (buttonType === 'complete') {
                completeBtn.disabled = true;
                completeBtn.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" width="16" height="16" class="spin"><path stroke-linecap="round" stroke-linejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0 0 13.803-3.7M4.031 9.865a8.25 8.25 0 0 1 13.803-3.7l3.181 3.182m0-4.991v4.99" /></svg> Completing...`;
            } else {
                // General loading (start of analysis)
                buttons.forEach(btn => btn.disabled = true);
                uploadBtnTrigger.disabled = true; // Disable upload during analysis
                // Add visual cue to report area if needed
                reportOutput.value = "Analyzing image...";
                reportOutput.disabled = true; // Optionally disable textarea during analysis
            }
        } else {
            // Restore buttons
            generateBtn.disabled = false;
            generateBtn.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" width="16" height="16"><path stroke-linecap="round" stroke-linejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0 0 13.803-3.7M4.031 9.865a8.25 8.25 0 0 1 13.803-3.7l3.181 3.182m0-4.991v4.99" /></svg> Regenerate`;

            completeBtn.disabled = false;
            completeBtn.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" width="16" height="16"><path stroke-linecap="round" stroke-linejoin="round" d="m3.75 13.5 10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75Z" /></svg> Complete`;

            uploadBtnTrigger.disabled = false; // Re-enable upload button
            reportOutput.disabled = false; // Re-enable textarea
        }
    }

    function resetAIOutputs() {
        // Reset headers
        modalitySpan.textContent = 'N/A';
        regionSpan.textContent = 'N/A';
        modalitySpan.classList.add('placeholder-value');
        regionSpan.classList.add('placeholder-value');

        // Clear checkboxes
        diseaseCheckboxesContainer.innerHTML = '<span class="placeholder-value">Awaiting analysis...</span>';

        // Clear report
        reportOutput.value = '';
        reportOutput.placeholder = 'AI report draft will appear here...';

        // Hides everything that needs to be hidden
        setHidden(conditionsCard);
        setHidden(reportCard);
        setHidden(regionsPreviewCard);
    }

    // Initial state setup
    function initializePage() {
        unsetHidden(analysisPlaceholder);
        setHidden(aiOutputContainer);
        setLoadingState(false); // Ensure buttons are enabled
        // Disable action buttons until an image is loaded and analysed
        generateBtn.disabled = true;
        completeBtn.disabled = true;
        // Reset image preview area
        setHidden(uploadedImage);
        uploadedImage.src = "#";
        imagePreviewBox.classList.remove('has-image');
        resetAIOutputs(); // Clear any stale data
    }

    initializePage(); // Set initial state when the page loads

}); // End DOMContentLoaded
