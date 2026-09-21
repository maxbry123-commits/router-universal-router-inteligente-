function wirePanels(root, fetchJson) {
  const panels = {};

  // Banco panel
  const bancoSection = document.createElement('section');
  const bancoTitle = document.createElement('h3');
  bancoTitle.textContent = 'Banco';
  const bancoDiv = document.createElement('div');
  bancoSection.append(bancoTitle, bancoDiv);
  root.appendChild(bancoSection);
  if (typeof initVaultPanel === 'function') {
    initVaultPanel(bancoDiv, fetchJson);
  } else {
    bancoDiv.textContent = 'Panel de bóveda no disponible';
  }
  panels.banco = bancoDiv;

  // Router panel (using verified initRouterPanel)
  const routerSection = document.createElement('section');
  const routerTitle = document.createElement('h3');
  routerTitle.textContent = 'Router';
  const routerDiv = document.createElement('div');
  routerSection.append(routerTitle, routerDiv);
  root.appendChild(routerSection);
  if (typeof initRouterPanel === 'function') {
    initRouterPanel(routerDiv, fetchJson);
  } else {
    routerDiv.textContent = 'Panel de router no disponible';
  }
  panels.router = routerDiv;

  // Trabajos panel
  const trabajosSection = document.createElement('section');
  const trabajosTitle = document.createElement('h3');
  trabajosTitle.textContent = 'Trabajos';
  const trabajosDiv = document.createElement('div');
  trabajosSection.append(trabajosTitle, trabajosDiv);
  root.appendChild(trabajosSection);
  if (typeof initJobsPanel === 'function') {
    initJobsPanel(trabajosDiv, fetchJson);
  } else {
    trabajosDiv.textContent = 'Panel de trabajos pendiente';
  }
  panels.trabajos = trabajosDiv;

  return panels;
}
