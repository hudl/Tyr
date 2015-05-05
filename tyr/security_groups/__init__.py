from tyr.security_groups import management
from tyr.security_groups import cache

security_groups = {}

security_groups[management.rule] = management.definition
security_groups[cache.rule] = cache.definition
