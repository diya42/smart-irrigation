function getRandomValue(min, max) {
    return (Math.random() * (max - min) + min).toFixed(2);
}

function updateSensorData() {
    document.getElementById("humidity").innerText = getRandomValue(30, 80);
    document.getElementById("temperature").innerText = getRandomValue(20, 40);
    document.getElementById("moisture").innerText = getRandomValue(10, 90);
}

// Update values every 5 minutes (300,000 ms)
setInterval(updateSensorData, 300000);

// Initial load
updateSensorData();

document.getElementById("sensor-button").addEventListener("click", function(event) {
    event.stopPropagation();  // Prevents interference with other event listeners
    window.location.href = "sensor.html"; 
});

