import nova.conf
from nova.objects.request_spec import RequestSpec
from nova.objects.flavor import Flavor
from nova.objects.instance import Instance
from nova.scheduler.host_manager import HostState
from nova.scheduler.filters import utils as filterUtils
from nova.scheduler import utils
from nova.scheduler import weights
from oslo_log import log as logging
from schedulerbuilder.nova import extraSpecIsTrue, getExtraSpecsValue

CONF = nova.conf.CONF
LOG = logging.getLogger(__name__)

_SCOPE = 'gpu_weigher'

# This weigher requires scheduling GPU resources using the Placement API.
# Otherwise this may cause unexpected behavior during scheduling.

class GpuVirtualWeigher(weights.BaseHostWeigher):
    def weight_multiplier(self, host_state: HostState):
        """Override the weight multiplier."""
        return utils.get_weight_multiplier(
            host_state, 'gpu_virtual_weight_multiplier',
            1.0)

    def _weigh_object(self, host_state: HostState, request_spec: RequestSpec):
        if not extraSpecIsTrue(request_spec.flavor, 'enabled', _SCOPE):
            # If GPU filtering is disabled do not change weighing
            return 0

        mode = getExtraSpecsValue(request_spec.flavor, 'mode', _SCOPE)

        if not mode:
            LOG.warning("Flavor does not have gpu_weigher:mode set - Disable weighing.")
            return 0

        resource = getExtraSpecsValue(request_spec.flavor, 'resource', _SCOPE)

        if not resource:
            LOG.warning("Flavor does not have gpu_weigher:resource set - Disable weighing.")
            return 0

        count = 0

        Instance: Instance
        for (_, instance) in host_state.instances.items():
            instanceResource = getExtraSpecsValue(instance.flavor, resource, '')

            if instanceResource:
                count += int(instanceResource)

        if mode == "pull":
            return count
        elif mode == "push":
            return - count
        
        LOG.warning("Unknown gpu_weigher:mode set - Disable weighing.")
        return 0
