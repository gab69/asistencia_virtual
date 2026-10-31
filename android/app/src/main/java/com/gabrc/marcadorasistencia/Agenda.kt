package com.gabrc.marcadorasistencia

import android.app.AlarmManager
import android.app.PendingIntent
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import java.time.LocalDateTime
import java.time.ZoneId

/** Mantiene programada en el sistema la siguiente marcación; Android la dispara aunque la app esté cerrada. */
private const val EXTRA_NOMBRE = "nombre"

fun programarProximaMarcacion(contexto: Context): Proxima? {
    val alarmas = contexto.getSystemService(AlarmManager::class.java)
    val configuracion = cargarConfiguracion(contexto)
    val proxima = proximaMarcacion(configuracion, LocalDateTime.now())
    if (proxima == null || !configuracion.estaConfigurada) {
        alarmas.cancel(intencionDeAlarma(contexto, ""))
        return null
    }
    val momento = proxima.momento.atZone(ZoneId.systemDefault()).toInstant().toEpochMilli()
    val alAbrirDesdeReloj = PendingIntent.getActivity(
        contexto, 0, Intent(contexto, MainActivity::class.java), PendingIntent.FLAG_IMMUTABLE,
    )
    alarmas.setAlarmClock(
        AlarmManager.AlarmClockInfo(momento, alAbrirDesdeReloj),
        intencionDeAlarma(contexto, proxima.marcacion.nombre),
    )
    return proxima
}

private fun intencionDeAlarma(contexto: Context, nombre: String): PendingIntent {
    val intencion = Intent(contexto, ReceptorAlarma::class.java).putExtra(EXTRA_NOMBRE, nombre)
    return PendingIntent.getBroadcast(
        contexto, 0, intencion, PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT,
    )
}

class ReceptorAlarma : BroadcastReceiver() {
    override fun onReceive(contexto: Context, intencion: Intent) {
        val nombre = intencion.getStringExtra(EXTRA_NOMBRE) ?: return
        val configuracion = cargarConfiguracion(contexto)
        programarProximaMarcacion(contexto)
        if (!ServicioBloqueo.activo) {
            ServicioBloqueo.iniciar(contexto, configuracion, nombre)
        }
    }
}

/** Las alarmas se pierden al reiniciar y quedan desfasadas si cambia la hora. */
class ReceptorSistema : BroadcastReceiver() {
    override fun onReceive(contexto: Context, intencion: Intent) {
        when (intencion.action) {
            Intent.ACTION_BOOT_COMPLETED,
            Intent.ACTION_MY_PACKAGE_REPLACED,
            Intent.ACTION_TIME_CHANGED,
            Intent.ACTION_TIMEZONE_CHANGED -> programarProximaMarcacion(contexto)
        }
    }
}
