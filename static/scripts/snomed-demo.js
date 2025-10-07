let currentTab = 'annotated';

function switchTab(tabName) {
    currentTab = tabName;
    const tabs = document.querySelectorAll('.tab');
    const contents = document.querySelectorAll('.tab-content');

    tabs.forEach(tab => tab.classList.remove('active'));
    contents.forEach(content => content.classList.remove('active'));

    event.target.classList.add('active');
    document.getElementById(tabName + 'Tab').classList.add('active');
}

function processText() {
    const inputText = document.getElementById('inputText').value.trim();
    const soapFormat = document.getElementById('soapFormat').checked;

    if (!inputText) {
        alert('Please enter some text to process.');
        return;
    }

    let textToProcess = inputText;

    if (soapFormat) {
        textToProcess = convertToSOAP(inputText);
    }

    const entities = extractEntities(textToProcess);
    processedEntities = entities; // Store for tooltip access
    displayAnnotatedText(textToProcess, entities);
    displayEntities(entities);
}

function convertToSOAP(text) {
    // Simple SOAP conversion simulation
    const sections = {
        subjective: [],
        objective: [],
        assessment: [],
        plan: []
    };

    const sentences = text.split(/[.!?]+/).filter(s => s.trim());

    sentences.forEach(sentence => {
        const lower = sentence.toLowerCase();
        if (lower.includes('complain') || lower.includes('feel') || lower.includes('pain') || lower.includes('patient report')) {
            sections.subjective.push(sentence.trim());
        } else if (lower.includes('exam') || lower.includes('vital') || lower.includes('temperature') || lower.includes('pressure')) {
            sections.objective.push(sentence.trim());
        } else if (lower.includes('diagnos') || lower.includes('condition') || lower.includes('indicate')) {
            sections.assessment.push(sentence.trim());
        } else {
            sections.plan.push(sentence.trim());
        }
    });

    return `SUBJECTIVE:\n${sections.subjective.join('. ') || 'None documented'}.\n\nOBJECTIVE:\n${sections.objective.join('. ') || 'None documented'}.\n\nASSESSMENT:\n${sections.assessment.join('. ') || 'None documented'}.\n\nPLAN:\n${sections.plan.join('. ') || 'None documented'}.`;
}

function extractEntities(text) {
    // Simulated cTAKES entity extraction with CUIs and properties
    const entities = [];

    const medicalTerms = {

        'pain': {
            type: 'Symptom',
            cuis: ['C0030193'],
            negation: false,
            uncertainty: false
        },
        'fever': {
            type: 'Symptom',
            cuis: ['C0015967', 'C0239938'],
            negation: false,
            uncertainty: false
        },
        'headache': {
            type: 'Symptom',
            cuis: ['C0018681'],
            negation: false,
            uncertainty: false
        },
        'nausea': {
            type: 'Symptom',
            cuis: ['C0027497'],
            negation: false,
            uncertainty: false
        },
        'cough': {
            type: 'Symptom',
            cuis: ['C0010200'],
            negation: false,
            uncertainty: false
        },
        'fatigue': {
            type: 'Symptom',
            cuis: ['C0015672'],
            negation: false,
            uncertainty: false
        },
        'diabetes': {
            type: 'Disease',
            cuis: ['C0011849', 'C0011854'],
            negation: false,
            uncertainty: false
        },
        'hypertension': {
            type: 'Disease',
            cuis: ['C0020538'],
            negation: false,
            uncertainty: false
        },
        'pneumonia': {
            type: 'Disease',
            cuis: ['C0032285'],
            negation: false,
            uncertainty: false
        },
        'influenza': {
            type: 'Disease',
            cuis: ['C0021400'],
            negation: false,
            uncertainty: false
        },
        'covid': {
            type: 'Disease',
            cuis: ['C5203670'],
            negation: false,
            uncertainty: false
        },
        'aspirin': {
            type: 'Medication',
            cuis: ['C0004057'],
            negation: false,
            uncertainty: false
        },
        'ibuprofen': {
            type: 'Medication',
            cuis: ['C0020740'],
            negation: false,
            uncertainty: false
        },
        'acetaminophen': {
            type: 'Medication',
            cuis: ['C0000970'],
            negation: false,
            uncertainty: false
        },
        'metformin': {
            type: 'Medication',
            cuis: ['C0025598'],
            negation: false,
            uncertainty: false
        },
        'amoxicillin': {
            type: 'Medication',
            cuis: ['C0002645'],
            negation: false,
            uncertainty: false
        },
        'blood pressure': {
            type: 'Vital Sign',
            cuis: ['C0005823'],
            negation: false,
            uncertainty: false
        },
        'temperature': {
            type: 'Vital Sign',
            cuis: ['C0005903'],
            negation: false,
            uncertainty: false
        },
        'heart rate': {
            type: 'Vital Sign',
            cuis: ['C0018810'],
            negation: false,
            uncertainty: false
        },
        'respiratory rate': {
            type: 'Vital Sign',
            cuis: ['C0231832'],
            negation: false,
            uncertainty: false
        },
        'pressure': {
            type: 'Vital Sign',
            cuis: ['C0039606', 'C0011595'],
            negation: false,
            uncertainty: false
        },
        'examination': {
            type: 'Procedure',
            cuis: ['C0031809'],
            negation: false,
            uncertainty: false
        },
        'x-ray': {
            type: 'Procedure',
            cuis: ['C0034571'],
            negation: false,
            uncertainty: false
        },
        'ct scan': {
            type: 'Procedure',
            cuis: ['C0040405'],
            negation: false,
            uncertainty: false
        },
        'blood test': {
            type: 'Procedure',
            cuis: ['C0018941'],
            negation: false,
            uncertainty: false
        },
        'mri': {
            type: 'Procedure',
            cuis: ['C0024485'],
            negation: false,
            uncertainty: false
        }
    };

    // Check for negation and uncertainty context
    Object.keys(medicalTerms).forEach(term => {
        const regex = new RegExp('\\b' + term + '\\b', 'gi');
        let match;
        while ((match = regex.exec(text)) !== null) {
            entities.push({
                text: match[0],
                type: medicalTerms[term.toLowerCase()].type,
                cuis: medicalTerms[term.toLowerCase()].cuis,
                negation: medicalTerms[term.toLowerCase()].negation,
                uncertainty: medicalTerms[term.toLowerCase()].uncertainty,
                start: match.index,
                end: match.index + match[0].length
            });
        }
    });

    return entities.sort((a, b) => a.start - b.start);
}

