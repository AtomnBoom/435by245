// ==========================================================================
// A.E.G.I.S. SYSTEM — INPUT_ENGINE.JS — БЛОК 1: РЕЖИМЫ И УМНЫЙ СЕССИОННЫЙ КЭШ
// ==========================================================================

document.addEventListener('DOMContentLoaded', () => {
    const promptInput = document.getElementById('promptInput');
    const mutationBtn = document.getElementById('mutationBtn');
    const voiceCallBtn = document.getElementById('voiceCallBtn');
    const modePills = document.querySelectorAll('.mode-pill');
    
    const attachBtn = document.getElementById('attachBtn');
    const hiddenFileInput = document.getElementById('hiddenFileInput');
    const filePreviews = document.getElementById('filePreviews');
    const attachTooltip = document.getElementById('attachTooltip');

    if (!promptInput) return; 

    let uploadedFiles = [];
    let isRecordingText = false;
    let isAutoFilling = false; 
    let recognitionInstance = null;
    let activeAudioStream = null;
    let tooltipTimeout = null; 

    const pageKey = window.location.pathname.split('/').pop() || 'index.html';

    function adjustInputHeight() {
        promptInput.style.height = 'auto';
        promptInput.style.height = promptInput.scrollHeight + 'px';
    }

    modePills.forEach(pill => {
        pill.addEventListener('click', () => {
            modePills.forEach(p => p.classList.remove('active'));
            pill.classList.add('active');
            
            document.querySelectorAll('.mode-indicator').forEach(i => i.remove());
            const indicator = document.createElement('span');
            indicator.className = 'mode-indicator';
            pill.insertBefore(indicator, pill.firstChild);
            
            saveInputStateToCache(); 
        });
    });

    promptInput.addEventListener('input', () => {
        adjustInputHeight();
        evaluateInputMutation();
    });

    function saveInputStateToCache() {
        sessionStorage.setItem(`aegis_text_${pageKey}`, promptInput.value);
        const activeMode = document.querySelector('.mode-pill.active')?.dataset.mode || 'aegis';
        sessionStorage.setItem(`aegis_mode_${pageKey}`, activeMode);

        const filesCacheData = uploadedFiles.map(f => ({
            name: f.name,
            type: f.type,
            size: f.size,
            base64: f.cachedContent || null
        }));
        sessionStorage.setItem(`aegis_files_${pageKey}`, JSON.stringify(filesCacheData));
    }

    function restoreInputState() {
        // Проверяем тип навигации: был ли это переход или обычная перезагрузка F5
        const navEntries = performance.getEntriesByType('navigation');
        const isReload = navEntries.length > 0 && navEntries[0].type === 'reload';

        // Если это переход на другую страницу или возврат — намертво очищаем сессию
        if (!isReload) {
            sessionStorage.removeItem(`aegis_text_${pageKey}`);
            sessionStorage.removeItem(`aegis_files_${pageKey}`);
            evaluateInputMutation();
            return;
        }

        const cachedText = sessionStorage.getItem(`aegis_text_${pageKey}`);
        if (cachedText) {
            promptInput.value = cachedText;
            adjustInputHeight();
        }
        
        const cachedMode = sessionStorage.getItem(`aegis_mode_${pageKey}`);
        if (cachedMode) {
            modePills.forEach(p => {
                if (p.dataset.mode === cachedMode) {
                    p.classList.add('active');
                    document.querySelectorAll('.mode-indicator').forEach(i => i.remove());
                    const ind = document.createElement('span');
                    ind.className = 'mode-indicator';
                    p.insertBefore(ind, p.firstChild);
                }
            });
        }

        try {
            const cachedFiles = JSON.parse(sessionStorage.getItem(`aegis_files_${pageKey}`) || '[]');
            uploadedFiles = []; 
            if (filePreviews) filePreviews.innerHTML = ''; 
            
            cachedFiles.forEach(fileMeta => { 
                const rawData = fileMeta.base64 || "";
                const blob = new Blob([rawData], { type: fileMeta.type });
                const recoveredFile = new File([blob], fileMeta.name, { type: fileMeta.type });
                
                recoveredFile.cachedContent = rawData;
                if (fileMeta.size) Object.defineProperty(recoveredFile, 'size', { value: fileMeta.size });
                
                uploadedFiles.push(recoveredFile); 
                renderFileCard(recoveredFile, fileMeta.type.startsWith('image/'), fileMeta.base64); 
            });
        } catch (e) {}

        evaluateInputMutation();
    }

    if (voiceCallBtn) {
        voiceCallBtn.addEventListener('click', (e) => {
            e.preventDefault();
            const urlParams = new URLSearchParams(window.location.search);
            const currentChatId = urlParams.get('chat_id') || urlParams.get('id') || document.querySelector('.chat-session-tile.active')?.dataset.id;
            localStorage.removeItem(`aegis_text_${pageKey}`);
            if (currentChatId) {
                window.location.href = `voice.html?chat_id=${encodeURIComponent(currentChatId)}`;
            } else {
                window.location.href = `voice.html`;
            }
        });
    }
// ==========================================================================
// A.E.G.I.S. SYSTEM — INPUT_ENGINE.JS — БЛОК 2: МИКРОФОН И РАСПОЗНАВАНИЕ РЕЧИ
// ==========================================================================

    function evaluateInputMutation() {
        // Если идет автоматическая вставка или сброс текста — полностью выходим
        if (isAutoFilling) return; 

        const text = promptInput.value.trim();
        if (text.length > 0) {
            mutationBtn.classList.remove('audio-state', 'recording-active');
            mutationBtn.classList.add('text-state');
            mutationBtn.setAttribute('title', 'Отправить запрос');
            promptInput.placeholder = "Спросите A.E.G.I.S.";
        } else {
            mutationBtn.classList.remove('text-state');
            mutationBtn.classList.add('audio-state');
            mutationBtn.setAttribute('title', 'Голосовой ввод текста');
            
            // 🛠️ ЖЕЛЕЗНЫЙ ФИКС: Защищаем активную фазу записи от ложного сброса стилей
            if (isRecordingText) {
                mutationBtn.classList.add('recording-active');
            } else {
                mutationBtn.classList.remove('recording-active');
            }
        }
        saveInputStateToCache();
    }

    promptInput.addEventListener('keydown', (e) => {
        if (isRecordingText) {
            if (e.key === 'Enter') {
                e.preventDefault();
                stopVoiceRecognition(true);
                executeFormSubmission();
            } else if (e.key.length === 1 && !e.ctrlKey && !e.altKey && !e.metaKey) {
                // 🛠️ ЖЕЛЕЗНЫЙ ФИКС: Гасим микрофон ТОЛЬКО если нажата печатная клавиша (буква/цифра/пробел)
                stopVoiceRecognition(true); 
            }
        } else if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            executeFormSubmission();
        }
    });

    function initSpeechRecognition() {
        const SpeechClass = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechClass) return null;
        const recognition = new SpeechClass();
        recognition.continuous = true;
        recognition.interimResults = true;
        recognition.lang = 'ru-RU';

        recognition.onresult = (event) => {
            let streamBuffer = '';
            for (let i = event.resultIndex; i < event.results.length; ++i) {
                if (event.results[i] && event.results[i][0] && event.results[i][0].transcript) {
                    if (event.results[i].isFinal) streamBuffer += event.results[i][0].transcript;
                }
            }
            
            if (streamBuffer && streamBuffer.trim().length > 0 && streamBuffer !== 'undefined') {
                isAutoFilling = true;
                if (promptInput.value.endsWith(' ') || promptInput.value === '') {
                    promptInput.value += streamBuffer.trim();
                } else {
                    promptInput.value += ' ' + streamBuffer.trim();
                }
                adjustInputHeight();
                evaluateInputMutation();
                isAutoFilling = false;
            }
        };
        
        recognition.onerror = () => stopVoiceRecognition(true);
        recognition.onend = () => { if (isRecordingText) recognition.start(); };
        return recognition;
    }

    async function startVoiceRecognition() {
        if (!activeAudioStream) {
            try { activeAudioStream = await navigator.mediaDevices.getUserMedia({ audio: true }); }
            catch (err) { alert("Доступ к микрофону заблокирован."); return; }
        }
        if (!recognitionInstance) recognitionInstance = initSpeechRecognition();
        
        isRecordingText = true;
        
        // Включаем предохранитель перед очисткой инпута, чтобы не триггерить лаг кнопок
        isAutoFilling = true;
        promptInput.value = ""; 
        isAutoFilling = false;
        
        promptInput.placeholder = "Я вас слушаю, распознаю речь..."; 
        mutationBtn.classList.add('recording-active');
        if (recognitionInstance) recognitionInstance.start();
    }

    function stopVoiceRecognition(keepText = false) {
        isRecordingText = false;
        promptInput.placeholder = "Спросите A.E.G.I.S."; 
        mutationBtn.classList.remove('recording-active');
        
        if (recognitionInstance) {
            try { 
                // 🛠️ ЖЕЛЕЗНЫЙ ФИКС: Намертво обрываем распознавание в фоне Chrome
                recognitionInstance.abort(); 
                recognitionInstance.stop(); 
            } catch(e){}
            recognitionInstance = null; 
        }
        if (activeAudioStream) {
            activeAudioStream.getTracks().forEach(track => {
                track.stop();
                track.enabled = false;
            });
            activeAudioStream = null;
        }
        if (!keepText) promptInput.value = "";
        evaluateInputMutation();
        adjustInputHeight();
    }

    mutationBtn.addEventListener('click', () => {
        if (mutationBtn.classList.contains('text-state')) { executeFormSubmission(); return; }
        if (!isRecordingText) startVoiceRecognition(); else stopVoiceRecognition(true);
    });
