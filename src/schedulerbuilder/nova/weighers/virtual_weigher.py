"""
GPU Virtual Weigher class.

This weigher will weigh based on an metadata value defined in the flavor metadata.

Specifically we can either stack or spread specific flavors on hosts.

To enable this weigher the gpu_weigher:enabled key must be set to 'true' in the flavor metadata.
Additionally gpu_weigher:mode must either be 'stack' or 'spread' and gpu_weigher:resource set to the key
that is used to search for instances to be used during the weighing process.

It is important to note that this weigher should only be used with a custom resource defined in the
Placement API to not overallocate hosts due to the way nova scheduler allocates resources.
"""

import nova.conf
from nova.objects.request_spec import RequestSpec
from nova.objects.instance import Instance
from nova.scheduler.host_manager import HostState
from nova.scheduler import utils
from nova.scheduler import weights
from oslo_log import log as logging
from schedulerbuilder.nova import extraSpecIsTrue, getExtraSpecsValue

CONF = nova.conf.CONF
LOG = logging.getLogger(__name__)

_SCOPE = 'gpu_weigher'


class GpuVirtualWeigher(weights.BaseHostWeigher):
    def weight_multiplier(self, host_state: HostState):
        """Override the weight multiplier."""
        return utils.get_weight_multiplier(
            host_state, 'gpu_virtual_weight_multiplier',
            1.0)

    def _weigh_object(self, host_state: HostState, request_spec: RequestSpec):
        """Weighs a request_spec and returns a positive or negative weight based on the
        stacking or spreading behavior.
        """
        if not extraSpecIsTrue(request_spec.flavor, 'enabled', _SCOPE):
            # If GPU filtering is disabled do not change weighing
            return 0

        mode = getExtraSpecsValue(request_spec.flavor, 'mode', _SCOPE)

        if not mode:
            LOG.warning("Flavor does not have gpu_weigher:mode set - Disable weighing.")
            return 0

        resource = getExtraSpecsValue(request_spec.flavor, 'resource', _SCOPE)

        if not resource:
            LOG.warning(
                "Flavor does not have gpu_weigher:resource set - Disable weighing.")
            return 0

        count = 0

        Instance: Instance
        for (_, instance) in host_state.instances.items():
            instanceResource = getExtraSpecsValue(instance.flavor, resource, '')

            if instanceResource:
                count += int(instanceResource)

        if mode == "stack":
            return count
        elif mode == "spread":
            return - count

        LOG.warning("Unknown gpu_weigher:mode set - Disable weighing.")
        return 0
