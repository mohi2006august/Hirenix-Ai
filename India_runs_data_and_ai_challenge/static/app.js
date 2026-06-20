/**
 * HirenixAI — Dashboard Client-Side Application
 * Handles data fetching, rendering, search/filter, and candidate detail modal.
 */

// ── State ────────────────────────────────────────────────────────────────────
let allCandidates = [];
let statsData = {};
let currentFilter = 'all';
let searchQuery = '';
let currentSort = 'rank-asc';
let compareList = new Set();

// ── Init ─────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', async () => {
    await Promise.all([loadCandidates(), loadStats()]);
    setupSearch();
    setupFilters();
    setupModal();
    animateCounters();
    setupThemes();
    setupSorting();
    setupCompare();
});

// ── Data Loading ─────────────────────────────────────────────────────────────

async function loadCandidates() {
    try {
        const res = await fetch('/api/candidates');
        allCandidates = await res.json();
        renderCandidates(allCandidates);
    } catch (err) {
        document.getElementById('loading').innerHTML =
            '<div class="loading__text" style="color: #ef4444;">Failed to load candidates. Ensure the server is running.</div>';
    }
}

async function loadStats() {
    try {
        const res = await fetch('/api/stats');
        statsData = await res.json();
        renderScoreDistribution(statsData.score_distribution);
        renderSkillsCloud(statsData.top_skills);
        renderRoleDistribution(statsData.role_distribution);
    } catch (err) {
        console.error('Failed to load stats:', err);
    }
}

// ── Counter Animation ────────────────────────────────────────────────────────

function animateCounters() {
    const counters = document.querySelectorAll('.pipeline__stage-value[data-target]');
    counters.forEach((el, i) => {
        const target = parseInt(el.dataset.target);
        setTimeout(() => animateValue(el, 0, target, 1200), i * 250);
    });
}

function animateValue(el, start, end, duration) {
    const startTime = performance.now();
    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        // Ease out cubic
        const eased = 1 - Math.pow(1 - progress, 3);
        const current = Math.round(start + (end - start) * eased);
        el.textContent = current.toLocaleString();
        if (progress < 1) requestAnimationFrame(update);
    }
    requestAnimationFrame(update);
}

// ── Render Functions ─────────────────────────────────────────────────────────

function renderCandidates(candidates) {
    const grid = document.getElementById('candidates-grid');
    const loading = document.getElementById('loading');
    if (loading) loading.remove();

    const countEl = document.getElementById('results-count');
    countEl.innerHTML = `Showing <span>${candidates.length}</span> of <span>${allCandidates.length}</span> candidates`;

    if (candidates.length === 0) {
        grid.innerHTML = '<div class="loading"><div class="loading__text">No candidates match your search.</div></div>';
        return;
    }

    grid.innerHTML = candidates.map((c, i) => {
        const rankClass = c.rank <= 3 ? 'gold' : c.rank <= 10 ? 'silver' : c.rank <= 25 ? 'bronze' : 'default';
        const scoreClass = c.score >= 0.85 ? 'high' : c.score >= 0.75 ? 'mid' : 'low';
        const scorePercent = ((c.score / 1.0) * 100).toFixed(0);
        const skillsHtml = c.top_skills.slice(0, 3).map(s => `<span class="skill-pill">${s}</span>`).join('');

        const isChecked = compareList.has(c.candidate_id) ? 'checked' : '';
        return `
            <div class="candidate-row" data-id="${c.candidate_id}" style="animation-delay: ${i * 0.03}s">
                <div class="compare-checkbox-container" onclick="event.stopPropagation()">
                    <input type="checkbox" class="compare-checkbox" value="${c.candidate_id}" ${isChecked}>
                </div>
                <div class="rank-badge rank-badge--${rankClass}">${c.rank}</div>
                <div>
                    <div class="candidate-info__name">${c.name}</div>
                    <div class="candidate-info__title">${c.title}</div>
                    <div class="candidate-info__company">${c.company} · ${c.location}</div>
                </div>
                <div class="score-cell">
                    <div class="score-value">${c.score.toFixed(4)}</div>
                    <div class="score-bar">
                        <div class="score-bar__fill score-bar__fill--${scoreClass}" style="width: ${scorePercent}%"></div>
                    </div>
                </div>
                <div class="exp-cell">
                    <div class="exp-cell__years">${c.years_of_experience.toFixed(1)}</div>
                    <div style="font-size:10px;color:var(--text-tertiary)">years</div>
                </div>
                <div class="skill-pills">${skillsHtml}</div>
                <div class="row-arrow">→</div>
            </div>
        `;
    }).join('');

    // Add click handlers
    grid.querySelectorAll('.candidate-row').forEach(row => {
        row.addEventListener('click', () => openModal(row.dataset.id));
    });

    // Add checkbox handlers
    grid.querySelectorAll('.compare-checkbox').forEach(cb => {
        cb.addEventListener('click', (e) => e.stopPropagation());
        cb.addEventListener('change', (e) => {
            e.stopPropagation();
            const id = e.target.value;
            if (e.target.checked) compareList.add(id);
            else compareList.delete(id);
            updateCompareDrawer();
        });
    });
}

