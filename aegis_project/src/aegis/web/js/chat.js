// ==========================================================================
// A.E.G.I.S. SYSTEM — CHAT.JS — БЛОК 1: АВТОМАТИЧЕСКАЯ СБОРКА ТОП-БАРА ИСТОРИИ
// ==========================================================================

document.addEventListener('DOMContentLoaded', () => {
    const historyScrollZone = document.getElementById('historyScrollZone');
    const contextMenu = document.getElementById('sessionContextMenu');
    const tabs = document.querySelectorAll('.history-tab');
    const messagesStream = document.getElementById('messagesStream');

    let currentActiveTab = 'all';
    let targetSessionId = null; 
    let isMultiSelectMode = false; 
    let selectedSessionIds = new Set(); 

    let mockSessions = [
        { id: 1, title: 'New chat', timestamp: '10:42', dateGroup: 'Today', favorite: false, pinned: false, messages: [] },
        { id: 2, title: 'Работяга', timestamp: 'Вчера, 18:12', dateGroup: '7 Days', favorite: true, pinned: false, messages: [
            { role: 'user', text: 'Работяга' },
            { role: 'agent', text: 'Анализ завершен. Защита метаданных в памяти устройства зафиксирована.' }
        ]},
        { id: 3, title: 'Интерактивный таймер в Discord', timestamp: '24.08.2026', dateGroup: '2026-08', favorite: false, pinned: false, messages: [] }
    ];

    // 🛠️ РЕАЛИЗАЦИЯ ПУНКТА 4: Динамическая сборка Топ-Бара над списком чатов, если его нет в HTML
    let searchChatInput = document.getElementById('searchChatInput');
    let multiSelectBtn = document.getElementById('multiSelectBtn');
    let bulkActionPanel = document.getElementById('bulkActionPanel');

    function buildSystemTopBarUi() {
        const sidebar = document.querySelector('.chats-history-sidebar');
        if (!sidebar || document.getElementById('aegisTopBarZone')) return;

        const topBarZone = document.createElement('div');
        topBarZone.id = 'aegisTopBarZone';
        topBarZone.className = 'history-top-bar-container';
        
        // Верстка: История запросов уходит влево, кнопки лупы и мульти-выбора — вправо
        topBarZone.innerHTML = `
            <div class="aegis-history-title-row">
                <span class="aegis-history-main-title">История запросов</span>
                <div class="aegis-history-action-group">
                    <button class="aegis-top-action-btn" id="aegisSearchToggle" title="Поиск по словам">🔍</button>
                    <button class="aegis-top-action-btn" id="multiSelectBtn" title="Выбрать несколько чатов">☰</button>
                </div>
            </div>
            <div class="aegis-search-expand-panel" id="aegisSearchPanel" style="display: none;">
                <input type="text" id="searchChatInput" placeholder="Поиск по сообщениям..." autocomplete="off">
            </div>
            <div class="aegis-bulk-action-panel" id="bulkActionPanel" style="display: none;">
                <button class="aegis-bulk-btn btn-bulk-pin" id="bulkPinBtn">📌 Закрепить</button>
                <button class="aegis-bulk-btn btn-bulk-del" id="bulkDeleteBtn">🗑️ Удалить</button>
            </div>
        `;
        // Вставляем созданную панель в самый верх бокового меню истории
        sidebar.insertBefore(topBarZone, sidebar.firstChild);

        // Перепривязываем динамически созданные элементы к рабочим переменным
        searchChatInput = document.getElementById('searchChatInput');
        multiSelectBtn = document.getElementById('multiSelectBtn');
        bulkActionPanel = document.getElementById('bulkActionPanel');
        
        initTopBarEventListeners();
    }

    buildSystemTopBarUi(); // Запускаем сборку интерфейса
// ==========================================================================
// CHAT.JS — БЛОК 2: ОТРИСОВКА ПЛИТОК СЕССИЙ И ПОДДЕРЖКА МУЛЬТИ-ВЫБОРА
// ==========================================================================

    function renderHistoryList(searchQuery = '') {
        if (!historyScrollZone) return;
        historyScrollZone.innerHTML = '';
        
        let filtered = mockSessions.filter(s => currentActiveTab === 'all' || s.favorite);
        
        // Умный поиск (Пункт 4): фильтруем и по заголовку, и по содержимому реплик
        if (searchQuery) {
            filtered = filtered.filter(s => 
                s.title.toLowerCase().includes(searchQuery) || 
                s.messages.some(m => m.text.toLowerCase().includes(searchQuery))
            );
        }

        filtered.sort((a, b) => (b.pinned ? 1 : 0) - (a.pinned ? 1 : 0));
        const groups = [...new Set(filtered.map(s => s.dateGroup))];
        
        groups.forEach(groupName => {
            const groupHeader = document.createElement('div');
            groupHeader.className = 'history-date-group-title';
            groupHeader.textContent = groupName;
            historyScrollZone.appendChild(groupHeader);
            
            filtered.filter(s => s.dateGroup === groupName).forEach(session => {
                const tile = document.createElement('div');
                tile.className = 'chat-session-tile';
                if (session.favorite) tile.classList.add('is-favorite');
                if (session.pinned) tile.classList.add('is-pinned');
                if (selectedSessionIds.has(session.id)) tile.classList.add('selected-for-bulk');
                if (document.querySelector(`.chat-session-tile.active[data-id="${session.id}"]`)) tile.classList.add('active');
                tile.dataset.id = session.id;
                
                tile.innerHTML = `
                    <div class="chat-session-header-row">
                        <span class="chat-session-fav-marker"></span>
                        <div class="chat-session-title-text" id="titleContainer_${session.id}">${escapeHtml(session.title)}</div>
                        <div class="chat-session-trigger-dots">...</div>
                    </div>
                    <div class="chat-session-time-subtext">${session.timestamp}</div>
                `;
                
                tile.addEventListener('click', (e) => {
                    if (e.target.classList.contains('chat-session-trigger-dots') || e.target.tagName === 'INPUT') return;
                    
                    if (isMultiSelectMode) {
                        // ПУНКТ 4: Тоггл выделения чатов кликами мышки (ЛКМ)
                        if (selectedSessionIds.has(session.id)) {
                            selectedSessionIds.delete(session.id);
                            tile.classList.remove('selected-for-bulk');
                        } else {
                            selectedSessionIds.add(session.id);
                            tile.classList.add('selected-for-bulk');
                        }
                    } else {
                        document.querySelectorAll('.chat-session-tile').forEach(t => t.classList.remove('active'));
                        tile.classList.add('active');
                        loadActiveSessionDialog(session);
                    }
                });

                tile.querySelector('.chat-session-trigger-dots').addEventListener('click', (e) => {
                    e.stopPropagation();
                    if (isMultiSelectMode) return;
                    targetSessionId = session.id;
                    const rect = e.target.getBoundingClientRect();
                    showContextMenu(rect.left - 150, rect.bottom + window.scrollY, session);
                });

                historyScrollZone.appendChild(tile);
            });
        });
        evaluateInputZoneVisibility(); // Прячем инпут, если нет выбранного активного чата
    }
// ==========================================================================
// CHAT.JS — БЛОК 3: КОНТЕКСТНЫЕ ОПЕРАЦИИ И ИСПРАВЛЕННЫЙ ВЫВОД СООБЩЕНИЙ
// ==========================================================================

    function startInlineRename(sessionId) {
        const session = mockSessions.find(s => s.id === sessionId);
        const container = document.getElementById(`titleContainer_${sessionId}`);
        if (!session || !container) return;

        const input = document.createElement('input');
        input.type = 'text';
        input.className = 'chat-session-rename-input';
        input.value = session.title;
        input.addEventListener('click', (e) => e.stopPropagation());

        function commitRename() {
            const val = input.value.trim();
            if (val.length > 0) session.title = val;
            renderHistoryList();
        }

        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') commitRename();
            if (e.key === 'Escape') renderHistoryList();
        });

        input.addEventListener('blur', commitRename);
        container.innerHTML = ''; container.appendChild(input);
        input.focus(); input.select();
    }

    document.addEventListener('click', (e) => { 
        if(contextMenu && !e.target.classList.contains('chat-session-trigger-dots')) contextMenu.style.display = 'none'; 
    });
    
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            tabs.forEach(t => t.classList.remove('active')); tab.classList.add('active');
            currentActiveTab = tab.dataset.tab; selectedSessionIds.clear(); renderHistoryList();
        });
    });

    document.getElementById('ctxToggleFavorite').addEventListener('click', () => {
        const session = mockSessions.find(s => s.id === targetSessionId);
        if (session) { session.favorite = !session.favorite; renderHistoryList(); }
    });

    document.getElementById('ctxRename').addEventListener('click', () => {
        if (targetSessionId) startInlineRename(targetSessionId);
    });

    document.getElementById('ctxDelete').addEventListener('click', () => {
        mockSessions = mockSessions.filter(s => s.id !== targetSessionId);
        if (messagesStream) messagesStream.innerHTML = '<div class="empty-chat-stub"><p>Начните чат или выберите сессию из истории слева</p></div>';
        renderHistoryList();
    });

    function loadActiveSessionDialog(session) {
        if (!messagesStream) return;
        messagesStream.innerHTML = ''; 
        
        const userNode = document.createElement('div');
        userNode.className = 'message-node user-type';
        userNode.innerHTML = `
            <div class="message-bubble">${escapeHtml(session.title)}</div>
            <div class="message-action-toolbar">
                <button class="msg-tool-btn btn-copy" title="Копировать промпт">Копировать</button>
            </div>
        `;
        
        // 🛠️ ЖЕЛЕЗНЫЙ ФИКС: Безопасное чтение сообщений без падения в ошибку undefined
        let agentResponseText = "Анализ завершен. Защита метаданных в памяти устройства зафиксирована.";
        if (session.messages && session.messages.length > 1 && session.messages[1]) {
            agentResponseText = formatAgentResponse(session.messages[1].text);
        }

        const agentNode = document.createElement('div');
        agentNode.className = 'message-node agent-type';
        agentNode.innerHTML = `
            <div class="message-bubble">${agentResponseText}</div>
            <div class="message-action-toolbar">
                <button class="msg-tool-btn btn-copy" title="Копировать ответ">Копировать</button>
                <button class="msg-tool-btn btn-download" title="Скачать как TXT">Скачать</button>
            </div>
        `;

        messagesStream.appendChild(userNode); 
        messagesStream.appendChild(agentNode);
        setupToolbarListeners();
    }
