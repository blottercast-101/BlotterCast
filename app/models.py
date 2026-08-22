from datetime import datetime

from .extensions import db


def now():
    return datetime.utcnow()


class Zone(db.Model):
    __tablename__ = "zones"
    zone_id = db.Column(db.String(10), primary_key=True)
    label = db.Column(db.String(100), nullable=False)
    lat = db.Column(db.Numeric(9, 6), nullable=False)
    lng = db.Column(db.Numeric(9, 6), nullable=False)
    weight = db.Column(db.Numeric(4, 3), nullable=False)


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)  # bcrypt hash
    full_name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150))
    contact_no = db.Column(db.String(30))
    role = db.Column(db.String(30), nullable=False, default="Desk Officer")
    status = db.Column(db.String(20), nullable=False, default="Active")
    mfa_enabled = db.Column(db.Boolean, nullable=False, default=True)
    google_id = db.Column(db.String(100))
    auth_provider = db.Column(db.String(30), nullable=False, default="local")
    signature_path = db.Column(db.String(255))
    last_login = db.Column(db.DateTime)
    failed_attempts = db.Column(db.Integer, nullable=False, default=0)
    locked_until = db.Column(db.DateTime)
    password_changed_at = db.Column(db.DateTime, default=now)
    created_at = db.Column(db.DateTime, default=now)

    @property
    def is_2fa_enabled(self) -> bool:
        return bool(self.mfa_enabled)

    @is_2fa_enabled.setter
    def is_2fa_enabled(self, val: bool) -> None:
        self.mfa_enabled = bool(val)

    def __init__(
        self,
        username=None,
        password=None,
        full_name=None,
        email=None,
        contact_no=None,
        role="Desk Officer",
        status="Active",
        mfa_enabled=True,
        google_id=None,
        auth_provider="local",
        signature_path=None,
        last_login=None,
        failed_attempts=0,
        locked_until=None,
        password_changed_at=None,
        created_at=None,
        **kwargs
    ):
        super().__init__(
            username=username,
            password=password,
            full_name=full_name,
            email=email,
            contact_no=contact_no,
            role=role,
            status=status,
            mfa_enabled=mfa_enabled,
            google_id=google_id,
            auth_provider=auth_provider,
            signature_path=signature_path,
            last_login=last_login,
            failed_attempts=failed_attempts,
            locked_until=locked_until,
            password_changed_at=password_changed_at,
            created_at=created_at,
            **kwargs
        )


class OtpCode(db.Model):
    __tablename__ = "otp_codes"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    code_hash = db.Column(db.String(64), nullable=False)
    purpose = db.Column(db.String(20), nullable=False, default="login")
    expires_at = db.Column(db.DateTime, nullable=False)
    attempts = db.Column(db.Integer, nullable=False, default=0)
    consumed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=now, index=True)

    def __init__(
        self,
        user_id=None,
        code_hash=None,
        purpose="login",
        expires_at=None,
        attempts=0,
        consumed_at=None,
        created_at=None,
        **kwargs
    ):
        super().__init__(
            user_id=user_id,
            code_hash=code_hash,
            purpose=purpose,
            expires_at=expires_at,
            attempts=attempts,
            consumed_at=consumed_at,
            created_at=created_at,
            **kwargs
        )


class AuditLog(db.Model):
    __tablename__ = "audit_logs"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    action = db.Column(db.String(50), nullable=False)
    module = db.Column(db.String(50), nullable=False)
    details = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=now, index=True)

    def __init__(self, username=None, action=None, module=None, details=None, created_at=None, **kwargs):
        super().__init__(username=username, action=action, module=module, details=details, created_at=created_at, **kwargs)


class SystemSetting(db.Model):
    __tablename__ = "system_settings"
    setting_key = db.Column(db.String(100), primary_key=True)
    setting_value = db.Column(db.Text, nullable=False)
    updated_at = db.Column(db.DateTime, default=now, onupdate=now)


class Incident(db.Model):
    __tablename__ = "incidents"
    id = db.Column(db.Integer, primary_key=True)
    report_no = db.Column(db.String(30), nullable=False, unique=True)
    incident_date = db.Column(db.Date, nullable=False, index=True)
    time_reported = db.Column(db.Time, nullable=False)
    hour = db.Column(db.SmallInteger, nullable=False)
    zone_id = db.Column(db.String(10), db.ForeignKey("zones.zone_id"), nullable=False)
    location = db.Column(db.String(255))
    lat = db.Column(db.Numeric(9, 6))
    lng = db.Column(db.Numeric(9, 6))
    category = db.Column(db.String(60), nullable=False)
    description = db.Column(db.Text)
    reporter = db.Column(db.String(150))
    officer = db.Column(db.String(100))
    priority = db.Column(db.String(10), nullable=False, default="Medium")
    status = db.Column(db.String(30), nullable=False, default="Under Investigation")
    created_at = db.Column(db.DateTime, default=now)
    updated_at = db.Column(db.DateTime, default=now, onupdate=now)

    def to_dict(self):
        return {
            "id": self.id, "report_no": self.report_no,
            "incident_date": self.incident_date.isoformat() if self.incident_date else None,
            "time_reported": self.time_reported.isoformat() if self.time_reported else None,
            "hour": self.hour, "zone_id": self.zone_id, "location": self.location,
            "lat": float(self.lat) if self.lat is not None else None,
            "lng": float(self.lng) if self.lng is not None else None,
            "category": self.category, "description": self.description,
            "reporter": self.reporter, "officer": self.officer,
            "priority": self.priority, "status": self.status,
        }


