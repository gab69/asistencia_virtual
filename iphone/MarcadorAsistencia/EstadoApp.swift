import Foundation
import SwiftUI

/// Conecta configuración, horario, bloqueo y alarma.
@MainActor
final class EstadoApp: ObservableObject {
    private static let claveConfirmada = "ultima_confirmada"
    private static let duracionPruebaSonido: Duration = .seconds(3)

    @Published private(set) var configuracion: Configuracion
    @Published var vigente: Vigente?
    @Published private(set) var faltanPermisos = false

    private let almacen = AlmacenConfiguracion()
    private let alarma = Alarma()
    private var configuracionDelBloqueo: Configuracion
    private var pruebaDeSonido: Task<Void, Never>?

    /// El código y la página del bloqueo no cambian si se edita la configuración mientras dura.
    var bloqueo: Configuracion { configuracionDelBloqueo }

    init() {
        let cargada = almacen.cargar()
        configuracion = cargada
        configuracionDelBloqueo = cargada
    }

    func preparar() async {
        await Agenda.pedirPermisos()
        await Agenda.reprogramar(configuracion)
        faltanPermisos = await Agenda.faltanPermisos()
    }

    // ---------- acciones ----------
    /// Devuelve el texto a mostrar al usuario.
    func guardar(_ nueva: Configuracion) async -> String {
        if let error = nueva.error { return error }
        do {
            try almacen.guardar(nueva)
        } catch {
            return "No se pudo guardar la configuración."
        }
        configuracion = nueva
        await Agenda.reprogramar(nueva)
        guard let proxima = proximaMarcacion(nueva, ahora: Date()) else { return "Configuración guardada." }
        let cuando = proxima.momento.formatted(
            .dateTime.weekday(.abbreviated).day().hour(.twoDigits(amPM: .omitted)).minute()
                .locale(Locale(identifier: "es_ES"))
        )
        return "Guardado. Próxima: \(proxima.marcacion.nombre), \(cuando)"
    }

    /// Devuelve el error, si la configuración no es válida.
    func probarBloqueo(_ borrador: Configuracion) -> String? {
        if let error = borrador.error { return error }
        guard vigente == nil else { return nil }
        let plazo = TimeInterval(borrador.limiteBloqueoMinutos * 60)
        let prueba = Vigente(
            marcacion: Marcacion(nombre: "Prueba", hora: "--:--"),
            clave: "prueba",
            vence: Date().addingTimeInterval(plazo)
        )
        iniciarBloqueo(prueba, borrador)
        return nil
    }

    func probarSonido() {
        pruebaDeSonido?.cancel()
        alarma.iniciar(sonido: true, vibrar: false)
        pruebaDeSonido = Task {
            try? await Task.sleep(for: EstadoApp.duracionPruebaSonido)
            if !Task.isCancelled, vigente == nil { alarma.detener() }
        }
    }

    func liberar() {
        guard let actual = vigente else { return }
        if actual.clave != "prueba" {
            UserDefaults.standard.set(actual.clave, forKey: EstadoApp.claveConfirmada)
        }
        alarma.detener()
        Agenda.cancelarAvisosDeRegreso()
        vigente = nil
    }

    // ---------- ciclo de vida ----------
    /// Se llama cada segundo mientras la app está visible.
    func revisar() {
        if let actual = vigente {
            if Date() >= actual.vence { liberar() }
            return
        }
        let confirmada = UserDefaults.standard.string(forKey: EstadoApp.claveConfirmada)
        if let nueva = marcacionVigente(configuracion, ahora: Date(), ultimaConfirmada: confirmada) {
            iniciarBloqueo(nueva, configuracion)
        }
    }

    func alVolver() {
        Agenda.cancelarAvisosDeRegreso()
        Task { faltanPermisos = await Agenda.faltanPermisos() }
        revisar()
        if vigente != nil { sonar() }
    }

    func alSalir() {
        guard let actual = vigente else { return }
        alarma.detener()
        Agenda.avisarRegreso(actual, conSonido: configuracionDelBloqueo.alarmaSonora)
    }

    private func iniciarBloqueo(_ nuevo: Vigente, _ datos: Configuracion) {
        configuracionDelBloqueo = datos
        vigente = nuevo
        sonar()
    }

    private func sonar() {
        pruebaDeSonido?.cancel()
        alarma.detener()
        alarma.iniciar(sonido: configuracionDelBloqueo.alarmaSonora, vibrar: configuracionDelBloqueo.vibracion)
    }
}
