/**
 * Research Verifier - Frontend Application
 * Handles file uploads, API communication, and UI updates
 */

// State management
let currentSessionId = null;
let statusPollingInterval = null;

// DOM Elements
const uploadSection = document.getElementById('upload-section');
const progressSection = document.getElementById('progress-section');
const resultsSection = document.getElementById('results-section');
const uploadForm = document.getElementById('upload-form');
const analyzeBtn = document.getElementById('analyze-btn');

// File inputs
const paperInput = document.getElementById('paper-input');
const logsInput = document.getElementById('logs-input');
const scriptsInput = document.getElementById('scripts-input');
const bibtexInput = document.getElementById('bibtex-input');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    setupFileInputs();
    setupFormSubmission();
});

/**
 * Setup file input change handlers
 */
function setupFileInputs() {
    paperInput.addEventListener('change', (e) => {
        const fileName = e.target.files[0]?.name || '';
        document.getElementById('paper-name').textContent = fileName;
    });

    logsInput.addEventListener('change', (e) => {
        const files = Array.from(e.target.files);
        const names = files.map(f => f.name).join(', ');
        document.getElementById('logs-name').textContent = names || '';
    });

    scriptsInput.addEventListener('change', (e) => {
        const files = Array.from(e.target.files);
        const names = files.map(f => f.name).join(', ');
        document.getElementById('scripts-name').textContent = names || '';
    });

    bibtexInput.addEventListener('change', (e) => {
        const fileName = e.target.files[0]?.name || '';
        document.getElementById('bibtex-name').textContent = fileName;
    });
}

/**
 * Setup form submission
 */
function setupFormSubmission() {
    uploadForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        if (!paperInput.files[0]) {
            alert('Please select a research paper file');
            return;
        }

        await startAnalysis();
    });
}

/**
 * Start the analysis process
 */
async function startAnalysis() {
    // Disable button
    analyzeBtn.disabled = true;
    analyzeBtn.innerHTML = '<span class="btn-icon">⏳</span><span class="btn-text">Uploading...</span>';

    try {
        // Create FormData
        const formData = new FormData();
        formData.append('paper', paperInput.files[0]);

        // Add optional files
        if (logsInput.files.length > 0) {
            for (const file of logsInput.files) {
                formData.append('logs', file);
            }
        }

        if (scriptsInput.files.length > 0) {
            for (const file of scriptsInput.files) {
                formData.append('scripts', file);
            }
        }

        if (bibtexInput.files[0]) {
            formData.append('bibtex', bibtexInput.files[0]);
        }

        // Upload files
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error('Upload failed');
        }

        const data = await response.json();
        currentSessionId = data.session_id;

        // Switch to progress view
        showProgressView();

        // Start polling for status
        startStatusPolling();

    } catch (error) {
        console.error('Upload error:', error);
        alert('Failed to upload files. Please try again.');
        resetButton();
    }
}

/**
 * Show progress view
 */
function showProgressView() {
    uploadSection.classList.add('hidden');
    progressSection.classList.remove('hidden');
    resultsSection.classList.add('hidden');

    // Reset agent statuses
    document.querySelectorAll('.agent-item').forEach(item => {
        item.classList.remove('active', 'completed');
        item.querySelector('.agent-status').textContent = '⏳';
    });
}

/**
 * Start polling for analysis status
 */
function startStatusPolling() {
    let completedAgents = new Set();

    statusPollingInterval = setInterval(async () => {
        try {
            const response = await fetch(`/api/status/${currentSessionId}`);

            if (!response.ok) {
                throw new Error('Status check failed');
            }

            const status = await response.json();

            // Update progress bar
            const progressBar = document.getElementById('progress-bar');
            const progressPercentage = document.getElementById('progress-percentage');
            progressBar.style.width = `${status.progress}%`;
            progressPercentage.textContent = `${status.progress}%`;

            // Update current agent
            const currentAgentEl = document.getElementById('current-agent');
            if (status.current_agent) {
                currentAgentEl.textContent = formatAgentName(status.current_agent);

                // Update agent list
                updateAgentList(status.current_agent, completedAgents);
            }

            // Check if completed
            if (status.status === 'completed') {
                clearInterval(statusPollingInterval);
                // Mark all agents as completed
                document.querySelectorAll('.agent-item').forEach(item => {
                    item.classList.remove('active');
                    item.classList.add('completed');
                    item.querySelector('.agent-status').textContent = '✅';
                });

                // Wait a moment then show results
                setTimeout(() => {
                    showResults(status.results);
                }, 1000);
            }

            // Check for error
            if (status.status === 'error') {
                clearInterval(statusPollingInterval);
                alert(`Analysis failed: ${status.error}`);
                resetAnalysis();
            }

        } catch (error) {
            console.error('Status polling error:', error);
        }
    }, 1000);
}

