package com.swecode.agente;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.Service;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.os.Handler;
import android.os.IBinder;
import android.os.Looper;

import org.json.JSONObject;

import java.util.concurrent.TimeUnit;

import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.Response;
import okhttp3.WebSocket;
import okhttp3.WebSocketListener;

// Servicio en primer plano: mantiene WSS saliente al puente-movil.
// Recibe {id, accion, args} y responde {id, resultado}.
// Reintenta solo — cero fricción tras la primera conexión.
public class AgenteService extends Service {
    // El puente-movil corre dentro del Space riu-router y el proxy lo expone en /agente. URL y token se escriben en la app y quedan guardados.
    public static final String URL_DEFECTO = "wss://comand-center-1-riu-router.hf.space/agente";
    public static String URL = URL_DEFECTO;
    public static String TOKEN = "";              // el PUENTE_TOKEN del servidor (la app agrega el prefijo "token-")
    public static volatile boolean conectado = false;

    private OkHttpClient http;
    private WebSocket ws;
    private Handler h;
    private boolean vivo = true;

    public static SharedPreferences prefs(Context c) {
        return c.getSharedPreferences("puente", Context.MODE_PRIVATE);
    }

    public static void cargar(Context c) {
        SharedPreferences p = prefs(c);
        String u = p.getString("url", URL_DEFECTO).trim();
        URL = u.isEmpty() ? URL_DEFECTO : u;
        TOKEN = p.getString("token", "").trim();
    }

    @Override
    public void onCreate() {
        super.onCreate();
        cargar(this);
        http = new OkHttpClient.Builder()
            .pingInterval(20, TimeUnit.SECONDS)
            .retryOnConnectionFailure(true)
            .build();
        h = new Handler(Looper.getMainLooper());
        NotificationChannel ch = new NotificationChannel("agente", "Agente SWE Code",
            NotificationManager.IMPORTANCE_LOW);
        getSystemService(NotificationManager.class).createNotificationChannel(ch);
        Notification n = new Notification.Builder(this, "agente")
            .setContentTitle("Agente SWE Code")
            .setContentText("Canal al puente activo")
            .setSmallIcon(android.R.drawable.stat_sys_data_bluetooth)
            .build();
        startForeground(1, n);
        conectar();
    }

    private void conectar() {
        Request.Builder rb = new Request.Builder().url(URL);
        if (!TOKEN.isEmpty()) rb.header("Sec-WebSocket-Protocol", "token-" + TOKEN);
        ws = http.newWebSocket(rb.build(), new WebSocketListener() {
            @Override public void onOpen(WebSocket w, Response r) { conectado = true; }
            @Override public void onMessage(WebSocket w, String text) { ejecutar(text); }
            @Override public void onClosed(WebSocket w, int c, String r) { reintenta(); }
            @Override public void onFailure(WebSocket w, Throwable t, Response r) { reintenta(); }
        });
    }

    private void reintenta() {
        conectado = false;
        if (vivo) h.postDelayed(this::conectar, 5000);
    }

    private void ejecutar(String text) {
        try {
            JSONObject m = new JSONObject(text);
            int id = m.getInt("id");
            String accion = m.getString("accion");
            JSONObject args = m.optJSONObject("args");
            Object res = AccesibilidadAgente.ejecutar(this, accion, args);
            ws.send(new JSONObject().put("id", id).put("resultado", res).toString());
        } catch (Exception e) {
            try {
                ws.send(new JSONObject().put("id", new JSONObject(text).optInt("id"))
                    .put("resultado", "ERROR:" + e.getMessage()).toString());
            } catch (Exception ignored) {}
        }
    }

    @Override public IBinder onBind(Intent i) { return null; }

    @Override
    public void onDestroy() {
        vivo = false;
        conectado = false;
        if (ws != null) ws.close(1000, "stop");
        super.onDestroy();
    }
}
