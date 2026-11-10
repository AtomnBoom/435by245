// ==========================================================================
// A.E.G.I.S. SYSTEM — INDEX.JS — БЛОК 1: ИНИЦИАЛИЗАЦИЯ И СЛУЧАЙНЫЕ ПРИВЕТСТВИЯ
// ==========================================================================

document.addEventListener('DOMContentLoaded', () => {
    const welcomeTitle = document.getElementById('welcomeTitle');
    const btnCapabilities = document.getElementById('btnCapabilities');
    const btnInteresting = document.getElementById('btnInteresting');
    const lightbox = document.getElementById('aegisLightbox');

    // СТРОГИЙ ПРЕДОХРАНИТЕЛЬ: Если элементов главной нет (мы в чате) — полностью выходим
    if (!welcomeTitle) return;

    // 🛠️ РЕАЛИЗАЦИЯ: Рендер случайных приветствий искусственного интеллекта
    const welcomePhrases = [
        "С чего начнём?",
        "Чем помочь?",
        "A.E.G.I.S. готов к работе.",
        "Какой запрос?",
        "Какие задачи решить?",
        "Привет Бро!"
    ];
    
    // Задаем случайную фразу при каждом открытии главного экрана
    welcomeTitle.textContent = welcomePhrases[Math.floor(Math.random() * welcomePhrases.length)];
// ==========================================================================
// A.E.G.I.S. SYSTEM — INDEX.JS — БЛОК 2: МОДАЛЬНЫЕ ОКНА ИНТЕРАКТИВНЫХ ПОДСКАЗОК
// ==========================================================================

    // Функция, которая выводит ответ ИИ-агента прямо поверх главной страницы
    async function showMainModalResponse(promptTitle, hiddenPrompt) {
        if (!lightbox) return;
        
        // Рендерим структуру модального окна внутри готового лайтбокса
        lightbox.innerHTML = `
            <div class="aegis-modal-window" style="background: #121214; border: 1px solid #27272A; padding: 24px; border-radius: 12px; width: 90%; max-width: 600px; color: #F4F4F5; box-shadow: 0 20px 50px rgba(0,0,0,0.8); animation: fadeInVoice 0.2s ease-out;">
                <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #27272A; padding-bottom: 12px; margin-bottom: 16px;">
                    <h3 style="margin: 0; font-size: 16px; color: #22C55E; font-weight: 500; letter-spacing: 0.3px;">${promptTitle}</h3>
                    <span style="font-size: 24px; cursor: pointer; color: #71717A; user-select: none;" id="closeMainModalBtn">&times;</span>
                </div>
                <div style="font-size: 14px; line-height: 1.6; color: #D4D4D8;" id="modalAiTextZone">A.E.G.I.S. формирует ответ ядра...</div>
            </div>
        `;
        lightbox.classList.add('active');

        // Вешаем событие закрытия на крестик модального окна
        document.getElementById('closeMainModalBtn').onclick = () => {
            lightbox.classList.remove('active');
        };

        try {
            // ТОЧКА ИНТЕГРАЦИИ: В будущем здесь будет fetch() запрос к вашему Python-серверу:
            // const response = await fetch('http://localhost:8190/api/prompt', { method: 'POST', body: JSON.stringify({ prompt: hiddenPrompt }) });
            // const data = await response.json();
            
            setTimeout(() => {
                const textZone = document.getElementById('modalAiTextZone');
                if (!textZone) return;
                
                // ИСПРАВЛЕНО: Выводим развернутые профессиональные отчеты в зависимости от кнопки
                if (hiddenPrompt.includes('умеешь')) {
                    textZone.innerHTML = `
                        Я — автономный десктопный ИИ-агент <b>A.E.G.I.S.</b>, спроектированный для комплексного управления локальными и сетевыми задачами. Мой текущий стек возможностей:<br><br>
                        • 📄 <b>ГОСТ Читатель документов:</b> Глубокий парсинг, извлечение текста и анализ метаданных из файлов форматов <i>.docx, .xlsx, .pptx, .pdf</i>.<br>
                        • 🌐 <b>Автономное Веб-исследование:</b> Многопоточный сбор информации, сканирование URL-адресов и умная саммаризация сетевых данных.<br>
                        • 🛠️ <b>Docker-песочница:</b> Изолированная компиляция, валидация исходного кода по ГОСТ-стандартам и автоматическое исправление синтаксических ошибок ИИ-ядром.
                    `;
                } else {
                    textZone.innerHTML = `
                        <b>Анализ ваших предпочтений завершен. Актуальная сводка новостей из сети:</b><br><br>
                        1. 🧠 <b>Локальные нейросети:</b> Модели класса Qwen получили оптимизацию контекста, увеличив скорость работы в изолированных Windows-средах на 40%.<br>
                        2. 🛠️ <b>Docker-контейнеризация:</b> Разработан новый асинхронный метод проброса бинарных компиляторов, ускоряющий авто-починку кода в песочнице.<br>
                        3. 🔊 <b>Голосовые интерфейсы:</b> Стандарты WebSpeech API научились полностью освобождать аудиокарту ПК при деактивации листенеров, предотвращая фоновые утечки звука.
                    `;
                }
            }, 600); // Имитация быстрой генерации ответа локальной моделью

        } catch (err) {
            const textZone = document.getElementById('modalAiTextZone');
            if (textZone) textZone.textContent = "Ошибка связи с локальным ИИ-сервером A.E.G.I.S.";
        }
    }

    // 🛠️ РЕАЛИЗАЦИЯ: Привязка скрытых промптов к кнопкам подсказок
    if (btnCapabilities) {
        btnCapabilities.addEventListener('click', (e) => {
            e.preventDefault();
            showMainModalResponse("Профессиональный отчет: Навыки A.E.G.I.S.", "Расскажи, что ты умеешь делать?");
        });
    }

    if (btnInteresting) {
        btnInteresting.addEventListener('click', (e) => {
            e.preventDefault();
            showMainModalResponse("Персональная лента новостей", "покажи интересные новости под мои предпочтения");
        });
    }
});
