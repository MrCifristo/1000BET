/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        // Cowboy Bebop / retro-tech noir palette
        base:  '#141009', // warm near-black
        panel: '#1D1810', // warm dark panel
        ink:   '#EFE7D4', // warm cream — main text (high contrast)
        dim:   '#A99A80', // muted warm grey
        pitch: '#E8B23A', // mustard/amber — primary accent
        goal:  '#D8452A', // blood orange-red — secondary
        py:    '#4FB0A3', // muted teal/cyan — tertiary
        gold:  '#F0C75A', // light gold highlight
      },
      fontFamily: {
        display: ['Oswald', '"Arial Narrow"', 'system-ui', 'sans-serif'],
        sans: ['Barlow', 'system-ui', 'sans-serif'],
        mono: ['"Space Mono"', 'ui-monospace', 'monospace'],
      },
      letterSpacing: {
        tightest: '-0.01em',
      },
    },
  },
  plugins: [],
}
