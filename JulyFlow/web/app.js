/* ══════════════════════════════════════════════════════════════════════
   JulyFlow — Frontend Application Controller
   Quản lý toàn bộ giao diện, âm thanh, phím tắt, thuật toán SRS và AI Hub
   ══════════════════════════════════════════════════════════════════════ */

// ── STATE ──
let currentTab = 'dashboard';
let currentFcList = [];
let currentFcIndex = 0;
let isFcFlipped = false;
let currentPracticeWords = [];
let currentPracticeIndex = 0;
let practiceStreak = 0;
let practiceBestStreak = 0;
let currentPracticeAnswer = '';
let currentPracticeWordObj = null;

// ── INITIALIZATION ──
document.addEventListener('DOMContentLoaded', () => {
  setupKeyboardShortcuts();
  refreshHeaderStats();
  loadDashboard();
  loadTopicsFilter();
});

// ── NAVIGATION & TAB SWITCHING ──
function switchTab(tabId) {
  currentTab = tabId;

  document.querySelectorAll('.nav-btn').forEach(btn => {
    btn.classList.toggle('active', btn.getAttribute('data-tab') === tabId);
  });

  document.querySelectorAll('.tab-panel').forEach(panel => {
    panel.classList.remove('active');
  });

  const activePanel = document.getElementById(`tab-${tabId}`);
  if (activePanel) {
    activePanel.classList.add('active');
  }

  // Load data tương ứng khi mở tab
  if (tabId === 'dashboard') loadDashboard();
  if (tabId === 'flashcards') loadFlashcardSession('due');
  if (tabId === 'vocabulary') loadVocabularyTable();
  if (tabId === 'analytics') loadAnalyticsTab();
}

function showToast(message, isError = false) {
  const toast = document.getElementById('toast');
  toast.textContent = message;
  toast.style.borderColor = isError ? 'var(--tn-magenta)' : 'var(--tn-blue)';
  toast.style.display = 'block';
  setTimeout(() => {
    toast.style.display = 'none';
  }, 2800);
}

// ── HEADER & STATS ──
async function refreshHeaderStats() {
  try {
    const res = await fetch('/api/stats/summary');
    const data = await res.json();

    document.getElementById('header-streak').textContent = `${data.streak_days || 0} ngày`;
    document.getElementById('header-due').textContent = `${data.due_words || 0} cần ôn`;
    document.getElementById('header-total').textContent = `${data.total_words || 0} từ`;
    
    // Update dashboard cards if visible
    const statTotal = document.getElementById('stat-total');
    if (statTotal) {
      statTotal.textContent = data.total_words || 0;
      document.getElementById('stat-due').textContent = data.due_words || 0;
      document.getElementById('stat-streak').textContent = `${data.streak_days || 0} ngày`;
      document.getElementById('stat-mastered').textContent = data.mastered_words || 0;
      document.getElementById('stat-accuracy').textContent = `Độ chính xác: ${data.accuracy || 0}%`;
    }
  } catch (err) {
    console.error('Failed to load header stats:', err);
  }
}

// ── DASHBOARD ──
async function loadDashboard() {
  await refreshHeaderStats();
  loadWeeklyChart();
  loadWeakWordsDashboard();
}

async function loadWeeklyChart() {
  try {
    const res = await fetch('/api/stats/weekly');
    const days = await res.json();
    const container = document.getElementById('weekly-chart');
    container.innerHTML = '';

    const maxTotal = Math.max(...days.map(d => d.correct + d.wrong), 1);

    days.forEach(d => {
      const col = document.createElement('div');
      col.style.cssText = 'flex: 1; display: flex; flex-direction: column; align-items: center; height: 100%; justify-content: flex-end;';

      const total = d.correct + d.wrong;
      const heightPct = Math.max(10, Math.round((total / maxTotal) * 100));

      const bar = document.createElement('div');
      bar.style.cssText = `width: 24px; height: ${heightPct}%; background: linear-gradient(to top, var(--tn-green) ${Math.round((d.correct/Math.max(1, total))*100)}%, var(--tn-magenta) 0%); border-radius: 4px; position: relative; transition: height 0.5s ease;`;
      bar.title = `${d.label}: ✅ ${d.correct} đúng, ❌ ${d.wrong} sai`;

      const label = document.createElement('span');
      label.style.cssText = 'font-size: 11px; color: var(--text-dim); margin-top: 6px;';
      label.textContent = d.label;

      col.appendChild(bar);
      col.appendChild(label);
      container.appendChild(col);
    });
  } catch (err) {
    console.error('Failed to load weekly chart:', err);
  }
}

async function loadWeakWordsDashboard() {
  try {
    const res = await fetch('/api/vocabulary/weak?limit=5');
    const words = await res.json();
    const container = document.getElementById('dash-weak-list');
    container.innerHTML = '';

    if (!words || words.length === 0) {
      container.innerHTML = '<div style="font-size: 12px; color: var(--text-muted); padding: 10px 0;">Tuyệt vời! Hiện tại bạn không có từ vựng nào bị sai nhiều. 💪</div>';
      return;
    }

    words.forEach(w => {
      const row = document.createElement('div');
      row.style.cssText = 'display: flex; justify-content: space-between; align-items: center; padding: 8px 12px; background: var(--bg-night); border-radius: 8px; margin-bottom: 6px;';
      row.innerHTML = `
        <div>
          <span style="font-weight: 700; color: #fff; margin-right: 8px;">${escapeHtml(w.word)}</span>
          <span style="font-size: 11px; color: var(--tn-cyan); margin-right: 8px;">(${escapeHtml(w.word_type || '')})</span>
          <span style="font-size: 12px; color: var(--text-muted);">${escapeHtml(w.definition_vi || '')}</span>
        </div>
        <div>
          <span style="font-size: 11px; color: var(--tn-magenta); font-weight: 700; margin-right: 10px;">❌ Sai ${w.times_wrong} lần</span>
          <button class="btn btn-secondary" style="padding: 2px 8px; font-size: 11px;" onclick="speakText('${escapeJs(w.word)}')">🔊</button>
        </div>
      `;
      container.appendChild(row);
    });
  } catch (err) {
    console.error('Failed to load weak words:', err);
  }
}