class BlotterRecord(db.Model):
    __tablename__ = "blotter_records"
    id = db.Column(db.Integer, primary_key=True)
    docket_no = db.Column(db.String(30), nullable=False, unique=True)
    date_filed = db.Column(db.Date, nullable=False)
    complainant = db.Column(db.String(150), nullable=False)
    complainant_id = db.Column(db.Integer, db.ForeignKey("census_records.id", ondelete="SET NULL"))
    complainant_addr = db.Column(db.String(255))
    respondent = db.Column(db.String(150), nullable=False)
    respondent_id = db.Column(db.Integer, db.ForeignKey("census_records.id", ondelete="SET NULL"))
    respondent_addr = db.Column(db.String(255))
    nature = db.Column(db.String(100))
    case_type = db.Column(db.String(10), nullable=False, default="CRIM")
    status = db.Column(db.String(20), nullable=False, default="Pending")
    zone_id = db.Column(db.String(10), db.ForeignKey("zones.zone_id"))
    archived = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, default=now)
    updated_at = db.Column(db.DateTime, default=now, onupdate=now)

    def to_dict(self):
        return {
            "id": self.id, "docket_no": self.docket_no,
            "date_filed": self.date_filed.isoformat() if self.date_filed else None,
            "complainant": self.complainant, "complainant_id": self.complainant_id,
            "complainant_addr": self.complainant_addr,
            "respondent": self.respondent, "respondent_id": self.respondent_id,
            "respondent_addr": self.respondent_addr, "nature": self.nature,
            "case_type": self.case_type, "status": self.status, "zone_id": self.zone_id,
            "archived": self.archived,
        }


class Settlement(db.Model):
    __tablename__ = "settlements"
    id = db.Column(db.Integer, primary_key=True)
    blotter_id = db.Column(db.Integer, db.ForeignKey("blotter_records.id", ondelete="CASCADE"), nullable=False)
    case_no = db.Column(db.String(30), nullable=False, unique=True)
    case_title = db.Column(db.String(200))
    complaint_title = db.Column(db.String(150))
    nature = db.Column(db.String(10), nullable=False, default="Civil")
    date_filed = db.Column(db.Date)
    date_confrontation = db.Column(db.Date)
    action_taken = db.Column(db.String(100))
    date_settlement = db.Column(db.Date)
    date_execution = db.Column(db.Date)
    main_point = db.Column(db.Text)
    status = db.Column(db.String(20), nullable=False, default="Pending")
    remarks = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=now)
    updated_at = db.Column(db.DateTime, default=now, onupdate=now)

    blotter = db.relationship("BlotterRecord")

    def to_dict(self):
        b = self.blotter
        return {
            "id": self.id, "blotter_id": self.blotter_id, "case_no": self.case_no,
            "case_title": self.case_title, "complaint_title": self.complaint_title,
            "nature": self.nature,
            "date_filed": self.date_filed.isoformat() if self.date_filed else None,
            "date_confrontation": self.date_confrontation.isoformat() if self.date_confrontation else None,
            "action_taken": self.action_taken,
            "date_settlement": self.date_settlement.isoformat() if self.date_settlement else None,
            "date_execution": self.date_execution.isoformat() if self.date_execution else None,
            "main_point": self.main_point, "status": self.status, "remarks": self.remarks,
            "blotter_docket_no": b.docket_no if b else None,
            "complainant": b.complainant if b else None,
            "complainant_addr": b.complainant_addr if b else None,
            "respondent": b.respondent if b else None,
            "respondent_addr": b.respondent_addr if b else None,
            "blotter_case_type": b.case_type if b else None,
        }


