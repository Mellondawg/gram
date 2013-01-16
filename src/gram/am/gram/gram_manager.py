
import os
import signal
import time

import config
from resources import Slice
import rspec_handler
import open_stack_interface
import utils
import Archiving
import threading

class SliceURNtoSliceObject :
    """
        Class maps slice URNs to slice objects
    """
    _slices = {}   # Slice objects at this aggregate, indexed by slice urn
    _lock = threading.RLock()

    def get_slice_object(slice_urn) :
        with _lock :
            if slice_urn in _slices :
                return _slices[slice_urn]
            else :
                return None
            
    def set_slice_object(slice_urn, slice_object) :
        with _lock :
            _slices[slice_urn] = slice_object


class GramManager :
    """
        Only one instances of this class is created.
    """
    _slices = {}   

    def __init__(self) :
        # open_stack_interface.init() # OpenStack related initialization

        # Set up a signal handler to clean up on a control-c
        # signal.signal(signal.SIGINT, open_stack_interface.cleanup)

        # Recover state from snapshot, if configured to do so
        self.restore_state()
        
        # Remove extraneous snapshots
        self.prune_snapshots()



    def allocate(self, slice_urn, creds, rspec, options) :
        """
            Request reservation of GRAM resources.  We assume that by the 
            time we get here the caller's credentials have been verified 
            by the gcf framework (see am3.py).

            Returns None if successful.
            Returns an error string on failure.
        """
        config.logger.info('Allocate called for slice %r' % slice_urn)

        # Check if we already have slivers for this slice
        slice_object = SliceURNtoSliceObject.get_slice_object(slice_run)
        if slice_object != None :
            # This is a request to add additional resources to this slice.
            # Feature not supported at this time.
            config.logger.error('Cannot call allocate while holding slivers');
            error_output = 'Slice already has slivers at this aggregate.  Delete the slice before calling allocate again'

            # Create and return an error struct
            code = {'geni_code': config.SLICE_ALREADY_EXISTS}
            return {'code': code, 'value': '', 'output': error_output}

        # This is a new slice at this aggregate.  Create Slice object and add
        # it the list of slices at this AM
        slice_object = Slice(slice_urn)
        SliceURNtoSliceObject.set_slice_object(slice_urn, slice_object)

        # Parse the request rspec.  Get back any error message from parsing
        # the rspec and a list of slivers created while parsing
        err_output, slivers = rspec_handler.parseRequestRspec(slice_object, rspec)
        if err_output != None :
            # Something went wrong.  First remove from the slice any sliver
            # objects created while parsing the bad rspec
            for sliver_object in slivers :
                slice_object.removeSliver(sliver_object)
                
            # Return an error struct.
            code = {'geni_code': config.REQUEST_PARSE_FAILED}
            return {'code': code, 'value': '', 'output': err_output}

        # Set expiration times on the allocated resources
        utils.AllocationTimesSetter(geni_slice, creds, \
                                        ('geni_end_time' in options \
                                             and \
                                             options['geni_end_time']))

        # Generate a manifest rpsec
        geni_slice.setRequestRspec(rspec)
        manifest, sliver_list = \
            rspec_handler.generateManifest(geni_slice, rspec)

        # Persist aggregate state
        self.persist_state()

        # Generate the return struct
        code = {'geni_code': config.SUCCESS}
        result_struct = {'geni_rspec': manifest, 'geni_slivers': sliver_list}
        return {'code': code, 'value': result_struct, 'output': ''}
        

    def provision(self, slice_urn, creds, options) :
        """
            For now we provision all resources allocated by a slice.  In the
            future we'll have to provision individual slivers.
        """
        # Find the slice object for this slice
        if slice_urn not in GramManager._slices :
            #  Unknown slice.  Return error message
            err_output = 'Search for slice %s failed' % slice_urn
            code = {'geni_code': config.UNKNOWN_SLICE}
            return {'code': code, 'value': '', 'output': err_output}
        geni_slice = GramManager._slices[slice_urn]    

        # Provision OpenStack Resources
        if options.has_key('geni_users'):
            users = options['geni_users']
        else :
            users = list()
        open_stack_interface.provisionResources(geni_slice, users)

        # Set operational/allocation state
        for sliver in geni_slice.getSlivers().values():
            sliver.setAllocationState(config.provisioned)
            sliver.setOperationalState(config.notready)

        # Set expiration times on the provisioned resources
        utils.ProvisionTimesSetter(geni_slice, creds, \
                                       ('geni_end_time' in options \
                                            and options['geni_end_time']))

        # Generate a manifest rpsec 
        req_rspec = geni_slice.getRequestRspec()
        manifest, sliver_list = rspec_handler.generateManifest(geni_slice,
                                                               req_rspec)
    
        # Save the manifest in the slice object.  THIS IS TEMPORARY.  WE
        # SHOULD BE GENERATING THE SLICE MANIFEST AS NEEDED
        geni_slice.setManifestRspec(manifest)

        # Persist new GramManager state
        self.persist_state()

        # Generate the return struct
        code = {'geni_code': config.SUCCESS}
        result_struct = {'geni_rspec': manifest, 'geni_slivers': sliver_list}
        return {'code': code, 'value': result_struct, 'output': ''}
        

    def describe(self, slice_urn, options) :
        """
            Describe the status of the resources allocated to this slice.
        """
        # Find the slice object
        if slice_urn not in GramManager._slices :
            config.logger.error('Asked to delete unknown slice %s' % urns[0])
            err_output = 'Search for slice %s failed' % slice_urn
            code = {'geni_code': config.UNKNOWN_SLICE}
            return {'code': code, 'value': '', 'output': err_output}
        slice_object = GramManager._slices[slice_urn]

        open_stack_interface.updateOperationalStatus(slice_object)
        
        sliver_stat_list = utils.SliverList()
        sliver_list = sliver_stat_list.getStatusAllSlivers(slice_object)

        # Generate the return struct
        code = {'geni_code': config.SUCCESS}
        result_struct = {'geni_rspec': slice_object.getManifestRspec(), \
                             'geni_slivers': sliver_list}
        return {'code': code, 'value': result_struct, 'output': ''}


    def delete(self, urns, options) :
        """
            Delete all resources held by a slice.  At this time we do 
            not support deletion of individual slivers.
        """
        config.logger.info('Delete called for slice %r' % urns)

        if urns[0] not in GramManager._slices :
            config.logger.error('Asked to delete unknown slice %s' % urns[0])
            err_output = 'Search for slice %s failed' % slice_urn
            code = {'geni_code': config.UNKNOWN_SLICE}
            return {'code': code, 'value': '', 'output': err_output}

        # We do have the slice.  Delete all resources held by the slice
        slice_object = GramManager._slices[urns[0]]
        sliver_status_list = \
            open_stack_interface.deleteAllResourcesForSlice(slice_object)

        # Remove slice from list of known slices
        del GramManager._slices[urns[0]]    

        # Persist new GramManager state
        self.persist_state()

        # Generate the return struct
        code = {'geni_code': config.SUCCESS}
        return {'code': code, 'value': sliver_status_list,  'output': ''}

    # Persist state to file based on current timestamp
    __persist_filename_format="%Y_%m_%d_%H_%M_%S"
    __recent_base_filename=None
    __base_filename_counter=0
    def persist_state(self):
        if not config.gram_snapshot_directory: return
        timestamp = time.time()
        now = time.localtime()
        base_filename = \
            time.strftime(GramManager.__persist_filename_format, now)
        counter = 0
        if base_filename==GramManager.__recent_base_filename:
            counter = GramManager.__base_filename_counter
            GramManager.__base_filename_counter = GramManager.__base_filename_counter + 1
        else:
            GramManager.__base_filename_counter=0
        filename = "%s/%s_%d.json" % (config.gram_snapshot_directory, \
                                          base_filename, counter)
        config.logger.info("Persisting state to %s" % filename)
        Archiving.write_slices(filename,GramManager. _slices)
        config.logger.info("Persisting state to %s in %.2f sec" % \
                               (filename, (time.time() - timestamp)))

    # Resolve a set of URN's to a slice and set of slivers
    # Either:
    # It is a single slice URN 
    #     (return slice and associated slivers)
    # Or it is a set of sliver URN's  
    #     (return slice and slivers for these sliver URN's)
    # Returns a slice and a list of slivers     
    def decode_urns(self, urns):
        slice = None
        slivers = list()
        if len(urns) == 1 and self._slices.has_key(urns[0]):
            # Case 1: This is a slice URN. 
            # Return slice and the urn's of the slivers
            slice_urn = urns[0]
            slice  = self._slices[slice_urn]
            slivers = slice.getSlivers().values()
        elif len(urns) > 0:
            # Case 2: This is a sliver URN.
            # Make sure they all belong to the same slice
            # And if so, return the slice and the slvers for these sliver urns
            sliver_urn = urns[0]
            slice = None
            for test_slice in self._slices.values():
                if test_slice.getSlivers().has_key(sliver_urn):
                    slice = test_slice
                    break
            if slice:
                for sliver_urn  in urns:
                    if not slice.getSlivers().has_key(sliver_urn):
                        raise ApiErrorException(AM_API.BAD_ARGS, 
                                                "Decode_URNs: All sliver " + 
                                                "URN's must be part of same slice")
                    else:
                        sliver = slice.getSlivers()[sliver_urn]
                        slivers.append(sliver)
        return slice, slivers

    def expire_slivers(self):
        # *** WRITE ME 
        pass

    def renew_slivers(self, slivers, expiration_time):
        # *** WRITE ME 
        pass

    def shutdown_slice(self, slice_urn):
        # *** WRITE ME 
        pass

    def list_flavors(self):
        return open_stack_interface._listFlavors()

    # See https://www.protogeni.net/trac/protogeni/wiki/RspecAdOpState
    def advert_header(self):
        header = '''<?xml version="1.0" encoding="UTF-8"?>
<rspec xmlns="http://www.geni.net/resources/rspec/3"
       xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
       xsi:schemaLocation="%s"
       type="advertisement">'''
        return header

    # Restore state from snapshot specified in config
    def restore_state(self):
        if config.gram_snapshot_directory is not None:
            if not os.path.exists(config.gram_snapshot_directory):
                os.makedirs(config.gram_snapshot_directory)

            # Use the specified one (if any)
            # Otherwise, use the most recent (if indicated)
            # Otherwise, no state to restore
            snapshot_file = None
            if config.recover_from_snapshot: 
                snapshot_file = config.recover_from_snapshot
            if not snapshot_file and config.recover_from_most_recent_snapshot:
                files = self.get_snapshots()
                if files and len(files) > 0:
                    snapshot_file = files[len(files)-1]

            if snapshot_file is not None:
                config.logger.info("Restoring state from snapshot : %s" \
                                       % snapshot_file)
                GramManager._slices = Archiving.read_slices(snapshot_file)
                config.logger.info("Restored %d slices" % \
                                       len(GramManager._slices))


    # Remove old snapshots, keeping only last config.snapshot_maintain_limit
    def prune_snapshots(self):
        files = self.get_snapshots()
        if files and len(files) > config.snapshot_maintain_limit:
            files_to_remove = files[0:config.snapshot_maintain_limit-1]
            for file in files_to_remove:
                os.unlink(file)

    # Return list of files in config.gam_snapshot_directory  in time
    # ascending order
    def get_snapshots(self):
        files = None
        if config.gram_snapshot_directory is not None:
            dir = config.gram_snapshot_directory
            files = [os.path.join(dir, s) for s in os.listdir(dir)
                     if os.path.isfile(os.path.join(dir, s))]
            files.sort(key = lambda s: os.path.getmtime(s))
        return files

    def __del__(self) :
        print ('In destructor')
        # open_stack_interface.cleanup(None, None)
