const formatDate = (date) => {
  const warsawDate = new Date(date.toLocaleString('en-US', {
    timeZone: 'Europe/Warsaw'
  }));
  
  return warsawDate.toLocaleString('pl-PL', {
    timeZone: 'Europe/Warsaw',
    dateStyle: 'full',
    timeStyle: 'long'
  });
};

const getCurrentTime = () => {
  return new Date().toLocaleString('pl-PL', {
    timeZone: 'Europe/Warsaw'
  });
};

const formatNapTime = (date) => {
  const warsawDate = new Date(date.toLocaleString('en-US', {
    timeZone: 'Europe/Warsaw'
  }));
  
  return warsawDate.toLocaleString('pl-PL', {
    timeZone: 'Europe/Warsaw',
    hour: '2-digit',
    minute: '2-digit',
    hour12: false
  });
};

module.exports = {
  formatDate,
  getCurrentTime,
  formatNapTime
}; 