// ==========================================================================
// CHAT.JS — БЛОК 4: ЛИСТЕНЕРЫ УПРАВЛЕНИЯ И ИНТЕГРАЦИЯ СИСТЕМНЫХ ТЕГОВ
// ==========================================================================

    function setupToolbarListeners() {
        document.querySelectorAll('.btn-copy').forEach(btn => {
            btn.onclick = () => {
                navigator.clipboard.writeText(btn.closest('.message-node').querySelector('.message-bubble').textContent);
                btn.style.color = '#22C55E'; setTimeout(() => { btn.style.color = ''; }, 800);
            };
        });
        document.querySelectorAll('.btn-download').forEach(btn => {
            btn.onclick = () => {
                const text = btn.closest('.message-node').querySelector('.message-bubble').textContent;
                const link = document.createElement('a');
                link.href = URL.createObjectURL(new Blob([text], { type: 'text/plain;charset=utf-8' }));
                link.download = `Aegis_${Date.now()}.txt`; link.click();
            };
        });
    }

    // Листенеры кликов по кнопкам новой панели управления
    function initTopBarEventListeners() {
        const searchToggle = document.getElementById('aegisSearchToggle');
        const searchPanel = document.getElementById('aegisSearchPanel');

        if (searchToggle && searchPanel) {
            searchToggle.onclick = () => {
                searchPanel.style.display = searchPanel.style.display === 'none' ? 'block' : 'none';
                if (searchPanel.style.display === 'block') document.getElementById('searchChatInput').focus();
            };
        }

        if (searchChatInput) {
            searchChatInput.addEventListener('input', (e) => {
                renderHistoryList(e.target.value.toLowerCase().trim());
            });
        }

        if (multiSelectBtn) {
            multiSelectBtn.onclick = () => {
                isMultiSelectMode = !isMultiSelectMode;
                multiSelectBtn.classList.toggle('active', isMultiSelectMode);
                if (bulkActionPanel) bulkActionPanel.style.display = isMultiSelectMode ? 'flex' : 'none';
                if (!isMultiSelectMode) selectedSessionIds.clear();
                renderHistoryList();
            };
        }

        if (document.getElementById('bulkDeleteBtn')) {
            document.getElementById('bulkDeleteBtn').onclick = () => {
                mockSessions = mockSessions.filter(s => !selectedSessionIds.has(s.id));
                selectedSessionIds.clear(); isMultiSelectMode = false;
                if (bulkActionPanel) bulkActionPanel.style.display = 'none';
                if (multiSelectBtn) multiSelectBtn.classList.remove('active');
                if (messagesStream) messagesStream.innerHTML = '<div class="empty-chat-stub"><p>Начните чат или выберите сессию из истории слева</p></div>';
                renderHistoryList();
            };
        }

        if (document.getElementById('bulkPinBtn')) {
            document.getElementById('bulkPinBtn').onclick = () => {
                mockSessions.forEach(s => { if (selectedSessionIds.has(s.id)) s.pinned = !s.pinned; });
                selectedSessionIds.clear(); isMultiSelectMode = false;
                if (bulkActionPanel) bulkActionPanel.style.display = 'none';
                if (multiSelectBtn) multiSelectBtn.classList.remove('active');
                renderHistoryList();
            };
        }
    }

    function evaluateInputZoneVisibility() {
        const inputZone = document.querySelector('.input-zone-container');
        const hasActiveSession = document.querySelector('.chat-session-tile.active');
        if (inputZone) {
            inputZone.style.setProperty('display', hasActiveSession ? 'flex' : 'none', 'important');
        }
    }

    function escapeHtml(str) { return str.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;'); }
    if (historyScrollZone) renderHistoryList();
});

