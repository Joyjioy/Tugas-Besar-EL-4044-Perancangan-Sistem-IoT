console.log("APP JS TERBARU KEBACA")

const soilText = document.getElementById("soil")
const soilStatusText = document.getElementById("soilStatus")
const pumpText = document.getElementById("pump")
const sensorStatusText = document.getElementById("sensorStatus")
const lastUpdateText = document.getElementById("lastUpdate")
const weatherText = document.getElementById("weather")
const recommendationText = document.getElementById("recommendation")

const totalReadingsText = document.getElementById("totalReadings")
const averageSoilText = document.getElementById("averageSoil")
const minSoilText = document.getElementById("minSoil")
const maxSoilText = document.getElementById("maxSoil")
const pumpOnCountText = document.getElementById("pumpOnCount")
const rainCountText = document.getElementById("rainCount")

const chartCanvas = document.getElementById("soilChart")

const labels = []
const values = []

let chart = null

if (chartCanvas) {
    const ctx = chartCanvas.getContext("2d")

    chart = new Chart(ctx, {
        type: "line",

        data: {
            labels: labels,
            datasets: [{
                label: "Soil Moisture",
                data: values,
                borderWidth: 3,
                tension: 0.35,
                fill: false
            }]
        },

        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: false,

            plugins: {
                legend: {
                    display: true
                }
            },

            scales: {
                y: {
                    min: 0,
                    max: 1024
                }
            }
        }
    })
}

function setText(element, value) {
    if (element) {
        element.innerText = value
    }
}

function setSoilStatusClass(status) {
    if (!soilStatusText) return

    soilStatusText.className = "metric-change"

    if (status === "Kering") {
        soilStatusText.classList.add("dry")
    }
    else if (status === "Normal") {
        soilStatusText.classList.add("normal")
    }
    else if (status === "Basah") {
        soilStatusText.classList.add("wet")
    }
}

function setSensorStatusClass(status) {
    if (!sensorStatusText) return

    sensorStatusText.classList.remove("online", "offline")

    if (status === "Online") {
        sensorStatusText.classList.add("online")
    }
    else {
        sensorStatusText.classList.add("offline")
    }
}

async function updateDashboard() {
    try {
        const response = await fetch("/api/status")

        if (!response.ok) {
            throw new Error(`/api/status error: ${response.status}`)
        }

        const data = await response.json()

        console.log("STATUS:", data)

        setText(soilText, data.soil ?? 0)
        setText(pumpText, data.pump ?? "OFF")

        const soilStatus = data.soil_status || "Unknown"
        setText(soilStatusText, soilStatus)
        setSoilStatusClass(soilStatus)

        const sensorStatus = data.sensor_status || "Offline"
        setText(sensorStatusText, sensorStatus)
        setSensorStatusClass(sensorStatus)

        if (data.seconds_since_update === null || data.seconds_since_update === undefined) {
            setText(lastUpdateText, "No data received")
        } else {
            setText(lastUpdateText, `Last update: ${data.seconds_since_update}s ago`)
        }

        setText(
            recommendationText,
            data.recommendation || "Menunggu data sensor."
        )

        const weather = data.weather || {}
        const rainStatus = weather.rain ? "Hujan" : "Tidak hujan"

        setText(
            weatherText,
            `Temp: ${weather.temperature || 0}°C
| Humidity: ${weather.humidity || 0}%
| Rain: ${rainStatus}`
        )

        if (chart && data.soil !== undefined) {
            labels.push(new Date().toLocaleTimeString())
            values.push(data.soil)

            if (labels.length > 20) {
                labels.shift()
                values.shift()
            }

            chart.update()
        }

    } catch (err) {
        console.error("updateDashboard failed:", err)
    }
}

async function updateStats() {
    try {
        const response = await fetch("/api/stats")

        if (!response.ok) {
            throw new Error(`/api/stats error: ${response.status}`)
        }

        const stats = await response.json()

        console.log("STATS:", stats)

        setText(totalReadingsText, stats.total_readings ?? 0)
        setText(averageSoilText, stats.average_soil ?? 0)
        setText(minSoilText, stats.min_soil ?? 0)
        setText(maxSoilText, stats.max_soil ?? 0)
        setText(pumpOnCountText, stats.pump_on_count ?? 0)
        setText(rainCountText, stats.rain_count ?? 0)

    } catch (err) {
        console.error("updateStats failed:", err)
    }
}

function updateAll() {
    updateDashboard()
    updateStats()
}

updateAll()
setInterval(updateAll, 1000)