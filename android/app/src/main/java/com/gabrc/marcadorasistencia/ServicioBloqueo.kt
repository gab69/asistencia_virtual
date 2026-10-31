package com.gabrc.marcadorasistencia

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.app.Service
import android.content.Context
import android.content.Intent
import android.os.Handler
import android.os.IBinder
import android.os.Looper
import android.os.PowerManager
import android.os.SystemClock
import android.provider.Settings
import androidx.core.app.NotificationCompat
import androidx.core.content.ContextCompat

private const val ACCION_LIBERAR = "liberar"
private const val EXTRA_CONFIGURACION = "configuracion"
private const val EXTRA_NOMBRE = "nombre"
private const val CANAL = "bloqueo"
private const val CANAL_SILENCIOSO = "bloqueo_silencioso"
private const val ID_NOTIFICACION = 1
private const val INTERVALO_VIGILANCIA_MS = 1000L
private const val MS_POR_MINUTO = 60_000L
private const val ETIQUETA_BLOQUEO_ACTIVO = "marcador:bloqueo"

/** Sostiene el bloqueo: alarma, regreso a la página y liberación automática por tiempo. */
class ServicioBloqueo : Service() {
    private val hilo = Handler(Looper.getMainLooper())
    private val alarma by lazy { Alarma(this) }
    private val vibracion by lazy { Vibracion(this) }
    private var despierto: PowerManager.WakeLock? = null
    private var intencionPantalla: Intent? = null
    private var notificacionSilenciosa: Notification? = null
    private var vibrar = false
    private var limite = 0L

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        if (intent?.action == ACCION_LIBERAR) {
            liberar()
            return START_NOT_STICKY
        }
        val datos = intent?.getStringExtra(EXTRA_CONFIGURACION)
        val nombre = intent?.getStringExtra(EXTRA_NOMBRE)
        if (datos == null || nombre == null) {
            stopSelf()
            return START_NOT_STICKY
        }
        val pantalla = BloqueoActivity.intencion(this, datos, nombre)
        startForeground(ID_NOTIFICACION, crearNotificacionAlerta(pantalla, nombre))
        if (!activo) comenzar(Configuracion.desdeJson(datos), pantalla, nombre)
        return START_NOT_STICKY
    }

    private fun comenzar(configuracion: Configuracion, pantalla: Intent, nombre: String) {
        activo = true
        intencionPantalla = pantalla
        notificacionSilenciosa = crearNotificacionSilenciosa(pantalla, nombre)
        val duracion = configuracion.limiteBloqueoMinutos * MS_POR_MINUTO
        limite = SystemClock.elapsedRealtime() + duracion
        mantenerDespierto(duracion)
        if (configuracion.alarmaSonora) alarma.iniciar()
        vibrar = configuracion.vibracion
        if (vibrar) vibracion.pulsar()
        startActivity(pantalla)
        hilo.postDelayed(::vigilar, INTERVALO_VIGILANCIA_MS)
    }

    /** Sin esto, con la pantalla apagada se detendría la cuenta del tiempo límite. */
    private fun mantenerDespierto(duracion: Long) {
        despierto = getSystemService(PowerManager::class.java)
            .newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, ETIQUETA_BLOQUEO_ACTIVO)
            .apply { acquire(duracion + MS_POR_MINUTO) }
    }

    private fun vigilar() {
        if (SystemClock.elapsedRealtime() > limite) {
            liberar()
            return
        }
        if (BloqueoActivity.visible) retirarAlerta()
        if (vibrar) vibracion.pulsar()
        if (debeVolverAPantalla()) intencionPantalla?.let(::startActivity)
        hilo.postDelayed(::vigilar, INTERVALO_VIGILANCIA_MS)
    }

    /** Con el teléfono en uso la alerta sale como aviso flotante y tapa los botones del bloqueo. */
    private fun retirarAlerta() {
        val silenciosa = notificacionSilenciosa ?: return
        notificacionSilenciosa = null
        getSystemService(NotificationManager::class.java).notify(ID_NOTIFICACION, silenciosa)
    }

    /** Android solo deja abrir pantallas desde segundo plano con el permiso de superposición. */
    private fun debeVolverAPantalla(): Boolean =
        !BloqueoActivity.visible &&
            Settings.canDrawOverlays(this) &&
            getSystemService(PowerManager::class.java).isInteractive

    private fun liberar() {
        activo = false
        hilo.removeCallbacksAndMessages(null)
        alarma.detener()
        vibracion.detener()
        despierto?.takeIf { it.isHeld }?.release()
        alLiberar?.invoke()
        stopForeground(STOP_FOREGROUND_REMOVE)
        stopSelf()
    }

    /** Abre el bloqueo aunque el teléfono esté bloqueado. */
    private fun crearNotificacionAlerta(pantalla: Intent, nombre: String): Notification {
        crearCanal(CANAL, R.string.canal_bloqueo, NotificationManager.IMPORTANCE_HIGH)
        return crearBase(CANAL, pantalla, nombre)
            .setCategory(NotificationCompat.CATEGORY_ALARM)
            .setPriority(NotificationCompat.PRIORITY_MAX)
            .setFullScreenIntent(intencionAbrir(pantalla), true)
            .build()
    }

    /** Android exige una notificación mientras dure el servicio: esta no flota sobre la pantalla. */
    private fun crearNotificacionSilenciosa(pantalla: Intent, nombre: String): Notification {
        crearCanal(CANAL_SILENCIOSO, R.string.canal_bloqueo_silencioso, NotificationManager.IMPORTANCE_LOW)
        return crearBase(CANAL_SILENCIOSO, pantalla, nombre).build()
    }

    private fun crearCanal(id: String, nombre: Int, importancia: Int) {
        val canal = NotificationChannel(id, getString(nombre), importancia)
            .apply { setSound(null, null) } // el sonido lo da la alarma, que se puede desactivar
        getSystemService(NotificationManager::class.java).createNotificationChannel(canal)
    }

    private fun crearBase(canal: String, pantalla: Intent, nombre: String) =
        NotificationCompat.Builder(this, canal)
            .setSmallIcon(R.drawable.ic_check)
            .setContentTitle(getString(R.string.marca_tu, nombre.lowercase()))
            .setContentText(getString(R.string.notificacion_detalle))
            .setOngoing(true)
            .setContentIntent(intencionAbrir(pantalla))

    private fun intencionAbrir(pantalla: Intent) = PendingIntent.getActivity(
        this, 0, pantalla, PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT,
    )

    companion object {
        @Volatile
        var activo = false
            private set
        var alLiberar: (() -> Unit)? = null

        fun iniciar(contexto: Context, configuracion: Configuracion, nombre: String) {
            val intencion = Intent(contexto, ServicioBloqueo::class.java)
                .putExtra(EXTRA_CONFIGURACION, configuracion.aJson())
                .putExtra(EXTRA_NOMBRE, nombre)
            ContextCompat.startForegroundService(contexto, intencion)
        }

        fun liberar(contexto: Context) {
            contexto.startService(
                Intent(contexto, ServicioBloqueo::class.java).setAction(ACCION_LIBERAR),
            )
        }
    }
}