// ── FLASHCARDS (SRS SM-2) ──
function startFlashcardReview() {
  switchTab('flashcards');
}

async function loadFlashcardSession(mode = 'due') {
  try {
    let url = '/api/vocabulary/due?limit=50';
    if (mode === 'new') url = '/api/vocabulary/new?limit=25';
    if (mode === 'all') url = '/api/vocabulary?sort_by=due_first';

    const res = await fetch(url);
    currentFcList = await res.json();
    currentFcIndex = 0;
    isFcFlipped = false;

    if (!currentFcList || currentFcList.length === 0) {
      document.getElementById('fc-word').textContent = '🎉 Hoàn thành!';
      document.getElementById('fc-ipa').textContent = 'Không còn từ nào cần ôn lúc này.';
      document.getElementById('fc-meaning').textContent = 'Bạn đã hoàn tất tất cả các mục.';
      document.getElementById('fc-meaning-en').textContent = '';
      document.getElementById('fc-example').textContent = '';
      document.getElementById('fc-progress').textContent = '0 / 0';
      return;
    }

    displayCurrentFlashcard();
  } catch (err) {
    console.error('Failed to load flashcard session:', err);
  }
}

function displayCurrentFlashcard() {
  if (currentFcIndex >= currentFcList.length) {
    showToast('🎉 Bạn đã hoàn thành phiên ôn tập flashcards!');
    loadFlashcardSession('due');
    return;
  }

  const word = currentFcList[currentFcIndex];
  isFcFlipped = false;
  const card = document.getElementById('flashcard');
  card.classList.remove('flipped');

  // Front
  document.getElementById('fc-word').textContent = word.word;
  document.getElementById('fc-ipa').textContent = word.pronunciation || '/.../';
  document.getElementById('fc-type').textContent = word.word_type || 'vocab';
  document.getElementById('fc-progress').textContent = `${currentFcIndex + 1} / ${currentFcList.length}`;

  // Back
  document.getElementById('fc-meaning').textContent = word.definition_vi || '(Chưa có nghĩa)';
  document.getElementById('fc-meaning-en').textContent = word.definition_en || '';
  
  const ex = word.example ? `📖 ${word.example}` : 'Chưa có ví dụ';
  const exTr = word.example_translation ? `\n🇻🇳 ${word.example_translation}` : '';
  document.getElementById('fc-example').textContent = ex + exTr;
  document.getElementById('fc-context-tag').textContent = word.usage_context || 'General Context';
}

function flipFlashcard() {
  const card = document.getElementById('flashcard');
  isFcFlipped = !isFcFlipped;
  card.classList.toggle('flipped', isFcFlipped);
}

async function rateFlashcard(quality) {
  if (currentFcIndex >= currentFcList.length) return;
  const word = currentFcList[currentFcIndex];

  try {
    await fetch('/api/srs/rate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: jsonBody({
        vocab_id: word.id,
        quality: quality,
        response_time_ms: 2000
      })
    });

    currentFcIndex++;
    displayCurrentFlashcard();
    refreshHeaderStats();
  } catch (err) {
    console.error('Failed to rate flashcard:', err);
  }
}

function speakCurrentWord() {
  if (currentFcList && currentFcList[currentFcIndex]) {
    speakText(currentFcList[currentFcIndex].word);
  }
}

// ── PRACTICE & TEST MODE ──
async function startPracticeSession() {
  const mode = document.getElementById('pr-mode-select').value;
  const count = parseInt(document.getElementById('pr-count-select').value, 10);

  let url = `/api/vocabulary?sort_by=due_first`;
  if (mode === 'mistakes') {
    url = `/api/vocabulary/weak?limit=${count}`;
  }

  try {
    const res = await fetch(url);
    const list = await res.json();
    if (!list || list.length === 0) {
      showToast('Không có đủ từ để tạo bài kiểm tra. Hãy thêm từ vựng trước!', true);
      return;
    }

    currentPracticeWords = list.slice(0, count);
    currentPracticeIndex = 0;
    practiceStreak = 0;

    document.getElementById('practice-setup').style.display = 'none';
    document.getElementById('practice-play').style.display = 'block';

    displayPracticeQuestion(mode);
  } catch (err) {
    console.error('Failed to start practice:', err);
  }
}

