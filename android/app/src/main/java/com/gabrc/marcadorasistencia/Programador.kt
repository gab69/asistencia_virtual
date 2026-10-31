package com.gabrc.marcadorasistencia

import java.time.LocalDateTime
import java.time.LocalTime

/** Decide cuál es la siguiente marcación a partir de un momento dado. */
data class Proxima(val marcacion: Marcacion, val momento: LocalDateTime)

private const val DIAS_A_REVISAR = 8L // hoy y el mismo día de la semana siguiente

fun proximaMarcacion(configuracion: Configuracion, ahora: LocalDateTime): Proxima? {
    val activas = configuracion.marcaciones.filter { it.activa }.sortedBy { it.hora }
    for (desplazamiento in 0 until DIAS_A_REVISAR) {
        val dia = ahora.toLocalDate().plusDays(desplazamiento)
        if (dia.dayOfWeek.value - 1 !in configuracion.diasLaborales) continue
        for (marcacion in activas) {
            val momento = dia.atTime(LocalTime.parse(marcacion.hora))
            if (momento.isAfter(ahora)) return Proxima(marcacion, momento)
        }
    }
    return null
}
