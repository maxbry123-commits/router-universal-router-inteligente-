package com.swecode.agente;

import android.accessibilityservice.AccessibilityService;
import android.accessibilityservice.GestureDescription;
import android.content.Context;
import android.content.Intent;
import android.graphics.Path;
import android.net.Uri;
import android.os.Bundle;
import android.view.accessibility.AccessibilityEvent;
import android.view.accessibility.AccessibilityNodeInfo;

import org.json.JSONObject;

import java.util.ArrayDeque;
import java.util.Deque;

// Acciones del modelo sobre el móvil (vía servicio de accesibilidad):
// abrir_url | leer_pantalla | escribir | tap | atras
public class AccesibilidadAgente extends AccessibilityService {
    private static AccesibilidadAgente yo;

    @Override
    public void onServiceConnected() { yo = this; }
    @Override
    public boolean onUnbind(Intent i) { yo = null; return false; }
    @Override public void onAccessibilityEvent(AccessibilityEvent e) {}
    @Override public void onInterrupt() {}

    public static Object ejecutar(Context ctx, String accion, JSONObject args) throws Exception {
        switch (accion) {
            case "abrir_url": {
                String url = args == null ? "" : args.optString("url", "").trim();
                Uri uri = Uri.parse(url);
                String esq = uri.getScheme();
                if (esq == null || !(esq.equalsIgnoreCase("http") || esq.equalsIgnoreCase("https"))) {
                    return "ERROR:esquema no permitido";   // nada de intent:, file:, tel:, etc.
                }
                Intent i = new Intent(Intent.ACTION_VIEW, uri);
                i.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                i.setPackage("com.android.chrome");   // solo Chrome de Google, sin reintento con otra app
                try { ctx.startActivity(i); }
                catch (Exception e) { return "ERROR:Chrome no disponible"; }
                return "OK";
            }
            case "leer_pantalla": {
                if (yo == null) return "ERROR:accesibilidad inactiva";
                AccessibilityNodeInfo root = yo.getRootInActiveWindow();
                if (root == null) return "";
                StringBuilder sb = new StringBuilder();
                Deque<AccessibilityNodeInfo> cola = new ArrayDeque<>();
                cola.add(root);
                while (!cola.isEmpty() && sb.length() < 20000) {
                    AccessibilityNodeInfo n = cola.poll();
                    if (n == null) continue;
                    CharSequence t = n.getText();
                    if (t != null && t.length() > 0) sb.append(t).append('\n');
                    for (int i = 0; i < n.getChildCount(); i++) cola.add(n.getChild(i));
                }
                return sb.toString();
            }
            case "escribir": {
                if (yo == null) return "ERROR:accesibilidad inactiva";
                AccessibilityNodeInfo n = yo.enfocadoEditable();
                if (n == null) return "ERROR:sin campo enfocado";
                Bundle b = new Bundle();
                b.putCharSequence(AccessibilityNodeInfo.ACTION_ARGUMENT_SET_TEXT_CHARSEQUENCE,
                    args.getString("texto"));
                n.performAction(AccessibilityNodeInfo.ACTION_SET_TEXT, b);
                return "OK";
            }
            case "tap": {
                if (yo == null) return "ERROR:accesibilidad inactiva";
                Path p = new Path();
                p.moveTo((float) args.getDouble("x"), (float) args.getDouble("y"));
                yo.dispatchGesture(new GestureDescription.Builder()
                    .addStroke(new GestureDescription.StrokeDescription(p, 0, 80)).build(),
                    null, null);
                return "OK";
            }
            case "atras": {
                if (yo == null) return "ERROR:accesibilidad inactiva";
                yo.performGlobalAction(GLOBAL_ACTION_BACK);
                return "OK";
            }
            default:
                return "ERROR:accion desconocida " + accion;
        }
    }

    private AccessibilityNodeInfo enfocadoEditable() {
        AccessibilityNodeInfo root = getRootInActiveWindow();
        if (root == null) return null;
        Deque<AccessibilityNodeInfo> cola = new ArrayDeque<>();
        cola.add(root);
        while (!cola.isEmpty()) {
            AccessibilityNodeInfo n = cola.poll();
            if (n == null) continue;
            if (n.isEditable() && n.isFocused()) return n;
            for (int i = 0; i < n.getChildCount(); i++) cola.add(n.getChild(i));
        }
        return null;
    }
}
