import SwiftUI

private let colorBarra = Color(red: 0xC6 / 255, green: 0x28 / 255, blue: 0x28 / 255)
private let colorConfirmar = Color(red: 0x2E / 255, green: 0x7D / 255, blue: 0x32 / 255)
private let segundosAvisoSitio: Duration = .seconds(2)

/// Pantalla que mantiene a la vista la página de asistencia.
struct BloqueoView: View {
    let vigente: Vigente
    let configuracion: Configuracion
    let alLiberar: () -> Void

    @State private var pidiendoCodigo = false
    @State private var sitioBloqueado = false

    var body: some View {
        VStack(spacing: 0) {
            encabezado
            PaginaWeb(configuracion: configuracion, alBloquearSitio: avisarSitioBloqueado)
                .overlay(alignment: .bottom) {
                    if sitioBloqueado { avisoSitio }
                }
        }
        .interactiveDismissDisabled()
        .onAppear { UIApplication.shared.isIdleTimerDisabled = true }
        .onDisappear { UIApplication.shared.isIdleTimerDisabled = false }
        .sheet(isPresented: $pidiendoCodigo) {
            CodigoEmergenciaView(codigoCorrecto: configuracion.codigoEmergencia, alAceptar: alLiberar)
                .presentationDetents([.medium])
        }
    }

    private var encabezado: some View {
        VStack(spacing: 10) {
            Text("Marca tu \(vigente.marcacion.nombre.lowercased()) ahora")
                .font(.headline)
                .foregroundStyle(.white)
                .multilineTextAlignment(.center)
            HStack(spacing: 10) {
                Button("Emergencia", systemImage: "lock.fill") { pidiendoCodigo = true }
                    .buttonStyle(.bordered)
                    .tint(.white)
                Button("Ya marqué", systemImage: "checkmark", action: alLiberar)
                    .buttonStyle(.borderedProminent)
                    .tint(colorConfirmar)
            }
        }
        .frame(maxWidth: .infinity)
        .padding(12)
        .background(colorBarra)
    }

    private var avisoSitio: some View {
        Text("Solo puedes usar la página de asistencia.")
            .font(.footnote)
            .padding(10)
            .background(.ultraThinMaterial, in: Capsule())
            .padding(.bottom, 16)
    }

    private func avisarSitioBloqueado() {
        sitioBloqueado = true
        Task {
            try? await Task.sleep(for: segundosAvisoSitio)
            sitioBloqueado = false
        }
    }
}

private struct CodigoEmergenciaView: View {
    let codigoCorrecto: String
    let alAceptar: () -> Void

    @Environment(\.dismiss) private var cerrar
    @State private var codigo = ""
    @State private var incorrecto = false
    @FocusState private var enCampo: Bool

    var body: some View {
        NavigationStack {
            Form {
                Section {
                    SecureField("Código", text: $codigo)
                        .focused($enCampo)
                        .onSubmit(comprobar)
                } footer: {
                    Text(incorrecto ? "Código incorrecto. Inténtalo de nuevo." : "Ingresa tu código para salir del bloqueo.")
                        .foregroundStyle(incorrecto ? .red : .secondary)
                }
            }
            .navigationTitle("Código de emergencia")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancelar") { cerrar() }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Desbloquear", action: comprobar)
                }
            }
            .onAppear { enCampo = true }
        }
    }

    private func comprobar() {
        guard codigo == codigoCorrecto else {
            incorrecto = true
            codigo = ""
            return
        }
        cerrar()
        alAceptar()
    }
}