function renderScoreDistribution(dist) {
    const container = document.getElementById('score-distribution');
    const maxVal = Math.max(...Object.values(dist));

    container.innerHTML = Object.entries(dist).map(([label, count]) => {
        const pct = maxVal > 0 ? (count / maxVal) * 100 : 0;
        return `
            <div class="chart-bar-row">
                <div class="chart-bar-label">${label}</div>
                <div class="chart-bar-track">
                    <div class="chart-bar-fill" style="width: ${pct}%" data-count="${count}"></div>
                </div>
            </div>
        `;
    }).join('');
}

function renderSkillsCloud(skills) {
    const container = document.getElementById('skills-cloud');
    container.innerHTML = skills.map(([name, count]) =>
        `<span class="skill-cloud__tag">${name}<span class="count">${count}</span></span>`
    ).join('');
}

function renderRoleDistribution(roles) {
    const container = document.getElementById('role-distribution');
    const sorted = Object.entries(roles).sort((a, b) => b[1] - a[1]);
    container.innerHTML = sorted.map(([name, count]) =>
        `<div class="role-item">
            <span class="role-item__name">${name}</span>
            <span class="role-item__count">${count}</span>
        </div>`
    ).join('');
}

// ── Search & Filter ──────────────────────────────────────────────────────────

function setupSearch() {
    const input = document.getElementById('search-input');
    let debounceTimer;

    input.addEventListener('input', () => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
            searchQuery = input.value.toLowerCase().trim();
            applyFilters();
        }, 200);
    });
}

function setupFilters() {
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentFilter = btn.dataset.filter;
            applyFilters();
        });
    });
}

function applyFilters() {
    let filtered = allCandidates;

    if (currentFilter !== 'all') {
        filtered = filtered.filter(c => c.role_category === currentFilter);
    }

    if (searchQuery) {
        filtered = filtered.filter(c => {
            const haystack = [
                c.name, c.title, c.company, c.candidate_id, c.location,
                ...c.top_skills
            ].join(' ').toLowerCase();
            return haystack.includes(searchQuery);
        });
    }

    filtered.sort((a, b) => {
        switch (currentSort) {
            case 'rank-asc': return a.rank - b.rank;
            case 'score-desc': return b.score - a.score;
            case 'exp-desc': return b.years_of_experience - a.years_of_experience;
            case 'notice-asc': return (a.notice_period_days || 999) - (b.notice_period_days || 999);
            case 'name-asc': return a.name.localeCompare(b.name);
            default: return a.rank - b.rank;
        }
    });

    renderCandidates(filtered);
}

// ── Modal ────────────────────────────────────────────────────────────────────

function setupModal() {
    const overlay = document.getElementById('modal-overlay');
    const closeBtn = document.getElementById('modal-close');

    closeBtn.addEventListener('click', closeModal);
    overlay.addEventListener('click', (e) => {
        if (e.target === overlay) closeModal();
    });

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') closeModal();
    });

    // Tab switching
    document.querySelectorAll('.modal__tab').forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelectorAll('.modal__tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
            tab.classList.add('active');
            document.getElementById(`tab-${tab.dataset.tab}`).classList.add('active');
        });
    });
}

