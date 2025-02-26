const moment = require('moment-timezone');
moment.tz.setDefault('Europe/Warsaw');

// Funkcja pomocnicza do formatowania czasu drzemki
const formatNapTime = (time) => {
  return moment(time).tz('Europe/Warsaw').format('HH:mm');
};

module.exports = {
  formatNapTime
}; 