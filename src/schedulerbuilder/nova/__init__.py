from nova.objects.flavor import Flavor
from typing import Any, Optional
from nova.scheduler.host_manager import HostState
from nova.scheduler.filters import utils as filterUtils
from oslo_log import log as logging
from oslo_utils import strutils

LOG = logging.getLogger(__name__)

def getExtraSpecsValue(flavor: Flavor, key: str, scope: str) -> Optional[str]:
    if scope:
        key = scope + ':' + key

    if 'extra_specs' in flavor and key in flavor.extra_specs:
        return flavor.extra_specs[key]

    return None

def extraSpecIsTrue(flavor: Flavor, key: str, scope: str) -> bool:
    return strutils.bool_from_string(getExtraSpecsValue(flavor, key, scope))

def getAggregateMetadataUnique(host_state: HostState, key: str, scope: str, default: Any = None):
    metadata = filterUtils.aggregate_metadata_get_by_host(host_state)

    # returns a set meaning that all values are unique.
    # although the host could be a member of multiple host aggregates,
    # the gpu_count property should only be defined once or be identical.
    # Otherwise the host would have a different number of gpus based on the host aggregate
    # it was scheduled in. This is not desired.
    search = scope + ':' + key
    aggregate_vals = metadata.get(search, None)

    if not aggregate_vals:
        return default
    elif len(aggregate_vals) > 1:
        LOG.warning("{} value is not unique. The host may be a member of multiple host aggregates with different {} values.".format(search, search))
        return None

    return aggregate_vals.pop()