// Глобальные парсеры тегов GigaChat Dark Canon
function formatAgentResponse(rawText) {
    let formattedHtml = rawText;
    const thoughtRegex = /<thought>([\s\S]*?)<\/thought>/g;
    formattedHtml = formattedHtml.replace(thoughtRegex, (match, content) => {
        return `<div class="aegis-thought-container"><div class="aegis-thought-header" onclick="this.parentElement.classList.toggle('active')"><span class="aegis-thought-icon">🧠</span><span class="aegis-thought-title">Thought (Рассуждение агента)</span><span class="aegis-thought-arrow">❯</span></div><div class="aegis-thought-body">${content.trim()}</div></div>`;
    });
    const researchRegex = /<research\s+query="([^"]*)">([\s\S]*?)<\/research>/g;
    formattedHtml = formattedHtml.replace(researchRegex, (match, query, logs) => {
        return `<div class="aegis-status-container component-research"><div class="aegis-status-card" onclick="openResearchModal('${btoa(encodeURIComponent(logs))}')"><div class="aegis-spinner"></div><div class="aegis-status-text"><span class="status-main">Провожу исследование</span><span class="status-sub">По запросу: "${query}"</span></div><div class="aegis-status-action">Детали ❯</div></div></div>`;
    });
    return formattedHtml;
}