// ==========================================================================
// A.E.G.I.S. SYSTEM — INPUT_ENGINE.JS — БЛОК 3: СКРЕПКА, DRAG-AND-DROP И ЛАЙТБОКС
// ==========================================================================

    if (attachBtn) {
        attachBtn.addEventListener('mouseenter', () => {
            clearTimeout(tooltipTimeout);
            if (attachTooltip) { tooltipTimeout = setTimeout(() => { attachTooltip.classList.add('active'); }, 900); }
        });
        attachBtn.addEventListener('mouseleave', () => {
            clearTimeout(tooltipTimeout);
            if (attachTooltip) { attachTooltip.classList.remove('active'); }
        });
        attachBtn.onclick = (e) => {
            e.preventDefault();
            if (hiddenFileInput) hiddenFileInput.click(); 
        };
    }

    if (hiddenFileInput) {
        hiddenFileInput.onchange = (e) => { processSelectedFiles(Array.from(e.target.files)); };
    }

 function processSelectedFiles(files) {
        const ALLOWED = ['docx','xlsx','pptx','pdf','txt','json','sql','lua','py','c','cpp','png','jpg','jpeg','webp','gif'];
        const MAX_SIZE_MB = 50;

        files.forEach(file => {
            // ЖЕЛЕЗНЫЙ ФИКС: Если у файла нет расширения (скриншот из буфера), ставим ему png
            let ext = file.name.includes('.') ? file.name.split('.').pop().toLowerCase() : 'png';
            const sizeMB = file.size / (1024 * 1024);
            if (!ALLOWED.includes(ext) || sizeMB > MAX_SIZE_MB) return; 
            
            if (!uploadedFiles.some(f => f.name === file.name)) {
                const reader = new FileReader();
                const isRawText = ['txt', 'json', 'sql', 'lua', 'py', 'c', 'cpp'].includes(ext);
                
                reader.onload = (e) => {
                    file.cachedContent = e.target.result; 
                    uploadedFiles.push(file);
                    renderFileCard(file, file.type.startsWith('image/'), e.target.result);
                    saveInputStateToCache(); 
                };
                if (isRawText) reader.readAsText(file); else reader.readAsDataURL(file);
            }
        });
        hiddenFileInput.value = '';
    }

    // Перехват картинок из буфера обмена (Нажатие Ctrl + V)
    document.addEventListener('paste', (e) => {
        const items = (e.clipboardData || window.clipboardData).items;
        for (let i = 0; i < items.length; i++) {
            // Если в буфере лежит картинка (скриншот экрана)
            if (items[i].type.indexOf('image') !== -1) {
                const fileBlob = items[i].getAsFile();
                // Генерируем уникальное системное имя для скриншота
                const generatedName = `Скриншот_${Date.now()}.png`;
                const imageFile = new File([fileBlob], generatedName, { type: 'image/png' });
                
                processSelectedFiles([imageFile]); 
                e.preventDefault(); // Блокируем стандартную вставку бинарного мусора в текст
            }
        }
    });

    function renderFileCard(file, isImage, rawData = null) {
        if (!filePreviews) return;
        const tile = document.createElement('div');
        tile.className = 'file-tile';
        tile.dataset.name = file.name;
        tile.setAttribute('title', file.name);
        
        const fileExt = file.name.split('.').pop().toLowerCase();
        const displayExt = isImage ? 'IMG' : fileExt.toUpperCase();

        if (isImage) {
            tile.classList.add('tile-has-image');
            tile.style.backgroundImage = `url('${rawData || file.cachedContent}')`;
        }

        tile.innerHTML = `
            <div class="file-tile-format-badge">${displayExt}</div>
            <span class="file-tile-remove">&times;</span>
            <div class="file-tile-text-info">${file.name}</div>
        `;

        tile.addEventListener('click', (e) => {
            if (!e.target.classList.contains('file-tile-remove')) executeSmartPreview(file, isImage);
        });

        tile.querySelector('.file-tile-remove').addEventListener('click', (e) => {
            e.stopPropagation();
            uploadedFiles = uploadedFiles.filter(f => f.name !== file.name);
            tile.remove();
            saveInputStateToCache(); // Синхронизируем кэш F5 при удалении плитки
        });
        filePreviews.appendChild(tile);
    }

    function executeSmartPreview(file, isImage) {
        const ext = file.name.split('.').pop().toLowerCase();
        const content = file.cachedContent;
        if (!content) return;

        if (isImage) { openLightbox(content, 'image'); return; }
        if (['txt', 'json', 'sql', 'lua', 'py', 'c', 'cpp'].includes(ext)) { openLightbox(content, 'text'); return; }
        if (ext === 'pdf') { openLightbox(content, 'pdf'); return; }

        if (['docx', 'xlsx', 'pptx'].includes(ext)) {
            const base64Data = content.includes(',') ? content.split(',')[1] : content;
            const rawBinaryString = atob(base64Data);
            const filterRegex = /[\u0400-\u04FFA-Za-z0-9\s.,;:!?()""'\-\+=]{6,120}/g;
            const matches = rawBinaryString.match(filterRegex);
            let finalText = "Текст документа пуст.";
            if (matches) {
                let lines = matches.map(l => l.trim()).filter(l => l.length > 5 && !['xml','schemas','props'].some(k => l.toLowerCase().includes(k)));
                lines = [...new Set(lines)];
                if (lines.length > 0) finalText = lines.join('\n\n');
            }
            openLightbox(`[A.E.G.I.S. Читатель Офиса]\n\nФайл: ${file.name}\n\n${finalText}`, 'text');
        }
    }

    const lightbox = document.getElementById('aegisLightbox');
    const lightboxImg = document.getElementById('lightboxImg');

    function openLightbox(source, type) {
        if (!lightbox) return;
        const oldText = document.getElementById('aegisLightboxTextZone');
        const oldPdf = document.getElementById('aegisLightboxPdfZone');
        if (oldText) oldText.remove(); if (oldPdf) oldPdf.remove();

        if (type === 'image' && lightboxImg) { lightboxImg.src = source; lightboxImg.style.display = 'block'; }
        else if (type === 'text') {
            if (lightboxImg) lightboxImg.style.display = 'none';
            const textZone = document.createElement('pre');
            textZone.id = 'aegisLightboxTextZone';
            textZone.style.cssText = 'max-width:80%; max-height:80%; overflow-y:auto; background:#121214; color:#F4F4F5; padding:24px; border-radius:12px; border:1px solid #27272A; font-family:monospace; font-size:14px; line-height:1.6; white-space:pre-wrap; word-break:break-all;';
            textZone.textContent = source; lightbox.appendChild(textZone);
        } else if (type === 'pdf') {
            if (lightboxImg) lightboxImg.style.display = 'none';
            const iframe = document.createElement('iframe');
            iframe.id = 'aegisLightboxPdfZone'; iframe.src = source;
            iframe.style.cssText = 'width:80%; height:85%; border:1px solid #27272A; border-radius:12px; background:#FFF;';
            lightbox.appendChild(iframe);
        }
        lightbox.classList.add('active');
    }

    if (lightbox) {
        lightbox.addEventListener('click', (e) => {
            if (e.target === lightbox || e.target === lightboxImg) {
                lightbox.classList.remove('active');
                setTimeout(() => { 
                    if (lightboxImg) lightboxImg.src = ''; 
                    const txt = document.getElementById('aegisLightboxTextZone'); if (txt) txt.remove();
                    const pdf = document.getElementById('aegisLightboxPdfZone'); if (pdf) pdf.remove();
                }, 200);
            }
        });
    }

     window.addEventListener('dragover', (e) => { 
        e.preventDefault(); 
        e.stopPropagation(); 
    }, false);

    window.addEventListener('drop', (e) => {
        e.preventDefault(); 
        e.stopPropagation();
        
        // 🛠️ ЖЕЛЕЗНЫЙ ФИКС: Исключаем боковые панели и меню из зоны сброса файлов
        const isOverSidebar = e.target.closest('.sidebar') || e.target.closest('.history-sidebar') || e.target.closest('#historyScrollZone');
        if (isOverSidebar) return; // Если бросили над меню чатов — полностью игнорируем

        // Если бросили в любую другую точку рабочей зоны экрана
        if (e.dataTransfer && e.dataTransfer.files.length > 0) {
            processSelectedFiles(Array.from(e.dataTransfer.files));
        }
    }, false);

    function executeFormSubmission() {
        const text = promptInput.value.trim();
        const mode = document.querySelector('.mode-pill.active')?.dataset.mode || 'aegis';
        if (text.length === 0 && uploadedFiles.length === 0) return;
        sessionStorage.removeItem(`aegis_text_${pageKey}`);
        sessionStorage.removeItem(`aegis_files_${pageKey}`);
        window.location.href = `chat.html?prompt=${encodeURIComponent(text)}&mode=${mode}`;
    }

    restoreInputState();
});
