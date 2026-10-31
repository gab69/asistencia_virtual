import Foundation

/// Decide qué marcación toca. iOS no ejecuta la app a la hora marcada: el bloqueo
/// se calcula al abrirla, a partir del horario y de la última marcación confirmada.
struct Proxima: Equatable {
    let marcacion: Marcacion
    let momento: Date
}

/// Marcación cuyo plazo sigue abierto: desde su hora hasta `limiteBloqueoMinutos` después.
struct Vigente: Equatable, Identifiable {
    let marcacion: Marcacion
    let clave: String // identifica esta ocurrencia para no repetirla tras confirmarla
    let vence: Date

    var id: String { clave }
}

private let diasARevisar = 8 // hoy y el mismo día de la semana siguiente

private func momento(de marcacion: Marcacion, en dia: Date, _ calendario: Calendar) -> Date? {
    let partes = marcacion.hora.split(separator: ":").compactMap { Int($0) }
    guard partes.count == 2 else { return nil }
    return calendario.date(bySettingHour: partes[0], minute: partes[1], second: 0, of: dia)
}

/// Índice de la configuración (0 = lunes) para una fecha.
private func indiceDeDia(_ fecha: Date, _ calendario: Calendar) -> Int {
    (calendario.component(.weekday, from: fecha) + 5) % 7
}

/// `weekday` de Apple (1 = domingo) para un índice de la configuración (0 = lunes).
func diaDeApple(indice: Int) -> Int {
    (indice + 1) % 7 + 1
}

func proximaMarcacion(_ configuracion: Configuracion, ahora: Date, calendario: Calendar = .current) -> Proxima? {
    let activas = configuracion.marcaciones.filter(\.activa).sorted { $0.hora < $1.hora }
    let hoy = calendario.startOfDay(for: ahora)
    for desplazamiento in 0..<diasARevisar {
        guard let dia = calendario.date(byAdding: .day, value: desplazamiento, to: hoy),
              configuracion.diasLaborales.contains(indiceDeDia(dia, calendario)) else { continue }
        for marcacion in activas {
            if let cuando = momento(de: marcacion, en: dia, calendario), cuando > ahora {
                return Proxima(marcacion: marcacion, momento: cuando)
            }
        }
    }
    return nil
}

/// Revisa también ayer: el plazo de una marcación nocturna puede cruzar la medianoche.
func marcacionVigente(
    _ configuracion: Configuracion,
    ahora: Date,
    ultimaConfirmada: String?,
    calendario: Calendar = .current
) -> Vigente? {
    guard configuracion.estaConfigurada else { return nil }
    let plazo = TimeInterval(configuracion.limiteBloqueoMinutos * 60)
    let hoy = calendario.startOfDay(for: ahora)
    var masReciente: (vigente: Vigente, momento: Date)?
    for desplazamiento in [-1, 0] {
        guard let dia = calendario.date(byAdding: .day, value: desplazamiento, to: hoy),
              configuracion.diasLaborales.contains(indiceDeDia(dia, calendario)) else { continue }
        for marcacion in configuracion.marcaciones where marcacion.activa {
            guard let cuando = momento(de: marcacion, en: dia, calendario),
                  cuando <= ahora, ahora < cuando.addingTimeInterval(plazo) else { continue }
            if masReciente == nil || cuando > masReciente!.momento {
                let clave = "\(Int(cuando.timeIntervalSince1970)) \(marcacion.nombre)"
                let vigente = Vigente(marcacion: marcacion, clave: clave, vence: cuando.addingTimeInterval(plazo))
                masReciente = (vigente, cuando)
            }
        }
    }
    guard let vigente = masReciente?.vigente, vigente.clave != ultimaConfirmada else { return nil }
    return vigente
}
