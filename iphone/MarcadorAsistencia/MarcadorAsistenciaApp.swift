import Combine
import SwiftUI

@main
struct MarcadorAsistenciaApp: App {
    @StateObject private var estado = EstadoApp()
    @Environment(\.scenePhase) private var fase

    private let reloj = Timer.publish(every: 1, on: .main, in: .common).autoconnect()

    var body: some Scene {
        WindowGroup {
            ConfiguracionView()
                .environmentObject(estado)
                .preferredColorScheme(.dark)
                .fullScreenCover(item: $estado.vigente) { vigente in
                    BloqueoView(vigente: vigente, configuracion: estado.bloqueo, alLiberar: estado.liberar)
                }
                .task { await estado.preparar() }
                .onReceive(reloj) { _ in
                    if fase == .active { estado.revisar() }
                }
        }
        .onChange(of: fase) { _, nueva in
            switch nueva {
            case .active: estado.alVolver()
            case .background: estado.alSalir()
            default: break
            }
        }
    }
}
