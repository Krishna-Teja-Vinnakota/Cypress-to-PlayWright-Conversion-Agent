// Modern Cypress to Playwright Converter App - Simplified Flow

// ==================== STATE ====================
let currentStep = 1;
let sessionId = null;
let websocket = null;
let selectedFiles = [];
let currentFileId = null;
let allFiles = [];

// Code Editors
let cypressEditor = null;
let playwrightEditor = null;

// ==================== INITIALIZATION ====================
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 App initialized');
    initializeCodeEditors();
    setupEventListeners();
    setupDragAndDrop();
});

// ==================== CODE EDITORS ====================
function initializeCodeEditors() {
    const cypressTextarea = document.getElementById('cypress-editor');
    const playwrightTextarea = document.getElementById('playwright-editor');
    
    if (cypressTextarea) {
        cypressEditor = CodeMirror.fromTextArea(cypressTextarea, {
            mode: 'javascript',
            theme: 'dracula',
            lineNumbers: true,
            readOnly: true,
            lineWrapping: true
        });
    }
    
    if (playwrightTextarea) {
        playwrightEditor = CodeMirror.fromTextArea(playwrightTextarea, {
            mode: 'javascript',
            theme: 'dracula',
            lineNumbers: true,
            readOnly: true,
            lineWrapping: true
        });
    }
}

// ==================== EVENT LISTENERS ====================
function setupEventListeners() {
    // File upload
    document.getElementById('file-input').addEventListener('change', handleFileSelect);
    
    // Code tabs
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', (e) => switchTab(e.target.dataset.tab));
    });
    
    // Review actions
    document.getElementById('modify-btn')?.addEventListener('click', showModificationPanel);
    document.getElementById('download-btn')?.addEventListener('click', handleDownload);
    document.getElementById('start-new-btn')?.addEventListener('click', startNew);
    
    // Modification panel
    document.getElementById('send-modification-btn')?.addEventListener('click', handleModification);
    document.getElementById('cancel-modification-btn')?.addEventListener('click', hideModificationPanel);
    document.getElementById('modify-image')?.addEventListener('change', handleImagePreview);
}

// ==================== DRAG & DROP ====================
function setupDragAndDrop() {
    const dropZone = document.getElementById('drop-zone');
    
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('drag-over');
    });
    
    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('drag-over');
    });
    
    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('drag-over');
        
        const files = Array.from(e.dataTransfer.files).filter(f => 
            f.name.endsWith('.cy.js') || f.name.endsWith('.cy.ts')
        );
        
        if (files.length > 0) {
            const dataTransfer = new DataTransfer();
            files.forEach(f => dataTransfer.items.add(f));
            document.getElementById('file-input').files = dataTransfer.files;
            handleFileSelect({ target: { files: dataTransfer.files } });
        }
    });
}

// ==================== FILE HANDLING ====================
function handleFileSelect(e) {
    const files = Array.from(e.target.files);
    selectedFiles = files;
    
    const preview = document.getElementById('file-preview');
    preview.innerHTML = '';
    
    files.forEach(file => {
        const ext = file.name.endsWith('.ts') ? 'TS' : 'JS';
        const div = document.createElement('div');
        div.className = 'file-item';
        div.innerHTML = `
            <div class="file-item-info">
                <div class="file-icon">${ext}</div>
                <div>
                    <div style="font-weight: 600;">${file.name}</div>
                    <div style="font-size: 12px; color: var(--text-secondary);">${(file.size / 1024).toFixed(1)} KB</div>
                </div>
            </div>
        `;
        preview.appendChild(div);
    });
    
    // Auto upload
    if (files.length > 0) {
        setTimeout(() => uploadFiles(), 500);
    }
}

async function uploadFiles() {
    const formData = new FormData();
    selectedFiles.forEach(file => formData.append('files', file));
    
    try {
        goToStep(2);
        
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        sessionId = data.session_id;
        allFiles = data.files;
        
        document.getElementById('session-id-text').textContent = sessionId;
        document.getElementById('session-display').style.display = 'block';
        
        showToast('Files uploaded successfully!', 'success');
        connectWebSocket(sessionId);
        
    } catch (error) {
        showToast('Upload failed: ' + error.message, 'error');
        goToStep(1);
    }
}

// ==================== WEBSOCKET ====================
function connectWebSocket(sid) {
    const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
    websocket = new WebSocket(`${protocol}//${location.host}/ws/${sid}`);
    
    websocket.onopen = () => {
        console.log('✅ WebSocket connected');
        updateWsStatus(true);
    };
    
    websocket.onmessage = (e) => {
        const msg = JSON.parse(e.data);
        handleWebSocketMessage(msg);
    };
    
    websocket.onerror = () => updateWsStatus(false);
    websocket.onclose = () => updateWsStatus(false);
}

