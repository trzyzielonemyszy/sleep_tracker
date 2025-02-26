// Utility function to ensure all dates are displayed in Warsaw time
export const formatToWarsawTime = (date) => {
  return new Date(date).toLocaleString('pl-PL', {
    timeZone: 'Europe/Warsaw'
  });
};

// For handling form inputs
export const getWarsawISOString = () => {
  const now = new Date();
  return new Date(now.toLocaleString('en-US', {
    timeZone: 'Europe/Warsaw'
  })).toISOString();
}; 