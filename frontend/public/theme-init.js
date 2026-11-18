(function () {
  var preference = 'system';
  try {
    var saved = localStorage.getItem('smartregression.theme');
    if (saved === 'light' || saved === 'dark') preference = saved;
  } catch { /* Browser storage may be disabled. */ }
  var dark = preference === 'dark' || (preference === 'system' && matchMedia('(prefers-color-scheme: dark)').matches);
  var root = document.documentElement;
  root.dataset.themePreference = preference;
  root.dataset.theme = dark ? 'dark' : 'light';
  root.style.colorScheme = dark ? 'dark' : 'light';
  var color = document.querySelector('meta[name="theme-color"]');
  if (color) color.content = dark ? '#10151e' : '#f4f6f8';
})();
