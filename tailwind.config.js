
module.exports = {
  content: [
    './templates/**/*.html',     // Wskazuje pliki HTML w folderze "templates"
    './**/*.html',               // Wskazuje pliki HTML w projekcie (np. w aplikacjach Django)
    './static/src/**/*.js',      // Wskazuje pliki JavaScript w "static/src"
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}

