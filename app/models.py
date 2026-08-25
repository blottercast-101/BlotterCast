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

    def __init__(self, zone_id=None, label="", lat=0.0, lng=0.0, weight=1.0, **kwargs):
        super().__init__()
        if zone_id is not None:
            self.zone_id = zone_id
        self.label = label
        self.lat = lat
        self.lng = lng
        self.weight = weight
        for k, v in kwargs.items():
            setattr(self, k, v)


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    password = db.Column(db.String(255), nullable=False)  # bcrypt hash
    full_name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150))
    contact_no = db.Column(db.String(30))
    role = db.Column(db.String(30), nullable=False, default="Desk Officer")
    status = db.Column(db.String(20), nullable=False, default="Inactive")
    mfa_enabled = db.Column(db.Boolean, nullable=False, default=True)
    google_id = db.Column(db.String(100))
    auth_provider = db.Column(db.String(30), nullable=False, default="local")
    signature_path = db.Column(db.String(255))
    last_login = db.Column(db.DateTime)
    last_seen = db.Column(db.DateTime)
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
        status="Inactive",
        mfa_enabled=True,
        google_id=None,
        auth_provider="local",
        signature_path=None,
        last_login=None,
        last_seen=None,
        failed_attempts=0,
        locked_until=None,
        password_changed_at=None,
        created_at=None,
        **kwargs
    ):
        super().__init__()
        if username is not None:
            self.username = username
        if password is not None:
            self.password = password
        if full_name is not None:
            self.full_name = full_name
        if email is not None:
            self.email = email
        if contact_no is not None:
            self.contact_no = contact_no
        self.role = role
        self.status = status
        self.mfa_enabled = mfa_enabled
        if google_id is not None:
            self.google_id = google_id
        self.auth_provider = auth_provider
        if signature_path is not None:
            self.signature_path = signature_path
        if last_login is not None:
            self.last_login = last_login
        if last_seen is not None:
            self.last_seen = last_seen
        self.failed_attempts = failed_attempts
        if locked_until is not None:
            self.locked_until = locked_until
        if password_changed_at is not None:
            self.password_changed_at = password_changed_at
        if created_at is not None:
            self.created_at = created_at
        for k, v in kwargs.items():
            setattr(self, k, v)


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
        super().__init__()
        if user_id is not None:
            self.user_id = user_id
        if code_hash is not None:
            self.code_hash = code_hash
        self.purpose = purpose
        if expires_at is not None:
            self.expires_at = expires_at
        self.attempts = attempts
        if consumed_at is not None:
            self.consumed_at = consumed_at
        if created_at is not None:
            self.created_at = created_at
        for k, v in kwargs.items():
            setattr(self, k, v)


class PasswordHistory(db.Model):
    __tablename__ = "password_history"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=now, index=True)

    def __init__(
        self,
        user_id=None,
        password_hash=None,
        created_at=None,
        **kwargs
    ):
        super().__init__()
        if user_id is not None:
            self.user_id = user_id
        if password_hash is not None:
            self.password_hash = password_hash
        if created_at is not None:
            self.created_at = created_at
        for k, v in kwargs.items():
            setattr(self, k, v)


class AuditLog(db.Model):
    __tablename__ = "audit_logs"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    action = db.Column(db.String(50), nullable=False)
    module = db.Column(db.String(50), nullable=False)
    details = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=now, index=True)

    def __init__(self, username=None, action=None, module=None, details=None, created_at=None, **kwargs):
        super().__init__()
        if username is not None:
            self.username = username
        if action is not None:
            self.action = action
        if module is not None:
            self.module = module
        if details is not None:
            self.details = details
        if created_at is not None:
            self.created_at = created_at
        for k, v in kwargs.items():
            setattr(self, k, v)


