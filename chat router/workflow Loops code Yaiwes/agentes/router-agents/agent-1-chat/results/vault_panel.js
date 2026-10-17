function initVaultPanel(container, fetchJson) {
  // Clear container (no server data)
  container.innerHTML = '';

  const pwInput = document.createElement('input');
  pwInput.type = 'password';
  pwInput.placeholder = 'Contraseña maestra';
  pwInput.style.marginRight = '8px';

  const unlockBtn = document.createElement('button');
  unlockBtn.textContent = 'Desbloquear';
  unlockBtn.style.marginRight = '8px';

  const lockBtn = document.createElement('button');
  lockBtn.textContent = 'Bloquear';

  const statusEl = document.createElement('span');
  statusEl.style.marginLeft = '12px';
  statusEl.textContent = 'bloqueado'; // initial state

  container.append(pwInput, unlockBtn, lockBtn, statusEl);

  unlockBtn.addEventListener('click', async () => {
    const pass = pwInput.value;
    pwInput.value = ''; // clear password field immediately
    try {
      const res = await fetchJson('/vault/unlock', {
        method: 'POST',
        body: JSON.stringify({ passphrase: pass })
      });
      if (res && res.status === 200) {
        statusEl.textContent = 'desbloqueado';
      } else {
        statusEl.textContent = 'error';
      }
    } catch (_) {
      statusEl.textContent = 'error';
    }
  });

  lockBtn.addEventListener('click', async () => {
    try {
      const res = await fetchJson('/vault/lock', { method: 'POST' });
      if (res && res.status === 200) {
        statusEl.textContent = 'bloqueado';
      } else {
        statusEl.textContent = 'error';
      }
    } catch (_) {
      statusEl.textContent = 'error';
    }
  });
}
