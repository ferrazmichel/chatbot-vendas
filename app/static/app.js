// ========== STATE ==========
let currentTable = "vendas_resumo";
let currentOffset = 0;
const PAGE_SIZE = 25;
let columnFilters = {};
let allRows = [];
let allColumns = [];

// ========== TAB NAVIGATION ==========
function switchTab(tab) {
    document.querySelectorAll(".tab-content").forEach(el => el.classList.remove("active"));
    document.querySelectorAll(".tab").forEach(el => el.classList.remove("active"));
    document.getElementById("tab-" + tab).classList.add("active");
    document.querySelector(`[data-tab="${tab}"]`).classList.add("active");

    if (tab === "dados") loadTable(currentTable);
    if (tab === "kpis") loadKPIs();
}

// ========== CHAT ==========
async function sendMessage(e) {
    e.preventDefault();
    const input = document.getElementById("chatInput");
    const pergunta = input.value.trim();
    if (!pergunta) return;

    addMessage(pergunta, "user");
    input.value = "";
    document.getElementById("sendBtn").disabled = true;

    const typingEl = addTyping();

    try {
        const resp = await fetch("/api/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ pergunta }),
        });
        typingEl.remove();

        if (!resp.ok) {
            const err = await resp.json();
            addMessage("❌ Erro: " + (err.detail || "Falha ao processar"), "bot");
            return;
        }

        const data = await resp.json();
        addBotResponse(data);
    } catch (err) {
        typingEl.remove();
        addMessage("❌ Erro de conexão com o servidor.", "bot");
    } finally {
        document.getElementById("sendBtn").disabled = false;
        document.getElementById("chatInput").focus();
    }
}

function addMessage(text, role) {
    const container = document.getElementById("chatMessages");
    const div = document.createElement("div");
    div.className = "message " + role;
    div.innerHTML = `
        <div class="avatar">${role === "user" ? "👤" : "🤖"}</div>
        <div class="bubble"><p>${escapeHtml(text)}</p></div>
    `;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
    return div;
}

function addBotResponse(data) {
    const container = document.getElementById("chatMessages");
    const div = document.createElement("div");
    div.className = "message bot";

    const sqlId = "sql-" + Date.now();
    let html = `
        <div class="avatar">🤖</div>
        <div class="bubble">
            <p>${formatResponse(data.resposta)}</p>
            <button class="sql-toggle" onclick="toggleSQL('${sqlId}')">📋 Ver SQL gerado</button>
            <div class="sql-block" id="${sqlId}" style="display:none">${escapeHtml(data.sql_gerado)}</div>
        </div>
    `;
    div.innerHTML = html;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}

function addTyping() {
    const container = document.getElementById("chatMessages");
    const div = document.createElement("div");
    div.className = "message bot";
    div.id = "typing";
    div.innerHTML = `
        <div class="avatar">🤖</div>
        <div class="bubble">
            <div class="typing-indicator">
                <span></span><span></span><span></span>
            </div>
        </div>
    `;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
    return div;
}

function toggleSQL(id) {
    const el = document.getElementById(id);
    el.style.display = el.style.display === "none" ? "block" : "none";
}

function formatResponse(text) {
    return text
        .replace(/\n/g, "<br>")
        .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
        .replace(/R\$\s?([\d.,]+)/g, "<strong>R$ $1</strong>");
}

function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}

// ========== DATA TABLE ==========
async function loadTable(table) {
    currentTable = table;
    currentOffset = 0;
    columnFilters = {};

    document.querySelectorAll(".toggle-btn").forEach(btn => {
        btn.classList.toggle("active", btn.textContent.toLowerCase().includes(table.split("_")[1]));
    });

    await fetchTablePage();
}

async function fetchTablePage() {
    try {
        const resp = await fetch(`/api/tables/${currentTable}?limit=${PAGE_SIZE}&offset=${currentOffset}`);
        const data = await resp.json();
        renderTable(data);
    } catch (err) {
        document.getElementById("tableInfo").textContent = "Erro ao carregar dados.";
    }
}