class SystemSecuritySetting(db.Model):
    __tablename__ = "system_security_settings"
    id = db.Column(db.Integer, primary_key=True, default=1)
    is_2fa_globally_enabled = db.Column(db.Boolean, nullable=False, default=False)
    is_idle_timeout_enabled = db.Column(db.Boolean, nullable=False, default=False)
    idle_timeout_duration_minutes = db.Column(db.Integer, nullable=False, default=120)
    updated_at = db.Column(db.DateTime, default=now, onupdate=now)
    updated_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    updater = db.relationship("User", foreign_keys=[updated_by], lazy="joined")

    def __init__(
        self,
        id=1,
        is_2fa_globally_enabled=False,
        is_idle_timeout_enabled=False,
        idle_timeout_duration_minutes=120,
        updated_by=None,
        **kwargs,
    ):
        super().__init__()
        self.id = id
        self.is_2fa_globally_enabled = bool(is_2fa_globally_enabled)
        self.is_idle_timeout_enabled = bool(is_idle_timeout_enabled)
        self.idle_timeout_duration_minutes = int(idle_timeout_duration_minutes)
        self.updated_by = updated_by
        for k, v in kwargs.items():
            setattr(self, k, v)


class SystemSetting(db.Model):
    __tablename__ = "system_settings"
    setting_key = db.Column(db.String(100), primary_key=True)
    setting_value = db.Column(db.Text, nullable=False)
    updated_at = db.Column(db.DateTime, default=now, onupdate=now)

    def __init__(self, setting_key=None, setting_value="", updated_at=None, **kwargs):
        super().__init__()
        if setting_key is not None:
            self.setting_key = setting_key
        self.setting_value = setting_value
        if updated_at is not None:
            self.updated_at = updated_at
        for k, v in kwargs.items():
            setattr(self, k, v)


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
    is_blotter = db.Column(db.Boolean, nullable=False, default=False)
    blotter_docket_no = db.Column(db.String(50))
    is_non_resident = db.Column(db.Boolean, nullable=False, default=False)
    reporter_resident_id = db.Column(db.Integer, db.ForeignKey("census_records.id", ondelete="SET NULL"), nullable=True)
    reporter_address = db.Column(db.Text, nullable=True, default="")
    resolved_at = db.Column(db.DateTime)
    archived = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, default=now)
    updated_at = db.Column(db.DateTime, default=now, onupdate=now)

    reporter_resident = db.relationship("CensusRecord", foreign_keys=[reporter_resident_id], lazy="joined")

    def __init__(
        self,
        report_no=None,
        incident_date=None,
        time_reported=None,
        hour=0,
        zone_id="Zone 1",
        location="",
        lat=None,
        lng=None,
        category="Other",
        description="",
        reporter="",
        officer="",
        priority="Medium",
        status="Under Investigation",
        is_blotter=False,
        blotter_docket_no=None,
        is_non_resident=False,
        reporter_resident_id=None,
        reporter_address="",
        resolved_at=None,
        archived=False,
        created_at=None,
        updated_at=None,
        **kwargs
    ):
        super().__init__()
        if report_no is not None:
            self.report_no = report_no
        if incident_date is not None:
            self.incident_date = incident_date
        if time_reported is not None:
            self.time_reported = time_reported
        self.hour = hour
        self.zone_id = zone_id
        self.location = location
        if lat is not None:
            self.lat = lat
        if lng is not None:
            self.lng = lng
        self.category = category
        self.description = description
        self.reporter = reporter
        self.officer = officer
        self.priority = priority
        self.status = status
        self.is_blotter = bool(is_blotter)
        self.blotter_docket_no = blotter_docket_no
        self.is_non_resident = bool(is_non_resident)
        self.reporter_resident_id = reporter_resident_id
        self.reporter_address = reporter_address
        self.resolved_at = resolved_at
        self.archived = archived
        if created_at is not None:
            self.created_at = created_at
        if updated_at is not None:
            self.updated_at = updated_at
        for k, v in kwargs.items():
            setattr(self, k, v)

    def to_dict(self):
        return {
            "id": self.id, "report_no": self.report_no,
            "incident_date": self.incident_date.isoformat() if hasattr(self.incident_date, "isoformat") else (str(self.incident_date) if self.incident_date else None),
            "time_reported": self.time_reported.isoformat() if hasattr(self.time_reported, "isoformat") else (str(self.time_reported) if self.time_reported else None),
            "hour": self.hour, "zone_id": self.zone_id, "location": self.location,
            "lat": float(self.lat) if self.lat is not None else None,
            "lng": float(self.lng) if self.lng is not None else None,
            "category": self.category, "description": self.description,
            "reporter": self.reporter, "officer": self.officer,
            "priority": self.priority, "status": self.status,
            "is_blotter": bool(self.is_blotter),
            "blotter_docket_no": self.blotter_docket_no,
            "is_non_resident": bool(self.is_non_resident),
            "reporter_resident_id": self.reporter_resident_id,
            "reporter_address": self.reporter_address or "",
            "resolved_at": self.resolved_at.isoformat() if hasattr(self.resolved_at, "isoformat") else (str(self.resolved_at) if self.resolved_at else None),
            "archived": bool(self.archived),
        }


