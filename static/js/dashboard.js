'use strict';

const tempHistory = [];
const pressureHistory = [];
const MAX_HISTORY = 30;

function updateClock() {
    const now = new Date();
    document.getElementById('hora-atual').textContent =
        now.toLocaleTimeString('pt-PT', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
}

async function fetchData() {
    try {
        const response = await fetch('/api/data');
        if (!response.ok) throw new Error('API error');
        const data = await response.json();

        document.getElementById('alerta-erro').style.display = 'none';

        const connected = data.connected !== false;
        const dot = document.getElementById('ponto-conexao');
        const text = document.getElementById('texto-conexao');
        if (connected) {
            dot.classList.remove('offline');
            text.textContent = 'PLC Connected';
        } else {
            dot.classList.add('offline');
            text.textContent = 'PLC Offline';
        }

        document.getElementById('valor-temperatura').textContent = data.Temperature.value;
        document.getElementById('valor-pressao').textContent = data.Pressure.value;
        document.getElementById('valor-nivel').textContent = data.Level.value;
        document.getElementById('valor-velocidade').textContent = data.Agitator.value;
        document.getElementById('tempo-operacao').textContent = data['Elapsed Time'].value + ' min';
        document.getElementById('lotes-produzidos').textContent = data.Batches.value;

        // Progress bars
        const pctTemp = Math.min(100, Math.max(0, ((data.Temperature.value - 18) / (30 - 18)) * 100));
        document.querySelector('#barra-temperatura .barra-preenchimento').style.width = pctTemp + '%';

        const pctPressure = Math.min(100, Math.max(0, ((data.Pressure.value - 98) / (106 - 98)) * 100));
        document.querySelector('#barra-pressao .barra-preenchimento').style.width = pctPressure + '%';

        const pctLevel = Math.min(100, Math.max(0, data.Level.value));
        document.querySelector('#barra-nivel .barra-preenchimento').style.width = pctLevel + '%';

        // Agitator radial gauge
        const maxRPM = 1500;
        const pctSpeed = Math.min(1, data.Agitator.value / maxRPM);
        const circumference = 2 * Math.PI * 40;
        const arc = pctSpeed * circumference;
        document.getElementById('arco-velocidade').setAttribute('stroke-dasharray', arc + ' ' + circumference);
        document.getElementById('texto-velocidade').textContent = data.Agitator.value;

        // Alarms
        document.getElementById('alarme-temperatura').classList.toggle('ativo', data['Temp Alarm'].alarm);
        document.getElementById('texto-alarme-temp').textContent = data['Temp Alarm'].alarm ? 'ACTIVE' : 'OK';

        document.getElementById('alarme-pressao-baixa').classList.toggle('ativo', data['Low Pressure Alarm'].alarm);
        document.getElementById('texto-alarme-pressao-baixa').textContent = data['Low Pressure Alarm'].alarm ? 'ACTIVE' : 'OK';

        document.getElementById('alarme-pressao-alta').classList.toggle('ativo', data['High Pressure Alarm'].alarm);
        document.getElementById('texto-alarme-pressao-alta').textContent = data['High Pressure Alarm'].alarm ? 'ACTIVE' : 'OK';

        // Batch state
        const state = data['State'] ? data['State'].raw : 0;
        const pressValue = data.Pressure.value;

        const btnFill = document.getElementById('btn-fill');
        const btnFerment = document.getElementById('btn-ferment');
        const btnEmpty = document.getElementById('btn-empty');
        const btnClean = document.getElementById('btn-clean');

        // Remove active class from all
        document.querySelectorAll('.batch-btn').forEach(b => b.classList.remove('active'));

        // Enable/disable logic and highlight current state
        if (state === 0) {
            btnFill.disabled = false;
            btnFerment.disabled = true;
            btnEmpty.disabled = true;
            btnClean.disabled = true;
            btnFill.classList.add('active');
        } else if (state === 1) {
            btnFill.disabled = true;
            btnFerment.disabled = false;
            btnEmpty.disabled = true;
            btnClean.disabled = true;
            btnFill.classList.add('active');
        } else if (state === 2) {
            btnFill.disabled = true;
            btnFerment.disabled = true;
            btnEmpty.disabled = false;
            btnClean.disabled = false;
            btnFerment.classList.add('active');
            if (pressValue < 99.0) {
                btnEmpty.disabled = true;
                btnEmpty.title = 'Pressure too low to empty safely';
            } else {
                btnEmpty.title = '';
            }
        } else if (state === 3) {
            btnFill.disabled = true;
            btnFerment.disabled = true;
            btnEmpty.disabled = true;
            btnClean.disabled = false;
            btnEmpty.classList.add('active');
        } else if (state === 4) {
            btnFill.disabled = true;
            btnFerment.disabled = true;
            btnEmpty.disabled = true;
            btnClean.disabled = true;
            btnClean.classList.add('active');
        }

        // Cooling button
        const cooling = data.Cooling.value;
        const btnCooling = document.getElementById('btn-cooling');
        btnCooling.querySelector('span').textContent = cooling === 1 ? 'Cooling ON' : 'Cooling OFF';
        btnCooling.classList.toggle('active', cooling === 1);

        // PRV button
        const prv = data['PRV'] ? data['PRV'].value : 0;
        const btnPrv = document.getElementById('btn-prv');
        btnPrv.querySelector('span').textContent = prv === 1 ? 'PRV ON' : 'PRV OFF';
        btnPrv.classList.toggle('active', prv === 1);

        // Agitator slider
        const speed = data.Agitator.value;
        const slider = document.getElementById('slider-velocidade');
        if (document.activeElement !== slider) {
            slider.value = speed;
            document.getElementById('valor-slider').textContent = speed;
        }

        // Update chart history
        tempHistory.push(data.Temperature.value);
        pressureHistory.push(data.Pressure.value);
        if (tempHistory.length > MAX_HISTORY) {
            tempHistory.shift();
            pressureHistory.shift();
        }
        chart.update();

    } catch (err) {
        console.error('Error updating dashboard:', err);
        document.getElementById('alerta-erro').style.display = 'block';
    }
}

// Trend chart
const ctx = document.getElementById('grafico-tendencia').getContext('2d');
const chart = new Chart(ctx, {
    type: 'line',
    data: {
        labels: Array(MAX_HISTORY).fill(''),
        datasets: [
            {
                label: 'Temperature (C)',
                data: tempHistory,
                borderColor: '#e44c55',
                backgroundColor: 'rgba(228,76,85,0.1)',
                fill: true,
                tension: 0.3,
                pointRadius: 0,
                borderWidth: 2,
                yAxisID: 'y',
            },
            {
                label: 'Pressure (kPa)',
                data: pressureHistory,
                borderColor: '#4ecdc4',
                backgroundColor: 'rgba(78,205,196,0.1)',
                fill: true,
                tension: 0.3,
                pointRadius: 0,
                borderWidth: 2,
                yAxisID: 'y1',
            }
        ]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
            legend: {
                labels: {
                    color: '#cccccc',
                    font: { family: 'Inter', size: 12 },
                    usePointStyle: true,
                }
            }
        },
        scales: {
            x: {
                ticks: { display: false },
                grid: { display: false }
            },
            y: {
                type: 'linear',
                display: true,
                position: 'left',
                min: 15,
                max: 30,
                ticks: {
                    color: '#e44c55',
                    font: { family: 'Inter', size: 11 },
                    stepSize: 5,
                },
                grid: { color: '#2E2C2C' },
                title: {
                    display: true,
                    text: 'Temperature (C)',
                    color: '#e44c55',
                    font: { family: 'Inter', size: 10 }
                }
            },
            y1: {
                type: 'linear',
                display: true,
                position: 'right',
                min: 98,
                max: 106,
                ticks: {
                    color: '#4ecdc4',
                    font: { family: 'Inter', size: 11 },
                    stepSize: 2,
                },
                grid: { drawOnChartArea: false },
                title: {
                    display: true,
                    text: 'Pressure (kPa)',
                    color: '#4ecdc4',
                    font: { family: 'Inter', size: 10 }
                }
            }
        }
    }
});

