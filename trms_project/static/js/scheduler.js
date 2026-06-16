document.addEventListener("DOMContentLoaded", () => {
    const el = document.getElementById("enterpriseScheduler");
    if (!el || typeof FullCalendar === "undefined") {
        return;
    }

    const batchFilter = document.getElementById("batchFilter");
    const trainerFilter = document.getElementById("trainerFilter");
    const exportDateInput = document.getElementById("exportDate");
    const downloadButton = document.getElementById("downloadDailyTimetable");
    const modalEl = document.getElementById("schedulerDayModal");
    const modal = modalEl ? new bootstrap.Modal(modalEl) : null;
    const modalDate = document.getElementById("schedulerModalDate");
    const modalBody = document.getElementById("schedulerModalBody");

    function filtersAsQuery() {
        const params = new URLSearchParams();
        if (batchFilter && batchFilter.value) {
            params.set("batch", batchFilter.value);
        }
        if (trainerFilter && trainerFilter.value) {
            params.set("trainer", trainerFilter.value);
        }
        return params;
    }

    function updateExportLink(dateValue) {
        if (!downloadButton) {
            return;
        }
        const params = filtersAsQuery();
        params.set("date", dateValue || (new Date().toISOString().slice(0, 10)));
        downloadButton.href = `${el.dataset.exportUrl}?${params.toString()}`;
    }

    function renderRows(rows) {
        if (!modalBody) {
            return;
        }
        if (!rows.length) {
            modalBody.innerHTML = '<tr><td colspan="9" class="text-center text-muted py-4">No schedule found for this day.</td></tr>';
            return;
        }
        modalBody.innerHTML = rows.map((row) => `
            <tr>
                <td>${row.trainer}</td>
                <td><span class="legend-swatch me-1" style="background:${row.batch_color};"></span>${row.batch}</td>
                <td><span class="legend-swatch me-1" style="background:${row.task_color};"></span>${row.task_type}</td>
                <td>${row.start_time}</td>
                <td>${row.end_time}</td>
                <td>${row.occupancy_status}</td>
                <td>${row.duration}h</td>
                <td>${row.circle}</td>
                <td>${row.description}</td>
            </tr>
        `).join("");
    }

    async function openDayModal(dateStr) {
        if (!modal) {
            return;
        }
        if (exportDateInput) {
            exportDateInput.value = dateStr;
        }
        updateExportLink(dateStr);
        modalDate.textContent = `Timetable for ${dateStr}`;
        modal.show();
        const params = filtersAsQuery();
        const baseUrl = el.dataset.dayUrlTemplate.replace("2000-01-01", dateStr);
        const url = `${baseUrl}?${params.toString()}`;
        try {
            const response = await fetch(url, { headers: { "X-Requested-With": "XMLHttpRequest" } });
            const rows = await response.json();
            renderRows(rows);
        } catch (error) {
            renderRows([]);
        }
    }

    const scheduler = new FullCalendar.Calendar(el, {
        initialView: "timeGridWeek",
        height: "auto",
        slotMinTime: "08:00:00",
        slotMaxTime: "20:00:00",
        slotDuration: "01:00:00",
        nowIndicator: true,
        allDaySlot: false,
        headerToolbar: {
            left: "prev,next today",
            center: "title",
            right: "timeGridDay,timeGridWeek,dayGridMonth",
        },
        events: async (fetchInfo, successCallback, failureCallback) => {
            const params = filtersAsQuery();
            params.set("start", fetchInfo.startStr.slice(0, 10));
            params.set("end", fetchInfo.endStr.slice(0, 10));
            const url = `${el.dataset.eventsUrl}?${params.toString()}`;
            try {
                const response = await fetch(url, { headers: { "X-Requested-With": "XMLHttpRequest" } });
                const events = await response.json();
                successCallback(events);
            } catch (error) {
                failureCallback(error);
            }
        },
        eventDidMount: (info) => {
            info.el.style.borderWidth = "2px";
            info.el.style.borderLeftWidth = "8px";
            info.el.classList.add("scheduler-event");
            const p = info.event.extendedProps || {};
            const tooltip = `
                <div class="small">
                    <div><strong>Trainer:</strong> ${p.trainer || "-"}</div>
                    <div><strong>Batch:</strong> ${p.batch || "-"}</div>
                    <div><strong>Topic:</strong> ${p.task_type || "-"}</div>
                    <div><strong>Time:</strong> ${p.start_time || "-"} - ${p.end_time || "-"}</div>
                    <div><strong>Occupancy %:</strong> ${p.occupancy_percent || 0}%</div>
                </div>`;
            if (typeof tippy !== "undefined") {
                tippy(info.el, { content: tooltip, allowHTML: true, theme: "light-border", placement: "top" });
            }
        },
        dateClick: (info) => {
            openDayModal(info.dateStr);
        },
        eventClick: (info) => {
            openDayModal(info.event.startStr.slice(0, 10));
        },
    });

    scheduler.render();
    updateExportLink(exportDateInput ? exportDateInput.value : null);

    [batchFilter, trainerFilter].forEach((control) => {
        if (!control) {
            return;
        }
        control.addEventListener("change", () => {
            scheduler.refetchEvents();
            updateExportLink(exportDateInput ? exportDateInput.value : null);
        });
    });

    if (exportDateInput) {
        exportDateInput.addEventListener("change", () => updateExportLink(exportDateInput.value));
    }
});
