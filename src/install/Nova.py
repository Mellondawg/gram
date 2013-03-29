from GenericInstaller import GenericInstaller
from Configuration import Configuration

class Nova(GenericInstaller):

    nova_directory = "/etc/nova"
    api_paste_filename = "api-paste.ini"
    service_tenant_name = "service"
    config_filename = "nova.conf"
    nova_compute_filename = "nova-compute.conf"

    def __init__(self, controller_node):
        self._controller_node = controller_node
        self.nova_user = None
        self.nova_password = None
        self.quantum_user = None
        self.quantum_password = None
        self.rabbit_password = None
        self.os_password = None
        self.backup_directory = None
        self.connection = None
        self.controller_host = None

    # Return a list of command strings for installing this component
    def installCommands(self, params):
        self.nova_user = params[Configuration.ENV.NOVA_USER]
        self.nova_password = params[Configuration.ENV.NOVA_PASSWORD]
        self.quantum_user = params[Configuration.ENV.QUANTUM_USER]
        self.quantum_password = params[Configuration.ENV.QUANTUM_PASSWORD]
        self.rabbit_password = params[Configuration.ENV.RABBIT_PASSWORD]
        self.os_password = params[Configuration.ENV.OS_PASSWORD]
        self.backup_directory = params[Configuration.ENV.BACKUP_DIRECTORY]
        self.controller_host = params[Configuration.ENV.CONTROL_ADDRESS]

        self.connection = "sql_connection = mysql://" + self.nova_user + ":" +\
            self.nova_password + "@" + self.controller_host + ":3306/nova"

        if self._controller_node:
            self.installCommandsController(params)
        else:
            self.installCommandsCompute(params)

    def installCommandsController(self, params):
        self.comment("*** Nova Install (controller) ***")

        self.aptGet("nova-api nova-cert nova-common nova-scheduler python-nova python-novaclient nova-consoleauth novnc nova-novncproxy")


        self.modify_api_paste_file()

        self.backup(self.nova_directory, self.backup_directory, \
                        self.config_filename)
        nova_conf = self.nova_directory + "/" + self.config_filename

        self.writeToFile("[DEFAULT]", nova_conf)
        self.appendToFile("# MySQL Connection #", nova_conf)
        self.appendToFile(self.connection, nova_conf)
        self.appendToFile("# nova-scheduler #", nova_conf)
        self.appendToFile("rabbit_password=" + self.rabbit_password, nova_conf)
        self.appendToFile("scheduler_driver=nova.scheduler.simple.SimpleScheduler", nova_conf)
        self.appendToFile("# nova-api #", nova_conf)
        self.appendToFile("cc_host=localhost", nova_conf)
        self.appendToFile("auth_strategy=keystone", nova_conf)
        self.appendToFile("s3_host=localhost", nova_conf)
        self.appendToFile("ec2_host=localhost", nova_conf)
        self.appendToFile("nova_url=http://localhost:8774/v1.1/", nova_conf)
        self.appendToFile("ec2_url=http://localhost:8773/services/Cloud", nova_conf)
        self.appendToFile("keystone_ec2_url=http://localhost:5000/v2.0/ec2tokens", nova_conf)
        self.appendToFile("api_paste_config=/etc/nova/api-paste.ini", nova_conf)
        self.appendToFile("allow_admin_api=true", nova_conf)
        self.appendToFile("use_deprecated_auth=false", nova_conf)
        self.appendToFile("ec2_private_dns_show_ip=True", nova_conf)
        self.appendToFile("dmz_cidr=169.254.169.254/32", nova_conf)
        self.appendToFile("ec2_dmz_host=localhost", nova_conf)
        self.appendToFile("metadata_host=localhost", nova_conf)
        self.appendToFile("metadata_listen=0.0.0.0", nova_conf)
        self.appendToFile("enabled_apis=ec2,osapi_compute,metadata", nova_conf)
        self.appendToFile("# Networking #", nova_conf)
        self.appendToFile("network_api_class=nova.network.quantumv2.api.API", nova_conf)
        self.appendToFile("quantum_url=http://localhost:9696", nova_conf)
        self.appendToFile("quantum_auth_strategy=keystone", nova_conf)
        self.appendToFile("quantum_admin_tenant_name=service", nova_conf)
        self.appendToFile("quantum_admin_username=" + self.quantum_user, nova_conf)
        self.appendToFile("quantum_admin_password=" + self.os_password, nova_conf)
        self.appendToFile("quantum_admin_auth_url=http://localhost:35357/v2.0", nova_conf)
        self.appendToFile("libvirt_vif_driver=nova.virt.libvirt.vif.LibvirtHybridOVSBridgeDriver", nova_conf)
        self.appendToFile("linuxnet_interface_driver=nova.network.linux_net.LinuxOVSInterfaceDriver", nova_conf)
        self.appendToFile("firewall_driver=nova.virt.libvirt.firewall.IptablesFirewallDriver", nova_conf)
        self.appendToFile("# Cinder #", nova_conf)
        self.appendToFile("volume_api_class=nova.volume.cinder.API", nova_conf)
        self.appendToFile("# Glance #", nova_conf)
        self.appendToFile("glance_api_servers=localhost:9292", nova_conf)
        self.appendToFile("image_service=nova.image.glance.GlanceImageService", nova_conf)
        self.appendToFile("# novnc #", nova_conf)
        self.appendToFile("novnc_enable=true", nova_conf)
        self.appendToFile("novncproxy_base_url=http://localhost:6080/vnc_auto.html", nova_conf)
        self.appendToFile("vncserver_proxyclient_address=127.0.0.1", nova_conf)
        self.appendToFile("vncserver_listen=0.0.0.0", nova_conf)
        self.appendToFile("# Misc #", nova_conf)
        self.appendToFile("logdir=/var/log/nova", nova_conf)
        self.appendToFile("state_path=/var/lib/nova", nova_conf)
        self.appendToFile("lock_path=/var/lock/nova", nova_conf)
        self.appendToFile("root_helper=sudo nova-rootwrap /etc/nova/rootwrap.conf", nova_conf)
        self.appendToFile("verbose=true", nova_conf)

        self.add('nova-manage db sync')
        self.add('service nova-api restart')
        self.add('service nova-cert restart')
        self.add('service nova-consoleauth restart')
        self.add('service nova-scheduler restart')
        self.add('service novnc restart')

    def installCommandsCompute(self, params):
        self.comment("*** Nova Install (compute) ***")

        self.aptGet("nova-api-metadata nova-compute-kvm", force=True)

        self.comment("Configure NOVA")
        self.modify_api_paste_file()

        self.backup(self.nova_directory, self.backup_directory, \
                        self.nova_compute_filename)
        nova_compute_file = self.nova_directory + "/" + self.nova_compute_filename
        self.sed("s/libvirt_type.*/libvirt_type=kvm/", nova_compute_file)
        self.appendToFile("libvirt_ovs_bridge=br-int", nova_compute_file)
        self.appendToFile("libvirt_vif_type=ethernet", nova_compute_file)
        self.appendToFile("libvirt_vif_driver=nova.virt.libvirt.vif.LibvirtHybridOVSBridgeDriver", nova_compute_file)
        self.appendToFile("libvirt_use_virtio_for_bridges=True", nova_compute_file)

        self.backup(self.nova_directory, self.backup_directory, self.config_filename)
        nova_conf = self.nova_directory + "/" + self.config_filename
        self.writeToFile("[DEFAULT]", nova_conf)
        self.appendToFile("# MySQL Connection #", nova_conf)
        self.appendToFile(self.connection, nova_conf)
        self.appendToFile("rabbit_host=" + self.controller_host, nova_conf)
        self.appendToFile("rabbit_password=" + self.rabbit_password, nova_conf)
        self.appendToFile("scheduler_driver=nova.scheduler.simple.SimpleScheduler", nova_conf)
        self.appendToFile("# nova-api #", nova_conf)
        self.appendToFile("cc_host=" + self.controller_host, nova_conf)
        self.appendToFile("auth_strategy=keystone", nova_conf)
        self.appendToFile("s3_host=" + self.controller_host, nova_conf)
        self.appendToFile("ec2_host=" + self.controller_host, nova_conf)
        self.appendToFile("nova_url=http://" + self.controller_host + ":8774/v1.1/", nova_conf)
        self.appendToFile("ec2_url=http://" + self.controller_host + ":8773/services/Cloud", nova_conf)
        self.appendToFile("keystone_ec2_url=http://" + self.controller_host + ":5000/v2.0/ec2tokens", nova_conf)
        self.appendToFile("api_paste_config=/etc/nova/api-paste.ini", nova_conf)
        self.appendToFile("allow_admin_api=true", nova_conf)
        self.appendToFile("use_deprecated_auth=false", nova_conf)
        self.appendToFile("ec2_private_dns_show_ip=True", nova_conf)
        self.appendToFile("dmz_cidr=169.254.169.254/32", nova_conf)
        self.appendToFile("ec2_dmz_host=" + self.controller_host, nova_conf)
        self.appendToFile("metadata_host=" + self.controller_host, nova_conf)
        self.appendToFile("metadata_listen=0.0.0.0", nova_conf)
        self.appendToFile("enabled_apis=metadata", nova_conf)
        self.appendToFile("# Networking #", nova_conf)
        self.appendToFile("network_api_class=nova.network.quantumv2.api.API", nova_conf)
        self.appendToFile("quantum_url=http://" + self.controller_host + ":9696", nova_conf)
        self.appendToFile("quantum_auth_strategy=keystone", nova_conf)
        self.appendToFile("quantum_admin_tenant_name=service", nova_conf)
        self.appendToFile("quantum_admin_username=" + self.quantum_user, nova_conf)
        self.appendToFile("quantum_admin_password=" + self.os_password, nova_conf)
        self.appendToFile("quantum_admin_auth_url=http://" + self.controller_host + ":35357/v2.0", nova_conf)
        self.appendToFile("libvirt_vif_driver=nova.virt.libvirt.vif.LibvirtHybridOVSBridgeDriver", nova_conf)
        self.appendToFile("linuxnet_interface_driver=nova.network.linux_net.LinuxOVSInterfaceDriver", nova_conf)
        self.appendToFile("firewall_driver=nova.virt.libvirt.firewall.IptablesFirewallDriver", nova_conf)
        self.appendToFile("# Compute #", nova_conf)
        self.appendToFile("compute_driver=libvirt.LibvirtDriver", nova_conf)
        self.appendToFile("# Cinder #", nova_conf)
        self.appendToFile("volume_api_class=nova.volume.cinder.API", nova_conf)
        self.appendToFile("# Glance #", nova_conf)
        self.appendToFile("glance_api_servers=" + self.controller_host + ":9292", nova_conf)
        self.appendToFile("image_service=nova.image.glance.GlanceImageService", nova_conf)
        self.appendToFile("# novnc #", nova_conf)
        self.appendToFile("novnc_enable=true", nova_conf)
        self.appendToFile("novncproxy_base_url=http://" + self.controller_host + ":6080/vnc_auto.html", nova_conf)
        self.appendToFile("vncserver_proxyclient_address=127.0.0.1", nova_conf)
        self.appendToFile("vncserver_listen=0.0.0.0", nova_conf)
        self.appendToFile("# Misc #", nova_conf)
        self.appendToFile("logdir=/var/log/nova", nova_conf)
        self.appendToFile("state_path=/var/lib/nova", nova_conf)
        self.appendToFile("lock_path=/var/lock/nova", nova_conf)
        self.appendToFile("root_helper=sudo nova-rootwrap /etc/nova/rootwrap.conf", nova_conf)
        self.appendToFile("verbose=true", nova_conf)

        
        self.comment("Restart Nova Services")
        self.add("service nova-api-metadata restart")
        self.add("service nova-compute restart")

    # Return a list of command strings for uninstalling this component
    def uninstallCommands(self, params):
        self.nova_user = params[Configuration.ENV.NOVA_USER]
        self.nova_password = params[Configuration.ENV.NOVA_PASSWORD]
        self.rabbit_password = params[Configuration.ENV.RABBIT_PASSWORD]
        self.os_password = params[Configuration.ENV.OS_PASSWORD]
        self.backup_directory = params[Configuration.ENV.BACKUP_DIRECTORY]
        if self._controller_node:
            self.uninstallCommandsController(params)
        else:
            self.uninstallCommandsCompute(params)

    def uninstallCommandsController(self, params):
        self.comment("*** Nova Uninstall (controller) ***")

        self.aptGet("nova-api nova-cert nova-common nova-scheduler python-nova python-novaclient nova-consoleauth novnc nova-novncproxy", True)
        self.restore(self.nova_directory, self.backup_directory, \
                         self.api_paste_filename)
        self.restore(self.nova_directory, self.backup_directory, self.config_filename)

    def uninstallCommandsCompute(self, params):
        self.comment("*** Nova Uninstall (compute) ***")

        self.aptGet("nova-api-metadata nova-compute-kvm", True)
        self.restore(self.nova_directory, self.backup_directory, \
                         self.api_paste_filename)
        self.restore(self.nova_directory, self.backup_directory, \
                         self.nova_compute_filename)
        self.restore(self.nova_directory, self.backup_directory, self.config_filename)


    def modify_api_paste_file(self):
        self.backup(self.nova_directory, self.backup_directory, \
                        self.api_paste_filename)
        self.sed("s/admin_tenant_name.*/admin_tenant_name = " + \
                     self.service_tenant_name + "/", 
                 self.nova_directory + "/" + self.api_paste_filename)
        self.sed("s/admin_user.*/admin_user = " + self.nova_user + "/", 
                 self.nova_directory + "/" + self.api_paste_filename)
        self.sed("s/admin_password.*/admin_password = " + self.os_password + "/", 
                 self.nova_directory + "/" + self.api_paste_filename)
        if self._controller_node:
            self.sed("/volume/d", 
                     self.nova_directory + "/" + self.api_paste_filename)



