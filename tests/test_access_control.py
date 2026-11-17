"""
Write tests here proving:
  1. A PropertyManager scoped to la-001 (pm-001) is DENIED access to la-002's tenant's
     screening report (rep-002).
  2. The same PropertyManager (pm-001) IS allowed access to their own account's screening
     report (rep-001).

Use the `property_managers`, `properties`, `tenants`, and `screening_reports` fixtures from
conftest.py — don't re-invent the seed data here.
"""
from app.access_control import can_access_screening_report
from app.models import ScreeningReport


def _by_id(records, record_id):
    return next(record for record in records if record.id == record_id)


def test_cross_account_screening_report_is_denied(
    property_managers, properties, tenants, screening_reports
):
    manager = _by_id(property_managers, "pm-001")
    other_account_report = _by_id(screening_reports, "rep-002")

    assert (
        can_access_screening_report(
            manager,
            other_account_report,
            properties=properties,
            tenants=tenants,
        )
        is False
    )


def test_same_account_screening_report_is_allowed(
    property_managers, properties, tenants, screening_reports
):
    manager = _by_id(property_managers, "pm-001")
    own_report = _by_id(screening_reports, "rep-001")

    assert (
        can_access_screening_report(
            manager,
            own_report,
            properties=properties,
            tenants=tenants,
        )
        is True
    )


def test_missing_tenant_or_property_fails_closed(
    property_managers, properties, tenants, screening_reports
):
    manager = _by_id(property_managers, "pm-001")
    own_report = _by_id(screening_reports, "rep-001")
    unknown_tenant = ScreeningReport(
        id="rep-missing",
        tenant_id="ten-does-not-exist",
        ssn_last4="0000",
        credit_score=0,
    )
    orphan_tenant = next(tenant for tenant in tenants if tenant.property_id == "prop-001")
    properties_without_match = [
        prop for prop in properties if prop.id != orphan_tenant.property_id
    ]

    assert (
        can_access_screening_report(
            manager,
            unknown_tenant,
            properties=properties,
            tenants=tenants,
        )
        is False
    )
    assert (
        can_access_screening_report(
            manager,
            own_report,
            properties=properties_without_match,
            tenants=tenants,
        )
        is False
    )
