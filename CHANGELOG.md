# CHANGELOG

<https://keepachangelog.com/en/1.0.0/>

## [2.4.0]
- Update the Chef Installation script location to point at a file we store in S3
    - Full details about why in [this PR](https://github.com/hudl/hudl-chef-omnitruck-installer/pull/2)

## [2.3.0]

- Update the bundler version embedded in chef to `1.17.3`.
    - In a recent Prod Incident we found some problems with some Ruby gems
      dependencies that are used in the MongoDB provision process and in other
      places as well. You can read more about the prod incident in
      https://sync.hudlnet.com/x/BiT6FQ
    - Vandelay investigated how to fix this for our role_mongo Cookbook in
      https://docs.google.com/document/d/11EJwHkUYwzol3HaqnAD8O1YX5lRYI1MTa8AblFPBVs8/edit?usp=sharing
    - The TLDR is we need to update the version of bundler before running chef.
    - To centralise the change in a single place, we are updating Tyr to place
      tge upgrade command in the user data of the instances provisioned by Tyr
      (MongoDB and RabbitMQ are provisioned by Tyr for example).
    - With this change here, Aspen will work as well as Aspen uses Tyr under the
      hood to provision the instances.

## [2.2.0]

- Allow for specifying the Chef client version in the Tyr request
  - Fixes a bug where a new Ruby gem (`aws-eventstream`) only supports Ruby >= 2.3. Chef Client used this for provisioning, so this broke Tyr provisioning. The Chef version now defaults to 12.14 (where this was fixed) but is configurable via API request.
