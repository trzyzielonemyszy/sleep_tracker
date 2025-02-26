// Funkcja do zapisywania czasu rozpoczęcia drzemki
const startNapTime = () => {
  return new Date();
};

// Funkcja do zapisywania czasu zakończenia drzemki
const stopNapTime = () => {
  return new Date();
};

// Funkcja do formatowania wyświetlanego czasu drzemki
const formatNapTimeDisplay = (timestamp) => {
  const date = new Date(timestamp);
  return date.toLocaleTimeString('pl-PL', {
    hour: '2-digit',
    minute: '2-digit',
    hour12: false
  });
};

module.exports = {
  startNapTime,
  stopNapTime,
  formatNapTimeDisplay
}; 