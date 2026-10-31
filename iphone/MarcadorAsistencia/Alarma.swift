import AVFoundation
import AudioToolbox

/// Sonido y vibración mientras el bloqueo está en pantalla.
@MainActor
final class Alarma {
    private static let intervaloVibracion: TimeInterval = 1

    private var reproductor: AVAudioPlayer?
    private var vibracion: Timer?

    func iniciar(sonido: Bool, vibrar: Bool) {
        if sonido { iniciarSonido() }
        if vibrar { iniciarVibracion() }
    }

    func detener() {
        reproductor?.stop()
        reproductor = nil
        vibracion?.invalidate()
        vibracion = nil
    }

    private func iniciarSonido() {
        guard reproductor == nil,
              let archivo = Bundle.main.url(forResource: "alarma", withExtension: "wav") else { return }
        do {
            // .playback suena aunque el interruptor de silencio esté activado.
            try AVAudioSession.sharedInstance().setCategory(.playback)
            try AVAudioSession.sharedInstance().setActive(true)
            let nuevo = try AVAudioPlayer(contentsOf: archivo)
            nuevo.numberOfLoops = -1
            nuevo.play()
            reproductor = nuevo
        } catch {
            reproductor = nil // sin audio disponible el bloqueo sigue en silencio
        }
    }

    private func iniciarVibracion() {
        guard vibracion == nil else { return }
        AudioServicesPlaySystemSound(kSystemSoundID_Vibrate)
        vibracion = Timer.scheduledTimer(withTimeInterval: Alarma.intervaloVibracion, repeats: true) { _ in
            AudioServicesPlaySystemSound(kSystemSoundID_Vibrate)
        }
    }
}
