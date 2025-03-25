let napStartTime = null;
let timerInterval = null;

// Funkcja do pobierania parametrów z URL
function getUrlParameter(name) {
    name = name.replace(/[\[]/, '\\[').replace(/[\]]/, '\\]');
    const regex = new RegExp('[\\?&]' + name + '=([^&#]*)');
    const results = regex.exec(location.search);
    return results === null ? '' : decodeURIComponent(results[1].replace(/\+/g, ' '));
}

function toggleNap() {
    const button = document.getElementById('napButton');
    const timerContainer = document.getElementById('timer-container');
    const selectedDate = getUrlParameter('date');

    if (button.textContent === 'START') {
        // Start nap
        fetch('/start_nap', {
            method: 'POST',
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                // Konwertujemy string na obiekt Date
                // JavaScript automatycznie obsłuży strefę czasową z ISO string
                napStartTime = new Date(data.start_time);
                console.log('Nap start time (local):', napStartTime.toLocaleString());
                console.log('Nap start time (ISO):', napStartTime.toISOString());
                
                // Zapisujemy czas rozpoczęcia drzemki w localStorage
                localStorage.setItem('napStartTime', napStartTime.toISOString());
                localStorage.setItem('napActive', 'true');
                
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
                
                // Usuwamy dane o drzemce z localStorage
                localStorage.removeItem('napStartTime');
                localStorage.removeItem('napActive');
                
                // Jeśli to sen nocny, zapytaj czy chce ocenić sen teraz
                if (data.is_night_sleep) {
                    if (confirm('Czy chcesz ocenić jakość snu teraz?')) {
                        window.location.href = '/rate_sleep/' + data.record_id + (selectedDate ? '?date=' + selectedDate : '');
                    } else {
                        window.location.href = '/' + (selectedDate ? '?date=' + selectedDate : '');  // Wracamy na stronę główną
                    }
                } else {
                    window.location.href = '/' + (selectedDate ? '?date=' + selectedDate : '');  // Wracamy na stronę główną
                }
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

// Sprawdzamy przy ładowaniu strony, czy drzemka była aktywna
document.addEventListener('DOMContentLoaded', function() {
    // Obsługa filtra daty
    const dateFilter = document.getElementById('dateFilter');
    const selectedDate = getUrlParameter('date');
    const today = new Date().toISOString().split('T')[0]; // Format YYYY-MM-DD
    
    if (dateFilter) {
        dateFilter.addEventListener('change', function() {
            // Jeśli drzemka jest aktywna i użytkownik chce zmienić datę, wyświetl ostrzeżenie
            const isNapActive = localStorage.getItem('napActive') === 'true';
            if (isNapActive && this.value !== today) {
                if (confirm('Masz aktywną drzemkę. Zmiana daty spowoduje anulowanie bieżącej drzemki. Czy chcesz kontynuować?')) {
                    // Użytkownik potwierdził - anuluj drzemkę i przejdź do wybranej daty
                    localStorage.removeItem('napStartTime');
                    localStorage.removeItem('napActive');
                    window.location.href = '/?date=' + this.value;
                } else {
                    // Użytkownik anulował - przywróć poprzednią wartość selektora daty
                    this.value = selectedDate || today;
                    return;
                }
            } else {
                window.location.href = '/?date=' + this.value;
            }
        });
    }
    
    // Sprawdzamy, czy drzemka jest aktywna
    const isNapActive = localStorage.getItem('napActive') === 'true';
    if (isNapActive) {
        const storedStartTime = localStorage.getItem('napStartTime');
        if (storedStartTime) {
            // Sprawdź, czy jesteśmy na dzisiejszej dacie - tylko wtedy pokaż aktywną drzemkę
            if (!selectedDate || selectedDate === today) {
                napStartTime = new Date(storedStartTime);
                const button = document.getElementById('napButton');
                const timerContainer = document.getElementById('timer-container');
                
                if (button && timerContainer) {
                    button.textContent = 'STOP';
                    button.style.backgroundColor = '#dc3545'; // czerwony kolor dla STOP
                    timerContainer.style.display = 'block';
                    startTimer();
                    updateTimer();
                }
            } else {
                // Jesteśmy na innej dacie niż dzisiejsza, ale jest aktywna drzemka
                // Dodajmy informację dla użytkownika
                const napControl = document.querySelector('.nap-control');
                if (napControl) {
                    const alertDiv = document.createElement('div');
                    alertDiv.className = 'alert';
                    alertDiv.textContent = 'Masz aktywną drzemkę na dzisiejszej dacie';
                    napControl.prepend(alertDiv);
                }
            }
        }
    }
}); 