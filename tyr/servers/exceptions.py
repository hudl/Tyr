class RegionDoesNotExist(Exception):
    pass


class InvalidRole(Exception):
    pass


class InvalidCluster(Exception):
    pass


class InvalidKeyPair(Exception):
    pass


class InvalidAMI(Exception):
    pass


class InvalidAvailabilityZone(Exception):
    pass


class NoSubnetReturned(Exception):
    pass


class NoVPCReturned(Exception):
    pass


class NoSecurityGroupsReturned(Exception):
    pass


class MultipleSecurityGroupsReturned(Exception):
    pass
