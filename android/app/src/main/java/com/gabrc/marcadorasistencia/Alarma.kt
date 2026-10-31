package com.gabrc.marcadorasistencia

import android.content.Context
import android.media.AudioAttributes
import android.media.MediaPlayer
import android.media.RingtoneManager
import android.os.VibrationEffect
import android.os.Vibrator

private const val DURACION_PULSO_MS = 500L

/** Vibración por pulsos: si el sistema corta uno, el siguiente la retoma. */
class Vibracion(contexto: Context) {
    private val vibrador = contexto.getSystemService(Vibrator::class.java)

    fun pulsar() {
        vibrador.vibrate(
            VibrationEffect.createOneShot(DURACION_PULSO_MS, VibrationEffect.DEFAULT_AMPLITUDE),
            AudioAttributes.Builder().setUsage(AudioAttributes.USAGE_ALARM).build(),
        )
    }

    fun detener() {
        vibrador.cancel()
    }
}

/** Alarma sonora que se repite mientras la pantalla está bloqueada. */
class Alarma(private val contexto: Context) {
    private var reproductor: MediaPlayer? = null

    fun iniciar() {
        if (reproductor != null) return
        val sonido = RingtoneManager.getDefaultUri(RingtoneManager.TYPE_ALARM)
            ?: RingtoneManager.getDefaultUri(RingtoneManager.TYPE_NOTIFICATION)
            ?: return
        val nuevo = MediaPlayer()
        try {
            nuevo.setAudioAttributes(
                AudioAttributes.Builder().setUsage(AudioAttributes.USAGE_ALARM).build(),
            )
            nuevo.setDataSource(contexto, sonido)
            nuevo.isLooping = true
            nuevo.prepare()
            nuevo.start()
            reproductor = nuevo
        } catch (_: Exception) {
            nuevo.release() // tono no disponible o sin acceso: el bloqueo sigue sin sonido
        }
    }

    fun detener() {
        reproductor?.release()
        reproductor = null
    }
}
