package com.gabrc.marcadorasistencia

import android.Manifest
import android.app.NotificationManager
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.os.Handler
import android.os.Looper
import android.provider.Settings
import android.view.View
import android.widget.Button
import android.widget.LinearLayout
import android.widget.NumberPicker
import android.widget.TextView
import androidx.activity.result.contract.ActivityResultContracts
import androidx.appcompat.app.AppCompatActivity
import androidx.core.content.ContextCompat
import com.google.android.material.dialog.MaterialAlertDialogBuilder
import com.google.android.material.materialswitch.MaterialSwitch
import com.google.android.material.snackbar.Snackbar
import com.google.android.material.textfield.TextInputEditText
import java.time.format.DateTimeFormatter
import java.util.Locale

private val OPCIONES_LIMITE = listOf(5, 10, 15, 20, 30, 45, 60)
private val DIAS_SEMANA = listOf("Lu", "Ma", "Mi", "Ju", "Vi", "Sá", "Do")
private const val HORAS_DEL_DIA = 24
private const val MINUTOS_DE_HORA = 60
private const val DURACION_PRUEBA_SONIDO_MS = 3000L
private val FORMATO_PROXIMA = DateTimeFormatter.ofPattern("EEE d, HH:mm", Locale.forLanguageTag("es"))

/** Pantalla de configuración: una sola columna pensada para usarse con el pulgar. */
class MainActivity : AppCompatActivity() {
    private class FilaMarcacion(val nombre: String, val hora: Button, val activa: MaterialSwitch)
    private class Permiso(val texto: Int, val solicitar: () -> Unit)

    private val hilo = Handler(Looper.getMainLooper())
    private val alarmaDePrueba by lazy { Alarma(this) }
    private val filas = mutableListOf<FilaMarcacion>()
    private val dias = mutableListOf<View>()
    private var limiteMinutos = 0
    private val pedirNotificaciones =
        registerForActivityResult(ActivityResultContracts.RequestPermission()) { mostrarPermisoPendiente() }

    private lateinit var url: TextInputEditText
    private lateinit var navegadorCompleto: MaterialSwitch
    private lateinit var alarma: MaterialSwitch
    private lateinit var vibracion: MaterialSwitch
    private lateinit var codigo: TextInputEditText
    private lateinit var botonLimite: Button

    override fun onCreate(estado: Bundle?) {
        super.onCreate(estado)
        setContentView(R.layout.activity_principal)
        aplicarMargenesDeSistema(findViewById(R.id.raiz))
        val configuracion = cargarConfiguracion(this)
        construirPagina(configuracion)
        construirHorarios(configuracion)
        construirDias(configuracion)
        construirSeguridad(configuracion)
        findViewById<View>(R.id.boton_guardar).setOnClickListener { guardar() }
        findViewById<View>(R.id.boton_probar).setOnClickListener { probar() }
        programarProximaMarcacion(this)
    }

    override fun onResume() {
        super.onResume()
        mostrarPermisoPendiente()
    }

    override fun onStop() {
        super.onStop()
        detenerPruebaDeSonido()
    }

    // ---------- secciones ----------
    private fun construirPagina(configuracion: Configuracion) {
        url = findViewById(R.id.campo_url)
        url.setText(configuracion.url)
        navegadorCompleto = findViewById(R.id.interruptor_navegador)
        navegadorCompleto.isChecked = configuracion.permitirNavegadorCompleto
    }

    private fun construirHorarios(configuracion: Configuracion) {
        val lista = findViewById<LinearLayout>(R.id.lista_horarios)
        for (marcacion in configuracion.marcaciones) {
            val fila = layoutInflater.inflate(R.layout.fila_marcacion, lista, false)
            fila.findViewById<TextView>(R.id.nombre).text = marcacion.nombre
            val hora = fila.findViewById<Button>(R.id.hora)
            hora.text = marcacion.hora
            hora.setOnClickListener { elegirHora(hora) }
            val activa = fila.findViewById<MaterialSwitch>(R.id.activa)
            activa.isChecked = marcacion.activa
            activa.contentDescription = marcacion.nombre
            lista.addView(fila)
            filas += FilaMarcacion(marcacion.nombre, hora, activa)
        }
    }