function handleWebSocketMessage(msg) {
    console.log('📨 Message:', msg);
    
    switch (msg.type) {
        case 'conversion_progress':
            updateConversionProgress(msg);
            break;
        case 'conversion_done':
            updateFileConverted(msg);
            break;
        case 'conversion_complete':
            handleConversionComplete(msg);
            break;
        case 'modification_done':
            handleModificationComplete(msg);
            break;
    }
}

function updateWsStatus(connected) {
    const status = document.getElementById('ws-status');
    const dot = status.querySelector('.status-dot');
    const text = status.querySelector('.status-text');
    
    if (connected) {
        dot.style.background = 'var(--green)';
        text.textContent = 'Connected';
    } else {
        dot.style.background = 'var(--red)';
        text.textContent = 'Disconnected';
    }
}

// ==================== CONVERSION PROGRESS ====================
function updateConversionProgress(msg) {
    const progress = (msg.current / msg.total) * 100;
    document.getElementById('convert-progress').style.width = progress + '%';
    document.getElementById('convert-percentage').textContent = Math.round(progress) + '%';
    
    const container = document.getElementById('converting-files');
    let fileDiv = document.getElementById('converting-' + msg.file_id);
    
    if (!fileDiv) {
        fileDiv = document.createElement('div');
        fileDiv.id = 'converting-' + msg.file_id;
        fileDiv.className = 'converting-file';
        fileDiv.innerHTML = `
            <div class="loader"></div>
            <span>${msg.file_name}</span>
        `;
        container.appendChild(fileDiv);
    }
}

function updateFileConverted(msg) {
    const fileDiv = document.getElementById('converting-' + msg.file_id);
    if (fileDiv) {
        fileDiv.innerHTML = `
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="color: var(--green);">
                <polyline points="20 6 9 17 4 12"></polyline>
            </svg>
            <span>${msg.file_name}</span>
        `;
    }
}

function handleConversionComplete(msg) {
    showToast('Conversion complete!', 'success');
    setTimeout(() => {
        goToStep(3);
        loadFilesForReview();
    }, 1000);
}

// ==================== REVIEW ====================
async function loadFilesForReview() {
    const filesList = document.getElementById('files-list');
    filesList.innerHTML = '';
    
    for (const file of allFiles) {
        const response = await fetch(`/api/file/${sessionId}/${file.file_id}`);
        const fileData = await response.json();
        
        const item = createFileItem(fileData);
        filesList.appendChild(item);
    }
    
    if (allFiles.length > 0) {
        loadFile(allFiles[0].file_id);
    }
}

function createFileItem(fileData) {
    const div = document.createElement('div');
    div.className = 'file-sidebar-item';
    
    const versions = fileData.playwright_versions || [];
    let versionsHtml = '';
    
    versions.reverse().forEach(v => {
        const isActive = v.version === fileData.current_version;
        versionsHtml += `
            <div class="version-item ${isActive ? 'active' : ''}" 
                 data-file-id="${fileData.file_id}" 
                 data-version="${v.version}"
                 onclick="selectVersion('${fileData.file_id}', ${v.version})">
                v${v.version} ${isActive ? '(Current)' : ''}
            </div>
        `;
    });
    
    div.innerHTML = `
        <div class="file-sidebar-header ${fileData.file_id === currentFileId ? 'active' : ''}" 
             onclick="loadFile('${fileData.file_id}')">
            ${fileData.file_name}
        </div>
        <div class="versions-list">${versionsHtml}</div>
    `;
    
    return div;
}

async function loadFile(fileId) {
    try {
        const response = await fetch(`/api/file/${sessionId}/${fileId}`);
        const fileData = await response.json();
        
        currentFileId = fileId;
        
        document.getElementById('current-file-title').textContent = fileData.file_name;
        document.getElementById('version-badge').textContent = `v${fileData.current_version}`;
        
        const currentVersion = fileData.playwright_versions.find(v => v.version === fileData.current_version);
        
        if (currentVersion && playwrightEditor && cypressEditor) {
            // Set values
            playwrightEditor.setValue(currentVersion.code || '// No code available');
            cypressEditor.setValue(fileData.cypress_code || '// No code available');
            
            // Refresh editors to display content
            setTimeout(() => {
                playwrightEditor.refresh();
                cypressEditor.refresh();
            }, 100);
        }
        
        // Update approve button
        const approveBtn = document.getElementById('approve-btn-main');
        if (fileData.approved_version) {
            approveBtn.textContent = '✓ Approved';
            approveBtn.disabled = true;
            approvedFiles.add(fileId);
        } else {
            approveBtn.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"></polyline></svg> Approve';
            approveBtn.disabled = false;
        }
        
        updateApprovedCount();
        
        // Update sidebar active state
        document.querySelectorAll('.file-sidebar-header').forEach(h => h.classList.remove('active'));
        const header = document.querySelector(`.file-sidebar-header[onclick*="${fileId}"]`);
        if (header) header.classList.add('active');
    } catch (error) {
        console.error('Error loading file:', error);
        showToast('Failed to load file', 'error');
    }
}

