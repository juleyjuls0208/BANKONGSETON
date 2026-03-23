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

    init(studentId: String, name: String, cardStatus: String?) {
        self.studentId = studentId
        self.name = name
        self.cardStatus = cardStatus
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)

        if let idString = try? container.decode(String.self, forKey: .studentId) {
            studentId = idString
        } else if let idInt = try? container.decode(Int.self, forKey: .studentId) {
            studentId = String(idInt)
        } else {
            throw DecodingError.dataCorruptedError(
                forKey: .studentId,
                in: container,
                debugDescription: "Expected student id to be a string or integer"
            )
        }

        name = try container.decode(String.self, forKey: .name)
        cardStatus = try container.decodeIfPresent(String.self, forKey: .cardStatus)
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
