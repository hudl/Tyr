from tyr.security_groups import management
from tyr.security_groups import chef_nodes
from tyr.security_groups import cache

security_groups = {}

security_groups[management.rule] = management.definition
security_groups[chef_nodes.rule] = chef_nodes.definition
security_groups[cache.rule] = cache.definition
