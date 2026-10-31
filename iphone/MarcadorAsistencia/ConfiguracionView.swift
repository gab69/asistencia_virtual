import SwiftUI

private let opcionesLimite = [5, 10, 15, 20, 30, 45, 60]
private let diasSemana = ["Lu", "Ma", "Mi", "Ju", "Vi", "Sá", "Do"]
private let credito = "Desarrollado por @GabRec"

/// Pantalla de configuración: una sola columna pensada para usarse con el pulgar.
struct ConfiguracionView: View {
    @EnvironmentObject private var estado: EstadoApp
    @Environment(\.openURL) private var abrirEnlace

    @State private var borrador: Configuracion?
    @State private var mensaje: String?

    var body: some View {
        NavigationStack {
            Group {
                if let borrador = Binding($borrador) {
                    formulario(borrador)
                }
            }
            .navigationTitle("Marcador de asistencia")
            .navigationBarTitleDisplayMode(.inline)
        }
        .onAppear { if borrador == nil { borrador = estado.configuracion } }
        .alert(
            mensaje ?? "",
            isPresented: Binding(get: { mensaje != nil }, set: { if !$0 { mensaje = nil } })
        ) {
            Button("Aceptar", role: .cancel) {}
        }
    }

    private func formulario(_ datos: Binding<Configuracion>) -> some View {
        Form {
            if estado.faltanPermisos { avisoPermisos }
            seccionPagina(datos)
            seccionHorarios(datos)
            seccionDias(datos)
            seccionSeguridad(datos)
            seccionAcciones(datos)
        }
        .environment(\.locale, Locale(identifier: "es_ES")) // reloj de 24 horas
    }

    private var avisoPermisos: some View {
        Section {
            Text("Permite las notificaciones para que la app te avise a la hora de marcar.")
            Button("Conceder") {
                if let ajustes = URL(string: UIApplication.openSettingsURLString) { abrirEnlace(ajustes) }
            }
        }
        .listRowBackground(Color.orange.opacity(0.25))
    }

    private func seccionPagina(_ datos: Binding<Configuracion>) -> some View {
        Section {
            TextField("Dirección (URL)", text: datos.url)
                .keyboardType(.URL)
                .textContentType(.URL)
                .textInputAutocapitalization(.never)
                .autocorrectionDisabled()
            Toggle("Permitir otros sitios", isOn: datos.permitirNavegadorCompleto)
        } header: {
            Text("Página de asistencia")
        } footer: {
            Text("Déjalo activo si la página te lleva a otro sitio para iniciar sesión.")
        }
    }

    private func seccionHorarios(_ datos: Binding<Configuracion>) -> some View {
        Section("Horarios de marcación") {
            ForEach(datos.marcaciones) { $marcacion in
                HStack {
                    Toggle(marcacion.nombre, isOn: $marcacion.activa)
                    DatePicker(
                        marcacion.nombre,
                        selection: hora(de: $marcacion),
                        displayedComponents: .hourAndMinute
                    )
                    .labelsHidden()
                }
            }
        }
    }

    private func hora(de marcacion: Binding<Marcacion>) -> Binding<Date> {
        let calendario = Calendar.current
        return Binding(
            get: {
                let partes = marcacion.wrappedValue.hora.split(separator: ":").compactMap { Int($0) }
                return calendario.date(
                    bySettingHour: partes.first ?? 0, minute: partes.last ?? 0, second: 0, of: Date()
                ) ?? Date()
            },
            set: { nueva in
                let partes = calendario.dateComponents([.hour, .minute], from: nueva)
                marcacion.wrappedValue.hora = String(format: "%02d:%02d", partes.hour ?? 0, partes.minute ?? 0)
            }
        )
    }

    private func seccionDias(_ datos: Binding<Configuracion>) -> some View {
        Section("Días laborales") {
            HStack(spacing: 6) {
                ForEach(diasSemana.indices, id: \.self) { indice in
                    let elegido = datos.wrappedValue.diasLaborales.contains(indice)
                    Button(diasSemana[indice]) { alternar(indice, datos) }
                        .buttonStyle(.plain)
                        .frame(maxWidth: .infinity, minHeight: 40)
                        .background(elegido ? Color.blue : Color.gray.opacity(0.25), in: Circle())
                        .accessibilityAddTraits(elegido ? .isSelected : [])
                }
            }
        }
    }

    private func alternar(_ dia: Int, _ datos: Binding<Configuracion>) {
        if let posicion = datos.wrappedValue.diasLaborales.firstIndex(of: dia) {
            datos.wrappedValue.diasLaborales.remove(at: posicion)
        } else {
            datos.wrappedValue.diasLaborales.append(dia)
            datos.wrappedValue.diasLaborales.sort()
        }
    }

    private func seccionSeguridad(_ datos: Binding<Configuracion>) -> some View {
        Section("Seguridad y alarma") {
            Toggle("Alarma sonora", isOn: datos.alarmaSonora)
            Toggle("Vibración", isOn: datos.vibracion)
            Button("Probar sonido", systemImage: "speaker.wave.2", action: estado.probarSonido)
            Picker("Liberar automáticamente tras", selection: datos.limiteBloqueoMinutos) {
                ForEach(opcionesLimite, id: \.self) { Text("\($0) min") }
            }
            SecureField("Código de emergencia", text: datos.codigoEmergencia)
        }
    }

    private func seccionAcciones(_ datos: Binding<Configuracion>) -> some View {
        Section {
            Button("Guardar") {
                Task { mensaje = await estado.guardar(datos.wrappedValue) }
            }
            .bold()
            Button("Probar bloqueo") { mensaje = estado.probarBloqueo(datos.wrappedValue) }
        } footer: {
            Text(credito).frame(maxWidth: .infinity)
        }
    }
}
