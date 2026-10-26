self.addEventListener('install',e=>e.waitUntil(caches.open('yaiwes-1').then(c=>c.addAll(['../Ui Yaiwes interface beta/02-fromted/HOST.html']))));