function displayPracticeQuestion(mode) {
  if (currentPracticeIndex >= currentPracticeWords.length) {
    showToast(`🎉 Hoàn thành bài kiểm tra! Chuỗi tốt nhất: ${practiceBestStreak}`);
    quitPracticeSession();
    return;
  }

  const w = currentPracticeWords[currentPracticeIndex];
  currentPracticeWordObj = w;
  currentPracticeAnswer = w.word.trim();

  document.getElementById('pr-progress').textContent = `Câu ${currentPracticeIndex + 1} / ${currentPracticeWords.length}`;
  document.getElementById('pr-streak').textContent = `🔥 ${practiceStreak} chuỗi`;
  document.getElementById('pr-feedback').textContent = '';
  document.getElementById('pr-feedback').style.color = '';

  const typingArea = document.getElementById('pr-typing-area');
  const mcArea = document.getElementById('pr-mc-area');

  if (mode === 'multiple_choice') {
    typingArea.style.display = 'none';
    mcArea.style.display = 'grid';
    setupMultipleChoice(w);
  } else if (mode === 'fill_blank') {
    typingArea.style.display = 'block';
    mcArea.style.display = 'none';

    document.getElementById('pr-prompt-label').textContent = 'Điền từ còn thiếu vào câu';
    const regex = new RegExp(`\\b${escapeRegExp(w.word)}\\b`, 'gi');
    const maskedSentence = w.example ? w.example.replace(regex, '________') : `________: ${w.definition_vi}`;
    document.getElementById('pr-question').textContent = maskedSentence;
    document.getElementById('pr-sub-question').textContent = `Gợi ý: (${w.word_type || 'vocab'}) — ${w.definition_vi}`;

    const input = document.getElementById('pr-input');
    input.value = '';
    input.focus();
  } else {
    // Typing mode default
    typingArea.style.display = 'block';
    mcArea.style.display = 'none';

    document.getElementById('pr-prompt-label').textContent = 'Gõ từ tiếng Anh tương ứng';
    document.getElementById('pr-question').textContent = w.definition_vi || w.word;
    document.getElementById('pr-sub-question').textContent = `Loại từ: (${w.word_type || 'vocab'}) ${w.usage_context ? '• Ngữ cảnh: ' + w.usage_context : ''}`;

    const input = document.getElementById('pr-input');
    input.value = '';
    input.focus();
  }
}

function setupMultipleChoice(targetWord) {
  document.getElementById('pr-prompt-label').textContent = 'Chọn đáp án tiếng Anh chính xác';
  document.getElementById('pr-question').textContent = targetWord.definition_vi;
  document.getElementById('pr-sub-question').textContent = `Loại từ: (${targetWord.word_type || 'vocab'})`;

  // Lấy 3 đáp án sai ngẫu nhiên
  const otherWords = currentPracticeWords.filter(w => w.word !== targetWord.word);
  const shuffledOthers = otherWords.sort(() => 0.5 - Math.random()).slice(0, 3);
  const choices = [targetWord, ...shuffledOthers].sort(() => 0.5 - Math.random());

  const container = document.getElementById('pr-mc-area');
  container.innerHTML = '';

  choices.forEach(c => {
    const btn = document.createElement('button');
    btn.className = 'mc-option';
    btn.textContent = c.word;
    btn.onclick = () => handlePracticeChoice(btn, c.word === targetWord.word);
    container.appendChild(btn);
  });
}

function handlePracticeChoice(btn, isCorrect) {
  const fb = document.getElementById('pr-feedback');
  if (isCorrect) {
    btn.classList.add('correct');
    fb.textContent = '✔ Chính xác!';
    fb.style.color = 'var(--tn-green)';
    practiceStreak++;
    if (practiceStreak > practiceBestStreak) practiceBestStreak = practiceStreak;
    speakText(currentPracticeAnswer);
    setTimeout(() => {
      currentPracticeIndex++;
      displayPracticeQuestion(document.getElementById('pr-mode-select').value);
    }, 1200);
  } else {
    btn.classList.add('wrong');
    fb.textContent = `✘ Sai! Đáp án đúng là: ${currentPracticeAnswer}`;
    fb.style.color = 'var(--tn-magenta)';
    practiceStreak = 0;
    // Rate quality 0 in background
    ratePracticeFail();
    setTimeout(() => {
      currentPracticeIndex++;
      displayPracticeQuestion(document.getElementById('pr-mode-select').value);
    }, 2200);
  }
}

function submitPracticeAnswer() {
  const input = document.getElementById('pr-input');
  const userVal = input.value.trim().toLowerCase();
  const correctVal = currentPracticeAnswer.toLowerCase();
  const fb = document.getElementById('pr-feedback');

  if (!userVal) return;

  if (userVal === correctVal) {
    fb.textContent = '✔ Hoàn hảo! Bạn đã gõ đúng từ.';
    fb.style.color = 'var(--tn-green)';
    practiceStreak++;
    if (practiceStreak > practiceBestStreak) practiceBestStreak = practiceStreak;
    speakText(currentPracticeAnswer);
    setTimeout(() => {
      currentPracticeIndex++;
      displayPracticeQuestion(document.getElementById('pr-mode-select').value);
    }, 1200);
  } else {
    fb.textContent = `✘ Chưa đúng! Đáp án chính xác là: "${currentPracticeAnswer}"`;
    fb.style.color = 'var(--tn-magenta)';
    practiceStreak = 0;
    ratePracticeFail();
    setTimeout(() => {
      currentPracticeIndex++;
      displayPracticeQuestion(document.getElementById('pr-mode-select').value);
    }, 2400);
  }
}

function givePracticeHint() {
  const input = document.getElementById('pr-input');
  if (currentPracticeAnswer) {
    const hint = currentPracticeAnswer.charAt(0) + '_'.repeat(currentPracticeAnswer.length - 1);
    input.value = currentPracticeAnswer.charAt(0);
    showToast(`💡 Gợi ý: Từ bắt đầu bằng chữ '${currentPracticeAnswer.charAt(0)}' (${currentPracticeAnswer.length} chữ cái)`);
  }
}

