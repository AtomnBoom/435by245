-- Таблица для сессий работы с документами
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    created_at TEXT NOT NULL,
    status TEXT NOT NULL
);

-- Таблица для хранения "живого JSON-дерева" (IR) каждой версии документа.
-- Поле parent_version связывает версии в граф, фиксируя ручные правки человека.
CREATE TABLE IF NOT EXISTS document_versions (
    id TEXT PRIMARY KEY,
    doc_id TEXT NOT NULL,
    parent_version TEXT,
    ir_json TEXT NOT NULL,
    created_at TEXT NOT NULL,
    source TEXT CHECK(source IN ('agent', 'human', 'system')) NOT NULL
);

-- Таблица для самообучения: здесь Джарвис хранит извлеченные кванты опыта
CREATE TABLE IF NOT EXISTS learned_patterns (
    id TEXT PRIMARY KEY,
    task_signature TEXT NOT NULL,
    pattern_json TEXT NOT NULL,
    success_count INTEGER DEFAULT 1,
    last_used_at TEXT NOT NULL
);

-- Иммутабельный (неизменяемый) лог правок для фиксации диффов правок
CREATE TABLE IF NOT EXISTS modification_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    doc_id TEXT NOT NULL,
    from_version TEXT NOT NULL,
    to_version TEXT NOT NULL,
    diff_json TEXT NOT NULL,
    source TEXT CHECK(source IN ('agent', 'human')) NOT NULL,
    created_at TEXT NOT NULL
);

-- Создаем индексы, чтобы поиск по истории документов и опыта работал мгновенно
CREATE INDEX IF NOT EXISTS idx_versions_doc ON document_versions(doc_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_patterns_sig ON learned_patterns(task_signature);
