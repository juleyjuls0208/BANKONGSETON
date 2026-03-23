import Foundation

// MARK: - LoginRequest

struct LoginRequest: Codable {
    let studentId: String

    enum CodingKeys: String, CodingKey {
        case studentId = "student_id"
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
    let jwtToken: String?

    enum CodingKeys: String, CodingKey {
        case token
        case student
        case jwtToken = "jwt_token"
    }
}

// MARK: - GenericSuccessResponse

struct GenericSuccessResponse: Codable {
    let success: Bool
    let message: String?
}
