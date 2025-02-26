app.use((req, res, next) => {
  // Ensure dates are handled in Warsaw timezone
  process.env.TZ = 'Europe/Warsaw';
  next();
}); 