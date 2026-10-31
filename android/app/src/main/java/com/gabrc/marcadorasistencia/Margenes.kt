package com.gabrc.marcadorasistencia

import android.view.View
import androidx.core.view.ViewCompat
import androidx.core.view.WindowInsetsCompat

/** Android dibuja bajo las barras del sistema: evita que tapen el contenido o que el teclado lo oculte. */
fun aplicarMargenesDeSistema(vista: View) {
    ViewCompat.setOnApplyWindowInsetsListener(vista) { v, margenes ->
        val zona = margenes.getInsets(
            WindowInsetsCompat.Type.systemBars() or
                WindowInsetsCompat.Type.displayCutout() or
                WindowInsetsCompat.Type.ime(),
        )
        v.setPadding(zona.left, zona.top, zona.right, zona.bottom)
        WindowInsetsCompat.CONSUMED
    }
}
