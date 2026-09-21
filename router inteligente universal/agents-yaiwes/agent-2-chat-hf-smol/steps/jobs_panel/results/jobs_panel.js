function initJobsPanel(container, fetchJson) {
    // clear container
    container.innerHTML = '';

    // create textarea
    const textarea = document.createElement('textarea');
    textarea.placeholder = 'Pega aquí un arreglo JSON de trabajos';
    textarea.style.width = '100%';
    textarea.style.height = '150px';
    container.appendChild(textarea);

    // create button
    const button = document.createElement('button');
    button.textContent = 'Ejecutar en paralelo';
    container.appendChild(button);

    // create result list container
    const resultDiv = document.createElement('div');
    container.appendChild(resultDiv);

    // helper to display error
    const showError = (msg) => {
        const err = document.createElement('div');
        err.textContent = msg;
        err.style.color = 'red';
        resultDiv.innerHTML = '';
        resultDiv.appendChild(err);
    };

    button.addEventListener('click', () => {
        resultDiv.innerHTML = '';
        let jobs;
        try {
            const parsed = JSON.parse(textarea.value);
            if (!Array.isArray(parsed)) {
                throw new Error('El JSON debe ser un arreglo.');
            }
            jobs = parsed;
        } catch (e) {
            showError('JSON inválido: ' + e.message);
            return;
        }

        fetchJson('/chat/jobs/run', {
            method: 'POST',
            body: JSON.stringify({jobs: jobs, max_parallel: 8})
        }).then(resp => {
            if (!resp || typeof resp.status === 'undefined' || typeof resp.body === 'undefined') {
                throw new Error('Respuesta del servidor inesperada');
            }
            return resp;
        }).then(resp => {
            const list = document.createElement('ul');
            resp.body.forEach(item => {
                const li = document.createElement('li');
                li.textContent = `id: ${item.id}, status: ${item.status}`;
                list.appendChild(li);
            });
            resultDiv.appendChild(list);
        }).catch(err => {
            showError('Error al ejecutar: ' + err.message);
        });
    });
}
