// Per-team accent colors for the pinned highlight. Keys are football-data.org
// team IDs. When a team isn't in this map we fall back to a neutral cyan/amber
// pair so the UI still highlights the pinned country.

export const TEAM_COLORS = {
  762: { primary: "#75aadb", secondary: "#ffffff", name: "Argentina" },
  764: { primary: "#00d68f", secondary: "#ffcb0e", name: "Brazil" },   // default
  760: { primary: "#f4c542", secondary: "#c60b1e", name: "Spain" },
  773: { primary: "#0055a4", secondary: "#ef4135", name: "France" },
  770: { primary: "#ffffff", secondary: "#c8102e", name: "England" },
  759: { primary: "#f5c518", secondary: "#000000", name: "Germany" },
  765: { primary: "#046a38", secondary: "#da291c", name: "Portugal" },
  8601: { primary: "#f36c21", secondary: "#ffffff", name: "Netherlands" },
  769: { primary: "#006341", secondary: "#c8102e", name: "Mexico" },
  8872: { primary: "#ba0c2f", secondary: "#00205b", name: "Norway" },
  818: { primary: "#fcd116", secondary: "#003893", name: "Colombia" },
  815: { primary: "#c1272d", secondary: "#006233", name: "Morocco" },
  766: { primary: "#bc002d", secondary: "#ffffff", name: "Japan" },
  788: { primary: "#d52b1e", secondary: "#ffffff", name: "Switzerland" },
  791: { primary: "#ffdd00", secondary: "#0072ce", name: "Ecuador" },
  771: { primary: "#3c3b6e", secondary: "#b22234", name: "USA" },
  828: { primary: "#d80621", secondary: "#ffffff", name: "Canada" },
  774: { primary: "#007749", secondary: "#ffb612", name: "South Africa" },
  761: { primary: "#d32011", secondary: "#0038a8", name: "Paraguay" },
  1935: { primary: "#ff8200", secondary: "#009e60", name: "Ivory Coast" },
};

export const DEFAULT_ACCENT = { primary: "#00d68f", secondary: "#ffcb0e" };

export function colorFor(teamId) {
  return TEAM_COLORS[teamId] ?? DEFAULT_ACCENT;
}
