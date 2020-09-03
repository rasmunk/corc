from corc.providers.oci.instance import OCIInstanceOrchestrator


def start_instance(provider_kwargs, instance={}, vcn={}):
    response = {}
    if provider_kwargs:

        internetgateway = vcn.pop("internetgateway", {})
        routetable = vcn.pop("routetable", {})
        subnet = vcn.pop("subnet", {})

        instance_options = dict(
            profile=provider_kwargs["profile"],
            instance=instance,
            vcn=vcn,
            internetgateway=internetgateway,
            routetable=routetable,
            subnet=subnet
        )
        OCIInstanceOrchestrator.validate_options(instance_options)
        orchestrator = OCIInstanceOrchestrator(instance_options)

        orchestrator.setup()
        orchestrator.poll()
        if not orchestrator.is_ready():
            response["msg"] = "The instance is not ready"
            return False, response

        if not orchestrator.is_reachable():
            response["msg"] = "The instance is ready but not reachable"
            return False, response

        return True, response
    return False, response
