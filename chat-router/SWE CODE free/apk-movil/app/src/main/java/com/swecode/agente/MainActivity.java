package com.swecode.agente;

import android.app.Activity;
import android.content.Intent;
import android.os.Bundle;
import android.provider.Settings;
import android.text.InputType;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.TextView;

// Una sola pantalla: estado + botón "conectar" + acceso directo a accesibilidad.
// Uso: instalar una vez, activar el servicio de accesibilidad (1 vez), listo.
public class MainActivity extends Activity {
    private TextView estado;

    @Override
    protected void onCreate(Bundle b) {
        super.onCreate(b);
        LinearLayout lay = new LinearLayout(this);
        lay.setOrientation(LinearLayout.VERTICAL);
        lay.setPadding(40, 40, 40, 40);

        estado = new TextView(this);
        estado.setTextSize(16);
        lay.addView(estado);

        AgenteService.cargar(this);
        EditText url = new EditText(this);
        url.setHint("URL del puente (wss://…/agente)");
        url.setText(AgenteService.URL);
        url.setSingleLine(true);
        lay.addView(url);

        EditText token = new EditText(this);
        token.setHint("PUENTE_TOKEN");
        token.setText(AgenteService.TOKEN);
        token.setSingleLine(true);
        token.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_VARIATION_PASSWORD);
        lay.addView(token);

        Button conectar = new Button(this);
        conectar.setText("Conectar agente");
        conectar.setOnClickListener(v -> {
            AgenteService.prefs(this).edit()
                .putString("url", url.getText().toString().trim())
                .putString("token", token.getText().toString().trim()).apply();
            stopService(new Intent(this, AgenteService.class));
            startForegroundService(new Intent(this, AgenteService.class));
            refrescar();
        });
        lay.addView(conectar);

        Button accesibilidad = new Button(this);
        accesibilidad.setText("Activar accesibilidad (1 vez)");
        accesibilidad.setOnClickListener(v ->
            startActivity(new Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS)));
        lay.addView(accesibilidad);

        Button desconectar = new Button(this);
        desconectar.setText("Desconectar");
        desconectar.setOnClickListener(v ->
            stopService(new Intent(this, AgenteService.class)));
        lay.addView(desconectar);

        setContentView(lay);
        refrescar();
    }

    @Override
    protected void onResume() {
        super.onResume();
        refrescar();
    }

    private void refrescar() {
        String acc = Settings.Secure.getString(getContentResolver(),
            Settings.Secure.ENABLED_ACCESSIBILITY_SERVICES);
        boolean ok = acc != null && acc.contains(getPackageName());
        estado.setText("Puente: " + AgenteService.URL +
            "\nAccesibilidad: " + (ok ? "ACTIVA" : "PENDIENTE (tocar botón)") +
            "\nCanal: " + (AgenteService.conectado ? "conectado" : "desconectado"));
    }
}
