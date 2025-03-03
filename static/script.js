let napStartTime = null;
let timerInterval = null;

function toggleNap() {
    const button = document.getElementById('napButton');
    const timerContainer = document.getElementById('timer-container');

    if (button.textContent === 'START') {
        // Start nap
        fetch('/start_nap', {
            method: 'POST',
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                // Konwertujemy string na obiekt Date
                napStartTime = new Date(data.start_time);
                button.textContent = 'STOP';
                button.style.backgroundColor = '#dc3545'; // czerwony kolor dla STOP
                timerContainer.style.display = 'block';
                startTimer();
                
                // Resetujemy licznik
                updateTimer();
            }
        })
        .catch(error => console.error('Error:', error));
    } else {
        // Stop nap
        const endTime = new Date();
        
        fetch('/stop_nap', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                start_time: napStartTime.toISOString(),
                end_time: endTime.toISOString()
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                stopTimer();
                window.location.href = '/';  // Wracamy na stronę główną
            }
        })
        .catch(error => console.error('Error:', error));
    }
}

function startTimer() {
    timerInterval = setInterval(updateTimer, 1000);
}

function stopTimer() {
    if (timerInterval) {
        clearInterval(timerInterval);
    }
}

function updateTimer() {
    if (!napStartTime) return;

    // Pobierz aktualny czas
    const now = new Date();
    
    // Obliczamy różnicę w milisekundach
    const diff = Math.max(0, now - napStartTime);
    
    const hours = Math.floor(diff / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
    const seconds = Math.floor((diff % (1000 * 60)) / 1000);
    
    document.getElementById('hours').textContent = hours.toString().padStart(2, '0');
    document.getElementById('minutes').textContent = minutes.toString().padStart(2, '0');
    document.getElementById('seconds').textContent = seconds.toString().padStart(2, '0');
}

document.addEventListener('DOMContentLoaded', function() {
    const dateFilter = document.getElementById('dateFilter');
    if (dateFilter) {
        dateFilter.addEventListener('change', function() {
            window.location.href = '/?date=' + this.value;
        });
    }
}); 