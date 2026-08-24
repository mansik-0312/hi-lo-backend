from enum import Enum

class LoginStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"

class LanguageEnum(str, Enum):
    EN = "en"
    FR = "fr"

class NotificationRecipientType(str, Enum):
    USER = "user"
    ADMIN = "admin"

class NotificationType(str, Enum):
    REGISTRATION = "registration"
    REPORT = "report"
    BLOCK = "block"

