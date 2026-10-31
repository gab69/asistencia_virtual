import SwiftUI
import WebKit

/// Página de asistencia. La sesión iniciada se conserva entre bloqueos.
struct PaginaWeb: UIViewRepresentable {
    let configuracion: Configuracion
    let alBloquearSitio: () -> Void

    func makeCoordinator() -> Coordinador {
        Coordinador(configuracion: configuracion, alBloquearSitio: alBloquearSitio)
    }

    func makeUIView(context: Context) -> WKWebView {
        let pagina = WKWebView()
        pagina.navigationDelegate = context.coordinator
        pagina.uiDelegate = context.coordinator
        pagina.allowsBackForwardNavigationGestures = true
        if let direccion = URL(string: configuracion.url) {
            pagina.load(URLRequest(url: direccion))
        }
        return pagina
    }

    func updateUIView(_ pagina: WKWebView, context: Context) {}

    final class Coordinador: NSObject, WKNavigationDelegate, WKUIDelegate {
        private let configuracion: Configuracion
        private let sitioPermitido: String?
        private let alBloquearSitio: () -> Void

        init(configuracion: Configuracion, alBloquearSitio: @escaping () -> Void) {
            self.configuracion = configuracion
            self.alBloquearSitio = alBloquearSitio
            sitioPermitido = URL(string: configuracion.url)?.host
        }

        func webView(
            _ pagina: WKWebView,
            decidePolicyFor accion: WKNavigationAction,
            decisionHandler: @escaping (WKNavigationActionPolicy) -> Void
        ) {
            let esPrincipal = accion.targetFrame?.isMainFrame ?? true
            guard esPrincipal, let destino = accion.request.url else {
                decisionHandler(.allow)
                return
            }
            let esWeb = destino.scheme == "http" || destino.scheme == "https"
            let fueraDelSitio = !configuracion.permitirNavegadorCompleto && destino.host != sitioPermitido
            if esWeb && fueraDelSitio { alBloquearSitio() }
            decisionHandler(esWeb && !fueraDelSitio ? .allow : .cancel)
        }

        /// Los enlaces que abrirían otra pestaña se cargan en esta misma vista.
        func webView(
            _ pagina: WKWebView,
            createWebViewWith ajustes: WKWebViewConfiguration,
            for accion: WKNavigationAction,
            windowFeatures: WKWindowFeatures
        ) -> WKWebView? {
            pagina.load(accion.request)
            return nil
        }
    }
}
