export function nextColorTheme(classList: {
  contains(token: string): boolean
}) {
  return classList.contains("dark") ? "light" : "dark"
}
