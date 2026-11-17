# B2 — assistant session

Record of the B2 work in this session. The written answers for B0 and B1 were done in the
same pass; this file is the B2 trail the submission asks for, including the first reading
that the README rules out.

## Prompt

> I ve attached the job assignment PDF Sr-Cloud-Engineer-Technical-Assessment.pdf please review the requirments and help me to complete

The PDF points at https://github.com/ajackus/haven-infra-assessment and says to read that
README before writing B2. B2 is the access check and the cost-tag check. Seed data, models,
`fixtures/plan.json`, and `terraform/terraform.tfstate` stay unchanged.

## First reading, and why it is wrong

`fixtures/plan.json` tags `aws_s3_bucket.listing_media` with `tenant_id` and tags
`screening_report_export` with both `tenant_id` and `landlord_account_id`. A first pass that
treats the fixture as the spec writes the cost check like this:

```python
def _tagged(tags):
    # listing_media carries tenant_id, so require that
    value = (tags or {}).get("tenant_id")
    return isinstance(value, str) and value != ""
```

and writes the access check by comparing whatever id is closest on the two objects:

```python
def can_access_screening_report(actor, report, *, properties, tenants):
    tenant = next((t for t in tenants if t.id == report.tenant_id), None)
    return tenant is not None and actor.id == tenant.id
```

That fails the assignment in two directions at once.

- `listing_media` would pass the cost check. It is the resource the fixture is there to
  flag. `mls_feed_sync` has an empty tag map, so it would still fail, and a test that only
  looked at that one function would look green while the billing unit was wrong.
- `pm-001` would be denied `rep-001`. The manager's id is `pm-001` and the tenant's id is
  `ten-001`. They are not the same kind of id. The same-account case, which must be allowed,
  would fail. Cross-account would also be denied, so a test that only checked the denial
  would pass for the wrong reason.

`scripts/cost_tag_check.py` already names `landlord_account_id` in the docstring. The README
is what says why, and it says it before the docstring should be trusted on its own: a
`LandlordAccount` is the billing unit, a `PropertyManager` is scoped to exactly one of those,
and the ids currently sitting on tags and checks are how the code was built, not the rule to
copy. `tenant_id` on `listing_media` is the bug the check exists to catch.

## What was implemented instead

Access walks report → tenant → property and returns true only when
`actor.landlord_account_id == property.landlord_account_id`. A missing tenant or a missing
property returns false. The manager is allowed every report under their landlord account, not
one tenant.

The cost check looks at every `resource_changes` entry whose actions include `create` or
`update`, including a replacement (`["delete", "create"]`). It fails when
`change.after.tags.landlord_account_id` is absent or blank. `no-op`, `read`, and `delete`
are skipped, so the delete entry with `"after": null` does not get inspected and does not
raise. Nothing in the check names `listing_media` or `mls_feed_sync`.

A second wrong idea for the idempotency note was to hash the plan file and remember the last
exit code. That is a cache, and it is not what the design-notes prompt asks. The question is
which key makes two resources in the same run the same resource. That key is
`resource_changes[].address`. The call builds a set of failing addresses, prints them
sorted, and drops the set when it returns. The next call has nothing left from the first one.
Running `fixtures/plan.json` twice prints the same two lines and exits 1 both times, because
the plan still has missing tags. Same result is the requirement. A second run that flipped
to exit 0 would mean the script had stored the failure and then swallowed it.

## Tests that lock the correction in

- `pm-001` is denied `rep-002` and allowed `rep-001`, using the fixtures from `conftest.py`.
- A report whose tenant does not exist, and a report whose property was removed from the
  list, are both denied.
- `fixtures/plan.json` exits 1 and prints only `aws_lambda_function.mls_feed_sync` and
  `aws_s3_bucket.listing_media`. The tagged resources, the no-op, and the delete do not
  appear.
- The same call a second time returns the same exit code and the same text, with each
  address once.
- A `tmp_path` plan containing an SQS queue tagged only with `tenant_id` fails, and a
  DynamoDB table tagged with `landlord_account_id` does not. The check is not a list of the
  two fixture addresses.
- Two changes that share one address produce one line.
