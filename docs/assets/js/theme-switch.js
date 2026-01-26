window.addEventListener("DOMContentLoaded", function() {
  const toggleDarkMode = document.getElementById("theme-toggle");
  const themeStylesheet = document.getElementById("theme-stylesheet");
  
  if (localStorage.getItem('theme') === 'light') {
    setTheme('light');
  } else {
    setTheme('dark');
  }
  
  jtd.addEvent(toggleDarkMode, 'click', function(){
    const currentTheme = getTheme();
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    localStorage.setItem('theme', newTheme);
    setTheme(newTheme);
  });
  
  function getTheme() {
    return themeStylesheet.href.includes('mocha') ? 'dark' : 'light';
  }
  
  function setTheme(theme) {
    if (theme === 'dark') {
      toggleDarkMode.innerHTML = `<svg width='18px' height='18px'><use href="#svg-moon"></use></svg>`;
      themeStylesheet.href = themeStylesheet.href.replace('catppuccin-latte.css', 'catppuccin-mocha.css');
    } else {
      toggleDarkMode.innerHTML = `<svg width='18px' height='18px'><use href="#svg-sun"></use></svg>`;
      themeStylesheet.href = themeStylesheet.href.replace('catppuccin-mocha.css', 'catppuccin-latte.css');
    }
  }
});
