"""
This file defines Nova validators that are used by the Nova Compute API version 2.86 or later
to validate metadata values of the gpu_weigher scope.
"""

from nova.api.validation.extra_specs import base


def register():
    """Returns a list of Nova validators.
    """
    validators = [
        base.ExtraSpecValidator(
            name='gpu_weigher:enabled',
            description='Enable GPU weighing.',
            value={
                'type': bool
            }
        ),
        base.ExtraSpecValidator(
            name='gpu_weigher:mode',
            description='Weighing mode - stack or spread instances',
            value={
                'type': str,
                'enum': [
                    'stack',
                    'spread'
                ]
            }
        ),
        base.ExtraSpecValidator(
            name='gpu_weigher:resource',
            description='Resource to use for weighing.',
            value={
                'type': str
            }
        )
    ]

    return validators