/**
 * Format agent name for display
 */
function formatAgentName(agentName) {
    const names = {
        'PaperParserAgent': 'Parsing Paper...',
        'ReproducibilityAgent': 'Checking Reproducibility...',
        'ExperimentEvidenceAgent': 'Mapping Experiments...',
        'StatisticalAuditorAgent': 'Auditing Statistics...',
        'RelatedWorkBaselineAgent': 'Analyzing Citations...',
        'ReviewerSimulationAgent': 'Simulating Reviews...',
        'VerdictAgent': 'Generating Verdict...'
    };
    return names[agentName] || agentName;
}

/**
 * Update agent list UI
 */
function updateAgentList(currentAgent, completedAgents) {
    const agentOrder = [
        'PaperParserAgent',
        'ReproducibilityAgent',
        'ExperimentEvidenceAgent',
        'StatisticalAuditorAgent',
        'RelatedWorkBaselineAgent',
        'ReviewerSimulationAgent',
        'VerdictAgent'
    ];

    const currentIndex = agentOrder.indexOf(currentAgent);

    document.querySelectorAll('.agent-item').forEach((item, index) => {
        const agentName = agentOrder[index];

        if (index < currentIndex) {
            item.classList.remove('active');
            item.classList.add('completed');
            item.querySelector('.agent-status').textContent = '✅';
            completedAgents.add(agentName);
        } else if (index === currentIndex) {
            item.classList.add('active');
            item.classList.remove('completed');
            item.querySelector('.agent-status').textContent = '🔄';
        } else {
            item.classList.remove('active', 'completed');
            item.querySelector('.agent-status').textContent = '⏳';
        }
    });
}

/**
 * Show results view
 */
function showResults(results) {
    uploadSection.classList.add('hidden');
    progressSection.classList.add('hidden');
    resultsSection.classList.remove('hidden');

    // Update verdict card
    updateVerdictCard(results.verdict);

    // Update critical issues
    updateCriticalIssues(results.verdict?.critical_issues || []);

    // Update action items
    updateActionItems(results.verdict?.action_items || []);

    // Update reviewer comments
    updateReviewerComments(results.reviewer_simulation?.comments || []);

    // Update paper analysis
    updatePaperAnalysis(results.paper_analysis);

    // Update reproducibility
    updateReproducibility(results.reproducibility);

    // Update related work
    updateRelatedWork(results.related_work);
}

/**
 * Update verdict card
 */
function updateVerdictCard(verdict) {
    const card = document.getElementById('verdict-card');
    const readiness = document.getElementById('verdict-readiness');
    const text = document.getElementById('verdict-text');
    const confidence = document.getElementById('confidence-score');
    const repro = document.getElementById('repro-score');

    // Set readiness text
    readiness.textContent = verdict?.submission_readiness || 'Unknown';
    text.textContent = verdict?.overall_verdict || 'Analysis complete.';

    // Set scores
    confidence.textContent = `${verdict?.confidence_score || 0}%`;
    repro.textContent = `${verdict?.reproducibility_score || 0}%`;

    // Set card style based on readiness
    card.classList.remove('ready', 'warning', 'critical');
    if (verdict?.submission_readiness?.includes('READY') && !verdict?.submission_readiness?.includes('NOT')) {
        card.classList.add('ready');
    } else if (verdict?.submission_readiness?.includes('ALMOST')) {
        card.classList.add('warning');
    } else {
        card.classList.add('critical');
    }
}

/**
 * Update critical issues list
 */
function updateCriticalIssues(issues) {
    const list = document.getElementById('critical-issues');

    if (issues.length === 0) {
        list.innerHTML = '<li style="border-left-color: var(--success);">No critical issues found! 🎉</li>';
        return;
    }

    list.innerHTML = issues.map(issue => `<li>${escapeHtml(issue)}</li>`).join('');
}

