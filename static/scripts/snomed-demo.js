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

function toggleProcessButton() {
    const button = document.getElementById('processButton');
    if (button?.disabled == undefined || button.disabled) {
        button.disabled = false;
    } else {
        button.disabled = true;
    }
    button.classList.toggle('disable');
}

async function processText() {
    const inputText = document.getElementById('inputText').value.trim();
    const useSoap = document.getElementById('soapFormat').checked;
    toggleProcessButton();

    if (!inputText) {
        alert('Please enter some text to process.');
        return;
    }

    let textToProcess = inputText;

    const { text, medicalTerms } = await getSoapAndEntities(textToProcess, useSoap)
    const entities = extractEntities(text, medicalTerms);
    processedEntities = entities;
    displayAnnotatedText(text, entities);
    displayEntities(entities);
    toggleProcessButton();
}

async function getSoapAndEntities(text, useSoap) {
    try {
        const response = await fetch("/index", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text: text, use_soap: useSoap })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    } catch (error) {
        console.error("Failed to extract entities:", error);
        return { 'text': "", 'medicalTerms': [] };
    }
}

function fuse_entities(indexedList) {
    let entities = [];
    let processed = new Set();

    indexedList.forEach((entity, i) => {
        if (processed.has(i)) return;

        entities.push({
            meanings: [entity],
            start: entity.spans.start,
            end: entity.spans.end
        });

        let last_idx = entities.length - 1;

        for (let it = i + 1; it < indexedList.length; it++) {
            if (entity.spans.start === indexedList[it].spans.start && entity.spans.end === indexedList[it].spans.end) {
                entities[last_idx].meanings.push(indexedList[it]);
                processed.add(it);
            }
        }
    });

    return entities;
}

function extractEntities(text, medicalTerms) {
    const entities = [];

    Object.values(medicalTerms).forEach(indexedList => {
        fuse_entities(indexedList).forEach(entity => {
            entities.push(
                {
                    text: text.substring(entity.start, entity.end),
                    meanings: entity.meanings,
                    start: entity.start,
                    end: entity.end
                }
            )
        });
    });

    return entities.sort((a, b) => a.start - b.start);
}

function resolveOverlaps(entities) {
    // Sort by start position, then by length (longer first)
    const sorted = entities.slice().sort((a, b) => {
        if (a.start !== b.start) return a.start - b.start;
        return (b.end - b.start) - (a.end - a.start);
    });

    const resolved = [];

    for (let i = 0; i < sorted.length; i++) {
        const current = sorted[i];
        let hasOverlap = false;

        // Check if current entity overlaps with any already resolved entity
        for (let j = 0; j < resolved.length; j++) {
            const existing = resolved[j];

            // Check for overlap
            if (!(current.end <= existing.start || current.start >= existing.end)) {
                hasOverlap = true;

                // Keep the longer entity (more specific)
                if ((current.end - current.start) > (existing.end - existing.start)) {
                    resolved[j] = current;
                }
                break;
            }
        }

        if (!hasOverlap) {
            resolved.push(current);
        }
    }

    // Sort back by start position
    return resolved.sort((a, b) => a.start - b.start);
}

function displayAnnotatedText(text, entities) {
    const annotatedTab = document.getElementById('annotatedTab');

    if (entities.length === 0) {
        annotatedTab.innerHTML = `<div style="color: #c7d2fe; line-height: 1.8;">${text}</div>`;
        return;
    }

    // Resolve overlapping entities
    const resolvedEntities = resolveOverlaps(entities);


    let html = '';
    let lastIndex = 0;

    resolvedEntities.forEach((entity, index) => {
        html += text.substring(lastIndex, entity.start);

        // Check if ambiguous (multiple meanings)
        const isAmbiguous = entity.meanings.length > 1;
        const typeLabel = isAmbiguous
            ? entity.meanings.map(m => m.semanticGroup).join('/')
            : entity.meanings[0].semanticGroup;
        const typeClass = isAmbiguous ? 'annotation-type ambiguous' : 'annotation-type';

        let badges = '';
        if (!isAmbiguous) {
            if (entity.meanings[0].negated) {
                badges += '<span class="property-badge negated">NEG</span>';
            }
            if (entity.meanings[0].uncertain) {
                badges += '<span class="property-badge uncertain">UNC</span>';
            }
        }

        // Find original index for tooltip
        const originalIndex = entities.indexOf(entity);

        html += `<span class="annotation" data-entity-index="${originalIndex}" onmouseenter="showTooltip(event, ${originalIndex})" onmouseleave="hideTooltip()">${entity.text}<span class="${typeClass}">${typeLabel}</span>${badges}</span>`;
        lastIndex = entity.end;
    });

    html += text.substring(lastIndex);
    annotatedTab.innerHTML = `<div style="color: #c7d2fe; line-height: 1.8;">${html}</div>`;
}

