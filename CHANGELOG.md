# CHANGELOG

<https://keepachangelog.com/en/1.0.0/>

## [2.2.0]

- Allow for specifying the Chef client version in the Tyr request
  - Fixes a bug where a new Ruby gem (`aws-eventstream`) only supports Ruby >= 2.3. Chef Client used this for provisioning, so this broke Tyr provisioning. The Chef version now defaults to 12.14 (where this was fixed) but is configurable via API request.
