package com.gabrc.marcadorasistencia

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test
import java.time.LocalDateTime

class ProgramadorTest {
    private val base = Configuracion()

    @Test
    fun eligeLaSiguienteHoraDelMismoDia() {
        val proxima = proximaMarcacion(base, LocalDateTime.of(2026, 11, 2, 9, 0)) // lunes
        assertEquals("Salida a refrigerio", proxima?.marcacion?.nombre)
        assertEquals(LocalDateTime.of(2026, 11, 2, 13, 0), proxima?.momento)
    }

    @Test
    fun enLaHoraExactaPasaALaSiguiente() {
        val proxima = proximaMarcacion(base, LocalDateTime.of(2026, 11, 2, 8, 0))
        assertEquals("Salida a refrigerio", proxima?.marcacion?.nombre)
    }

    @Test
    fun saltaElFinDeSemana() {
        val proxima = proximaMarcacion(base, LocalDateTime.of(2026, 11, 6, 18, 0)) // viernes
        assertEquals(LocalDateTime.of(2026, 11, 9, 8, 0), proxima?.momento)
    }

    @Test
    fun ignoraMarcacionesInactivas() {
        val configuracion = base.copy(
            marcaciones = listOf(Marcacion("Entrada", "08:00", false), Marcacion("Salida", "17:00")),
        )
        val proxima = proximaMarcacion(configuracion, LocalDateTime.of(2026, 11, 2, 7, 0))
        assertEquals("Salida", proxima?.marcacion?.nombre)
    }

    @Test
    fun conUnSoloDiaYaPasadoEsperaUnaSemana() {
        val configuracion = base.copy(diasLaborales = listOf(0))
        val proxima = proximaMarcacion(configuracion, LocalDateTime.of(2026, 11, 2, 18, 0))
        assertEquals(LocalDateTime.of(2026, 11, 9, 8, 0), proxima?.momento)
    }

    @Test
    fun sinMarcacionesActivasNoHayProxima() {
        val configuracion = base.copy(marcaciones = listOf(Marcacion("Entrada", "08:00", false)))
        assertNull(proximaMarcacion(configuracion, LocalDateTime.of(2026, 11, 2, 7, 0)))
    }
}
