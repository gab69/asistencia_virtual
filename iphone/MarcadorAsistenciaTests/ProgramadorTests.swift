import Foundation
import Testing
@testable import MarcadorAsistencia

private var calendario: Calendar = {
    var calendario = Calendar(identifier: .gregorian)
    calendario.timeZone = TimeZone(identifier: "America/Lima")!
    return calendario
}()

/// 2026-11-02 es lunes.
private func fecha(_ dia: Int, _ hora: Int, _ minuto: Int = 0, mes: Int = 11) -> Date {
    calendario.date(from: DateComponents(year: 2026, month: mes, day: dia, hour: hora, minute: minuto))!
}

private func configuracion(limite: Int = 15, dias: [Int] = [0, 1, 2, 3, 4]) -> Configuracion {
    var configuracion = Configuracion()
    configuracion.url = "https://empresa.example/asistencia"
    configuracion.limiteBloqueoMinutos = limite
    configuracion.diasLaborales = dias
    return configuracion
}

private func vigente(_ configuracion: Configuracion, _ ahora: Date, confirmada: String? = nil) -> Vigente? {
    marcacionVigente(configuracion, ahora: ahora, ultimaConfirmada: confirmada, calendario: calendario)
}

@Suite struct ProximaMarcacionTests {
    @Test func tomaLaSiguienteDelMismoDia() {
        let proxima = proximaMarcacion(configuracion(), ahora: fecha(2, 9), calendario: calendario)
        #expect(proxima?.marcacion.nombre == "Salida a refrigerio")
        #expect(proxima?.momento == fecha(2, 13))
    }

    @Test func laHoraExactaYaPaso() {
        let proxima = proximaMarcacion(configuracion(), ahora: fecha(2, 8), calendario: calendario)
        #expect(proxima?.marcacion.nombre == "Salida a refrigerio")
    }

    @Test func viernesPorLaNocheSaltaAlLunes() {
        let proxima = proximaMarcacion(configuracion(), ahora: fecha(6, 18), calendario: calendario)
        #expect(proxima?.momento == fecha(9, 8))
    }

    @Test func mismoDiaDeLaSemanaSiguiente() {
        let proxima = proximaMarcacion(configuracion(dias: [0]), ahora: fecha(2, 18), calendario: calendario)
        #expect(proxima?.momento == fecha(9, 8))
    }

    @Test func sinMarcacionesActivasNoHayProxima() {
        var sinActivas = configuracion()
        sinActivas.marcaciones = sinActivas.marcaciones.map {
            Marcacion(nombre: $0.nombre, hora: $0.hora, activa: false)
        }
        #expect(proximaMarcacion(sinActivas, ahora: fecha(2, 9), calendario: calendario) == nil)
    }
}

@Suite struct MarcacionVigenteTests {
    @Test func dentroDelPlazo() {
        let resultado = vigente(configuracion(), fecha(2, 8, 10))
        #expect(resultado?.marcacion.nombre == "Entrada")
        #expect(resultado?.vence == fecha(2, 8, 15))
    }

    @Test func alVencerElPlazoSeLibera() {
        #expect(vigente(configuracion(), fecha(2, 8, 15)) == nil)
    }

    @Test func antesDeLaHoraNoHayBloqueo() {
        #expect(vigente(configuracion(), fecha(2, 7, 59)) == nil)
    }

    @Test func unaVezConfirmadaNoSeRepite() throws {
        let ocurrencia = try #require(vigente(configuracion(), fecha(2, 8, 1)))
        #expect(vigente(configuracion(), fecha(2, 8, 5), confirmada: ocurrencia.clave) == nil)
    }

    @Test func laConfirmacionDeAyerNoAfectaHoy() throws {
        let ayer = try #require(vigente(configuracion(), fecha(2, 8, 1)))
        #expect(vigente(configuracion(), fecha(3, 8, 1), confirmada: ayer.clave) != nil)
    }

    @Test func noSeBloqueaEnDiasNoLaborales() {
        #expect(vigente(configuracion(), fecha(7, 8, 1)) == nil)
    }

    @Test func conPlazosSolapadosGanaLaMasReciente() {
        var cercanas = configuracion(limite: 60)
        cercanas.marcaciones = [
            Marcacion(nombre: "Primera", hora: "08:00"),
            Marcacion(nombre: "Segunda", hora: "08:30"),
        ]
        #expect(vigente(cercanas, fecha(2, 8, 40))?.marcacion.nombre == "Segunda")
    }

    @Test func elPlazoCruzaLaMedianoche() {
        var nocturna = configuracion(limite: 60)
        nocturna.marcaciones = [Marcacion(nombre: "Salida", hora: "23:50")]
        #expect(vigente(nocturna, fecha(3, 0, 10))?.vence == fecha(3, 0, 50))
    }

    @Test func sinUrlConfiguradaNoSeBloquea() {
        var sinUrl = configuracion()
        sinUrl.url = Configuracion.urlVacia
        #expect(vigente(sinUrl, fecha(2, 8, 1)) == nil)
    }
}

@Suite struct DiasTests {
    @Test func convierteAlFormatoDeApple() {
        #expect((0...6).map(diaDeApple) == [2, 3, 4, 5, 6, 7, 1])
    }
}

@Suite struct ConfiguracionTests {
    @Test func validaLosDatos() {
        var datos = Configuracion()
        #expect(datos.error?.contains("dirección") == true)
        datos.url = "ftp://x"
        #expect(datos.error?.contains("dirección") == true)
        datos.url = "http://x"
        #expect(datos.error == nil)
        datos.codigoEmergencia = ""
        #expect(datos.error == "Define un código de emergencia.")
        datos.diasLaborales = []
        #expect(datos.error == "Selecciona al menos un día laboral.")
    }

    @Test func leeElJsonDeAndroidSinVibracion() throws {
        let json = """
        {"url":"https://a.example","permitir_navegador_completo":false,"alarma_sonora":false,
         "dias_laborales":[0,5],"limite_bloqueo_minutos":30,"codigo_emergencia":"99",
         "marcaciones":[{"nombre":"Entrada","hora":"09:15","activa":false}]}
        """
        let datos = try JSONDecoder().decode(Configuracion.self, from: Data(json.utf8))
        #expect(datos.vibracion)
        #expect(!datos.permitirNavegadorCompleto)
        #expect(datos.diasLaborales == [0, 5])
        #expect(datos.marcaciones == [Marcacion(nombre: "Entrada", hora: "09:15", activa: false)])
    }

    @Test func guardarYCargarConservaLosDatos() throws {
        let carpeta = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        try FileManager.default.createDirectory(at: carpeta, withIntermediateDirectories: true)
        defer { try? FileManager.default.removeItem(at: carpeta) }
        let almacen = AlmacenConfiguracion(carpeta: carpeta)
        #expect(almacen.cargar() == Configuracion())
        try almacen.guardar(configuracion(limite: 45))
        #expect(almacen.cargar() == configuracion(limite: 45))
    }

    @Test func unArchivoDanadoDevuelveLosValoresPorDefecto() throws {
        let carpeta = FileManager.default.temporaryDirectory.appendingPathComponent(UUID().uuidString)
        try FileManager.default.createDirectory(at: carpeta, withIntermediateDirectories: true)
        defer { try? FileManager.default.removeItem(at: carpeta) }
        let almacen = AlmacenConfiguracion(carpeta: carpeta)
        try Data("no es json".utf8).write(to: almacen.ruta)
        #expect(almacen.cargar() == Configuracion())
    }
}