let processedEntities = [];

function showTooltip(event, entityIndex) {
    const entity = processedEntities[entityIndex];
    const tooltip = document.getElementById('tooltip');

    let tooltipContent = `<div class="tooltip-header">${entity.text}</div>`;

    // Show all meanings for ambiguous terms
    if (entity.meanings.length > 1) {
        tooltipContent += `<div style="color: #ec4899; font-size: 11px; margin: 4px 0;">⚠ Ambiguous Term - Multiple Meanings Detected</div>`;
    }

    entity.meanings.forEach((meaning, idx) => {
        if (entity.meanings.length > 1) {
            tooltipContent += `<div class="meaning-section">
                        <div class="meaning-header">Meaning ${idx + 1}: ${meaning.semanticGroup}</div>
                        `;
        } else {
            tooltipContent += `<div class="tooltip-row">
                        <span class="tooltip-label">Semantic Type:</span>
                        <span class="tooltip-value">${meaning.semanticGroup}</span>
                    </div>`;
        }

        let cuisHtml = meaning.cuis.map(_cui => `<span class="cui-badge">${_cui}</span>`).join('');

        if (entity.meanings.length > 1) {
            tooltipContent += `<div class="tooltip-row">
                        <span class="tooltip-label">CUI(s):</span>
                    </div>
                    <div class="cui-list">${cuisHtml}</div>

                    <div class="tooltip-row">
                        <span class="tooltip-label">Negated:</span>
                        <span class="tooltip-value">${meaning.negated ? 'Yes' : 'No'}</span>
                    </div>

                    <div class="tooltip-row">
                        <span class="tooltip-label">Uncertain:</span>
                        <span class="tooltip-value">${meaning.uncertain ? 'Yes' : 'No'}</span>
                    </div>
                    </div>
                    `;
        } else {
            tooltipContent += `<div class="tooltip-row">
                        <span class="tooltip-label">CUI(s):</span>
                    </div>
                    <div class="cui-list">${cuisHtml}</div>

                    <div class="tooltip-row">
                        <span class="tooltip-label">Negated:</span>
                        <span class="tooltip-value">${meaning.negated ? 'Yes' : 'No'}</span>
                    </div>

                    <div class="tooltip-row">
                        <span class="tooltip-label">Uncertain:</span>
                        <span class="tooltip-value">${meaning.uncertain ? 'Yes' : 'No'}</span>
                    </div>`
        }
    });

    // tooltipContent += `
    //             <div class="tooltip-row">
    //                 <span class="tooltip-label">Negated:</span>
    //                 <span class="tooltip-value">${entity.negation ? 'Yes' : 'No'}</span>
    //             </div>
    //             <div class="tooltip-row">
    //                 <span class="tooltip-label">Uncertain:</span>
    //                 <span class="tooltip-value">${entity.uncertain ? 'Yes' : 'No'}</span>
    //             </div>
    //         `;

    tooltip.innerHTML = tooltipContent;
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

    let html = '';

    entities.forEach((entity, idx) => {
        entity.meanings.forEach((meaning, meaningIdx) => {
            const cuisDisplay = meaning.cuis.map(_cui => `<span class="cui-badge">${_cui}</span>`).join('');
            let badges = '';

            if (entity.meanings.length > 1) {
                badges += '<span class="property-badge" style="background: rgba(236, 72, 153, 0.3); color: #f9a8d4; border: 1px solid rgba(236, 72, 153, 0.5);">AMBIGUOUS</span>';
            }
            if (meaning.negated) {
                badges += '<span class="property-badge negated">NEGATED</span>';
            }
            if (meaning.uncertain) {
                badges += '<span class="property-badge uncertain">UNCERTAIN</span>';
            }

            html += `
                        <div class="entity-item">
                            <div class="entity-header">
                                <span class="entity-text">${entity.text}${entity.meanings.length > 1 ? ` (Meaning ${meaningIdx + 1})` : ''}</span>
                                <span class="entity-type-badge">${meaning.semanticGroup}</span>
                            </div>
                            <div class="entity-details">
                                <span class="label">CUI(s):</span>
                                <div class="cui-list">${cuisDisplay}</div>
                                <span class="label">Negation:</span>
                                <span class="value">${meaning.negated ? 'Yes' : 'No'}</span>
                                <span class="label">Uncertainty:</span>
                                <span class="value">${meaning.uncertain ? 'Yes' : 'No'}</span>
                                ${entity.meanings.length > 1 ? `
                                <span class="label">Status:</span>
                                <span class="value">Ambiguous (${entity.meanings.length} possible meanings)</span>
                                ` : ''}
                            </div>
                            ${badges ? `<div style="margin-top: 8px;">${badges}</div>` : ''}
                        </div>
                    `;
        });
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