    private fun elegirHora(boton: Button) {
        val (horas, minutos) = boton.text.split(":").map(String::toInt)
        val contenido = layoutInflater.inflate(R.layout.dialogo_hora, null)
        val selectorHoras = prepararSelector(contenido, R.id.selector_horas, HORAS_DEL_DIA, horas)
        val selectorMinutos = prepararSelector(contenido, R.id.selector_minutos, MINUTOS_DE_HORA, minutos)
        MaterialAlertDialogBuilder(this)
            .setTitle(R.string.elegir_hora)
            .setView(contenido)
            .setNegativeButton(R.string.cancelar, null)
            .setPositiveButton(R.string.aceptar) { _, _ ->
                boton.text = String.format(Locale.ROOT, "%02d:%02d", selectorHoras.value, selectorMinutos.value)
            }
            .show()
    }

    private fun prepararSelector(contenido: View, id: Int, cantidad: Int, valor: Int): NumberPicker {
        val selector = contenido.findViewById<NumberPicker>(id)
        selector.minValue = 0
        selector.maxValue = cantidad - 1
        selector.displayedValues = Array(cantidad) { String.format(Locale.ROOT, "%02d", it) }
        selector.value = valor
        return selector
    }

    private fun construirDias(configuracion: Configuracion) {
        val fila = findViewById<LinearLayout>(R.id.fila_dias)
        DIAS_SEMANA.forEachIndexed { indice, nombre ->
            val celda = layoutInflater.inflate(R.layout.celda_dia, fila, false)
            celda.findViewById<TextView>(R.id.dia).text = nombre
            celda.isSelected = indice in configuracion.diasLaborales
            celda.setOnClickListener { celda.isSelected = !celda.isSelected }
            fila.addView(celda)
            dias += celda
        }
    }

    private fun construirSeguridad(configuracion: Configuracion) {
        alarma = findViewById(R.id.interruptor_alarma)
        alarma.isChecked = configuracion.alarmaSonora
        vibracion = findViewById(R.id.interruptor_vibracion)
        vibracion.isChecked = configuracion.vibracion
        findViewById<View>(R.id.boton_probar_sonido).setOnClickListener { probarSonido() }
        codigo = findViewById(R.id.campo_codigo)
        codigo.setText(configuracion.codigoEmergencia)
        limiteMinutos = configuracion.limiteBloqueoMinutos
        botonLimite = findViewById(R.id.boton_limite)
        mostrarLimite()
        botonLimite.setOnClickListener { elegirLimite() }
    }

    private fun mostrarLimite() {
        botonLimite.text = getString(R.string.minutos, limiteMinutos)
    }

    private fun elegirLimite() {
        val opciones = OPCIONES_LIMITE.map { getString(R.string.minutos, it) }.toTypedArray()
        MaterialAlertDialogBuilder(this)
            .setTitle(R.string.liberar_tras)
            .setItems(opciones) { _, indice ->
                limiteMinutos = OPCIONES_LIMITE[indice]
                mostrarLimite()
            }
            .show()
    }

    // ---------- permisos ----------
    /** Se pide uno a la vez y la tarjeta desaparece cuando ya no falta ninguno. */
    private fun mostrarPermisoPendiente() {
        val pendiente = buscarPermisoPendiente()
        val tarjeta = findViewById<View>(R.id.tarjeta_permiso)
        tarjeta.visibility = if (pendiente == null) View.GONE else View.VISIBLE
        if (pendiente == null) return
        findViewById<TextView>(R.id.texto_permiso).setText(pendiente.texto)
        findViewById<View>(R.id.boton_permiso).setOnClickListener { pendiente.solicitar() }
    }