async function ratePracticeFail() {
  if (currentPracticeWordObj) {
    try {
      await fetch('/api/srs/rate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: jsonBody({
          vocab_id: currentPracticeWordObj.id,
          quality: 0,
          response_time_ms: 3000
        })
      });
      refreshHeaderStats();
    } catch (e) {}
  }
}

function quitPracticeSession() {
  document.getElementById('practice-play').style.display = 'none';
  document.getElementById('practice-setup').style.display = 'block';
  refreshHeaderStats();
}

// ── VOCABULARY HUB ──
async function loadVocabularyTable() {
  const topicId = document.getElementById('vocab-filter-topic').value;
  const status = document.getElementById('vocab-filter-status').value;
  
  let url = `/api/vocabulary?sort_by=created_at_desc`;
  if (topicId) url += `&topic_id=${topicId}`;
  if (status) url += `&status=${status}`;

  try {
    const res = await fetch(url);
    const words = await res.json();
    renderVocabTable(words);
  } catch (err) {
    console.error('Failed to load vocab table:', err);
  }
}

async function onVocabSearch() {
  const query = document.getElementById('vocab-search-input').value.trim();
  if (!query) {
    loadVocabularyTable();
    return;
  }

  try {
    const res = await fetch(`/api/vocabulary/search?q=${encodeURIComponent(query)}`);
    const words = await res.json();
    renderVocabTable(words);
  } catch (err) {
    console.error('Search error:', err);
  }
}

function renderVocabTable(words) {
  const tbody = document.getElementById('vocab-table-body');
  tbody.innerHTML = '';

  if (!words || words.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; padding: 24px; color: var(--text-muted);">Không tìm thấy từ vựng nào.</td></tr>`;
    return;
  }

  const statusEmojis = { new: '🆕', learning: '📖', reviewing: '🔄', relearning: '🔁', mastered: '⭐' };

  words.forEach(w => {
    const tr = document.createElement('tr');
    tr.style.cssText = 'border-bottom: 1px solid var(--border); transition: background 0.15s;';
    tr.onmouseenter = () => tr.style.background = 'var(--bg-card-hover)';
    tr.onmouseleave = () => tr.style.background = 'transparent';

    const emoji = statusEmojis[w.learning_status] || '❓';
    const intervalStr = w.interval_days ? `${Math.round(w.interval_days)}d` : '0d';

    tr.innerHTML = `
      <td style="padding: 10px 16px; font-size: 16px;">${emoji}</td>
      <td style="padding: 10px 16px; font-weight: 700; color: #fff;">
        ${escapeHtml(w.word)}
        <button class="btn btn-secondary" style="padding: 2px 6px; font-size: 10px; margin-left: 6px;" onclick="speakText('${escapeJs(w.word)}')">🔊</button>
        <div style="font-size: 11px; color: var(--tn-cyan); font-family: monospace;">${escapeHtml(w.pronunciation || '')}</div>
      </td>
      <td style="padding: 10px 16px; color: var(--tn-purple); font-size: 12px;">${escapeHtml(w.word_type || '—')}</td>
      <td style="padding: 10px 16px; color: var(--text-main); font-weight: 500;">${escapeHtml(w.definition_vi || '—')}</td>
      <td style="padding: 10px 16px; font-size: 12px; color: var(--text-muted); max-width: 250px;">
        <div>${escapeHtml((w.example || '').slice(0, 75))}</div>
        <div style="font-size: 11px; color: var(--tn-orange);">${escapeHtml(w.usage_context ? '• ' + w.usage_context : '')}</div>
      </td>
      <td style="padding: 10px 16px; font-size: 12px; color: var(--tn-blue); font-weight: 600;">${intervalStr}</td>
      <td style="padding: 10px 16px; text-align: right;">
        <button class="btn btn-secondary" style="padding: 4px 8px; font-size: 11px; margin-right: 4px;" onclick="openEditWordModal(${w.id})">✏️</button>
        <button class="btn btn-danger" style="padding: 4px 8px; font-size: 11px;" onclick="deleteWord(${w.id}, '${escapeJs(w.word)}')">🗑</button>
      </td>
    `;
    tbody.appendChild(tr);
  });
}

async function loadTopicsFilter() {
  try {
    const res = await fetch('/api/topics');
    const topics = await res.json();
    const select = document.getElementById('vocab-filter-topic');
    select.innerHTML = '<option value="">Tất cả chủ đề</option>';
    topics.forEach(t => {
      const opt = document.createElement('option');
      opt.value = t.id;
      opt.textContent = `${t.name} (${t.word_count || 0})`;
      select.appendChild(opt);
    });
  } catch (e) {}
}

// ── WORD MODAL (ADD / EDIT) ──
function openAddWordModal() {
  document.getElementById('modal-word-id').value = '';
  document.getElementById('word-modal-title').textContent = 'Thêm từ vựng mới';
  document.getElementById('modal-word').value = '';
  document.getElementById('modal-type').value = '';
  document.getElementById('modal-pron').value = '';
  document.getElementById('modal-mean-vi').value = '';
  document.getElementById('modal-mean-en').value = '';
  document.getElementById('modal-example').value = '';
  document.getElementById('modal-example-trans').value = '';
  document.getElementById('modal-context').value = '';
  document.getElementById('word-modal').classList.add('active');
  document.getElementById('modal-word').focus();
}

