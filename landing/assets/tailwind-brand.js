/** Shared LaunchLook theme for Tailwind CDN (load before tailwindcss.com script). */
tailwind.config = {
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        serif: ["Fraunces", "Georgia", "serif"],
      },
      colors: {
        paper: "#FAF7F2",
        ink: "#1F1B16",
        muted: "#6B6359",
        accent: "#B45309",
        "accent-soft": "#FDE68A",
        "surface-warm": "#F3EDE4",
        "surface-tint": "#FBF6EE",
        line: "#E7E0D6",
      },
      maxWidth: { prose: "40rem" },
    },
  },
};