    private fun buscarPermisoPendiente(): Permiso? {
        if (faltaPermisoNotificaciones()) {
            return Permiso(R.string.permiso_notificaciones) {
                pedirNotificaciones.launch(Manifest.permission.POST_NOTIFICATIONS)
            }
        }
        if (!Settings.canDrawOverlays(this)) {
            return Permiso(R.string.permiso_superposicion) {
                abrirAjuste(Settings.ACTION_MANAGE_OVERLAY_PERMISSION)
            }
        }
        if (faltaPermisoPantallaCompleta()) {
            return Permiso(R.string.permiso_pantalla_completa) {
                abrirAjuste(Settings.ACTION_MANAGE_APP_USE_FULL_SCREEN_INTENT)
            }
        }
        return null
    }

    private fun faltaPermisoNotificaciones() =
        Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU &&
            ContextCompat.checkSelfPermission(this, Manifest.permission.POST_NOTIFICATIONS) !=
            PackageManager.PERMISSION_GRANTED

    private fun faltaPermisoPantallaCompleta() =
        Build.VERSION.SDK_INT >= Build.VERSION_CODES.UPSIDE_DOWN_CAKE &&
            !getSystemService(NotificationManager::class.java).canUseFullScreenIntent()

    private fun abrirAjuste(accion: String) {
        startActivity(Intent(accion, Uri.parse("package:$packageName")))
    }

    // ---------- lectura y validación ----------
    private fun leerConfiguracion() = Configuracion(
        url = url.text.toString().trim(),
        permitirNavegadorCompleto = navegadorCompleto.isChecked,
        alarmaSonora = alarma.isChecked,
        vibracion = vibracion.isChecked,
        diasLaborales = dias.indices.filter { dias[it].isSelected },
        limiteBloqueoMinutos = limiteMinutos,
        codigoEmergencia = codigo.text.toString(),
        marcaciones = filas.map { Marcacion(it.nombre, it.hora.text.toString(), it.activa.isChecked) },
    )

    private fun buscarError(configuracion: Configuracion): Int? = when {
        !configuracion.url.startsWith("http://") && !configuracion.url.startsWith("https://") ||
            !configuracion.estaConfigurada -> R.string.error_url
        configuracion.diasLaborales.isEmpty() -> R.string.error_dias
        configuracion.codigoEmergencia.isEmpty() -> R.string.error_codigo
        else -> null
    }

    private fun configuracionValida(): Configuracion? {
        val configuracion = leerConfiguracion()
        val error = buscarError(configuracion) ?: return configuracion
        avisar(getString(error))
        return null
    }

    private fun avisar(texto: String) {
        Snackbar.make(findViewById(R.id.raiz), texto, Snackbar.LENGTH_LONG)
            .setAnchorView(R.id.barra_acciones)
            .show()
    }

    // ---------- acciones ----------
    private fun guardar() {
        val configuracion = configuracionValida() ?: return
        guardarConfiguracion(this, configuracion)
        val proxima = programarProximaMarcacion(this)
        avisar(
            if (proxima == null) {
                getString(R.string.guardado)
            } else {
                getString(
                    R.string.guardado_proxima,
                    proxima.marcacion.nombre, proxima.momento.format(FORMATO_PROXIMA),
                )
            },
        )
    }

    private fun probar() {
        val configuracion = configuracionValida() ?: return
        if (!ServicioBloqueo.activo) {
            ServicioBloqueo.iniciar(this, configuracion, getString(R.string.prueba))
        }
    }

    private fun probarSonido() {
        detenerPruebaDeSonido()
        alarmaDePrueba.iniciar()
        hilo.postDelayed(::detenerPruebaDeSonido, DURACION_PRUEBA_SONIDO_MS)
    }

    private fun detenerPruebaDeSonido() {
        hilo.removeCallbacksAndMessages(null)
        alarmaDePrueba.detener()
    }
}