function displayAnnotatedText(text, entities) {
    const annotatedTab = document.getElementById('annotatedTab');

    if (entities.length === 0) {
        annotatedTab.innerHTML = `<div style="color: #c7d2fe; line-height: 1.8;">${text}</div>`;
        return;
    }

    let html = '';
    let lastIndex = 0;

    entities.forEach((entity, index) => {
        html += text.substring(lastIndex, entity.start);

        let badges = '';
        if (entity.negation) {
            badges += '<span class="property-badge negated">NEG</span>';
        }
        if (entity.uncertainty) {
            badges += '<span class="property-badge uncertain">UNC</span>';
        }

        html += `<span class="annotation" data-entity-index="${index}" onmouseenter="showTooltip(event, ${index})" onmouseleave="hideTooltip()">${entity.text}<span class="annotation-type">${entity.type}</span>${badges}</span>`;
        lastIndex = entity.end;
    });

    html += text.substring(lastIndex);
    annotatedTab.innerHTML = `<div style="color: #c7d2fe; line-height: 1.8;">${html}</div>`;
}

let processedEntities = [];

function showTooltip(event, entityIndex) {
    const entity = processedEntities[entityIndex];
    const tooltip = document.getElementById('tooltip');

    let cuisHtml = entity.cuis.map(cui => `<span class="cui-badge">${cui}</span>`).join('');

    tooltip.innerHTML = `
                <div class="tooltip-header">${entity.text}</div>
                <div class="tooltip-row">
                    <span class="tooltip-label">Semantic Type:</span>
                    <span class="tooltip-value">${entity.type}</span>
                </div>
                <div class="tooltip-row">
                    <span class="tooltip-label">CUI(s):</span>
                </div>
                <div class="cui-list">${cuisHtml}</div>
                <div class="tooltip-row">
                    <span class="tooltip-label">Negated:</span>
                    <span class="tooltip-value">${entity.negation ? 'Yes' : 'No'}</span>
                </div>
                <div class="tooltip-row">
                    <span class="tooltip-label">Uncertain:</span>
                    <span class="tooltip-value">${entity.uncertainty ? 'Yes' : 'No'}</span>
                </div>
            `;

    tooltip.style.display = 'block';
    tooltip.style.left = event.pageX + 10 + 'px';
    tooltip.style.top = event.pageY + 10 + 'px';
}

function hideTooltip() {
    const tooltip = document.getElementById('tooltip');
    tooltip.style.display = 'none';
}

function displayEntities(entities) {
    const entitiesTab = document.getElementById('entitiesTab');

    if (entities.length === 0) {
        entitiesTab.innerHTML = `<div class="empty-state">
                    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z"></path>
                    </svg>
                    <p>No entities found in the text.</p>
                </div>`;
        return;
    }

    const grouped = {};
    entities.forEach(entity => {
        if (!grouped[entity.type]) {
            grouped[entity.type] = [];
        }
        grouped[entity.type].push(entity);
    });

    let html = '';
    Object.keys(grouped).forEach(type => {
        html += `<div class="soap-section">
                    <h3>${type} (${grouped[type].length})</h3>`;

        grouped[type].forEach(entity => {
            const cuisDisplay = entity.cuis.map(cui => `<span class="cui-badge">${cui}</span>`).join('');
            let badges = '';
            if (entity.negation) {
                badges += '<span class="property-badge negated">NEGATED</span>';
            }
            if (entity.uncertainty) {
                badges += '<span class="property-badge uncertain">UNCERTAIN</span>';
            }

            html += `
                        <div class="entity-item">
                            <div class="entity-header">
                                <span class="entity-text">${entity.text}</span>
                                <span class="entity-type-badge">${entity.type}</span>
                            </div>
                            <div class="entity-details">
                                <span class="label">CUI(s):</span>
                                <div class="cui-list">${cuisDisplay}</div>
                                <span class="label">Negation:</span>
                                <span class="value">${entity.negation ? 'Yes' : 'No'}</span>
                                <span class="label">Uncertainty:</span>
                                <span class="value">${entity.uncertainty ? 'Yes' : 'No'}</span>
                            </div>
                            ${badges ? `<div style="margin-top: 8px;">${badges}</div>` : ''}
                        </div>
                    `;
        });

        html += '</div>';
    });

    entitiesTab.innerHTML = html;
}

function clearText() {
    document.getElementById('inputText').value = '';
    document.getElementById('soapFormat').checked = false;
    document.getElementById('annotatedTab').innerHTML = `<div class="empty-state">
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
                </svg>
                <p>No annotations yet. Process text to see results.</p>
            </div>`;
    document.getElementById('entitiesTab').innerHTML = `<div class="empty-state">
                <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z"></path>
                </svg>
                <p>No entities extracted yet. Process text to see results.</p>
            </div>`;
}