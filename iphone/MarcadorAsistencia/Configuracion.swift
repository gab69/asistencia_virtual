import Foundation

/// Modelo de configuración y su persistencia en disco (mismo JSON que la versión de Android).
struct Marcacion: Codable, Equatable, Identifiable {
    var nombre: String
    var hora: String // formato "HH:MM"
    var activa: Bool = true

    var id: String { nombre }
}

struct Configuracion: Codable, Equatable {
    static let urlVacia = "https://"

    var url = Configuracion.urlVacia
    var permitirNavegadorCompleto = true
    var alarmaSonora = true
    var vibracion = true
    var diasLaborales = [0, 1, 2, 3, 4] // 0 = lunes
    var limiteBloqueoMinutos = 15
    var codigoEmergencia = "1234"
    var marcaciones = [
        Marcacion(nombre: "Entrada", hora: "08:00"),
        Marcacion(nombre: "Salida a refrigerio", hora: "13:00"),
        Marcacion(nombre: "Regreso de refrigerio", hora: "14:00"),
        Marcacion(nombre: "Salida", hora: "17:00"),
    ]

    var estaConfigurada: Bool { url != Configuracion.urlVacia }

    enum CodingKeys: String, CodingKey {
        case url
        case permitirNavegadorCompleto = "permitir_navegador_completo"
        case alarmaSonora = "alarma_sonora"
        case vibracion
        case diasLaborales = "dias_laborales"
        case limiteBloqueoMinutos = "limite_bloqueo_minutos"
        case codigoEmergencia = "codigo_emergencia"
        case marcaciones
    }

    /// Mensaje del primer dato inválido, o nil si todo está bien.
    var error: String? {
        if !(url.hasPrefix("http://") || url.hasPrefix("https://")) || !estaConfigurada {
            return "Escribe una dirección que empiece con http:// o https://"
        }
        if diasLaborales.isEmpty { return "Selecciona al menos un día laboral." }
        if codigoEmergencia.isEmpty { return "Define un código de emergencia." }
        return nil
    }
}

extension Configuracion {
    init(from decoder: Decoder) throws {
        let datos = try decoder.container(keyedBy: CodingKeys.self)
        url = try datos.decode(String.self, forKey: .url)
        permitirNavegadorCompleto = try datos.decode(Bool.self, forKey: .permitirNavegadorCompleto)
        alarmaSonora = try datos.decode(Bool.self, forKey: .alarmaSonora)
        vibracion = try datos.decodeIfPresent(Bool.self, forKey: .vibracion) ?? true
        diasLaborales = try datos.decode([Int].self, forKey: .diasLaborales)
        limiteBloqueoMinutos = try datos.decode(Int.self, forKey: .limiteBloqueoMinutos)
        codigoEmergencia = try datos.decode(String.self, forKey: .codigoEmergencia)
        marcaciones = try datos.decode([Marcacion].self, forKey: .marcaciones)
    }
}

struct AlmacenConfiguracion {
    private static let nombreArchivo = "marcador_asistencia.json"

    let ruta: URL

    init(carpeta: URL = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]) {
        ruta = carpeta.appendingPathComponent(AlmacenConfiguracion.nombreArchivo)
    }

    func cargar() -> Configuracion {
        guard let datos = try? Data(contentsOf: ruta),
              let configuracion = try? JSONDecoder().decode(Configuracion.self, from: datos)
        else { return Configuracion() }
        return configuracion
    }

    func guardar(_ configuracion: Configuracion) throws {
        let codificador = JSONEncoder()
        codificador.outputFormatting = [.prettyPrinted, .sortedKeys, .withoutEscapingSlashes]
        try codificador.encode(configuracion).write(to: ruta, options: .atomic)
    }
}