async function selectVersion(fileId, version) {
    const formData = new FormData();
    formData.append('session_id', sessionId);
    formData.append('file_id', fileId);
    formData.append('version', version);
    
    try {
        const response = await fetch('/api/select-version', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        if (data.success && playwrightEditor) {
            playwrightEditor.setValue(data.code || '// No code available');
            document.getElementById('version-badge').textContent = `v${version}`;
            
            // Refresh editor
            setTimeout(() => playwrightEditor.refresh(), 100);
            
            // Update active state
            document.querySelectorAll('.version-item').forEach(item => {
                item.classList.remove('active');
                if (item.dataset.fileId === fileId && parseInt(item.dataset.version) === version) {
                    item.classList.add('active');
                }
            });
        }
    } catch (error) {
        console.error('Error selecting version:', error);
        showToast('Failed to select version', 'error');
    }
}

// ==================== MODIFICATION ====================
function showModificationPanel() {
    document.getElementById('modification-panel').classList.add('active');
}

function hideModificationPanel() {
    document.getElementById('modification-panel').classList.remove('active');
    document.getElementById('modify-text').value = '';
    document.getElementById('modify-error').value = '';
    document.getElementById('modify-image').value = '';
    document.getElementById('image-preview').innerHTML = '';
}

function handleImagePreview(e) {
    const file = e.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = (e) => {
            document.getElementById('image-preview').innerHTML = `
                <img src="${e.target.result}" style="max-width: 100%; border-radius: 8px; margin-top: 12px;">
            `;
        };
        reader.readAsDataURL(file);
    }
}

async function handleModification() {
    const query = document.getElementById('modify-text').value.trim();
    const error = document.getElementById('modify-error').value.trim();
    const image = document.getElementById('modify-image').files[0];
    
    if (!query && !error && !image) {
        showToast('Please provide modification details', 'error');
        return;
    }
    
    document.getElementById('modification-loading').classList.add('active');
    
    const formData = new FormData();
    formData.append('session_id', sessionId);
    formData.append('file_id', currentFileId);
    formData.append('query', query);
    formData.append('error_text', error);
    if (image) formData.append('image', image);
    
    try {
        const response = await fetch('/api/modify', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        if (data.success && playwrightEditor) {
            playwrightEditor.setValue(data.code || '// No code available');
            document.getElementById('version-badge').textContent = `v${data.new_version}`;
            
            // Refresh editor
            setTimeout(() => playwrightEditor.refresh(), 100);
            
            await loadFilesForReview();
            await loadFile(currentFileId);
            
            hideModificationPanel();
            showToast('Code modified successfully!', 'success');
        }
    } catch (error) {
        showToast('Modification failed', 'error');
        console.error('Modification error:', error);
    } finally {
        document.getElementById('modification-loading').classList.remove('active');
    }
}

function handleModificationComplete(msg) {
    // Handled in handleModification
}

// ==================== NAVIGATION ====================
function goToStep(step) {
    currentStep = step;
    
    // Hide all steps
    document.querySelectorAll('.step-view').forEach(v => v.classList.remove('active'));
    
    // Show current step
    const steps = ['upload', 'converting', 'review'];
    document.getElementById(`step-${steps[step - 1]}`).classList.add('active');
    
    // Update step indicator
    document.querySelectorAll('.step').forEach((s, i) => {
        s.classList.remove('active', 'completed');
        if (i + 1 === step) s.classList.add('active');
        else if (i + 1 < step) s.classList.add('completed');
    });
    
    // Show step indicator after upload
    document.getElementById('step-indicator').style.display = step > 1 ? 'flex' : 'none';
}

function switchTab(tabName) {
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.tab === tabName) btn.classList.add('active');
    });
    
    document.querySelectorAll('.tab-pane').forEach(pane => {
        pane.classList.remove('active');
    });
    
    document.getElementById(`tab-${tabName}`).classList.add('active');
}

async function handleDownload() {
    if (!currentFileId) {
        showToast('Please select a file first', 'error');
        return;
    }
    
    try {
        showToast('Downloading file...', 'info');
        window.location.href = `/api/download/${sessionId}/${currentFileId}`;
        setTimeout(() => showToast('Download started!', 'success'), 500);
    } catch (error) {
        showToast('Download failed', 'error');
        console.error('Download error:', error);
    }
}

function startNew() {
    location.reload();
}

// ==================== TOAST NOTIFICATIONS ====================
function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <div style="font-weight: 600; margin-bottom: 4px;">${type.charAt(0).toUpperCase() + type.slice(1)}</div>
        <div>${message}</div>
    `;
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// ==================== UTILITIES ====================
window.loadFile = loadFile;
window.selectVersion = selectVersion;