class BlotterRecord(db.Model):
    __tablename__ = "blotter_records"
    id = db.Column(db.Integer, primary_key=True)
    docket_no = db.Column(db.String(30), nullable=False, unique=True)
    date_filed = db.Column(db.Date, nullable=False)
    source_incident_id = db.Column(db.Integer, db.ForeignKey("incidents.id", ondelete="SET NULL"))
    incident_time = db.Column(db.Time)
    complainant = db.Column(db.String(150), nullable=False)
    complainant_id = db.Column(db.Integer, db.ForeignKey("census_records.id", ondelete="SET NULL"))
    complainant_addr = db.Column(db.String(255))
    respondent = db.Column(db.String(150), nullable=False)
    respondent_id = db.Column(db.Integer, db.ForeignKey("census_records.id", ondelete="SET NULL"))
    respondent_addr = db.Column(db.String(255))
    nature = db.Column(db.String(100))
    narrative = db.Column(db.Text)
    case_type = db.Column(db.String(10), nullable=False, default="CRIM")
    status = db.Column(db.String(20), nullable=False, default="Pending")
    zone_id = db.Column(db.String(10), db.ForeignKey("zones.zone_id"))
    resolved_at = db.Column(db.DateTime)
    archived = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, default=now)
    updated_at = db.Column(db.DateTime, default=now, onupdate=now)

    def __init__(
        self,
        docket_no=None,
        date_filed=None,
        source_incident_id=None,
        incident_time=None,
        complainant="",
        complainant_id=None,
        complainant_addr="",
        respondent="",
        respondent_id=None,
        respondent_addr="",
        nature="",
        narrative="",
        case_type="CRIM",
        status="Pending",
        zone_id=None,
        resolved_at=None,
        archived=False,
        created_at=None,
        updated_at=None,
        **kwargs
    ):
        super().__init__()
        if docket_no is not None:
            self.docket_no = docket_no
        if date_filed is not None:
            self.date_filed = date_filed
        self.source_incident_id = source_incident_id
        if incident_time is not None:
            self.incident_time = incident_time
        self.complainant = complainant
        if complainant_id is not None:
            self.complainant_id = complainant_id
        self.complainant_addr = complainant_addr
        self.respondent = respondent
        if respondent_id is not None:
            self.respondent_id = respondent_id
        self.respondent_addr = respondent_addr
        self.nature = nature
        self.narrative = narrative
        self.case_type = case_type
        self.status = status
        if zone_id is not None:
            self.zone_id = zone_id
        self.resolved_at = resolved_at
        self.archived = archived
        if created_at is not None:
            self.created_at = created_at
        if updated_at is not None:
            self.updated_at = updated_at
        for k, v in kwargs.items():
            setattr(self, k, v)

    def to_dict(self):
        return {
            "id": self.id, "docket_no": self.docket_no,
            "date_filed": self.date_filed.isoformat() if hasattr(self.date_filed, "isoformat") else (str(self.date_filed) if self.date_filed else None),
            "source_incident_id": self.source_incident_id,
            "incident_time": self.incident_time.isoformat() if hasattr(self.incident_time, "isoformat") else (str(self.incident_time) if self.incident_time else None),
            "complainant": self.complainant, "complainant_id": self.complainant_id,
            "complainant_addr": self.complainant_addr,
            "respondent": self.respondent, "respondent_id": self.respondent_id,
            "respondent_addr": self.respondent_addr,
            "nature": self.nature, "narrative": self.narrative,
            "case_type": self.case_type, "status": self.status, "zone_id": self.zone_id,
            "resolved_at": self.resolved_at.isoformat() if hasattr(self.resolved_at, "isoformat") else (str(self.resolved_at) if self.resolved_at else None),
            "archived": bool(self.archived),
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
    archived = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, default=now)
    updated_at = db.Column(db.DateTime, default=now, onupdate=now)

    blotter = db.relationship("BlotterRecord")

    def __init__(
        self,
        blotter_id=None,
        case_no=None,
        case_title="",
        complaint_title="",
        nature="Civil",
        date_filed=None,
        date_confrontation=None,
        action_taken="",
        date_settlement=None,
        date_execution=None,
        main_point="",
        status="Pending",
        remarks="",
        archived=False,
        created_at=None,
        updated_at=None,
        **kwargs
    ):
        super().__init__()
        if blotter_id is not None:
            self.blotter_id = blotter_id
        if case_no is not None:
            self.case_no = case_no
        self.case_title = case_title
        self.complaint_title = complaint_title
        self.nature = nature
        if date_filed is not None:
            self.date_filed = date_filed
        if date_confrontation is not None:
            self.date_confrontation = date_confrontation
        self.action_taken = action_taken
        if date_settlement is not None:
            self.date_settlement = date_settlement
        if date_execution is not None:
            self.date_execution = date_execution
        self.main_point = main_point
        self.status = status
        self.remarks = remarks
        self.archived = archived
        if created_at is not None:
            self.created_at = created_at
        if updated_at is not None:
            self.updated_at = updated_at
        for k, v in kwargs.items():
            setattr(self, k, v)

    def to_dict(self):
        b = self.blotter
        return {
            "id": self.id, "blotter_id": self.blotter_id, "case_no": self.case_no,
            "case_title": self.case_title, "complaint_title": self.complaint_title,
            "nature": self.nature,
            "date_filed": self.date_filed.isoformat() if hasattr(self.date_filed, "isoformat") else (str(self.date_filed) if self.date_filed else None),
            "date_confrontation": self.date_confrontation.isoformat() if hasattr(self.date_confrontation, "isoformat") else (str(self.date_confrontation) if self.date_confrontation else None),
            "action_taken": self.action_taken,
            "date_settlement": self.date_settlement.isoformat() if hasattr(self.date_settlement, "isoformat") else (str(self.date_settlement) if self.date_settlement else None),
            "date_execution": self.date_execution.isoformat() if hasattr(self.date_execution, "isoformat") else (str(self.date_execution) if self.date_execution else None),
            "main_point": self.main_point, "status": self.status, "remarks": self.remarks,
            "blotter_docket_no": b.docket_no if b else None,
            "complainant": b.complainant if b else None,
            "complainant_addr": b.complainant_addr if b else None,
            "respondent": b.respondent if b else None,
            "respondent_addr": b.respondent_addr if b else None,
            "blotter_case_type": b.case_type if b else None,
            "archived": bool(self.archived),
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
    archived = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, default=now)
    updated_at = db.Column(db.DateTime, default=now, onupdate=now)

    def __init__(
        self,
        resident_no=None,
        last_name="",
        first_name="",
        middle_name="",
        date_of_birth=None,
        sex="Male",
        civil_status="Single",
        nationality="Filipino",
        zone_id=None,
        address="",
        household_no="",
        contact_no="",
        voter_status="Not Registered",
        occupation="",
        status="Active",
        archived=False,
        created_at=None,
        updated_at=None,
        **kwargs
    ):
        super().__init__()
        if resident_no is not None:
            self.resident_no = resident_no
        self.last_name = last_name
        self.first_name = first_name
        self.middle_name = middle_name
        if date_of_birth is not None:
            self.date_of_birth = date_of_birth
        self.sex = sex
        self.civil_status = civil_status
        self.nationality = nationality
        if zone_id is not None:
            self.zone_id = zone_id
        self.address = address
        self.household_no = household_no
        self.contact_no = contact_no
        self.voter_status = voter_status
        self.occupation = occupation
        self.status = status
        self.archived = archived
        if created_at is not None:
            self.created_at = created_at
        if updated_at is not None:
            self.updated_at = updated_at
        for k, v in kwargs.items():
            setattr(self, k, v)

    def to_dict(self):
        return {
            "id": self.id, "resident_no": self.resident_no,
            "last_name": self.last_name, "first_name": self.first_name,
            "middle_name": self.middle_name,
            "date_of_birth": self.date_of_birth.isoformat() if hasattr(self.date_of_birth, "isoformat") else (str(self.date_of_birth) if self.date_of_birth else None),
            "sex": self.sex, "civil_status": self.civil_status, "nationality": self.nationality,
            "zone_id": self.zone_id, "address": self.address, "household_no": self.household_no,
            "contact_no": self.contact_no, "voter_status": self.voter_status,
            "occupation": self.occupation, "status": self.status,
            "archived": bool(self.archived),
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

    def __init__(
        self,
        resident_id=None,
        ctrl_no=None,
        full_name="",
        age=None,
        civil_status="Single",
        address="",
        voter_status="Not Registered",
        purpose="",
        or_no="",
        fee=20.00,
        date_issued=None,
        issued_by="",
        created_at=None,
        **kwargs
    ):
        super().__init__()
        if resident_id is not None:
            self.resident_id = resident_id
        if ctrl_no is not None:
            self.ctrl_no = ctrl_no
        self.full_name = full_name
        if age is not None:
            self.age = age
        self.civil_status = civil_status
        self.address = address
        self.voter_status = voter_status
        self.purpose = purpose
        self.or_no = or_no
        self.fee = fee
        if date_issued is not None:
            self.date_issued = date_issued
        self.issued_by = issued_by
        if created_at is not None:
            self.created_at = created_at
        for k, v in kwargs.items():
            setattr(self, k, v)

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

    def __init__(
        self,
        resident_id=None,
        ctrl_no=None,
        full_name="",
        age=None,
        civil_status="Single",
        address="",
        years_residency=None,
        duration_unit="years",
        purpose="",
        or_no="",
        fee=20.00,
        date_issued=None,
        issued_by="",
        created_at=None,
        **kwargs
    ):
        super().__init__()
        if resident_id is not None:
            self.resident_id = resident_id
        if ctrl_no is not None:
            self.ctrl_no = ctrl_no
        self.full_name = full_name
        if age is not None:
            self.age = age
        self.civil_status = civil_status
        self.address = address
        if years_residency is not None:
            self.years_residency = years_residency
        self.duration_unit = duration_unit
        self.purpose = purpose
        self.or_no = or_no
        self.fee = fee
        if date_issued is not None:
            self.date_issued = date_issued
        self.issued_by = issued_by
        if created_at is not None:
            self.created_at = created_at
        for k, v in kwargs.items():
            setattr(self, k, v)

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

    def __init__(
        self,
        resident_id=None,
        ctrl_no=None,
        full_name="",
        previous_address="",
        purpose="",
        or_no="",
        fee=20.00,
        date_issued=None,
        issued_by="",
        created_at=None,
        **kwargs
    ):
        super().__init__()
        if resident_id is not None:
            self.resident_id = resident_id
        if ctrl_no is not None:
            self.ctrl_no = ctrl_no
        self.full_name = full_name
        self.previous_address = previous_address
        self.purpose = purpose
        self.or_no = or_no
        self.fee = fee
        if date_issued is not None:
            self.date_issued = date_issued
        self.issued_by = issued_by
        if created_at is not None:
            self.created_at = created_at
        for k, v in kwargs.items():
            setattr(self, k, v)

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

    def __init__(
        self,
        resident_id=None,
        ctrl_no=None,
        full_name="",
        age=None,
        civil_status="Single",
        address="",
        purpose="",
        date_issued=None,
        issued_by="",
        created_at=None,
        **kwargs
    ):
        super().__init__()
        if resident_id is not None:
            self.resident_id = resident_id
        if ctrl_no is not None:
            self.ctrl_no = ctrl_no
        self.full_name = full_name
        if age is not None:
            self.age = age
        self.civil_status = civil_status
        self.address = address
        self.purpose = purpose
        if date_issued is not None:
            self.date_issued = date_issued
        self.issued_by = issued_by
        if created_at is not None:
            self.created_at = created_at
        for k, v in kwargs.items():
            setattr(self, k, v)

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

    def __init__(
        self,
        record_count=0,
        active_occurrence_model="random_forest",
        active_type_model="gradient_boosting",
        active_hotspot_model="random_forest",
        occurrence_metrics_json="{}",
        type_metrics_json="{}",
        hotspot_metrics_json="{}",
        hotspots_json="[]",
        trained_at=None,
        **kwargs
    ):
        super().__init__()
        self.record_count = record_count
        self.active_occurrence_model = active_occurrence_model
        self.active_type_model = active_type_model
        self.active_hotspot_model = active_hotspot_model
        self.occurrence_metrics_json = occurrence_metrics_json
        self.type_metrics_json = type_metrics_json
        self.hotspot_metrics_json = hotspot_metrics_json
        self.hotspots_json = hotspots_json
        if trained_at is not None:
            self.trained_at = trained_at
        for k, v in kwargs.items():
            setattr(self, k, v)


class SystemBackup(db.Model):
    __tablename__ = "backups"
    id = db.Column(db.Integer, primary_key=True)
    file_name = db.Column(db.String(255), nullable=False)
    size_bytes = db.Column(db.BigInteger, nullable=False, default=0)
    status = db.Column(db.String(20), nullable=False, default="Success")
    created_by = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=now)

    def __init__(self, file_name="", size_bytes=0, status="Success", created_by="", created_at=None, **kwargs):
        super().__init__()
        self.file_name = file_name
        self.size_bytes = size_bytes
        self.status = status
        self.created_by = created_by
        if created_at is not None:
            self.created_at = created_at
        for k, v in kwargs.items():
            setattr(self, k, v)


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

    def __init__(
        self,
        report_type="",
        generated_by="",
        period_from=None,
        period_to=None,
        format="PDF",
        file_path="",
        created_at=None,
        **kwargs
    ):
        super().__init__()
        self.report_type = report_type
        self.generated_by = generated_by
        if period_from is not None:
            self.period_from = period_from
        if period_to is not None:
            self.period_to = period_to
        self.format = format
        self.file_path = file_path
        if created_at is not None:
            self.created_at = created_at
        for k, v in kwargs.items():
            setattr(self, k, v)


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

    def __init__(
        self,
        type="info",
        title="",
        body="",
        severity="info",
        link=None,
        ref_table=None,
        ref_id=None,
        created_at=None,
        **kwargs
    ):
        super().__init__()
        self.type = type
        self.title = title
        self.body = body
        self.severity = severity
        if link is not None:
            self.link = link
        if ref_table is not None:
            self.ref_table = ref_table
        if ref_id is not None:
            self.ref_id = ref_id
        if created_at is not None:
            self.created_at = created_at
        for k, v in kwargs.items():
            setattr(self, k, v)


class NotificationRead(db.Model):
    __tablename__ = "notification_reads"
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    notification_id = db.Column(db.Integer, db.ForeignKey("notifications.id", ondelete="CASCADE"), primary_key=True)
    read_at = db.Column(db.DateTime, default=now)

    def __init__(self, user_id=None, notification_id=None, read_at=None, **kwargs):
        super().__init__()
        if user_id is not None:
            self.user_id = user_id
        if notification_id is not None:
            self.notification_id = notification_id
        if read_at is not None:
            self.read_at = read_at
        for k, v in kwargs.items():
            setattr(self, k, v)

