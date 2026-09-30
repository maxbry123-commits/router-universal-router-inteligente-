# recarga (bloque4)

POST /plugins/sync: PluginHost.sync() rescans plugins/ (new load, deleted leave, bad ficha marks only itself; counters kept; no restart).
POST /control/reload-policies: resilience.reload_policies() re-reads policies.json in place; invalid file keeps previous.
Optional rescan thread: env RIU_PLUGINS_AUTOSYNC_S=60 (off by default).
Tests: tests/test_plugins_sync.py.
