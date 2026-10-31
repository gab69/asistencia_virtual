package com.gabrc.marcadorasistencia

import android.app.AlarmManager
import android.app.Application
import android.app.NotificationManager
import android.content.Intent
import android.graphics.Bitmap
import android.graphics.Canvas
import android.os.Looper
import android.os.Vibrator
import android.view.View
import android.view.ViewGroup
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.NumberPicker
import android.widget.TextView
import androidx.appcompat.app.AlertDialog
import androidx.test.core.app.ApplicationProvider
import org.json.JSONObject
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNotNull
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test
import org.junit.runner.RunWith
import org.robolectric.Robolectric
import org.robolectric.RobolectricTestRunner
import org.robolectric.RuntimeEnvironment
import org.robolectric.Shadows.shadowOf
import org.robolectric.annotation.Config
import org.robolectric.annotation.GraphicsMode
import org.robolectric.shadows.ShadowDialog
import java.io.File
import java.time.Duration

private const val URL_PRUEBA = "https://asistencia.ejemplo.com/marcar"
private const val PANTALLA_PEQUENA = "w320dp-h640dp-xhdpi"
private const val PANTALLA_NORMAL = "w360dp-h780dp-xxhdpi"

/** Comprueba en un Android simulado que las pantallas caben en un teléfono y que el bloqueo funciona. */
@RunWith(RobolectricTestRunner::class)
@GraphicsMode(GraphicsMode.Mode.NATIVE)
@Config(sdk = [36])
class PantallasTest {
    private val aplicacion = ApplicationProvider.getApplicationContext<Application>()
    private val configuracion = Configuracion(
        url = URL_PRUEBA, codigoEmergencia = "4321", alarmaSonora = false,
    )

    @After
    fun liberarBloqueo() {
        if (ServicioBloqueo.activo) {
            Robolectric.buildService(ServicioBloqueo::class.java).create().get().let {
                it.onStartCommand(Intent(aplicacion, ServicioBloqueo::class.java).setAction("liberar"), 0, 0)
            }
        }
    }

    private fun comprobarQueCabe(vista: View, anchoDisponible: Int) {
        val posicion = IntArray(2).also(vista::getLocationInWindow)
        val derecha = posicion[0] + vista.width
        assertTrue("${vista.javaClass.simpleName} se sale: $derecha > $anchoDisponible", derecha <= anchoDisponible)
        if (vista is ViewGroup) {
            for (i in 0 until vista.childCount) {
                if (vista.getChildAt(i).visibility == View.VISIBLE) {
                    comprobarQueCabe(vista.getChildAt(i), anchoDisponible)
                }
            }
        }
    }

    private fun dibujar(raiz: View, ancho: Int, alto: Int, nombre: String) {
        raiz.measure(
            View.MeasureSpec.makeMeasureSpec(ancho, View.MeasureSpec.EXACTLY),
            View.MeasureSpec.makeMeasureSpec(alto, View.MeasureSpec.EXACTLY),
        )
        raiz.layout(0, 0, ancho, alto)
        comprobarQueCabe(raiz, ancho)
        val carpeta = System.getProperty("capturas").orEmpty()
        if (carpeta.isEmpty()) return
        val imagen = Bitmap.createBitmap(ancho, alto, Bitmap.Config.ARGB_8888)
        raiz.draw(Canvas(imagen))
        File(carpeta, "$nombre.png").outputStream().use {
            imagen.compress(Bitmap.CompressFormat.PNG, 100, it)
        }
    }

    private fun mainConfigurada() =
        Robolectric.buildActivity(MainActivity::class.java).also {
            guardarConfiguracion(aplicacion, configuracion)
        }.setup().get()

    private fun iniciarBloqueo(
        nombre: String,
        ajustes: Configuracion = configuracion,
    ): BloqueoActivity {
        val datos = Intent(aplicacion, ServicioBloqueo::class.java)
            .putExtra("configuracion", ajustes.aJson())
            .putExtra("nombre", nombre)
        Robolectric.buildService(ServicioBloqueo::class.java, datos).create().startCommand(0, 0)
        val pantalla = shadowOf(aplicacion).nextStartedActivity
        assertEquals(BloqueoActivity::class.java.name, pantalla.component?.className)
        return Robolectric.buildActivity(BloqueoActivity::class.java, pantalla).setup().get()
    }