// Agitator slider
const sliderAgit = document.getElementById('slider-velocidade');
sliderAgit.addEventListener('input', () => {
    document.getElementById('valor-slider').textContent = sliderAgit.value;
});
sliderAgit.addEventListener('change', async () => {
    await sendCommand('agitator', sliderAgit.value);
});

// Cooling button
document.getElementById('btn-cooling').addEventListener('click', async () => {
    const btn = document.getElementById('btn-cooling');
    const turnOn = btn.querySelector('span').textContent.includes('OFF');
    await sendCommand('cooling', turnOn ? 1 : 0);
});

// PRV button
document.getElementById('btn-prv').addEventListener('click', async () => {
    const btn = document.getElementById('btn-prv');
    const open = btn.querySelector('span').textContent === 'PRV OFF';
    await sendCommand('prv', open ? 1 : 0);
});

// State buttons
document.getElementById('btn-fill').addEventListener('click', () => sendCommand('set_state', 1));
document.getElementById('btn-ferment').addEventListener('click', () => sendCommand('set_state', 2));
document.getElementById('btn-empty').addEventListener('click', () => {
    const pressText = document.getElementById('valor-pressao').textContent;
    const press = parseFloat(pressText);
    if (press < 99.0) {
        alert('Cannot start emptying: pressure too low.\nClose PRV or wait for fermentation to raise pressure.');
        return;
    }
    sendCommand('set_state', 3);
});
document.getElementById('btn-clean').addEventListener('click', () => sendCommand('set_state', 4));

async function sendCommand(command, value) {
    try {
        const resp = await fetch('/api/command', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ command, value })
        });
        if (!resp.ok) throw new Error('Command failed');
    } catch (e) {
        console.error('Error sending command:', e);
    }
}

updateClock();
fetchData();
setInterval(updateClock, 1000);
setInterval(fetchData, 2000);