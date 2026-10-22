const deck = new Reveal({
  width: 1600,
  height: 900,
  margin: 0,
  minScale: 0.2,
  maxScale: 1.6,
  controls: true,
  controlsTutorial: false,
  progress: true,
  slideNumber: false,
  hash: true,
  history: true,
  keyboard: {
    70: () => {
      const root = document.documentElement;
      if (!document.fullscreenElement) root.requestFullscreen?.();
      else document.exitFullscreen?.();
    }
  },
  center: false,
  transition: 'fade',
  transitionSpeed: 'fast',
  backgroundTransition: 'fade',
  viewDistance: 3,
  plugins: [RevealNotes, RevealHighlight]
});

window.deck = deck;
deck.initialize();

// Keep the browser title useful while navigating or sharing a specific slide.
deck.on('slidechanged', event => {
  const title = event.currentSlide?.querySelector('h1, h2')?.textContent?.trim();
  document.title = title ? `${title} — Enterprise AI Security` : 'Enterprise AI Security';
});