async function openEditWordModal(vocabId) {
  try {
    const res = await fetch(`/api/vocabulary/detail?id=${vocabId}`);
    const w = await res.json();
    if (!w) return;

    document.getElementById('modal-word-id').value = w.id;
    document.getElementById('word-modal-title').textContent = `Sửa từ vựng: ${w.word}`;
    document.getElementById('modal-word').value = w.word || '';
    document.getElementById('modal-type').value = w.word_type || '';
    document.getElementById('modal-pron').value = w.pronunciation || '';
    document.getElementById('modal-mean-vi').value = w.definition_vi || '';
    document.getElementById('modal-mean-en').value = w.definition_en || '';
    document.getElementById('modal-example').value = w.example || '';
    document.getElementById('modal-example-trans').value = w.example_translation || '';
    document.getElementById('modal-context').value = w.usage_context || '';

    document.getElementById('word-modal').classList.add('active');
  } catch (e) {
    showToast('Không tải được thông tin từ vựng', true);
  }
}

function closeAddWordModal() {
  document.getElementById('word-modal').classList.remove('active');
}

async function saveWordFromModal() {
  const vid = document.getElementById('modal-word-id').value;
  const word = document.getElementById('modal-word').value.trim();
  const meanVi = document.getElementById('modal-mean-vi').value.trim();

  if (!word || !meanVi) {
    showToast('Vui lòng nhập Từ tiếng Anh và Nghĩa tiếng Việt!', true);
    return;
  }

  const payload = {
    word: word,
    word_type: document.getElementById('modal-type').value.trim(),
    pronunciation: document.getElementById('modal-pron').value.trim(),
    definition_vi: meanVi,
    definition_en: document.getElementById('modal-mean-en').value.trim(),
    example: document.getElementById('modal-example').value.trim(),
    example_translation: document.getElementById('modal-example-trans').value.trim(),
    usage_context: document.getElementById('modal-context').value.trim()
  };

  const endpoint = vid ? '/api/vocabulary/update' : '/api/vocabulary/add';
  if (vid) payload.id = parseInt(vid, 10);

  try {
    const res = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const result = await res.json();

    if (result.success) {
      showToast(vid ? `Đã cập nhật "${word}"` : `Đã thêm từ mới "${word}"!`);
      closeAddWordModal();
      refreshHeaderStats();
      if (currentTab === 'vocabulary') loadVocabularyTable();
    } else {
      showToast(result.error || 'Có lỗi xảy ra', true);
    }
  } catch (err) {
    showToast('Lỗi kết nối tới backend server', true);
  }
}

async function deleteWord(vocabId, wordText) {
  if (!confirm(`Bạn có chắc chắn muốn xóa từ "${wordText}" khỏi kho từ vựng không?`)) return;

  try {
    await fetch('/api/vocabulary/delete', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: jsonBody({ id: vocabId })
    });
    showToast(`Đã xóa từ "${wordText}"`);
    loadVocabularyTable();
    refreshHeaderStats();
  } catch (e) {
    showToast('Không thể xóa từ', true);
  }
}

// ── AI HUB FEATURES ──
function switchAiSubTab(subTab) {
  document.querySelectorAll('.ai-tab-btn').forEach(btn => btn.classList.remove('active'));
  document.querySelectorAll('.ai-subpanel').forEach(p => p.style.display = 'none');

  event.target.classList.add('active');
  const target = document.getElementById(`ai-sub-${subTab}`);
  if (target) target.style.display = 'block';
}