async function openModal(candidateId) {
    const overlay = document.getElementById('modal-overlay');
    overlay.classList.add('active');
    document.body.style.overflow = 'hidden';

    // Reset to first tab
    document.querySelectorAll('.modal__tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
    document.querySelector('.modal__tab[data-tab="why"]').classList.add('active');
    document.getElementById('tab-why').classList.add('active');

    // Show loading
    document.getElementById('tab-why').innerHTML = '<div class="loading"><div class="loading__spinner"></div></div>';

    try {
        const res = await fetch(`/api/candidates/${candidateId}`);
        const data = await res.json();
        renderModal(data);
    } catch (err) {
        document.getElementById('tab-why').innerHTML =
            '<div class="loading__text" style="color:#ef4444;">Failed to load candidate details.</div>';
    }
}

function closeModal() {
    document.getElementById('modal-overlay').classList.remove('active');
    document.body.style.overflow = '';
}

function renderModal(data) {
    const p = data.profile;
    const why = data.why_selected || {};
    const sb = why.score_breakdown || {};

    // Header
    const rankClass = data.rank <= 3 ? 'gold' : data.rank <= 10 ? 'silver' : data.rank <= 25 ? 'bronze' : 'default';
    document.getElementById('modal-rank').className = `rank-badge rank-badge--${rankClass}`;
    document.getElementById('modal-rank').textContent = `#${data.rank}`;
    document.getElementById('modal-name').textContent = p.name;
    document.getElementById('modal-headline').textContent = p.headline;
    document.getElementById('modal-meta').innerHTML = `
        <span class="modal__meta-item">📍 ${p.location}, ${p.country}</span>
        <span class="modal__meta-item">🏢 ${p.current_company} (${p.current_company_size})</span>
        <span class="modal__meta-item">📅 ${p.years_of_experience.toFixed(1)} yrs experience</span>
        <span class="modal__meta-item">🏷️ ${data.role_category}</span>
    `;

    // ── Tab: Why Selected ──
    const scoreColor = data.score >= 0.85 ? 'good' : data.score >= 0.75 ? 'warn' : 'bad';
    const expColor = sb.experience_fit === 'perfect' ? 'good' : sb.experience_fit === 'over-qualified' ? 'warn' : 'bad';
    const availColor = sb.availability === 'Immediate' || sb.availability === 'Short' ? 'good' : sb.availability === 'Standard' ? 'warn' : 'bad';

    document.getElementById('tab-why').innerHTML = `
        <div class="score-breakdown">
            <div class="breakdown-item">
                <div class="breakdown-item__label">Semantic Fit Score</div>
                <div class="breakdown-item__value breakdown-item__value--${scoreColor}">${data.score.toFixed(4)}</div>
            </div>
            <div class="breakdown-item">
                <div class="breakdown-item__label">Experience Fit</div>
                <div class="breakdown-item__value breakdown-item__value--${expColor}">${sb.experience_fit || 'N/A'} (${sb.years_of_experience || 0} yrs)</div>
            </div>
            <div class="breakdown-item">
                <div class="breakdown-item__label">JD Skill Matches</div>
                <div class="breakdown-item__value">${sb.matched_jd_skills || 0} skills</div>
            </div>
            <div class="breakdown-item">
                <div class="breakdown-item__label">Availability</div>
                <div class="breakdown-item__value breakdown-item__value--${availColor}">${sb.availability || 'N/A'} (${sb.notice_period_days || 0}d)</div>
            </div>
        </div>

        <div class="why-section">
            <div class="why-section__title"><span class="icon">✅</span> Strengths</div>
            ${(why.strengths || []).map(s => `
                <div class="strength-item"><span class="bullet">●</span> ${s}</div>
            `).join('')}
        </div>

        <div class="why-section">
            <div class="why-section__title"><span class="icon">⚠️</span> Potential Concerns</div>
            ${(why.concerns || []).map(c => `
                <div class="concern-item"><span class="bullet">●</span> ${c}</div>
            `).join('')}
        </div>

        <div class="why-section">
            <div class="why-section__title"><span class="icon">🎯</span> Key Expert Skills</div>
            <div class="skills-grid">
                ${(why.key_skills || []).map(s => `
                    <span class="skill-tag skill-tag--advanced">${s.name} · ${s.months}mo</span>
                `).join('')}
            </div>
        </div>

        <div class="summary-text">
            <strong>AI Reasoning:</strong> ${data.reasoning}
        </div>
    `;

    // ── Tab: Full Profile ──
    const allSkills = (data.skills || []).sort((a, b) => {
        const order = { expert: 0, advanced: 1, intermediate: 2, beginner: 3 };
        return (order[a.proficiency] || 4) - (order[b.proficiency] || 4);
    });

    document.getElementById('tab-profile').innerHTML = `
        <div class="summary-text">${p.summary || 'No summary available.'}</div>

        <div class="why-section">
            <div class="why-section__title"><span class="icon">🛠️</span> All Skills</div>
            <div class="skills-grid">
                ${allSkills.map(s => `
                    <span class="skill-tag skill-tag--${s.proficiency}">${s.name} <span style="opacity:0.6;font-size:10px">${s.proficiency}</span></span>
                `).join('')}
            </div>
        </div>

        ${data.education && data.education.length > 0 ? `
        <div class="why-section" style="margin-top:24px;">
            <div class="why-section__title"><span class="icon">🎓</span> Education</div>
            ${data.education.map(e => `
                <div style="padding:12px 16px; background:rgba(255,255,255,0.02); border:1px solid rgba(255,255,255,0.06); border-radius:8px; margin-bottom:8px;">
                    <div style="font-size:14px; font-weight:600; color:var(--text-primary);">${e.degree} in ${e.field_of_study}</div>
                    <div style="font-size:12px; color:var(--text-secondary); margin-top:2px;">${e.institution}</div>
                    <div style="font-size:11px; color:var(--text-tertiary); margin-top:4px;">${e.tier ? e.tier.replace('_', ' ').toUpperCase() : ''} ${e.grade ? '· ' + e.grade : ''}</div>
                </div>
            `).join('')}
        </div>
        ` : ''}
    `;

    // ── Tab: Career History ──
    document.getElementById('tab-career').innerHTML = `
        <div class="timeline">
            ${(data.career_history || []).map(j => `
                <div class="timeline__item ${j.is_current ? 'timeline__item--current' : ''}">
                    <div class="timeline__title">${j.title} ${j.is_current ? '<span class="badge badge--green">Current</span>' : ''}</div>
                    <div class="timeline__company">${j.company} · ${j.industry || ''}</div>
                    <div class="timeline__dates">${j.start_date || ''} → ${j.end_date || 'Present'} · ${j.duration_months} months</div>
                    ${j.description ? `<div class="timeline__desc">${j.description}</div>` : ''}
                </div>
            `).join('')}
        </div>
    `;

    // ── Tab: Behavioral Signals ──
    const sig = data.signals || {};
    document.getElementById('tab-signals').innerHTML = `
        <div class="signals-grid">
            ${renderGauge('Response Rate', (sig.recruiter_response_rate * 100).toFixed(0) + '%', sig.recruiter_response_rate * 100)}
            ${renderGauge('Interview Rate', (sig.interview_completion_rate * 100).toFixed(0) + '%', sig.interview_completion_rate * 100)}
            ${renderGauge('GitHub Score', sig.github_activity?.toFixed(1) || '0', (sig.github_activity || 0) * 10)}
            ${renderGauge('Profile Score', sig.profile_completeness?.toFixed(0) + '%' || '0', sig.profile_completeness || 0)}
            ${renderGauge('Notice Period', sig.notice_period_days + 'd', Math.max(0, 100 - sig.notice_period_days))}
            ${renderGauge('Offer Accept', (sig.offer_acceptance_rate * 100).toFixed(0) + '%', sig.offer_acceptance_rate * 100)}
            ${renderGauge('Profile Views', sig.profile_views_30d || 0, Math.min(100, (sig.profile_views_30d || 0) * 2))}
            ${renderGauge('Saved by Recruiters', sig.saved_by_recruiters_30d || 0, Math.min(100, (sig.saved_by_recruiters_30d || 0) * 10))}
        </div>

        <div style="margin-top:24px;">
            <div class="why-section__title"><span class="icon">📋</span> Additional Info</div>
            <div class="score-breakdown">
                <div class="breakdown-item">
                    <div class="breakdown-item__label">Open to Work</div>
                    <div class="breakdown-item__value ${sig.open_to_work ? 'breakdown-item__value--good' : ''}">${sig.open_to_work ? '✓ Yes' : '✗ No'}</div>
                </div>
                <div class="breakdown-item">
                    <div class="breakdown-item__label">Work Mode</div>
                    <div class="breakdown-item__value">${sig.preferred_work_mode || 'N/A'}</div>
                </div>
                <div class="breakdown-item">
                    <div class="breakdown-item__label">Willing to Relocate</div>
                    <div class="breakdown-item__value">${sig.willing_to_relocate ? '✓ Yes' : '✗ No'}</div>
                </div>
                <div class="breakdown-item">
                    <div class="breakdown-item__label">Expected Salary</div>
                    <div class="breakdown-item__value">${sig.expected_salary ? sig.expected_salary.min + ' – ' + sig.expected_salary.max + ' LPA' : 'N/A'}</div>
                </div>
            </div>
        </div>

        ${sig.skill_assessments && Object.keys(sig.skill_assessments).length > 0 ? `
        <div style="margin-top:20px;">
            <div class="why-section__title"><span class="icon">📊</span> Skill Assessment Scores</div>
            ${Object.entries(sig.skill_assessments).map(([skill, score]) => `
                <div class="chart-bar-row">
                    <div class="chart-bar-label">${skill}</div>
                    <div class="chart-bar-track">
                        <div class="chart-bar-fill" style="width:${score}%; background:${score >= 70 ? 'var(--gradient-score-high)' : score >= 40 ? 'var(--gradient-score-mid)' : 'var(--gradient-score-low)'}" data-count="${score.toFixed(0)}"></div>
                    </div>
                </div>
            `).join('')}
        </div>
        ` : ''}
    `;

    // ── Tab: Competitors ──
    const competitors = data.competitors || [];
    document.getElementById('tab-competitors').innerHTML = `
        <div style="margin-bottom:16px;">
            <div class="why-section__title"><span class="icon">🏆</span> Competing for: ${data.role_category}</div>
            <p style="font-size:13px; color:var(--text-secondary); margin-bottom:16px;">
                ${competitors.length} other candidates ranked for the same role category.
                This candidate is ranked <strong>#${data.rank}</strong> overall with a score of <strong>${data.score.toFixed(4)}</strong>.
            </p>
        </div>

        ${competitors.length === 0 ? '<div class="loading__text">No other candidates in this role category.</div>' :
        competitors.map(comp => {
            const compScoreColor = comp.score >= data.score ? 'var(--accent-emerald)' : 'var(--text-secondary)';
            return `
                <div class="competitor-card" onclick="closeModal(); setTimeout(() => openModal('${comp.candidate_id}'), 300);">
                    <div class="competitor-card__rank">#${comp.rank}</div>
                    <div>
                        <div class="competitor-card__name">${comp.name}</div>
                        <div class="competitor-card__title">${comp.title} · ${comp.years_of_experience.toFixed(1)} yrs</div>
                        <div class="skill-pills" style="margin-top:4px;">
                            ${comp.top_skills.map(s => `<span class="skill-pill">${s}</span>`).join('')}
                        </div>
                    </div>
                    <div class="competitor-card__score" style="color:${compScoreColor}">${comp.score.toFixed(4)}</div>
                </div>
            `;
        }).join('')}
    `;
}

function renderGauge(label, value, fillPct) {
    const color = fillPct >= 70 ? 'var(--accent-emerald)' : fillPct >= 40 ? 'var(--accent-indigo)' : 'var(--accent-amber)';
    return `
        <div class="signal-gauge">
            <div class="signal-gauge__label">${label}</div>
            <div class="signal-gauge__value">${value}</div>
            <div class="signal-gauge__bar">
                <div class="signal-gauge__bar-fill" style="width:${Math.min(fillPct, 100)}%; background:${color}"></div>
            </div>
        </div>
    `;
}

// ── Theme Customizer ─────────────────────────────────────────────────────────
function setupThemes() {
    const swatches = document.querySelectorAll('.theme-swatch');
    swatches.forEach(swatch => {
        swatch.addEventListener('click', () => {
            swatches.forEach(s => s.classList.remove('active'));
            swatch.classList.add('active');
            const theme = swatch.dataset.theme;
            document.body.className = `theme-${theme}`;
        });
    });
}

// ── Sorting ──────────────────────────────────────────────────────────────────
function setupSorting() {
    const sortSelect = document.getElementById('sort-select');
    if(sortSelect) {
        sortSelect.addEventListener('change', (e) => {
            currentSort = e.target.value;
            applyFilters();
        });
    }
}

// ── Candidate Comparison ─────────────────────────────────────────────────────
function setupCompare() {
    const clearBtn = document.getElementById('compare-clear');
    const compareBtn = document.getElementById('compare-trigger');
    
    if(clearBtn) {
        clearBtn.addEventListener('click', () => {
            compareList.clear();
            applyFilters(); // re-render checkboxes
            updateCompareDrawer();
        });
    }
    
    if(compareBtn) {
        compareBtn.addEventListener('click', openCompareModal);
    }
}

function updateCompareDrawer() {
    const drawer = document.getElementById('compare-drawer');
    const countEl = document.getElementById('compare-count');
    if (!drawer) return;
    
    if (compareList.size > 0) {
        countEl.textContent = compareList.size;
        drawer.classList.add('active');
    } else {
        drawer.classList.remove('active');
    }
}

async function openCompareModal() {
    if (compareList.size === 0) return;
    
    const overlay = document.getElementById('modal-overlay');
    overlay.classList.add('active');
    document.body.style.overflow = 'hidden';
    
    document.querySelectorAll('.modal__tab').forEach(t => t.style.display = 'none');
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
    
    const panel = document.getElementById('tab-why');
    panel.classList.add('active');
    panel.innerHTML = '<div class="loading"><div class="loading__spinner"></div></div>';
    
    document.getElementById('modal-rank').style.display = 'none';
    document.getElementById('modal-name').textContent = 'Candidate Comparison';
    document.getElementById('modal-headline').textContent = `Comparing ${compareList.size} candidates`;
    document.getElementById('modal-meta').innerHTML = '';
    
    try {
        const candidatesToCompare = [];
        for (const id of compareList) {
            const res = await fetch(`/api/candidates/${id}`);
            candidatesToCompare.push(await res.json());
        }
        
        renderCompareMatrix(candidatesToCompare);
    } catch (err) {
        panel.innerHTML = '<div class="loading__text" style="color:#ef4444;">Failed to load comparison data.</div>';
    }
}

function renderCompareMatrix(candidates) {
    const panel = document.getElementById('tab-why');
    
    const rows = [
        { label: '', render: c => `
            <div class="compare-card-header">
                <div class="rank-badge rank-badge--${c.rank <= 3 ? 'gold' : c.rank <= 10 ? 'silver' : 'default'}">#${c.rank}</div>
                <div class="name">${c.profile?.name || 'Unknown'}</div>
                <div class="title">${c.profile?.headline || ''}</div>
                <div style="font-size:12px; color:var(--text-tertiary)">${c.profile?.location || ''}</div>
            </div>
        ` },
        { label: 'Semantic Match', render: c => `<div class="compare-score-large">${(c.score || 0).toFixed(4)}</div>` },
        { label: 'Experience', render: c => `<strong>${(c.profile?.years_of_experience || 0).toFixed(1)} yrs</strong><br><span style="font-size:12px; color:var(--text-tertiary)">${c.why_selected?.score_breakdown?.experience_fit || ''}</span>` },
        { label: 'Availability', render: c => `<strong>${c.why_selected?.score_breakdown?.availability || 'N/A'}</strong><br><span style="font-size:12px; color:var(--text-tertiary)">${c.why_selected?.score_breakdown?.notice_period_days || 0} days</span>` },
        { label: 'Top Skills', render: c => `
            <div class="skill-cloud" style="gap:4px">
                ${(c.profile?.top_skills || []).slice(0, 5).map(s => `<span class="skill-cloud__tag">${s}</span>`).join('')}
            </div>
        ` },
        { label: 'Strengths', render: c => `
            <ul style="padding-left:16px; margin:0; font-size:13px; color:var(--text-secondary)">
                ${(c.why_selected?.strengths || []).map(s => `<li style="margin-bottom:4px">${s}</li>`).join('')}
            </ul>
        ` },
        { label: 'Concerns', render: c => `
            <ul style="padding-left:16px; margin:0; font-size:13px; color:var(--text-secondary)">
                ${(c.why_selected?.concerns || []).map(s => `<li style="margin-bottom:4px">${s}</li>`).join('')}
            </ul>
        ` }
    ];
    
    let html = `
        <div class="modal__body--compare">
            <table class="compare-table">
                <thead>
                    <tr>
                        <th style="width:150px">Metric</th>
                        ${candidates.map(c => `<th class="compare-column-header"></th>`).join('')}
                    </tr>
                </thead>
                <tbody>
                    ${rows.map(row => `
                        <tr>
                            <td style="font-weight:600; color:var(--text-secondary)">${row.label}</td>
                            ${candidates.map(c => `<td>${row.render(c)}</td>`).join('')}
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        </div>
    `;
    
    panel.innerHTML = html;
    
    // Restore tabs logic on modal close
    const overlay = document.getElementById('modal-overlay');
    const closeHandler = () => {
        document.querySelectorAll('.modal__tab').forEach(t => t.style.display = 'inline-block');
        document.getElementById('modal-rank').style.display = 'flex';
        overlay.removeEventListener('click', closeHandler);
    };
    overlay.addEventListener('click', closeHandler);
    document.getElementById('modal-close').addEventListener('click', closeHandler, { once: true });
}