/**
 * Update action items list
 */
function updateActionItems(actions) {
    const list = document.getElementById('action-items');

    if (actions.length === 0) {
        list.innerHTML = '<li style="border-left-color: var(--success);">No actions required</li>';
        return;
    }

    list.innerHTML = actions.map(action => {
        const priority = action.priority || 'medium';
        const category = action.category || 'general';
        const effort = action.effort || 'medium';

        return `
            <li>
                <div class="action-item">
                    <div>${escapeHtml(action.action)}</div>
                    <div class="action-meta">
                        <span class="priority-badge ${priority}">${priority}</span>
                        <span class="category-badge">${category}</span>
                        <span class="category-badge">Effort: ${effort}</span>
                    </div>
                </div>
            </li>
        `;
    }).join('');
}

/**
 * Update reviewer comments
 */
function updateReviewerComments(comments) {
    const container = document.getElementById('reviewer-comments');

    if (comments.length === 0) {
        container.innerHTML = '<div class="comment"><div class="comment-text">No specific reviewer concerns identified.</div></div>';
        return;
    }

    container.innerHTML = comments.map(comment => `
        <div class="comment">
            <div class="comment-text">${escapeHtml(comment.comment)}</div>
            <div class="comment-meta">
                <span class="severity-badge ${comment.severity || 'moderate'}">${comment.severity || 'moderate'}</span>
                <span class="category-badge">${comment.category || 'general'}</span>
            </div>
        </div>
    `).join('');
}

/**
 * Update paper analysis section
 */
function updatePaperAnalysis(analysis) {
    document.getElementById('datasets').textContent =
        (analysis?.datasets || []).join(', ') || 'None detected';
    document.getElementById('metrics').textContent =
        (analysis?.metrics || []).join(', ') || 'None detected';
    document.getElementById('claims').textContent =
        (analysis?.claims || []).length + ' claims extracted';
}

/**
 * Update reproducibility section
 */
function updateReproducibility(repro) {
    const score = repro?.reproducibility_score || 0;
    const center = document.getElementById('repro-center');
    const circle = document.getElementById('repro-circle');
    const missingList = document.getElementById('missing-items');

    center.textContent = `${score}%`;

    // Animate circle
    const circumference = 2 * Math.PI * 45;
    const offset = circumference - (score / 100) * circumference;
    circle.style.strokeDashoffset = offset;

    // Update missing items
    const missing = repro?.missing_items || [];
    if (missing.length === 0) {
        missingList.innerHTML = '<li style="border-left-color: var(--success);">All reproducibility items covered!</li>';
    } else {
        missingList.innerHTML = missing.map(item => `<li>${escapeHtml(item)}</li>`).join('');
    }
}

/**
 * Update related work section
 */
function updateRelatedWork(related) {
    document.getElementById('citation-count').textContent = related?.citations_found || 0;

    const issuesList = document.getElementById('related-issues');
    const issues = related?.issues || [];

    if (issues.length === 0) {
        issuesList.innerHTML = '';
    } else {
        issuesList.innerHTML = `
            <ul class="issue-list" style="margin-top: 12px;">
                ${issues.map(issue => `<li style="border-left-color: var(--warning);">${escapeHtml(issue)}</li>`).join('')}
            </ul>
        `;
    }
}

/**
 * Reset analysis and show upload view
 */
function resetAnalysis() {
    // Clear interval if running
    if (statusPollingInterval) {
        clearInterval(statusPollingInterval);
        statusPollingInterval = null;
    }

    // Reset session
    currentSessionId = null;

    // Reset form
    uploadForm.reset();
    document.querySelectorAll('.file-name').forEach(el => el.textContent = '');

    // Reset button
    resetButton();

    // Show upload view
    uploadSection.classList.remove('hidden');
    progressSection.classList.add('hidden');
    resultsSection.classList.add('hidden');
}

/**
 * Reset analyze button
 */
function resetButton() {
    analyzeBtn.disabled = false;
    analyzeBtn.innerHTML = '<span class="btn-icon">🚀</span><span class="btn-text">Analyze Paper</span>';
}

/**
 * Escape HTML for safe display
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Make resetAnalysis globally available
window.resetAnalysis = resetAnalysis;
