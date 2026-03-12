import Foundation

// MARK: - LoginRequest

struct LoginRequest: Codable {
    let studentId: String
    let pin: String

    enum CodingKeys: String, CodingKey {
        case studentId = "student_id"
        case pin
    }
}

// MARK: - Student

struct Student: Codable {
    let studentId: String
    let name: String
    let cardStatus: String?

    enum CodingKeys: String, CodingKey {
        case studentId = "id"
        case name
        case cardStatus = "status"
    }
}

// MARK: - LoginResponse

struct LoginResponse: Codable {
    let token: String
    let student: Student
}

// MARK: - GenericSuccessResponse

struct GenericSuccessResponse: Codable {
    let success: Bool
    let message: String?
}
