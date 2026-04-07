import Foundation

// MARK: - LoginRequest

struct LoginRequest: Codable {
    let studentId: String

    enum CodingKeys: String, CodingKey {
        case studentId = "student_id"
    }
}

// MARK: - Student

struct Student: Decodable {
    let studentId: String
    let name: String
    let cardStatus: String?

    init(studentId: String, name: String, cardStatus: String?) {
        self.studentId = studentId
        self.name = name
        self.cardStatus = cardStatus
    }

    private enum CodingKeys: String, CodingKey {
        case studentId = "id"
        case studentIdAlt = "student_id"
        case studentIdCamel = "studentId"
        case studentIdUpper = "StudentID"
        case studentIdLegacy = "ID"

        case name
        case nameAlt = "student_name"
        case nameFull = "full_name"
        case nameUpper = "Name"

        case cardStatus = "status"
        case cardStatusAlt = "card_status"
        case cardStatusUpper = "Status"
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)

        studentId = try container.decodeFirstLossyString(
            forKeys: [.studentId, .studentIdAlt, .studentIdCamel, .studentIdUpper, .studentIdLegacy]
        )

        name = try container.decodeFirstLossyString(
            forKeys: [.name, .nameAlt, .nameFull, .nameUpper]
        )

        cardStatus = try container.decodeFirstLossyStringIfPresent(
            forKeys: [.cardStatus, .cardStatusAlt, .cardStatusUpper]
        )
    }
}

// MARK: - LoginResponse

struct LoginResponse: Decodable {
    let token: String
    let student: Student
    let jwtToken: String?

    private enum CodingKeys: String, CodingKey {
        case token
        case sessionToken = "session_token"
        case accessToken = "access_token"
        case authToken = "auth_token"
        case jwtToken = "jwt_token"

        case student
        case user

        case data
        case payload
        case result

        case rootStudentId = "id"
        case rootStudentIdAlt = "student_id"
        case rootStudentIdCamel = "studentId"
        case rootStudentIdUpper = "StudentID"
        case rootStudentIdLegacy = "ID"

        case rootName = "name"
        case rootNameAlt = "student_name"
        case rootNameFull = "full_name"
        case rootNameUpper = "Name"

        case rootStatus = "status"
        case rootStatusAlt = "card_status"
        case rootStatusUpper = "Status"
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)

        if let nestedData = try container.decodeIfPresent(LoginEnvelope.self, forKey: .data)
            ?? container.decodeIfPresent(LoginEnvelope.self, forKey: .payload)
            ?? container.decodeIfPresent(LoginEnvelope.self, forKey: .result) {
            token = nestedData.token
            student = nestedData.student
            jwtToken = nestedData.jwtToken
            return
        }

        token = try container.decodeFirstLossyString(
            forKeys: [.token, .sessionToken, .accessToken, .authToken, .jwtToken]
        )

        let primaryStudent = try container.decodeIfPresent(Student.self, forKey: .student)
        let fallbackStudent = try container.decodeIfPresent(Student.self, forKey: .user)

        if let decodedStudent = primaryStudent ?? fallbackStudent {
            student = decodedStudent
        } else {
            let studentId = try container.decodeFirstLossyString(
                forKeys: [.rootStudentId, .rootStudentIdAlt, .rootStudentIdCamel, .rootStudentIdUpper, .rootStudentIdLegacy]
            )
            let studentName = try container.decodeFirstLossyString(
                forKeys: [.rootName, .rootNameAlt, .rootNameFull, .rootNameUpper]
            )
            let status = try container.decodeFirstLossyStringIfPresent(
                forKeys: [.rootStatus, .rootStatusAlt, .rootStatusUpper]
            )
            student = Student(studentId: studentId, name: studentName, cardStatus: status)
        }

        jwtToken = try container.decodeFirstLossyStringIfPresent(forKeys: [.jwtToken])
    }
}

private struct LoginEnvelope: Decodable {
    let token: String
    let student: Student
    let jwtToken: String?

    private enum CodingKeys: String, CodingKey {
        case token
        case sessionToken = "session_token"
        case accessToken = "access_token"
        case authToken = "auth_token"
        case jwtToken = "jwt_token"
        case student
        case user
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        token = try container.decodeFirstLossyString(
            forKeys: [.token, .sessionToken, .accessToken, .authToken, .jwtToken]
        )

        let primaryStudent = try container.decodeIfPresent(Student.self, forKey: .student)
        let fallbackStudent = try container.decodeIfPresent(Student.self, forKey: .user)

        if let decodedStudent = primaryStudent ?? fallbackStudent {
            student = decodedStudent
        } else {
            throw DecodingError.keyNotFound(
                CodingKeys.student,
                DecodingError.Context(
                    codingPath: decoder.codingPath,
                    debugDescription: "Missing student object in login envelope"
                )
            )
        }

        jwtToken = try container.decodeFirstLossyStringIfPresent(forKeys: [.jwtToken])
    }
}

// MARK: - GenericSuccessResponse

struct GenericSuccessResponse: Codable {
    let success: Bool
    let message: String?
}

// MARK: - Decoding helpers

private extension KeyedDecodingContainer {
    func decodeLossyString(forKey key: Key) throws -> String {
        if let value = try decodeIfPresent(String.self, forKey: key) {
            return value
        }

        if let value = try decodeIfPresent(Int.self, forKey: key) {
            return String(value)
        }

        if let value = try decodeIfPresent(Double.self, forKey: key) {
            if value.rounded() == value {
                return String(Int(value))
            }
            return String(value)
        }

        if let value = try decodeIfPresent(Bool.self, forKey: key) {
            return value ? "true" : "false"
        }

        throw DecodingError.dataCorruptedError(
            forKey: key,
            in: self,
            debugDescription: "Expected string-compatible value"
        )
    }

    func decodeLossyStringIfPresent(forKey key: Key) throws -> String? {
        guard contains(key), (try decodeNil(forKey: key)) == false else {
            return nil
        }
        return try decodeLossyString(forKey: key)
    }

    func decodeFirstLossyString(forKeys keys: [Key]) throws -> String {
        if let value = try decodeFirstLossyStringIfPresent(forKeys: keys) {
            return value
        }

        throw DecodingError.keyNotFound(
            keys.first!,
            DecodingError.Context(
                codingPath: codingPath,
                debugDescription: "Missing required string-compatible value"
            )
        )
    }

    func decodeFirstLossyStringIfPresent(forKeys keys: [Key]) throws -> String? {
        for key in keys {
            if let value = try decodeLossyStringIfPresent(forKey: key) {
                return value
            }
        }
        return nil
    }
}
