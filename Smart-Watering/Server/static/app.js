const soilText = document.getElementById("soil")
const pumpText = document.getElementById("pump")
const weatherText = document.getElementById("weather")

const ctx = document
    .getElementById("soilChart")
    .getContext("2d")

const labels = []
const values = []

const chart = new Chart(ctx, {

    type: "line",

    data: {
        labels: labels,

        datasets: [{
            label: "Soil Moisture",
            data: values,
            borderWidth: 2,
            tension: 0.3
        }]
    },

    options: {

        responsive: true,

        maintainAspectRatio: false,

        animation: false,

        scales: {
            y: {
                min: 0,
                max: 1024
            }
        }
    }
})

async function updateDashboard(){

    try{

        const response = await fetch("/api/status")

        const data = await response.json()

        soilText.innerText = data.soil
        pumpText.innerText = data.pump

        const weather = data.weather || {}

        weatherText.innerText =
            `Temp: ${weather.temperature || 0}°C
            | Humidity: ${weather.humidity || 0}%
            | Rain: ${weather.rain || false}`

        labels.push(
            new Date().toLocaleTimeString()
        )

        values.push(data.soil)

        if(labels.length > 20){

            labels.shift()
            values.shift()
        }

        chart.update()

    }catch(err){

        console.log(err)
    }
}

updateDashboard()

setInterval(updateDashboard, 1000)