// 1. AI Vocab Assistant
async function runAiExplainWord() {
  const word = document.getElementById('ai-word-input').value.trim();
  if (!word) return;

  const resDiv = document.getElementById('ai-word-result');
  resDiv.style.display = 'block';
  resDiv.innerHTML = '<div style="color: var(--tn-cyan); font-size: 13px;">✨ AI đang phân tích từ vựng, collocations và sắc thái...</div>';

  try {
    const res = await fetch('/api/ai/explain', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: jsonBody({ word: word })
    });
    const data = await res.json();

    const collocHtml = (data.collocations || []).map(c => `<span style="background: rgba(122, 162, 247, 0.15); color: var(--tn-blue); padding: 3px 8px; border-radius: 6px; font-size: 12px; margin-right: 6px; display: inline-block; margin-bottom: 4px;">• ${escapeHtml(c)}</span>`).join('');
    const exHtml = (data.examples || []).map(e => `<div style="font-size: 13px; margin-bottom: 6px;">📖 ${escapeHtml(e.en)}<br><span style="color: var(--text-dim); font-size: 12px;">🇻🇳 ${escapeHtml(e.vi)}</span></div>`).join('');

    resDiv.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px;">
        <div>
          <span style="font-size: 24px; font-weight: 800; color: #fff;">${escapeHtml(data.word)}</span>
          <span style="font-size: 14px; color: var(--tn-cyan); font-family: monospace; margin-left: 8px;">${escapeHtml(data.ipa || '')}</span>
          <span style="font-size: 12px; background: rgba(187, 154, 247, 0.2); color: var(--tn-purple); padding: 2px 8px; border-radius: 10px; margin-left: 8px;">${escapeHtml(data.pos || '')}</span>
          <span style="font-size: 12px; background: rgba(255, 158, 100, 0.2); color: var(--tn-orange); padding: 2px 8px; border-radius: 10px; margin-left: 4px;">${escapeHtml(data.level || '')}</span>
        </div>
        <button class="btn btn-success" style="padding: 6px 12px; font-size: 12px;" onclick="quickAddFromAi('${escapeJs(data.word)}', '${escapeJs(data.ipa)}', '${escapeJs(data.pos)}', '${escapeJs(data.meaning_vi)}')">
          ➕ Lưu vào kho
        </button>
      </div>

      <div style="font-size: 16px; font-weight: 700; color: var(--tn-yellow); margin-bottom: 6px;">${escapeHtml(data.meaning_vi)}</div>
      <div style="font-size: 13px; color: var(--text-muted); margin-bottom: 14px;">${escapeHtml(data.meaning_en || '')}</div>

      <div style="margin-bottom: 14px;">
        <div style="font-size: 11px; font-weight: 700; color: var(--tn-cyan); text-transform: uppercase; margin-bottom: 6px;">Sắc thái & Văn phong</div>
        <div style="font-size: 13px; color: var(--text-main); line-height: 1.5;">${escapeHtml(data.nuance || '')}</div>
      </div>

      <div style="margin-bottom: 14px;">
        <div style="font-size: 11px; font-weight: 700; color: var(--tn-blue); text-transform: uppercase; margin-bottom: 6px;">Collocations tự nhiên</div>
        <div>${collocHtml}</div>
      </div>

      <div style="margin-bottom: 14px;">
        <div style="font-size: 11px; font-weight: 700; color: var(--tn-green); text-transform: uppercase; margin-bottom: 6px;">Ví dụ thực tế</div>
        ${exHtml}
      </div>

      <div style="background: rgba(247, 118, 142, 0.1); border-left: 3px solid var(--tn-magenta); padding: 10px 14px; border-radius: 6px;">
        <div style="font-size: 11px; font-weight: 700; color: var(--tn-magenta); text-transform: uppercase; margin-bottom: 4px;">Lỗi người học hay gặp</div>
        <div style="font-size: 12px; color: var(--text-main);">${escapeHtml(data.common_mistakes || '')}</div>
      </div>
    `;
  } catch (e) {
    resDiv.innerHTML = '<div style="color: var(--tn-magenta);">Có lỗi khi phân tích từ vựng.</div>';
  }
}

// 2. Sentence Analyzer
async function runAiAnalyzeSentence() {
  const sentence = document.getElementById('ai-sentence-input').value.trim();
  const targetWord = document.getElementById('ai-sentence-target').value.trim();
  if (!sentence) return;

  const resDiv = document.getElementById('ai-sentence-result');
  resDiv.style.display = 'block';
  resDiv.innerHTML = '<div style="color: var(--tn-cyan); font-size: 13px;">🔍 AI đang chấm ngữ pháp, collocation và độ tự nhiên...</div>';

  try {
    const res = await fetch('/api/ai/analyze-sentence', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: jsonBody({ sentence: sentence, target_word: targetWord })
    });
    const data = await res.json();

    const improvedHtml = (data.improved_sentences || []).map(im => `
      <div style="background: rgba(0,0,0,0.25); border-left: 3px solid var(--tn-green); padding: 8px 12px; border-radius: 6px; margin-bottom: 8px;">
        <div style="font-weight: 600; color: #fff; font-size: 13px;">${escapeHtml(im.en)}</div>
        <div style="color: var(--text-dim); font-size: 12px; margin-top: 2px;">${escapeHtml(im.vi)}</div>
      </div>
    `).join('');

    resDiv.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
        <span style="font-size: 14px; font-weight: 700; color: var(--tn-blue);">Đánh giá câu viết của bạn:</span>
        <span style="font-size: 16px; font-weight: 800; color: var(--tn-yellow); background: rgba(224, 175, 104, 0.15); padding: 4px 12px; border-radius: 12px;">
          Độ tự nhiên: ${data.naturalness_score || 8}/10
        </span>
      </div>

      <div style="margin-bottom: 12px;">
        <div style="font-size: 11px; font-weight: 700; color: var(--tn-cyan); text-transform: uppercase; margin-bottom: 4px;">Ngữ pháp (Grammar)</div>
        <div style="font-size: 13px; color: var(--text-main);">${escapeHtml(data.grammar_feedback || '')}</div>
      </div>

      <div style="margin-bottom: 14px;">
        <div style="font-size: 11px; font-weight: 700; color: var(--tn-purple); text-transform: uppercase; margin-bottom: 4px;">Liên kết từ (Collocation)</div>
        <div style="font-size: 13px; color: var(--text-main);">${escapeHtml(data.collocation_feedback || '')}</div>
      </div>

      <div>
        <div style="font-size: 11px; font-weight: 700; color: var(--tn-green); text-transform: uppercase; margin-bottom: 6px;">Gợi ý câu tự nhiên hơn (Better Versions)</div>
        ${improvedHtml}
      </div>
    `;
  } catch (e) {
    resDiv.innerHTML = '<div style="color: var(--tn-magenta);">Có lỗi khi phân tích câu.</div>';
  }
}

