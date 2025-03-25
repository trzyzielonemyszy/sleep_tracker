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
    console.log('toggleNap called');
    
    const button = document.getElementById('napButton');
    const timerContainer = document.getElementById('timer-container');
    const selectedDate = getUrlParameter('date');

    // Sprawdź, czy przycisk nie jest wyłączony
    if (button.disabled || button.classList.contains('disabled')) {
        console.log('Button is disabled, cannot start nap on non-current date');
        return;
    }

    if (button.textContent === 'START') {
        console.log('Starting nap...');
        // Start nap
        fetch('/start_nap', {
            method: 'POST',
        })
        .then(response => {
            console.log('Start nap fetch response status:', response.status);
            return response.json();
        })
        .then(data => {
            console.log('Start nap response data:', data);
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
            } else {
                console.error('Error in start_nap response:', data.message || 'Unknown error');
                alert('Wystąpił błąd podczas rozpoczynania drzemki.');
            }
        })
        .catch(error => {
            console.error('Error fetching start_nap:', error);
            alert('Wystąpił błąd podczas komunikacji z serwerem.');
        });
    } else {
        console.log('Stopping nap...');
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
        .then(response => {
            console.log('Stop nap fetch response status:', response.status);
            return response.json();
        })
        .then(data => {
            console.log('Stop nap response data:', data);
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
            } else {
                console.error('Error in stop_nap response:', data.message || 'Unknown error');
                alert('Wystąpił błąd podczas kończenia drzemki.');
            }
        })
        .catch(error => {
            console.error('Error fetching stop_nap:', error);
            alert('Wystąpił błąd podczas komunikacji z serwerem.');
        });
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
    
    // Formatowanie dzisiejszej daty jako YYYY-MM-DD
    const now = new Date();
    const today = now.getFullYear() + '-' + 
                  String(now.getMonth() + 1).padStart(2, '0') + '-' + 
                  String(now.getDate()).padStart(2, '0');
    
    // Obsługa przycisku napButton
    const napButton = document.getElementById('napButton');
    if (napButton) {
        // Sprawdź czy jesteśmy na dzisiejszej dacie
        if (selectedDate && selectedDate !== today) {
            // Nie jesteśmy na dzisiejszej dacie - wyłącz przycisk
            napButton.classList.add('disabled');
            napButton.disabled = true;
            console.log('Button disabled - not today\'s date');
        } else {
            // Jesteśmy na dzisiejszej dacie - włącz przycisk
            napButton.classList.remove('disabled');
            napButton.disabled = false;
            // Dodaj obsługę zdarzenia onclick
            napButton.onclick = toggleNap;
            console.log('Button enabled - today\'s date');
        }
    }
    
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
                const timerContainer = document.getElementById('timer-container');
                
                if (napButton && timerContainer) {
                    napButton.textContent = 'STOP';
                    napButton.style.backgroundColor = '#dc3545'; // czerwony kolor dla STOP
                    timerContainer.style.display = 'block';
                    startTimer();
                    updateTimer();
                }
            } else {
                // Jesteśmy na innej dacie niż dzisiejsza, ale jest aktywna drzemka
                // Dodajmy informację dla użytkownika
                const napControl = document.querySelector('.nap-control');
                if (napControl) {
                    // Usuń istniejące alerty, żeby nie duplikować
                    const existingAlerts = napControl.querySelectorAll('.alert');
                    existingAlerts.forEach(alert => alert.remove());
                    
                    const alertDiv = document.createElement('div');
                    alertDiv.className = 'alert';
                    alertDiv.textContent = 'Masz aktywną drzemkę na dzisiejszej dacie';
                    napControl.prepend(alertDiv);
                }
            }
        }
    }

    // Dodaj log do celów debugowania
    console.log('DOMContentLoaded - selectedDate:', selectedDate, 'today:', today);
    console.log('NapButton state:', napButton ? {
        disabled: napButton.disabled,
        classList: napButton.classList.toString(),
        hasClickHandler: (typeof napButton.onclick === 'function')
    } : 'Not found');
}); 