    @Test
    fun laConfiguracionSobreviveAlGuardado() {
        val cambiada = configuracion.copy(
            permitirNavegadorCompleto = false,
            diasLaborales = listOf(5, 6),
            marcaciones = listOf(Marcacion("Entrada", "07:45", false)),
        )
        guardarConfiguracion(aplicacion, cambiada)
        assertEquals(cambiada, cargarConfiguracion(aplicacion))
    }

    @Test
    fun laConfiguracionDeLaVersionAnteriorConservaSusDatos() {
        val anterior = JSONObject(configuracion.aJson()).apply { remove("vibracion") }
        val cargada = Configuracion.desdeJson(anterior.toString())
        assertEquals(URL_PRUEBA, cargada.url)
        assertTrue(cargada.vibracion)
    }

    @Test
    fun laVibracionSigueElInterruptorYTerminaAlLiberar() {
        val vibrador = shadowOf(aplicacion.getSystemService(Vibrator::class.java))
        val pantalla = iniciarBloqueo("Entrada")
        assertTrue(vibrador.isVibrating)
        pantalla.findViewById<View>(R.id.boton_ya_marque).performClick()
        val liberar = shadowOf(aplicacion).nextStartedService
        Robolectric.buildService(ServicioBloqueo::class.java, liberar).create().startCommand(0, 0)
        assertFalse(vibrador.isVibrating)
    }

    @Test
    fun sinVibracionNoVibra() {
        val vibrador = shadowOf(aplicacion.getSystemService(Vibrator::class.java))
        iniciarBloqueo("Entrada", configuracion.copy(vibracion = false))
        assertFalse(vibrador.isVibrating)
    }

    @Test
    fun laVibracionSeRetomaSiElSistemaLaCorta() {
        val sistema = aplicacion.getSystemService(Vibrator::class.java)
        iniciarBloqueo("Entrada")
        sistema.cancel()
        assertFalse(shadowOf(sistema).isVibrating)
        shadowOf(Looper.getMainLooper()).idleFor(Duration.ofSeconds(1))
        assertTrue(shadowOf(sistema).isVibrating)
    }

    @Test
    fun laAlertaFlotanteDesapareceAlMostrarseElBloqueo() {
        val notificaciones = shadowOf(aplicacion.getSystemService(NotificationManager::class.java))
        iniciarBloqueo("Entrada")
        assertNotNull(notificaciones.getNotification(1).fullScreenIntent)
        shadowOf(Looper.getMainLooper()).idleFor(Duration.ofSeconds(1))
        val actual = notificaciones.getNotification(1)
        assertNull(actual.fullScreenIntent)
        assertEquals(
            NotificationManager.IMPORTANCE_LOW,
            aplicacion.getSystemService(NotificationManager::class.java)
                .getNotificationChannel(actual.channelId).importance,
        )
    }

    @Test
    @Config(qualifiers = PANTALLA_PEQUENA)
    fun elSelectorCambiaLaHoraDeLaFila() {
        val actividad = mainConfigurada()
        val hora = actividad.findViewById<LinearLayout>(R.id.lista_horarios)
            .getChildAt(0).findViewById<TextView>(R.id.hora)
        hora.performClick()
        val dialogo = ShadowDialog.getLatestDialog() as AlertDialog
        val horas = dialogo.findViewById<NumberPicker>(R.id.selector_horas)!!
        val minutos = dialogo.findViewById<NumberPicker>(R.id.selector_minutos)!!
        assertEquals(8, horas.value)
        assertEquals(0, minutos.value)
        shadowOf(Looper.getMainLooper()).idle()
        val boton = dialogo.getButton(AlertDialog.BUTTON_POSITIVE)
        assertEquals(View.VISIBLE, boton.visibility)
        assertEquals("Aceptar", boton.text.toString())
        dibujar(dialogo.window!!.decorView, 560, 900, "selector_hora_320dp")
        horas.value = 7
        minutos.value = 45
        dialogo.getButton(AlertDialog.BUTTON_POSITIVE).performClick()
        shadowOf(Looper.getMainLooper()).idle()
        assertEquals("07:45", hora.text.toString())
    }

