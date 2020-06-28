from corc.defaults import PROVIDERS_LOWER, DEFAULT_PROVIDER_LOWER


def select_provider(provider_kwargs=None, default_fallback=False, verbose=False):
    if not provider_kwargs:
        return False

    # Find the activated one
    selected_provider = [
        provider
        for provider in PROVIDERS_LOWER
        if provider in provider_kwargs and provider_kwargs[provider]
    ]

    if not selected_provider and default_fallback:
        return DEFAULT_PROVIDER_LOWER

    if not selected_provider and not default_fallback:
        if verbose:
            print("A least a single provider must be set: {}".format(provider_kwargs))
        return False

    if len(selected_provider) > 1:
        if verbose:
            print(
                "Only a single provider must be selected, you selected: {}".format(
                    select_provider
                )
            )
            return False

    provider = selected_provider[0]
    if provider not in PROVIDERS_LOWER:
        return False

    # Return the
    return provider
