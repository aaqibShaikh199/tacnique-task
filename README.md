# Haven — Platform Infrastructure Assessment

Haven is a multi-tenant real estate platform.

## Domain model

```
LandlordAccount  (the billing unit)
  └── Property
        └── Tenant
              └── ScreeningReport  (SSN, credit score)

PropertyManager  (scoped to exactly one LandlordAccount)
```

A `LandlordAccount` is the billing unit — every property, every tenant, every report underneath
it rolls up to exactly one. A `PropertyManager` is scoped to exactly one `LandlordAccount` and
everything under it.

This codebase currently tags and checks access using whatever ID happened to be on hand when
each piece was written — that reflects how it was built, not a spec to replicate.

## What not to modify

`app/seed_data.py`, `app/models.py`, `fixtures/plan.json`, `terraform/terraform.tfstate` — the
assignment's checks assume this data is unchanged.

`terraform/terraform.tfstate` is checked in deliberately, not an accident — it's a seeded state
representing 4 already-provisioned landlord media buckets, standing in for a real AWS account so
B0 can be reproduced with `terraform plan` instead of just reasoned about. See `terraform/main.tf`
for how to use it.

## Where things are

| Path | Task |
|---|---|
| `terraform/main.tf` | B0 |
| `terraform/lifecycle.tf` | B1 |
| `app/access_control.py`, `scripts/cost_tag_check.py` | B2 — stubs to implement |

## Recording

Unedited screen recording, from opening this repo through the end of the work:

| Recording | URL |
|---|---|
| VIDEO-01 | https://tacnique-task.s3.us-east-1.amazonaws.com/01.mov |
| VIDEO-02 | https://tacnique-task.s3.us-east-1.amazonaws.com/02.mov |
| VIDEO-03 | https://tacnique-task.s3.us-east-1.amazonaws.com/03.mov |
| VIDEO-04 | https://tacnique-task.s3.us-east-1.amazonaws.com/04.mov |