// 3. Flashcard Generator
let currentGeneratedCards = [];
async function runAiGenerateFlashcards() {
  const passage = document.getElementById('ai-generator-input').value.trim();
  if (!passage) return;

  const resDiv = document.getElementById('ai-generator-result');
  resDiv.style.display = 'block';
  resDiv.innerHTML = '<div style="color: var(--tn-purple); font-size: 13px;">⚡ AI đang quét văn bản và tạo bộ flashcards...</div>';

  try {
    const res = await fetch('/api/ai/generate-flashcards', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: jsonBody({ passage: passage })
    });
    currentGeneratedCards = await res.json();

    if (!currentGeneratedCards || currentGeneratedCards.length === 0) {
      resDiv.innerHTML = '<div style="color: var(--text-muted);">Không trích xuất được từ vựng từ đoạn văn bản này.</div>';
      return;
    }

    const cardsHtml = currentGeneratedCards.map((c, i) => `
      <div style="padding: 10px 14px; background: var(--bg-night); border-radius: 8px; margin-bottom: 8px; border: 1px solid var(--border);">
        <div style="display: flex; justify-content: space-between;">
          <span style="font-weight: 700; color: #fff; font-size: 14px;">${escapeHtml(c.word)} <span style="font-size: 12px; color: var(--tn-cyan); font-weight: 400;">(${escapeHtml(c.word_type || '')})</span></span>
          <span style="font-size: 12px; color: var(--tn-yellow); font-weight: 600;">${escapeHtml(c.definition_vi || '')}</span>
        </div>
        <div style="font-size: 12px; color: var(--text-muted); margin-top: 4px;">📖 "${escapeHtml(c.example || '')}"</div>
      </div>
    `).join('');

    resDiv.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
        <span style="font-size: 14px; font-weight: 700; color: var(--tn-cyan);">Đã tạo ${currentGeneratedCards.length} Flashcards từ bài đọc:</span>
        <button class="btn btn-success" onclick="importGeneratedCards()">📥 Lưu tất cả vào kho</button>
      </div>
      <div>${cardsHtml}</div>
    `;
  } catch (e) {
    resDiv.innerHTML = '<div style="color: var(--tn-magenta);">Có lỗi khi sinh flashcards.</div>';
  }
}

async function importGeneratedCards() {
  if (!currentGeneratedCards || currentGeneratedCards.length === 0) return;
  try {
    const res = await fetch('/api/ai/batch-add', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: jsonBody({ cards: currentGeneratedCards })
    });
    const d = await res.json();
    showToast(`✅ Đã lưu thành công ${d.added_count || currentGeneratedCards.length} từ vào kho!`);
    refreshHeaderStats();
  } catch (e) {
    showToast('Không lưu được flashcards', true);
  }
}

// 4. IELTS Writing & Diary Feedback
async function runAiIeltsFeedback() {
  const text = document.getElementById('ai-ielts-input').value.trim();
  if (!text) return;

  const resDiv = document.getElementById('ai-ielts-result');
  resDiv.style.display = 'block';
  resDiv.innerHTML = '<div style="color: var(--tn-yellow); font-size: 13px;">📝 AI IELTS Examiner đang phân tích Lexical Resource...</div>';

  try {
    const res = await fetch('/api/ai/feedback-writing', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: jsonBody({ text: text })
    });
    const data = await res.json();

    const upgradesHtml = (data.upgrades || []).map(u => `
      <div style="padding: 10px 14px; background: var(--bg-night); border-radius: 8px; margin-bottom: 8px;">
        <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
          <span style="color: var(--tn-magenta); font-weight: 700; font-size: 13px;">Từ gốc: "${escapeHtml(u.original_word)}"</span>
          <span style="color: var(--tn-green); font-weight: 700; font-size: 13px;">Gợi ý: ${(u.suggested_replacements || []).join(', ')}</span>
        </div>
        <div style="font-size: 12px; color: var(--text-muted);">${escapeHtml(u.explanation || '')}</div>
        <div style="font-size: 12px; color: var(--tn-blue); margin-top: 4px;">${escapeHtml(u.sample_upgraded_sentence || '')}</div>
      </div>
    `).join('');

    resDiv.innerHTML = `
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
        <span style="font-size: 14px; font-weight: 700; color: #fff;">Đánh giá Lexical Resource</span>
        <span style="font-size: 16px; font-weight: 800; color: var(--tn-purple); background: rgba(187, 154, 247, 0.15); padding: 4px 12px; border-radius: 12px;">
          Estimated Band: ${data.estimated_band || '6.5'}
        </span>
      </div>
      <div style="font-size: 13px; color: var(--text-main); margin-bottom: 16px; line-height: 1.5;">${escapeHtml(data.summary_comment || '')}</div>
      <div style="font-size: 11px; font-weight: 700; color: var(--tn-green); text-transform: uppercase; margin-bottom: 8px;">Từ vựng nâng cấp Band 7.5+</div>
      <div>${upgradesHtml}</div>
    `;
  } catch (e) {
    resDiv.innerHTML = '<div style="color: var(--tn-magenta);">Có lỗi khi phân tích bài viết.</div>';
  }
}

async function quickAddFromAi(word, ipa, pos, meanVi) {
  try {
    await fetch('/api/vocabulary/add', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: jsonBody({
        word: word,
        pronunciation: ipa,
        word_type: pos,
        definition_vi: meanVi,
        source: 'AI Assistant'
      })
    });
    showToast(`✅ Đã thêm "${word}" vào kho từ vựng!`);
    refreshHeaderStats();
  } catch (e) {}
}

// ── ANALYTICS TAB ──
async function loadAnalyticsTab() {
  try {
    const [summaryRes, sessionsRes] = await Promise.all([
      fetch('/api/stats/summary'),
      fetch('/api/sessions')
    ]);
    const summary = await summaryRes.json();
    const sessions = await sessionsRes.json();

    // Status breakdown
    const stContainer = document.getElementById('analytics-status-breakdown');
    stContainer.innerHTML = '';
    const statuses = summary.statuses || {};
    const total = summary.total_words || 1;

    const labels = [
      { key: 'new', label: '🆕 Từ mới', color: 'var(--tn-cyan)' },
      { key: 'learning', label: '📖 Đang học', color: 'var(--tn-yellow)' },
      { key: 'reviewing', label: '🔄 Đang ôn (SRS)', color: 'var(--tn-blue)' },
      { key: 'relearning', label: '🔁 Ôn lại sau sai', color: 'var(--tn-magenta)' },
      { key: 'mastered', label: '⭐ Đã thuộc (>30 ngày)', color: 'var(--tn-purple)' }
    ];

    labels.forEach(l => {
      const count = statuses[l.key] || 0;
      const pct = Math.round((count / total) * 100);
      const row = document.createElement('div');
      row.style.cssText = 'margin-bottom: 10px;';
      row.innerHTML = `
        <div style="display: flex; justify-content: space-between; font-size: 12px; margin-bottom: 4px;">
          <span>${l.label}</span>
          <span style="font-weight: 700; color: ${l.color};">${count} (${pct}%)</span>
        </div>
        <div style="height: 6px; background: var(--bg-night); border-radius: 4px; overflow: hidden;">
          <div style="width: ${pct}%; height: 100%; background: ${l.color}; border-radius: 4px;"></div>
        </div>
      `;
      stContainer.appendChild(row);
    });

    // Sessions history
    const sessContainer = document.getElementById('analytics-sessions-list');
    sessContainer.innerHTML = '';
    if (!sessions || sessions.length === 0) {
      sessContainer.innerHTML = '<div style="font-size: 12px; color: var(--text-muted); padding: 10px 0;">Chưa có phiên học nào được ghi lại.</div>';
      return;
    }

    sessions.forEach(s => {
      const row = document.createElement('div');
      row.style.cssText = 'padding: 8px 12px; background: var(--bg-night); border-radius: 6px; margin-bottom: 6px; font-size: 12px; display: flex; justify-content: space-between;';
      row.innerHTML = `
        <span>📚 ${escapeHtml(s.session_type)} • ${escapeHtml((s.started_at || '').slice(0, 16))}</span>
        <span style="color: var(--tn-green);">✅ ${s.correct_count || 0} / ❌ ${s.wrong_count || 0}</span>
      `;
      sessContainer.appendChild(row);
    });
  } catch (e) {
    console.error('Failed to load analytics:', e);
  }
}

// ── FILE IMPORT ──
async function handleFileImport() {
  const fileInput = document.getElementById('file-import-input');
  if (!fileInput.files || fileInput.files.length === 0) {
    showToast('Vui lòng chọn một file CSV hoặc Excel!', true);
    return;
  }

  const file = fileInput.files[0];
  const reader = new FileReader();

  reader.onload = async (e) => {
    try {
      const content = e.target.result;
      const res = await fetch('/api/import-raw', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: jsonBody({ content: content })
      });
      const d = await res.json();
      if (d.success) {
        showToast(`✅ Đã import thành công ${d.imported_count || 0} từ vào JulyFlow!`);
        refreshHeaderStats();
        fileInput.value = '';
      } else {
        showToast('Lỗi khi đọc file', true);
      }
    } catch (err) {
      showToast('Không gửi được file lên server', true);
    }
  };

  reader.readAsText(file, 'utf-8');
}

// ── SETTINGS MODAL ──
async function openSettingsModal() {
  try {
    const res = await fetch('/api/settings?key=gemini_api_key');
    const d = await res.json();
    document.getElementById('setting-gemini-key').value = d.value || '';
    document.getElementById('settings-modal').classList.add('active');
  } catch (e) {}
}

function closeSettingsModal() {
  document.getElementById('settings-modal').classList.remove('active');
}

async function saveAppSettings() {
  const key = document.getElementById('setting-gemini-key').value.trim();
  try {
    await fetch('/api/settings/save', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: jsonBody({ key: 'gemini_api_key', value: key })
    });
    showToast('✅ Đã lưu cài đặt!');
    closeSettingsModal();
  } catch (e) {
    showToast('Lỗi lưu cài đặt', true);
  }
}

// ── TEXT-TO-SPEECH (TTS) ──
function speakText(text) {
  if (!('speechSynthesis' in window)) return;
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = 'en-US';
  utterance.rate = 0.9;
  window.speechSynthesis.speak(utterance);
}

// ── KEYBOARD SHORTCUTS ──
function setupKeyboardShortcuts() {
  window.addEventListener('keydown', (e) => {
    // Không bắt phím tắt khi đang gõ vào input hoặc textarea
    if (['INPUT', 'TEXTAREA', 'SELECT'].includes(e.target.tagName)) {
      if (e.target.id === 'pr-input' && e.key === 'Enter') {
        submitPracticeAnswer();
      }
      return;
    }

    if (currentTab === 'flashcards') {
      if (e.code === 'Space') {
        e.preventDefault();
        flipFlashcard();
      } else if (e.key === '1') {
        rateFlashcard(0);
      } else if (e.key === '2') {
        rateFlashcard(3);
      } else if (e.key === '3') {
        rateFlashcard(4);
      } else if (e.key === '4') {
        rateFlashcard(5);
      }
    }
  });
}

// ── HELPERS ──
function jsonBody(obj) {
  return JSON.stringify(obj);
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

function escapeJs(str) {
  if (!str) return '';
  return String(str).replace(/'/g, "\\'").replace(/"/g, '\\"');
}

function escapeRegExp(string) {
  return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