class CensusRecord(db.Model):
    __tablename__ = "census_records"
    id = db.Column(db.Integer, primary_key=True)
    resident_no = db.Column(db.String(20), nullable=False, unique=True)
    last_name = db.Column(db.String(80), nullable=False)
    first_name = db.Column(db.String(80), nullable=False)
    middle_name = db.Column(db.String(80))
    date_of_birth = db.Column(db.Date)
    sex = db.Column(db.String(10), nullable=False, default="Male")
    civil_status = db.Column(db.String(20), nullable=False, default="Single")
    nationality = db.Column(db.String(60), nullable=False, default="Filipino")
    zone_id = db.Column(db.String(10), db.ForeignKey("zones.zone_id"))
    address = db.Column(db.String(255))
    household_no = db.Column(db.String(30))
    contact_no = db.Column(db.String(30))
    voter_status = db.Column(db.String(30), nullable=False, default="Not Registered")
    occupation = db.Column(db.String(100))
    status = db.Column(db.String(20), nullable=False, default="Active")
    created_at = db.Column(db.DateTime, default=now)
    updated_at = db.Column(db.DateTime, default=now, onupdate=now)

    def to_dict(self):
        return {
            "id": self.id, "resident_no": self.resident_no,
            "last_name": self.last_name, "first_name": self.first_name,
            "middle_name": self.middle_name,
            "date_of_birth": self.date_of_birth.isoformat() if self.date_of_birth else None,
            "sex": self.sex, "civil_status": self.civil_status, "nationality": self.nationality,
            "zone_id": self.zone_id, "address": self.address, "household_no": self.household_no,
            "contact_no": self.contact_no, "voter_status": self.voter_status,
            "occupation": self.occupation, "status": self.status,
        }


class BarangayClearance(db.Model):
    __tablename__ = "barangay_clearance"
    id = db.Column(db.Integer, primary_key=True)
    resident_id = db.Column(db.Integer, db.ForeignKey("census_records.id", ondelete="CASCADE"), nullable=False)
    ctrl_no = db.Column(db.String(30), nullable=False, unique=True)
    full_name = db.Column(db.String(150), nullable=False)
    age = db.Column(db.SmallInteger)
    civil_status = db.Column(db.String(20), nullable=False, default="Single")
    address = db.Column(db.String(255))
    voter_status = db.Column(db.String(30), nullable=False, default="Not Registered")
    purpose = db.Column(db.String(150))
    or_no = db.Column(db.String(30))
    fee = db.Column(db.Numeric(10, 2), nullable=False, default=20.00)
    date_issued = db.Column(db.Date, nullable=False)
    issued_by = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=now)

    resident = db.relationship("CensusRecord")

    def to_dict(self):
        r = self.resident
        return {
            "id": self.id, "resident_id": self.resident_id, "ctrl_no": self.ctrl_no,
            "full_name": self.full_name, "age": self.age, "civil_status": self.civil_status,
            "address": self.address, "voter_status": self.voter_status, "purpose": self.purpose,
            "or_no": self.or_no, "fee": float(self.fee) if self.fee is not None else None,
            "date_issued": self.date_issued.isoformat() if self.date_issued else None,
            "issued_by": self.issued_by,
            "resident_no": r.resident_no if r else None,
            "resident_last_name": r.last_name if r else None,
            "resident_first_name": r.first_name if r else None,
        }


class BarangayResidency(db.Model):
    __tablename__ = "barangay_residency"
    id = db.Column(db.Integer, primary_key=True)
    resident_id = db.Column(db.Integer, db.ForeignKey("census_records.id", ondelete="CASCADE"), nullable=False)
    ctrl_no = db.Column(db.String(30), nullable=False, unique=True)
    full_name = db.Column(db.String(150), nullable=False)
    age = db.Column(db.SmallInteger)
    civil_status = db.Column(db.String(20), nullable=False, default="Single")
    address = db.Column(db.String(255))
    years_residency = db.Column(db.SmallInteger)
    duration_unit = db.Column(db.String(10), nullable=False, default="years")
    purpose = db.Column(db.String(150))
    or_no = db.Column(db.String(30))
    fee = db.Column(db.Numeric(10, 2), nullable=False, default=20.00)
    date_issued = db.Column(db.Date, nullable=False)
    issued_by = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=now)

    resident = db.relationship("CensusRecord")

    def to_dict(self):
        r = self.resident
        return {
            "id": self.id, "resident_id": self.resident_id, "ctrl_no": self.ctrl_no,
            "full_name": self.full_name, "age": self.age, "civil_status": self.civil_status,
            "address": self.address, "years_residency": self.years_residency,
            "duration_unit": self.duration_unit, "purpose": self.purpose, "or_no": self.or_no,
            "fee": float(self.fee) if self.fee is not None else None,
            "date_issued": self.date_issued.isoformat() if self.date_issued else None,
            "issued_by": self.issued_by,
            "resident_no": r.resident_no if r else None,
            "resident_last_name": r.last_name if r else None,
            "resident_first_name": r.first_name if r else None,
            "voter_status": r.voter_status if r else None,
        }


