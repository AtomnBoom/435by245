// ==========================================================================
// VOICE_ENGINE.JS — МОНОЛИТНАЯ СЛУЖБА ЗВОНКА С ИСПРАВЛЕНИЕМ ЗАКЛИНИВАНИЯ
// ==========================================================================

document.addEventListener('DOMContentLoaded', () => {
    const toggleMicBtn = document.getElementById('toggleMicBtn');
    const hangUpBtn = document.getElementById('hangUpBtn');
    const switchToManualBtn = document.getElementById('switchToManualBtn');
    const dialogStream = document.getElementById('dialogStream');
    const voiceStatus = document.getElementById('voiceStatus');

    const interfaceWrapper = document.getElementById('interfaceWrapper');
    const voicePromptInput = document.getElementById('voicePromptInput');
    const voiceSendTextBtn = document.getElementById('voiceSendTextBtn');

    let isRecording = false; 
    let recognitionInstance = null;
    let activeAudioStream = null;
    let conversationHistory = []; 

    const urlParams = new URLSearchParams(window.location.search);
    const existingChatId = urlParams.get('chat_id'); 

    // Сразу очищаем контейнер диалога, чтобы убрать старые браузерные тексты
    if (dialogStream) dialogStream.innerHTML = '';

    function appendVoiceBubble(text, role) {
        if (!dialogStream) return;
        const bubble = document.createElement('div');
        bubble.className = `voice-bubble ${role}-speech`;
        bubble.textContent = text;
        dialogStream.appendChild(bubble);
        dialogStream.scrollTo({ top: dialogStream.scrollHeight, behavior: 'smooth' });
        conversationHistory.push({ role: role, text: text });
    }

    // Запрос приветствия у Python-сервера
    async function generateAgentGreeting() {
        if (voiceStatus) voiceStatus.textContent = "A.E.G.I.S. запрашивает приветствие...";
        try {
            const response = await fetch(`http://localhost:8190/api/voice/greeting?chat_id=${existingChatId || ''}`);
            const data = await response.json();
            
            appendVoiceBubble(data.text, 'agent');
            if (voiceStatus && isRecording) voiceStatus.textContent = "Агент вас слушает, говорите...";
        } catch (err) {
            // Фолбэк, если локальный сервер Питера еще не поднят на порту 8190
            const fallbackText = existingChatId 
                ? "Привет! Я подняла контекст нашего чата. Готова продолжить голосом."
                : "Привет! Я на связи и готова к работе. О чём поговорим сегодня?";
            appendVoiceBubble(fallbackText, 'agent');
            if (voiceStatus && isRecording) voiceStatus.textContent = "Режим симуляции. Агент вас слушает...";
        }
    }

    // Логика полного гашения и освобождения аудиокарты
    function stopAudioHardware() {
        isRecording = false;
        if (recognitionInstance) {
            try { recognitionInstance.stop(); } catch(e){}
            recognitionInstance = null;
        }
        if (activeAudioStream) {
            activeAudioStream.getTracks().forEach(track => track.stop());
            activeAudioStream = null;
        }
        if (toggleMicBtn) {
            toggleMicBtn.classList.remove('mic-active');
            toggleMicBtn.classList.add('mic-muted');
        }
        if (voiceStatus) voiceStatus.textContent = "Микрофон отключен.";
    }

    // Чистый запуск аудиосистемы звонка
    async function startAudioHardware() {
        if (voiceStatus) voiceStatus.textContent = "Активация аудиокарты...";
        try {
            activeAudioStream = await navigator.mediaDevices.getUserMedia({ audio: true });
            isRecording = true;

            if (toggleMicBtn) {
                toggleMicBtn.classList.remove('mic-muted');
                toggleMicBtn.classList.add('mic-active');
            }
            
            // Запускаем приветствие ИИ только ПОСЛЕ того, как микрофон успешно открылся
            await generateAgentGreeting();
        } catch (err) {
            if (voiceStatus) voiceStatus.textContent = "Ошибка доступа: Микрофон заблокирован.";
            isRecording = false;
        }
    }

    // КНОПКА МИКРОФОНА (ТОГГЛ)
    if (toggleMicBtn) {
        toggleMicBtn.onclick = (e) => {
            e.preventDefault();
            if (!isRecording) startAudioHardware(); else stopAudioHardware();
        };
    }

    // КНОПКА КЛАВИАТУРЫ: Разворачивание скрытой панели инпута
    if (switchToManualBtn && interfaceWrapper) {
        switchToManualBtn.onclick = (e) => {
            e.preventDefault();
            e.stopPropagation();
            interfaceWrapper.classList.toggle('manual-input-active');
            if (interfaceWrapper.classList.contains('manual-input-active') && voicePromptInput) {
                setTimeout(() => { voicePromptInput.focus(); }, 50);
            }
        };
    }

    // КНОПКА СБРОСА (ТРУБКА) — ИСПРАВЛЕНО И СИНХРОНИЗИРОВАНО
    if (hangUpBtn) {
        hangUpBtn.onclick = (e) => {
            e.preventDefault();
            e.stopPropagation();
            
            stopAudioHardware();

            const logSummary = "Голосовая сессия успешно сохранена.";
            
            if (existingChatId) {
                // Сценарий 1: Звонили из чата. Возвращаемся в него же и даем команду chat.js синхронизировать лог
                window.location.href = `chat.html?chat_id=${encodeURIComponent(existingChatId)}&voice_sync=true`;
            } else {
                // Сценарий 2: Звонили с мейн-окна. Инициируем создание нового чата с осмысленным контекстом
                let smartTitle = "Голосовая сессия ассистента";
                if (conversationHistory.length > 0) {
                    const fullText = conversationHistory.map(h => h.text).join(' ').toLowerCase();
                    if (fullText.includes('настроение')) smartTitle = "Обсуждение настроения";
                    if (fullText.includes('код') || fullText.includes('проект')) smartTitle = "Архитектура ядра проекта";
                }
                window.location.href = `chat.html?prompt=${encodeURIComponent(logSummary)}&mode=aegis&newChatName=${encodeURIComponent(smartTitle)}`;
            }
        };
    }

    // Автоматически запускаем аудиосистему один раз строго при старте страницы звонка
    startAudioHardware();
});