function renderTable(data) {
    const { total, limit, offset, data: rows } = data;
    allRows = rows;

    document.getElementById("tableInfo").textContent =
        `Exibindo ${offset + 1}–${Math.min(offset + limit, total)} de ${total} registros`;

    const thead = document.getElementById("tableHead");
    const tbody = document.getElementById("tableBody");

    if (rows.length === 0) {
        thead.innerHTML = "";
        tbody.innerHTML = "<tr><td>Nenhum dado encontrado.</td></tr>";
        return;
    }

    const columns = Object.keys(rows[0]);
    allColumns = columns;

    thead.innerHTML = "<tr>" + columns.map(c => `<th>${c}</th>`).join("") + "</tr>"
        + "<tr class=\"filter-row\">" + columns.map(c =>
            `<th><input type=\"text\" class=\"col-filter\" data-col=\"${c}\" placeholder=\"Filtrar...\" value=\"${columnFilters[c] || ""}\" oninput=\"applyColumnFilter(this)\"></th>`
        ).join("") + "</tr>";

    renderFilteredRows(rows, columns);
    renderPagination(total, limit, offset);
}

function applyColumnFilter(input) {
    const col = input.dataset.col;
    const val = input.value.trim().toLowerCase();
    if (val) {
        columnFilters[col] = val;
    } else {
        delete columnFilters[col];
    }
    renderFilteredRows(allRows, allColumns);
}

function renderFilteredRows(rows, columns) {
    const tbody = document.getElementById("tableBody");
    const filtered = rows.filter(row => {
        return Object.entries(columnFilters).every(([col, filter]) => {
            const cellVal = String(row[col] ?? "").toLowerCase();
            return cellVal.includes(filter);
        });
    });

    tbody.innerHTML = filtered.map(row => {
        return "<tr>" + columns.map(col => {
            let val = row[col];
            let cls = "";
            if (col === "status_carrinho") {
                cls = ` class="status-${val}"`;
            }
            if (typeof val === "number" && !col.startsWith("id")) {
                val = val.toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
            }
            return `<td${cls}>${val ?? ""}</td>`;
        }).join("") + "</tr>";
    }).join("");

    if (filtered.length === 0) {
        tbody.innerHTML = `<tr><td colspan="${columns.length}" style="text-align:center; color: var(--text-secondary);">Nenhum resultado com os filtros aplicados.</td></tr>`;
    }
}

function renderPagination(total, limit, offset) {
    const el = document.getElementById("pagination");
    const totalPages = Math.ceil(total / limit);
    const currentPage = Math.floor(offset / limit) + 1;

    el.innerHTML = `
        <button class="page-btn" onclick="goPage(${offset - limit})" ${offset <= 0 ? "disabled" : ""}>← Anterior</button>
        <span class="page-info">Página ${currentPage} de ${totalPages}</span>
        <button class="page-btn" onclick="goPage(${offset + limit})" ${offset + limit >= total ? "disabled" : ""}>Próxima →</button>
    `;
}

function goPage(newOffset) {
    currentOffset = Math.max(0, newOffset);
    fetchTablePage();
}

// ========== KPIs ==========
async function loadKPIs() {
    try {
        const resp = await fetch("/api/kpis");
        const data = await resp.json();

        document.getElementById("kpiCards").innerHTML = data.kpis.map(kpi => `
            <div class="kpi-card">
                <h4>${kpi.nome}</h4>
                <div class="formula">${kpi.formula}</div>
                <div class="desc">${kpi.descricao}</div>
            </div>
        `).join("");

        document.getElementById("examplesGrid").innerHTML = data.exemplos_perguntas.map(ex => `
            <div class="example-item" onclick="useExample('${ex}')">${ex}</div>
        `).join("");
    } catch (err) {
        document.getElementById("kpiCards").innerHTML = "<p>Erro ao carregar KPIs.</p>";
    }
}

function useExample(text) {
    switchTab("chat");
    document.getElementById("chatInput").value = text;
    document.getElementById("chatInput").focus();
}

// ========== ENTER KEY ==========
document.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey && document.activeElement.id === "chatInput") {
        sendMessage(e);
    }
});