class BarangayNonResidency(db.Model):
    __tablename__ = "barangay_non_residency"
    id = db.Column(db.Integer, primary_key=True)
    resident_id = db.Column(db.Integer, db.ForeignKey("census_records.id", ondelete="CASCADE"), nullable=False)
    ctrl_no = db.Column(db.String(30), nullable=False, unique=True)
    full_name = db.Column(db.String(150), nullable=False)
    previous_address = db.Column(db.String(255))
    purpose = db.Column(db.String(150))
    or_no = db.Column(db.String(30))
    fee = db.Column(db.Numeric(10, 2), nullable=False, default=20.00)
    date_issued = db.Column(db.Date, nullable=False)
    issued_by = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=now)

    resident = db.relationship("CensusRecord")

    def to_dict(self):
        r = self.resident
        return {
            "id": self.id, "resident_id": self.resident_id, "ctrl_no": self.ctrl_no,
            "full_name": self.full_name, "previous_address": self.previous_address,
            "purpose": self.purpose, "or_no": self.or_no,
            "fee": float(self.fee) if self.fee is not None else None,
            "date_issued": self.date_issued.isoformat() if self.date_issued else None,
            "issued_by": self.issued_by,
            "resident_no": r.resident_no if r else None,
            "resident_last_name": r.last_name if r else None,
            "resident_first_name": r.first_name if r else None,
            "voter_status": r.voter_status if r else None,
        }


class IndigencyCertificate(db.Model):
    __tablename__ = "indigency_certificates"
    id = db.Column(db.Integer, primary_key=True)
    resident_id = db.Column(db.Integer, db.ForeignKey("census_records.id", ondelete="CASCADE"), nullable=False)
    ctrl_no = db.Column(db.String(30), nullable=False, unique=True)
    full_name = db.Column(db.String(150), nullable=False)
    age = db.Column(db.SmallInteger)
    civil_status = db.Column(db.String(20), nullable=False, default="Single")
    address = db.Column(db.String(255))
    purpose = db.Column(db.String(150))
    date_issued = db.Column(db.Date, nullable=False)
    issued_by = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=now)

    resident = db.relationship("CensusRecord")

    def to_dict(self):
        r = self.resident
        return {
            "id": self.id, "resident_id": self.resident_id, "ctrl_no": self.ctrl_no,
            "full_name": self.full_name, "age": self.age, "civil_status": self.civil_status,
            "address": self.address, "purpose": self.purpose,
            "date_issued": self.date_issued.isoformat() if self.date_issued else None,
            "issued_by": self.issued_by,
            "resident_no": r.resident_no if r else None,
            "resident_last_name": r.last_name if r else None,
            "resident_first_name": r.first_name if r else None,
        }


class MlRun(db.Model):
    __tablename__ = "ml_runs"
    id = db.Column(db.Integer, primary_key=True)
    trained_at = db.Column(db.DateTime, default=now)
    record_count = db.Column(db.Integer, nullable=False)
    active_occurrence_model = db.Column(db.String(40), nullable=False, default="random_forest")
    active_type_model = db.Column(db.String(40), nullable=False, default="gradient_boosting")
    active_hotspot_model = db.Column(db.String(40), nullable=False, default="random_forest")
    occurrence_metrics_json = db.Column(db.Text, nullable=False)
    type_metrics_json = db.Column(db.Text, nullable=False)
    hotspot_metrics_json = db.Column(db.Text, nullable=False)
    hotspots_json = db.Column(db.Text, nullable=False)


class SystemBackup(db.Model):
    __tablename__ = "backups"
    id = db.Column(db.Integer, primary_key=True)
    file_name = db.Column(db.String(255), nullable=False)
    size_bytes = db.Column(db.BigInteger, nullable=False, default=0)
    status = db.Column(db.String(20), nullable=False, default="Success")
    created_by = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=now)


class GeneratedReport(db.Model):
    __tablename__ = "generated_reports"
    id = db.Column(db.Integer, primary_key=True)
    report_type = db.Column(db.String(100), nullable=False)
    generated_by = db.Column(db.String(100), nullable=False)
    period_from = db.Column(db.Date)
    period_to = db.Column(db.Date)
    format = db.Column(db.String(10), nullable=False, default="PDF")
    file_path = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=now)


class Notification(db.Model):
    __tablename__ = "notifications"
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(30), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    body = db.Column(db.String(255), nullable=False)
    severity = db.Column(db.String(10), nullable=False, default="info")
    link = db.Column(db.String(100))
    ref_table = db.Column(db.String(50))
    ref_id = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=now, index=True)


class NotificationRead(db.Model):
    __tablename__ = "notification_reads"
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    notification_id = db.Column(db.Integer, db.ForeignKey("notifications.id", ondelete="CASCADE"), primary_key=True)
    read_at = db.Column(db.DateTime, default=now)
