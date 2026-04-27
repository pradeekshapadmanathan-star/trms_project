window.renderBarChart = function (canvasId, config) {
    const canvas = document.getElementById(canvasId);
    if (!canvas || !config || !config.labels || !config.labels.length) {
        return;
    }

    new Chart(canvas, {
        type: "bar",
        data: {
            labels: config.labels,
            datasets: [{
                label: config.label || "Value",
                data: config.values,
                backgroundColor: "#2563eb",
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

    new Chart(canvas, {
        type: "pie",
        data: {
            labels: config.labels,
            datasets: [{
                data: config.values,
                backgroundColor: ["#2563eb", "#60a5fa", "#93c5fd", "#bfdbfe", "#1d4ed8"],
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

    if (calendarEl) {
        const events = JSON.parse(calendarEl.dataset.events || "[]");
        const canOpenSchedule = calendarEl.dataset.scheduleEnabled === "true";
        const scheduleTemplate = calendarEl.dataset.scheduleUrlTemplate;
        const scheduleModalElement = document.getElementById("scheduleModal");
        const scheduleModalDate = document.getElementById("scheduleModalDate");
        const scheduleModal = scheduleModalElement ? new bootstrap.Modal(scheduleModalElement) : null;

        const calendar = new FullCalendar.Calendar(calendarEl, {
            initialView: "dayGridMonth",
            height: "auto",
            headerToolbar: {
                left: "prev,next today",
                center: "title",
                right: "dayGridMonth,timeGridWeek",
            },
            events,
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
