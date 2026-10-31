import AppIntents
import Foundation
import SwiftUI
import UserNotifications
#if canImport(AlarmKit)
import AlarmKit
#endif

/// Deja programadas en el sistema las marcaciones: iOS las dispara aunque la app esté cerrada.
/// Con iOS 26 o superior usa alarmas reales, que suenan aunque el teléfono esté en silencio.
enum Agenda {
    private static let sonido = UNNotificationSoundName("alarma.wav")
    private static let prefijoRegreso = "regreso-"
    private static let maximoAvisosDeRegreso = 10
    private static let segundosEntreAvisos: TimeInterval = 60
    private static let segundosPrimerAviso: TimeInterval = 5

    private static var centro: UNUserNotificationCenter { .current() }

    static func pedirPermisos() async {
        _ = try? await centro.requestAuthorization(options: [.alert, .sound, .badge])
        #if canImport(AlarmKit)
        if #available(iOS 26.0, *) { _ = try? await AlarmManager.shared.requestAuthorization() }
        #endif
    }

    static func faltanPermisos() async -> Bool {
        let ajustes = await centro.notificationSettings()
        return ajustes.authorizationStatus == .denied
    }

    static func reprogramar(_ configuracion: Configuracion) async {
        centro.removeAllPendingNotificationRequests()
        #if canImport(AlarmKit)
        if #available(iOS 26.0, *) { cancelarAlarmas() }
        #endif
        guard configuracion.estaConfigurada else { return }
        // Una alarma siempre suena: si el usuario quiere silencio, se usan notificaciones.
        #if canImport(AlarmKit)
        if #available(iOS 26.0, *), configuracion.alarmaSonora,
           AlarmManager.shared.authorizationState == .authorized {
            await programarAlarmas(configuracion)
            return
        }
        #endif
        await programarNotificaciones(configuracion)
    }

    // ---------- notificaciones ----------
    /// Son 28 como máximo (4 marcaciones por 7 días); iOS admite 64 pendientes.
    private static func programarNotificaciones(_ configuracion: Configuracion) async {
        for marcacion in configuracion.marcaciones where marcacion.activa {
            let partes = marcacion.hora.split(separator: ":").compactMap { Int($0) }
            guard partes.count == 2 else { continue }
            for dia in configuracion.diasLaborales {
                var cuando = DateComponents()
                cuando.weekday = diaDeApple(indice: dia)
                cuando.hour = partes[0]
                cuando.minute = partes[1]
                let pedido = UNNotificationRequest(
                    identifier: "\(marcacion.nombre)-\(dia)",
                    content: contenido(marcacion.nombre, conSonido: configuracion.alarmaSonora),
                    trigger: UNCalendarNotificationTrigger(dateMatching: cuando, repeats: true)
                )
                try? await centro.add(pedido)
            }
        }
    }

    private static func contenido(_ nombre: String, conSonido: Bool) -> UNNotificationContent {
        let contenido = UNMutableNotificationContent()
        contenido.title = "Marca tu \(nombre.lowercased()) ahora"
        contenido.body = "Toca para abrir la página de asistencia."
        contenido.sound = conSonido ? UNNotificationSound(named: sonido) : nil
        return contenido
    }

    // ---------- avisos al salir del bloqueo ----------
    /// iOS no deja impedir que se salga de la app: se insiste hasta que vuelva o venza el plazo.
    static func avisarRegreso(_ vigente: Vigente, conSonido: Bool) {
        let disponible = vigente.vence.timeIntervalSinceNow
        for indice in 0..<maximoAvisosDeRegreso {
            let espera = segundosPrimerAviso + TimeInterval(indice) * segundosEntreAvisos
            guard espera < disponible else { return }
            let pedido = UNNotificationRequest(
                identifier: "\(prefijoRegreso)\(indice)",
                content: contenido(vigente.marcacion.nombre, conSonido: conSonido),
                trigger: UNTimeIntervalNotificationTrigger(timeInterval: espera, repeats: false)
            )
            centro.add(pedido, withCompletionHandler: nil)
        }
    }

    static func cancelarAvisosDeRegreso() {
        let identificadores = (0..<maximoAvisosDeRegreso).map { "\(prefijoRegreso)\($0)" }
        centro.removePendingNotificationRequests(withIdentifiers: identificadores)
        centro.removeDeliveredNotifications(withIdentifiers: identificadores)
    }

    // ---------- alarmas de iOS 26 ----------
    #if canImport(AlarmKit)
    @available(iOS 26.0, *)
    private static func cancelarAlarmas() {
        let existentes = (try? AlarmManager.shared.alarms) ?? []
        for alarma in existentes { try? AlarmManager.shared.cancel(id: alarma.id) }
    }

    @available(iOS 26.0, *)
    private static func programarAlarmas(_ configuracion: Configuracion) async {
        let dias = configuracion.diasLaborales.map(diaDeLocale)
        for marcacion in configuracion.marcaciones where marcacion.activa {
            let partes = marcacion.hora.split(separator: ":").compactMap { Int($0) }
            guard partes.count == 2 else { continue }
            let hora = Alarm.Schedule.Relative.Time(hour: partes[0], minute: partes[1])
            let alarma = AlarmManager.AlarmConfiguration<DatosAlarma>.alarm(
                schedule: .relative(.init(time: hora, repeats: .weekly(dias))),
                attributes: atributos(marcacion.nombre),
                secondaryIntent: AbrirPaginaDeAsistencia()
            )
            _ = try? await AlarmManager.shared.schedule(id: UUID(), configuration: alarma)
        }
    }

    /// `stopButton` es obligatorio en iOS 26.0; las versiones nuevas lo ignoran.
    @available(iOS 26.0, *)
    private static func atributos(_ nombre: String) -> AlarmAttributes<DatosAlarma> {
        let alerta = AlarmPresentation.Alert(
            title: LocalizedStringResource(stringLiteral: "Marca tu \(nombre.lowercased())"),
            stopButton: AlarmButton(text: "Detener", textColor: .white, systemImageName: "stop.circle"),
            secondaryButton: AlarmButton(text: "Abrir", textColor: .white, systemImageName: "checkmark.circle"),
            secondaryButtonBehavior: .custom
        )
        return AlarmAttributes(
            presentation: AlarmPresentation(alert: alerta),
            metadata: DatosAlarma(),
            tintColor: .blue
        )
    }

    @available(iOS 26.0, *)
    private static func diaDeLocale(_ indice: Int) -> Locale.Weekday {
        [.monday, .tuesday, .wednesday, .thursday, .friday, .saturday, .sunday][indice]
    }
    #endif
}

#if canImport(AlarmKit)
@available(iOS 26.0, *)
struct DatosAlarma: AlarmMetadata {}

/// Botón "Abrir" de la alarma: al entrar a la app aparece el bloqueo de la marcación vigente.
@available(iOS 26.0, *)
struct AbrirPaginaDeAsistencia: LiveActivityIntent {
    static var title: LocalizedStringResource { "Abrir página de asistencia" }
    static var openAppWhenRun: Bool { true }

    func perform() async throws -> some IntentResult { .result() }
}
#endif
