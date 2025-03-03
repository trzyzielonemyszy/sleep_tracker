app.use((req, res, next) => {
  // Ensure dates are handled in Warsaw timezone
  process.env.TZ = 'Europe/Warsaw';
  next();
});

// Sprawdźmy, na jakim porcie nasłuchuje aplikacja
const port = process.env.PORT || 5000;
app.listen(port, () => {
  console.log(`Server running on port ${port}`);
}); 