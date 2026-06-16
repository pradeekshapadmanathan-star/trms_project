window.renderBarChart = function (canvasId, config) {
    const canvas = document.getElementById(canvasId);
    if (!canvas || !config || !config.labels || !config.labels.length) {
        return;
    }

    const barColors = (config.values || []).map((value, index) => {
        const palette = ["#2563eb", "#16a34a", "#f97316", "#7c3aed", "#0891b2", "#dc2626"];
        return palette[index % palette.length];
    });

    new Chart(canvas, {
        type: "bar",
        data: {
            labels: config.labels,
            datasets: [{
                label: config.label || "Value",
                data: config.values,
                backgroundColor: barColors,
                borderRadius: 10,
                maxBarThickness: 34,
            }],
        },
        options: {
            responsive: true,
            plugins: {
                legend: { display: false },
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: { color: "#e2e8f0" },
                    ticks: { color: "#64748b" },
                },
                x: {
                    grid: { display: false },
                    ticks: { color: "#64748b" },
                },
            },
        },
    });
};

window.renderPieChart = function (canvasId, config) {
    const canvas = document.getElementById(canvasId);
    if (!canvas || !config || !config.labels || !config.labels.length) {
        return;
    }

    const taskColorMap = {
        training: "#16a34a",
        assessment: "#2563eb",
        free: "#9ca3af",
        deck: "#7c3aed",
        project: "#f97316",
        leave: "#facc15",
        holiday: "#dc2626",
        meeting: "#92400e",
        content: "#0ea5e9",
    };
    const pieColors = (config.labels || []).map((label, index) => {
        const key = String(label || "").toLowerCase().trim();
        return taskColorMap[key] || ["#2563eb", "#60a5fa", "#22c55e", "#f97316", "#7c3aed"][index % 5];
    });

    new Chart(canvas, {
        type: "pie",
        data: {
            labels: config.labels,
            datasets: [{
                data: config.values,
                backgroundColor: pieColors,
                borderColor: "#ffffff",
                borderWidth: 3,
            }],
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: "bottom",
                    labels: {
                        color: "#475569",
                        padding: 18,
                    },
                },
            },
        },
    });
};

function renderScheduleRows(rows) {
    const tbody = document.getElementById("scheduleModalBody");
    if (!tbody) {
        return;
    }

    if (!rows.length) {
        tbody.innerHTML = '<tr><td colspan="4" class="text-center text-muted py-4">No schedules available</td></tr>';
        return;
    }

    tbody.innerHTML = rows.map((row) => `
        <tr>
            <td>${row.trainer}</td>
            <td>${row.task}</td>
            <td>${row.hours}</td>
            <td>${row.status}</td>
        </tr>
    `).join("");
}

async function loadManagerSchedule(date, template) {
    const url = template.replace("2000-01-01", date);
    const response = await fetch(url, {
        headers: { "X-Requested-With": "XMLHttpRequest" },
    });

    if (!response.ok) {
        throw new Error("Failed to fetch schedule");
    }

    return response.json();
}

document.addEventListener("DOMContentLoaded", () => {
    const calendarEl = document.getElementById("calendar");
    const calendarDebug = document.getElementById("calendarDebug");

    if (calendarEl) {
        let events = [];
        try {
            events = JSON.parse(calendarEl.dataset.events || "[]");
        } catch (error) {
            if (calendarDebug) {
                calendarDebug.textContent = "Calendar data parse error. Please refresh.";
            }
            return;
        }

        const batchEvents = events.filter((event) => String(event.title || "").startsWith("Batch:"));
        if (calendarDebug) {
            calendarDebug.textContent = `Loaded events: ${events.length} | Batch events: ${batchEvents.length}`;
        }

        const canOpenSchedule = calendarEl.dataset.scheduleEnabled === "true";
        const scheduleTemplate = calendarEl.dataset.scheduleUrlTemplate;
        const scheduleModalElement = document.getElementById("scheduleModal");
        const scheduleModalDate = document.getElementById("scheduleModalDate");
        const scheduleModal = scheduleModalElement ? new bootstrap.Modal(scheduleModalElement) : null;

        const calendar = new FullCalendar.Calendar(calendarEl, {
            initialView: "dayGridMonth",
            height: "auto",
            eventDisplay: "block",
            headerToolbar: {
                left: "prev,next today",
                center: "title",
                right: "dayGridMonth,timeGridWeek",
            },
            events,
            eventDidMount: function (info) {
                if (String(info.event.title || "").startsWith("Batch:")) {
                    info.el.style.backgroundColor = "#20c997";
                    info.el.style.borderColor = "#20c997";
                    info.el.style.color = "#0f172a";
                    info.el.style.fontWeight = "600";
                }
            },
            dateClick: async function (info) {
                if (!canOpenSchedule || !scheduleModal) {
                    return;
                }

                scheduleModalDate.textContent = `Schedule for ${info.dateStr}`;
                renderScheduleRows([]);
                scheduleModal.show();

                try {
                    const rows = await loadManagerSchedule(info.dateStr, scheduleTemplate);
                    renderScheduleRows(rows);
                } catch (error) {
                    renderScheduleRows([]);
                    if (scheduleModalDate) {
                        scheduleModalDate.textContent = `Unable to load schedule for ${info.dateStr}`;
                    }
                }
            },
        });
        calendar.render();
    }
});
