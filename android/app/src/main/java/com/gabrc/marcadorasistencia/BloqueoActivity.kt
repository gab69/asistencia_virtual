package com.gabrc.marcadorasistencia

import android.annotation.SuppressLint
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.os.Bundle
import android.view.View
import android.webkit.CookieManager
import android.webkit.WebChromeClient
import android.webkit.WebResourceRequest
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.TextView
import android.widget.Toast
import androidx.activity.OnBackPressedCallback
import androidx.appcompat.app.AlertDialog
import androidx.appcompat.app.AppCompatActivity
import com.google.android.material.dialog.MaterialAlertDialogBuilder
import com.google.android.material.progressindicator.LinearProgressIndicator
import com.google.android.material.textfield.TextInputEditText
import com.google.android.material.textfield.TextInputLayout

private const val EXTRA_CONFIGURACION = "configuracion"
private const val EXTRA_NOMBRE = "nombre"
private const val PROGRESO_COMPLETO = 100

/** Pantalla que obliga a permanecer en la página de asistencia. */
class BloqueoActivity : AppCompatActivity() {
    private lateinit var configuracion: Configuracion
    private lateinit var pagina: WebView

    override fun onCreate(estado: Bundle?) {
        super.onCreate(estado)
        setShowWhenLocked(true)
        setTurnScreenOn(true)
        val datos = intent.getStringExtra(EXTRA_CONFIGURACION)
        if (!ServicioBloqueo.activo || datos == null) {
            finishAndRemoveTask()
            return
        }
        configuracion = Configuracion.desdeJson(datos)
        setContentView(R.layout.activity_bloqueo)
        aplicarMargenesDeSistema(findViewById(R.id.raiz))
        ServicioBloqueo.alLiberar = ::finishAndRemoveTask
        val nombre = intent.getStringExtra(EXTRA_NOMBRE).orEmpty()
        findViewById<TextView>(R.id.mensaje).text = getString(R.string.marca_tu, nombre.lowercase())
        findViewById<View>(R.id.boton_ya_marque).setOnClickListener { ServicioBloqueo.liberar(this) }
        findViewById<View>(R.id.boton_emergencia).setOnClickListener { pedirCodigoEmergencia() }
        configurarPagina()
        onBackPressedDispatcher.addCallback(this, object : OnBackPressedCallback(true) {
            override fun handleOnBackPressed() {
                if (pagina.canGoBack()) pagina.goBack() // nunca sale de la pantalla de bloqueo
            }
        })
    }

    override fun onStart() {
        super.onStart()
        visible = true
        if (!ServicioBloqueo.activo) finishAndRemoveTask()
    }

    override fun onStop() {
        super.onStop()
        visible = false
        CookieManager.getInstance().flush() // conserva la sesión iniciada en la página
    }

    override fun onDestroy() {
        if (::pagina.isInitialized) {
            ServicioBloqueo.alLiberar = null
            pagina.destroy()
        }
        super.onDestroy()
    }

    // ---------- página de asistencia ----------
    @SuppressLint("SetJavaScriptEnabled")
    private fun configurarPagina() {
        pagina = findViewById(R.id.pagina)
        val progreso = findViewById<LinearProgressIndicator>(R.id.progreso)
        pagina.settings.javaScriptEnabled = true
        pagina.settings.domStorageEnabled = true
        CookieManager.getInstance().setAcceptThirdPartyCookies(pagina, true)
        pagina.webViewClient = ClientePagina()
        pagina.webChromeClient = object : WebChromeClient() {
            override fun onProgressChanged(vista: WebView, avance: Int) {
                progreso.visibility = if (avance < PROGRESO_COMPLETO) View.VISIBLE else View.GONE
                progreso.progress = avance
            }
        }
        pagina.loadUrl(configuracion.url)
    }

    private inner class ClientePagina : WebViewClient() {
        private val sitioPermitido = Uri.parse(configuracion.url).host

        override fun shouldOverrideUrlLoading(vista: WebView, pedido: WebResourceRequest): Boolean {
            val destino = pedido.url
            if (destino.scheme != "http" && destino.scheme != "https") return true
            val bloqueada = pedido.isForMainFrame &&
                !configuracion.permitirNavegadorCompleto &&
                destino.host != sitioPermitido
            if (bloqueada) {
                Toast.makeText(this@BloqueoActivity, R.string.pagina_no_permitida, Toast.LENGTH_SHORT).show()
            }
            return bloqueada
        }
    }

    // ---------- salida ----------
    private fun pedirCodigoEmergencia() {
        val contenedor = layoutInflater.inflate(R.layout.dialogo_emergencia, null)
        val marco = contenedor.findViewById<TextInputLayout>(R.id.marco_codigo)
        val campo = contenedor.findViewById<TextInputEditText>(R.id.campo_codigo)
        val dialogo = MaterialAlertDialogBuilder(this)
            .setTitle(R.string.codigo_emergencia)
            .setMessage(R.string.ingresa_codigo)
            .setView(contenedor)
            .setNegativeButton(R.string.cancelar, null)
            .setPositiveButton(R.string.desbloquear, null)
            .show()
        dialogo.getButton(AlertDialog.BUTTON_POSITIVE).setOnClickListener {
            if (campo.text.toString() == configuracion.codigoEmergencia) {
                dialogo.dismiss()
                ServicioBloqueo.liberar(this)
            } else {
                marco.error = getString(R.string.codigo_incorrecto)
                campo.text = null
            }
        }
    }

    companion object {
        @Volatile
        var visible = false
            private set

        fun intencion(contexto: Context, configuracion: String, nombre: String): Intent =
            Intent(contexto, BloqueoActivity::class.java)
                .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                .putExtra(EXTRA_CONFIGURACION, configuracion)
                .putExtra(EXTRA_NOMBRE, nombre)
    }
}
