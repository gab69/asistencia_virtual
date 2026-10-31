package com.gabrc.marcadorasistencia

import android.content.Context
import org.json.JSONArray
import org.json.JSONException
import org.json.JSONObject
import java.io.File

/** Modelo de configuración y su persistencia en disco. */
private const val ARCHIVO_CONFIGURACION = "marcador_asistencia.json"
private const val URL_VACIA = "https://"

data class Marcacion(val nombre: String, val hora: String, val activa: Boolean = true) // hora "HH:MM"

private fun marcacionesPorDefecto() = listOf(
    Marcacion("Entrada", "08:00"),
    Marcacion("Salida a refrigerio", "13:00"),
    Marcacion("Regreso de refrigerio", "14:00"),
    Marcacion("Salida", "17:00"),
)

data class Configuracion(
    val url: String = URL_VACIA,
    val permitirNavegadorCompleto: Boolean = true,
    val alarmaSonora: Boolean = true,
    val vibracion: Boolean = true,
    val diasLaborales: List<Int> = listOf(0, 1, 2, 3, 4), // 0 = lunes
    val limiteBloqueoMinutos: Int = 15,
    val codigoEmergencia: String = "1234",
    val marcaciones: List<Marcacion> = marcacionesPorDefecto(),
) {
    val estaConfigurada: Boolean get() = url != URL_VACIA

    fun aJson(): String = JSONObject()
        .put("url", url)
        .put("permitir_navegador_completo", permitirNavegadorCompleto)
        .put("alarma_sonora", alarmaSonora)
        .put("vibracion", vibracion)
        .put("dias_laborales", JSONArray(diasLaborales))
        .put("limite_bloqueo_minutos", limiteBloqueoMinutos)
        .put("codigo_emergencia", codigoEmergencia)
        .put("marcaciones", JSONArray(marcaciones.map(::marcacionAJson)))
        .toString(2)

    companion object {
        fun desdeJson(texto: String): Configuracion {
            val datos = JSONObject(texto)
            return Configuracion(
                url = datos.getString("url"),
                permitirNavegadorCompleto = datos.getBoolean("permitir_navegador_completo"),
                alarmaSonora = datos.getBoolean("alarma_sonora"),
                vibracion = datos.optBoolean("vibracion", true), // ausente en la versión 1.0
                diasLaborales = datos.getJSONArray("dias_laborales").let { dias ->
                    List(dias.length()) { dias.getInt(it) }
                },
                limiteBloqueoMinutos = datos.getInt("limite_bloqueo_minutos"),
                codigoEmergencia = datos.getString("codigo_emergencia"),
                marcaciones = datos.getJSONArray("marcaciones").let { lista ->
                    List(lista.length()) { marcacionDesdeJson(lista.getJSONObject(it)) }
                },
            )
        }
    }
}

private fun marcacionAJson(marcacion: Marcacion) = JSONObject()
    .put("nombre", marcacion.nombre)
    .put("hora", marcacion.hora)
    .put("activa", marcacion.activa)

private fun marcacionDesdeJson(datos: JSONObject) = Marcacion(
    datos.getString("nombre"), datos.getString("hora"), datos.getBoolean("activa"),
)

private fun archivo(contexto: Context) = File(contexto.filesDir, ARCHIVO_CONFIGURACION)

fun cargarConfiguracion(contexto: Context): Configuracion {
    val ruta = archivo(contexto)
    if (!ruta.exists()) return Configuracion()
    return try {
        Configuracion.desdeJson(ruta.readText())
    } catch (_: JSONException) {
        Configuracion()
    }
}

fun guardarConfiguracion(contexto: Context, configuracion: Configuracion) {
    archivo(contexto).writeText(configuracion.aJson())
}
