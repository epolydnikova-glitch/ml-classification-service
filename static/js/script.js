document.addEventListener("DOMContentLoaded", function () {
    const deleteForms = document.querySelectorAll(".delete-form");
    deleteForms.forEach(function (form) {
        form.addEventListener("submit", function (event) {
            const confirmDelete = confirm("Вы уверены, что хотите удалить этот расчет из истории?");
            if (!confirmDelete) {
                event.preventDefault();
            }
        });
    });

    const awardForm = document.getElementById("awardForm");
    if (awardForm) {
        awardForm.addEventListener("submit", function (event) {
            event.preventDefault();

            const customIdInput = awardForm.querySelector("input[name='custom_id']");
            if (customIdInput && !customIdInput.disabled) {
                const rawId = customIdInput.value.trim();
                if (rawId !== "") {
                    const idRegex = /^[1-9][0-9]*$/;
                    if (!idRegex.test(rawId)) {
                        alert("Ошибка: ID должен быть целым положительным числом (без букв, пробелов, нуля в начале).");
                        customIdInput.focus();
                        return;
                    }
                }
            }

            const vkladInput = awardForm.querySelector("input[name='vklad']");
            if (vkladInput && vkladInput.value.trim() !== "") {
                const val = parseFloat(vkladInput.value);
                if (isNaN(val) || val < 0 || val > 100) {
                    alert("Ошибка: Процент вклада должен быть числом от 0 до 100.");
                    vkladInput.focus();
                    return;
                }
            }

            const formData = new FormData(awardForm);
            fetch("/predict", {
                method: "POST",
                body: formData,
                headers: {
                    "X-Requested-With": "XMLHttpRequest"
                }
            })
            .then(response => {
                const contentType = response.headers.get("content-type");
                if (contentType && contentType.includes("application/json")) {
                    return response.json().then(data => ({ json: data }));
                } else {
                    window.location.href = "/";
                    return null;
                }
            })
            .then(result => {
                if (result && result.json) {
                    if (result.json.error) {
                        alert("Ошибка: " + result.json.error);
                    } else {
                        showResultModal(result.json);
                    }
                }
            })
            .catch(error => {
                console.error("Ошибка сети:", error);
                alert("Произошла сетевая ошибка. Попробуйте снова.");
            });
        });

        const clearBtn = document.getElementById("clearBtn");
        if (clearBtn) {
            clearBtn.addEventListener("click", function () {
                awardForm.reset();
                awardForm.querySelectorAll("select").forEach(select => {
                    const defaultOption = select.querySelector('option[value=""]');
                    if (defaultOption) select.value = "";
                });
                const customIdInput = document.getElementById("custom_id");
                if (customIdInput && !customIdInput.disabled) customIdInput.value = "";
                const fp = document.querySelector("#data_vidachi")._flatpickr;
                if (fp) fp.clear();
            });
        }

        const resultModal = document.getElementById("resultModal");
        if (resultModal) {
            const modalCloseBtn = document.getElementById("modalCloseBtn");
            if (modalCloseBtn) {
                modalCloseBtn.addEventListener("click", () => hideModal(resultModal));
            }
            resultModal.addEventListener("click", (e) => {
                if (e.target === resultModal) hideModal(resultModal);
            });
            document.addEventListener("keydown", (e) => {
                if (e.key === "Escape" && resultModal.classList.contains("modal-overlay--visible")) {
                    hideModal(resultModal);
                }
            });
        }
    }

    function showResultModal(data) {
        const modal = document.getElementById("resultModal");
        const body = document.getElementById("modalBody");
        if (!modal || !body) return;

        const verdict = data.awarded_prediction || "—";
        const probability = data.awarded_probability || 0;
        let categoryClass = "medium";
        if (probability >= 70) categoryClass = "high";
        else if (probability < 40) categoryClass = "low";

        body.innerHTML = `
            <div class="result-block">
                <div class="result-block__score">${probability}%</div>
                <span class="result-block__category result-block__category--${categoryClass}">${verdict}</span>
                <p class="result-block__message">Прогноз успешно рассчитан и сохранён.</p>
            </div>
        `;

        const newBtn = document.getElementById("modalNewBtn");
        const historyBtn = document.getElementById("modalHistoryBtn");

        newBtn.style.display = "inline-flex";
        historyBtn.style.display = "inline-flex";

        modal.classList.add("modal-overlay--visible");
        document.body.style.overflow = "hidden";
        document.getElementById("modalCloseBtn").focus();
    }

    function hideModal(modal) {
        modal.classList.remove("modal-overlay--visible");
        document.body.style.overflow = "";
    }

    const historyTableBody = document.getElementById("historyTableBody");
    if (historyTableBody) {
        const searchInput = document.getElementById("searchId");
        const clearSearchBtn = document.getElementById("clearSearchBtn");
        const deleteSelectedBtn = document.getElementById("deleteSelectedBtn");
        const selectAllCheckbox = document.getElementById("selectAll");
        const detailModal = document.getElementById("detailModal");
        const detailModalBody = document.getElementById("detailModalBody");
        const detailModalCloseBtn = document.getElementById("detailModalCloseBtn");
        const detailModalEditBtn = document.getElementById("detailModalEditBtn");
        let currentEditId = null;

        searchInput.addEventListener("input", function () {
            const filter = this.value.toUpperCase();
            const rows = document.querySelectorAll("#historyTableBody tr");
            rows.forEach(row => {
                const idCell = row.querySelector(".col-id");
                if (!idCell) return;
                const id = idCell.textContent.toUpperCase();
                row.style.display = id.includes(filter) ? "" : "none";
            });
        });
        clearSearchBtn.addEventListener("click", () => {
            searchInput.value = "";
            document.querySelectorAll("#historyTableBody tr").forEach(row => row.style.display = "");
            searchInput.focus();
        });

        function updateSelectedCount() {
            const checked = document.querySelectorAll(".row-checkbox:checked");
            deleteSelectedBtn.disabled = checked.length === 0;
            deleteSelectedBtn.textContent = checked.length > 0 ? `🗑 Удалить выбранные (${checked.length})` : "🗑 Удалить выбранные";
        }
        document.querySelectorAll(".row-checkbox").forEach(cb => {
            cb.addEventListener("change", updateSelectedCount);
        });
        selectAllCheckbox.addEventListener("change", function () {
            document.querySelectorAll(".row-checkbox").forEach(cb => cb.checked = this.checked);
            updateSelectedCount();
        });
        updateSelectedCount();

        deleteSelectedBtn.addEventListener("click", function () {
            const checked = document.querySelectorAll(".row-checkbox:checked");
            if (checked.length === 0) return;
            if (!confirm(`Удалить ${checked.length} записей?`)) return;
            const ids = Array.from(checked).map(cb => cb.dataset.id);
            let completed = 0;
            ids.forEach(id => {
                fetch(`/delete/${id}`, { method: "POST" })
                .then(() => {
                    completed++;
                    if (completed === ids.length) {
                        window.location.reload();
                    }
                })
                .catch(() => {
                    alert(`Ошибка при удалении записи ${id}`);
                    window.location.reload();
                });
            });
        });

        document.querySelectorAll(".detail-btn").forEach(btn => {
            btn.addEventListener("click", function () {
                const record = JSON.parse(this.dataset.record);
                showDetailModal(record);
            });
        });

        detailModalEditBtn.addEventListener("click", function () {
            if (currentEditId) {
                window.location.href = `/prediction?edit=${currentEditId}`;
            }
        });

        detailModalCloseBtn.addEventListener("click", () => hideModal(detailModal));
        detailModal.addEventListener("click", (e) => {
            if (e.target === detailModal) hideModal(detailModal);
        });
        document.addEventListener("keydown", (e) => {
            if (e.key === "Escape" && detailModal.classList.contains("modal-overlay--visible")) {
                hideModal(detailModal);
            }
        });

        function showDetailModal(record) {
            const body = detailModalBody;
            const created = record.created_at ? new Date(record.created_at).toLocaleString() : '—';
            let html = `
                <div class="result-block">
                    <div class="result-block__score">${record.awarded_probability || 0}%</div>
                    <span class="result-block__category result-block__category--${(record.awarded_probability || 0) >= 70 ? 'high' : ((record.awarded_probability || 0) >= 40 ? 'medium' : 'low')}">${record.awarded_prediction || '—'}</span>
                    <p class="result-block__message">Создан: ${created}</p>
                </div>
                <table class="detail-table">
                    <thead><tr><th>Параметр</th><th>Значение</th></tr></thead>
                    <tbody>`;

            const fields = [
                ['ID', record.id],
                ['Google Scholar', record.google_scholar == 1 ? 'Да' : (record.google_scholar == 0 ? 'Нет' : '—')],
                ['Scopus', record.scopus == 1 ? 'Да' : (record.scopus == 0 ? 'Нет' : '—')],
                ['Web of Science', record.web_of_science == 1 ? 'Да' : (record.web_of_science == 0 ? 'Нет' : '—')],
                ['РИНЦ', record.rinc == 1 ? 'Да' : (record.rinc == 0 ? 'Нет' : '—')],
                ['ВАК', record.vak == 1 ? 'Да' : (record.vak == 0 ? 'Нет' : '—')],
                ['Вклад %', record.vklad != null ? record.vklad : '—'],
                ['Вид деятельности', record.vid_deyatelnosti || '—'],
                ['Вид достижения', record.vid_dostizheniya || '—'],
                ['Уровень мероприятия', record.uroven_meropriyatiya || '—'],
                ['Уровень участия', record.uroven_uchastiya || '—'],
                ['Авторы', record.autori || '—'],
                ['Наименование статьи', record.naimenovanie_stati || '—'],
                ['Подписант', record.podpisant || '—'],
                ['Ссылки на новости', record.ssilki_na_novosti || '—'],
                ['Номер патента', record.nomer_patenta || '—'],
                ['Номер удостоверения', record.nomer_udostovereniya || '—'],
                ['Ступень', record.stupen || '—'],
                ['Дата выдачи', record.data_vidachi || '—'],
                ['Создано', created]
            ];

            fields.forEach(([label, value]) => {
                html += `<tr><td>${label}</td><td>${value}</td></tr>`;
            });

            html += '</tbody></table>';
            body.innerHTML = html;
            currentEditId = record.id;
            detailModal.classList.add("modal-overlay--visible");
            document.body.style.overflow = "hidden";
            detailModalCloseBtn.focus();
        }
    }
});