    @Test
    fun sinUrlConfiguradaNoSeProgramaAlarma() {
        assertNull(programarProximaMarcacion(aplicacion))
    }

    @Test
    fun guardarProgramaLaProximaMarcacionEnElSistema() {
        guardarConfiguracion(aplicacion, configuracion)
        assertNotNull(programarProximaMarcacion(aplicacion))
        assertNotNull(aplicacion.getSystemService(AlarmManager::class.java).nextAlarmClock)
    }

    @Test
    @Config(qualifiers = PANTALLA_NORMAL)
    fun configuracionCabeEnTelefonoNormal() {
        val raiz = mainConfigurada().findViewById<View>(R.id.raiz)
        dibujar(raiz, 1080, 2340, "configuracion_360dp")
    }

    @Test
    @Config(qualifiers = PANTALLA_PEQUENA)
    fun configuracionCabeEnTelefonoPequeno() {
        val raiz = mainConfigurada().findViewById<View>(R.id.raiz)
        dibujar(raiz, 640, 1280, "configuracion_320dp")
    }

    @Test
    @Config(qualifiers = PANTALLA_PEQUENA)
    fun bloqueoCabeConElNombreMasLargo() {
        val raiz = iniciarBloqueo("Regreso de refrigerio").findViewById<View>(R.id.raiz)
        dibujar(raiz, 640, 1280, "bloqueo_320dp")
        val mensaje = raiz.findViewById<TextView>(R.id.mensaje)
        assertEquals(0, mensaje.layout.getEllipsisCount(mensaje.lineCount - 1))
    }

    @Test
    fun yaMarqueLiberaElBloqueo() {
        val pantalla = iniciarBloqueo("Entrada")
        assertTrue(ServicioBloqueo.activo)
        pantalla.findViewById<View>(R.id.boton_ya_marque).performClick()
        val liberar = shadowOf(aplicacion).nextStartedService
        assertEquals("liberar", liberar.action)
        Robolectric.buildService(ServicioBloqueo::class.java, liberar).create().startCommand(0, 0)
        assertFalse(ServicioBloqueo.activo)
        assertTrue(pantalla.isFinishing)
    }

    @Test
    fun codigoIncorrectoNoLibera() {
        val pantalla = iniciarBloqueo("Entrada")
        pantalla.findViewById<View>(R.id.boton_emergencia).performClick()
        val dialogo = ShadowDialog.getLatestDialog() as AlertDialog
        dialogo.findViewById<EditText>(R.id.campo_codigo)!!.setText("0000")
        dialogo.getButton(AlertDialog.BUTTON_POSITIVE).performClick()
        assertTrue(dialogo.isShowing)
        assertTrue(ServicioBloqueo.activo)
    }

    @Test
    fun codigoCorrectoLibera() {
        val pantalla = iniciarBloqueo("Entrada")
        shadowOf(aplicacion).clearStartedServices()
        pantalla.findViewById<View>(R.id.boton_emergencia).performClick()
        val dialogo = ShadowDialog.getLatestDialog() as AlertDialog
        dialogo.findViewById<EditText>(R.id.campo_codigo)!!.setText("4321")
        dialogo.getButton(AlertDialog.BUTTON_POSITIVE).performClick()
        assertFalse(dialogo.isShowing)
        assertEquals("liberar", shadowOf(aplicacion).nextStartedService.action)
    }

    @Test
    fun elBotonAtrasNoSaleDelBloqueo() {
        val pantalla = iniciarBloqueo("Entrada")
        pantalla.onBackPressedDispatcher.onBackPressed()
        assertFalse(pantalla.isFinishing)
    }
}
