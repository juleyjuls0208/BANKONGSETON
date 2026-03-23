import SwiftUI
import UIKit

extension Color {
    init(hex: String) {
        let rgba = HexColorParser.rgbaComponents(from: hex)
        self.init(
            .sRGB,
            red: rgba.red,
            green: rgba.green,
            blue: rgba.blue,
            opacity: rgba.alpha
        )
    }

    static func adaptive(light lightHex: String, dark darkHex: String) -> Color {
        Color(
            uiColor: UIColor { traits in
                if traits.userInterfaceStyle == .dark {
                    return UIColor(hex: darkHex)
                }
                return UIColor(hex: lightHex)
            }
        )
    }
}

extension UIColor {
    convenience init(hex: String) {
        let rgba = HexColorParser.rgbaComponents(from: hex)
        self.init(red: rgba.red, green: rgba.green, blue: rgba.blue, alpha: rgba.alpha)
    }
}

private enum HexColorParser {
    static func rgbaComponents(from rawHex: String) -> (red: CGFloat, green: CGFloat, blue: CGFloat, alpha: CGFloat) {
        let sanitized = rawHex.trimmingCharacters(in: CharacterSet.alphanumerics.inverted)
        var value: UInt64 = 0
        Scanner(string: sanitized).scanHexInt64(&value)

        let (alpha, red, green, blue): (UInt64, UInt64, UInt64, UInt64)

        switch sanitized.count {
        case 3:
            (alpha, red, green, blue) = (
                255,
                (value >> 8) * 17,
                (value >> 4 & 0xF) * 17,
                (value & 0xF) * 17
            )
        case 6:
            (alpha, red, green, blue) = (
                255,
                value >> 16,
                value >> 8 & 0xFF,
                value & 0xFF
            )
        case 8:
            (alpha, red, green, blue) = (
                value >> 24,
                value >> 16 & 0xFF,
                value >> 8 & 0xFF,
                value & 0xFF
            )
        default:
            (alpha, red, green, blue) = (255, 0, 0, 0)
        }

        return (
            red: CGFloat(red) / 255,
            green: CGFloat(green) / 255,
            blue: CGFloat(blue) / 255,
            alpha: CGFloat(alpha) / 255
        )
    }
}
