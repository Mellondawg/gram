# Registry of all slices managed by VMOC
#
# Manages list of all slices and associated controller (by URL)
# register_slice(slice_config, url)
# unregister_slice(slice_id)
# lookup_slices(url) => slice_configs
# lookup_slice_config(slice_id) => slice_config

from VMOCConfig import VMOCSliceConfiguration, VMOCVlanConfiguration
import pdb

class VMOCSliceRegistry:

    def __init__(self):
        self._slices_by_url = dict()
        self._slice_by_slice_id = dict()

    # Is given slice config registered?
    def is_registered(self, slice_config):
        url = slice_config.getControllerURL()
        slice_id = slice_config.getSliceID()
        return self._slice_by_slice_id.has_key(slice_id) and \
            self._slice_by_slice_id[slice_id].getControllerURL() == url

    # Register slice configuration by id and URL
    def register_slice(self, slice_config):
        url = slice_config.getControllerURL()
        slice_id = slice_config.getSliceID()
        assert not self._slice_by_slice_id.has_key(slice_id) or \
            self._slice_by_slice_id[slice_id].getControllerURL() == url
        if not self._slices_by_url.has_key(url):
            self._slices_by_url[url] = []
        self._slices_by_url[url].append(slice_config)
        self._slice_by_slice_id[slice_id] = slice_config

    # Remove information about slice associated with given slice ID
    def unregister_slice(self, slice_id):
        assert self._slice_by_slice_id.has_key(slice_id)
        slice_config = self._slice_by_slice_id[slice_id]
        url = slice_config.getControllerURL()
        del self._slice_by_slice_id[slice_id]
        assert self._slices_by_url.has_key(url)
        self._slices_by_url[url].remove(slice_config)

    # Lookup slice associated with controller url
    def lookup_slices(self, controller_url):
        assert self._slices_by_url.has_key(controller_url)
        return self._slices_by_url[controller_url]

    # Lookup slice config
    def lookup_slice_config(self, slice_id):
        assert self._slice_by_slice_id.has_key(slice_id)
        return self._slice_by_slice_id[slice_id]

    # Dump contents of registry
    def dump(self, print_results=False):
        image = ""
        for slice_id in self._slice_by_slice_id.keys():
            image += slice_id + " " + str(self._slice_by_slice_id[slice_id]) + "\n"
        for controller_url in self._slices_by_url.keys():
            image += controller_url + " " + str(self._slices_by_url[controller_url]) + "\n"
        if print_results:
            print image
        return image

# Static interface

__registry = VMOCSliceRegistry(); # Singleton class instance

# Register slice configuration with slice registry
def slice_registry_register_slice(slice_config):
    __registry.register_slice(slice_config)

# Remove slice configuration with slice registry
def slice_registry_unregister_slice(slice_id):
    __registry.unregister_slice(slice_id)

# Lookup slice_configs associated with given URL
def slice_registry_lookup_slices(controller_url):
    return __registry.lookup_slices(controller_url)

# Lookup slice_config associated with given slice_id
def slice_registry_lookup_slice_config(slice_id):
    return __registry.lookup_slice_config(slice_id)

# Is given slice configuraiton already registered (by name and url)?
def slice_registry_is_registered(slice_config):
    return __registry.is_registered(slice_config)

# Dump contents of slice registry
def slice_registry_dump(print_results=False):
    return __registry.dump(print_results)


if __name__ == "__main__":
    slice_id1 = 'S1'
    slice_id2 = 'S2'
    controller1 = 'http://localhost:9001'
    controller2 = 'http://localhost:9002'
    vlans_full = [VMOCVlanConfiguration(100, []), VMOCVlanConfiguration(101, [])]
    vlans_empty = []
    slice1 = VMOCSliceConfiguration(slice_id1, controller1, vlans_full)
    slice2 = VMOCSliceConfiguration(slice_id2, controller2, vlans_empty)
    slice_registry_register_slice(slice1)
    slice_registry_register_slice(slice2)
    slice_registry_dump(True)
    print "LOOKUP S1 " + str(slice_registry_lookup_slice_config(slice_id1))
    print "LOOKUP S2 " + str(slice_registry_lookup_slice_config(slice_id2))
    print "LOOKUP C1 " + str(slice_registry_lookup_slices(controller1))
    print "LOOKUP C2 " + str(slice_registry_lookup_slices(controller2))
    slice_registry_unregister_slice(slice_id2)
    slice2a = VMOCSliceConfiguration(slice_id2, controller1, vlans_empty)
    slice_registry_register_slice(slice2a)
    slice_registry_dump(True)


    
    
    
    




    